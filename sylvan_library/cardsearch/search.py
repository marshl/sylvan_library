"""
Running a card search from a query string
"""

import copy
import dataclasses
from typing import List, Optional, Union

from django.contrib.auth.models import AbstractBaseUser
from django.core.paginator import EmptyPage, Paginator
from django.db.models import (
    Expression,
    F,
    Max,
    Min,
    OrderBy,
    Q,
    QuerySet,
    prefetch_related_objects,
)

from sylvan_library.cards.models.card import Card, CardPrinting
from sylvan_library.cards.models.sets import Set
from sylvan_library.cards.serializers import card_prefetches
from sylvan_library.cardsearch.parameters.base_parameters import (
    CardSearchAnd,
    CardSearchBranchNode,
    CardSearchContext,
    CardSearchTreeNode,
    ParameterArgs,
    QueryContext,
    QueryValidationError,
    SortKey,
)
from sylvan_library.cardsearch.parameters.card_set_parameters import CardSetParam
from sylvan_library.cardsearch.parameters.sort_parameters import (
    CardNameSortParam,
    CardSortParam,
)
from sylvan_library.cardsearch.parser.base_parser import ParseError
from sylvan_library.cardsearch.parser.query_parser import CardQueryParser


class SearchResult:
    """
    A single search result: the card and which of its printings to show
    """

    def __init__(self, card: Card, selected_set: Optional[Set] = None):
        self.card = card
        printings = list(card.printings.all())
        self.selected_printing: Optional[CardPrinting] = next(
            (p for p in printings if selected_set and p.set == selected_set), None
        )
        if not self.selected_printing and printings:
            sorted_printings = sorted(
                printings,
                key=lambda p: (p.set.release_date, -(p.numerical_number or 0)),
            )
            # Prefer non-promotional printings if there are any
            non_promo = [p for p in sorted_printings if p.set.type != "promo"]
            self.selected_printing = (non_promo or sorted_printings)[-1]


@dataclasses.dataclass
class SearchOutcome:
    """
    What a search found, or why it couldn't run
    """

    results: List[SearchResult]
    count: int
    page: int
    num_pages: int
    pretty_query: Optional[str] = None
    error: Optional[str] = None


def parse_query(query_string: str) -> CardSearchTreeNode:
    """
    Parses a query string into a parameter tree. An empty query matches every card.
    Raises ParseError or ValueError if the query can't be parsed.
    """
    if not query_string:
        return CardSearchAnd()
    return CardQueryParser().parse(query_string)


def get_preferred_set(root: CardSearchTreeNode) -> Optional[Set]:
    """
    The set searched for at the top level of the query, if there is one, so results
    can show their printing from that set
    """
    if isinstance(root, CardSetParam):
        return root.set_obj
    if isinstance(root, CardSearchBranchNode):
        for child in root.child_parameters:
            if isinstance(child, CardSetParam):
                return child.set_obj
    return None


def is_single_valued(path: str) -> bool:
    """
    Whether a field path from CardPrinting leads to only one value for each printing
    """
    model = CardPrinting
    for name in path.split("__"):
        field = model._meta.get_field(name)
        if field.one_to_many or field.many_to_many:
            return False
        if not field.is_relation:
            break
        model = field.related_model
    return True


def with_prefix(expression: Union[str, Expression, Q], prefix: str):
    """
    A copy of a field path, expression or Q object, with every field path in it prefixed
    """
    if isinstance(expression, str):
        return prefix + expression
    if isinstance(expression, F):
        return F(prefix + expression.name)
    if isinstance(expression, Q):
        clone = copy.copy(expression)
        clone.children = [
            (
                with_prefix(child, prefix)
                if isinstance(child, Q)
                else (prefix + child[0], child[1])
            )
            for child in expression.children
        ]
        return clone
    clone = expression.copy()
    clone.set_source_expressions(
        [with_prefix(e, prefix) for e in expression.get_source_expressions()]
    )
    return clone


def card_sort_value(key: SortKey, descending: bool, matching_printings: QuerySet):
    """
    The value to sort each card by for a sort key. Card fields are used as they are, and
    anything else is summarised over the card's matching printings.
    """
    expression = key.expression
    if isinstance(expression, str):
        if (
            expression.startswith("card__")
            and key.filter is None
            and is_single_valued(expression)
        ):
            return F(expression.removeprefix("card__"))
    elif not any(isinstance(part, F) for part in expression.flatten()):
        # Doesn't depend on any field, like a random sort
        return expression

    printing_filter = Q(printings__in=matching_printings)
    if key.filter is not None:
        printing_filter &= with_prefix(key.filter, "printings__")
    aggregate = Max if descending else Min
    return aggregate(with_prefix(expression, "printings__"), filter=printing_filter)


def build_queryset(root: CardSearchTreeNode, query_context: QueryContext) -> QuerySet:
    """
    The sorted queryset of cards with at least one printing that matches the parameter
    tree
    """
    printings = CardPrinting.objects.filter(root.query(query_context))
    queryset = Card.objects.filter(id__in=printings.values("card_id"))

    sort_params: List[CardSortParam] = root.get_sort_parameters() + [
        CardNameSortParam(ParameterArgs(keyword="sort", operator=":", value="name"))
    ]
    ordering = []
    for sort_param in sort_params:
        for key in sort_param.get_sort_keys(query_context):
            descending = key.descending != sort_param.negated
            alias = f"sort_value_{len(ordering)}"
            queryset = queryset.alias(
                **{alias: card_sort_value(key, descending, printings)}
            )
            ordering.append(OrderBy(F(alias), descending=descending, nulls_last=True))
    # Cards can share a name, so this keeps the order the same from one page to the next
    ordering.append(F("scryfall_oracle_id").asc())
    return queryset.order_by(*ordering)


def run_search(
    query_string: str,
    user: Optional[AbstractBaseUser] = None,
    page: int = 1,
    page_size: int = 25,
) -> SearchOutcome:
    """
    Parses, validates and runs a search, returning one page of results
    """
    try:
        root = parse_query(query_string)
    except (ParseError, ValueError) as error:
        return SearchOutcome(results=[], count=0, page=1, num_pages=1, error=str(error))

    query_context = QueryContext(user=user, search_mode=CardSearchContext.CARD)
    try:
        root.validate(query_context)
    except QueryValidationError as error:
        return SearchOutcome(results=[], count=0, page=1, num_pages=1, error=str(error))

    paginator = Paginator(build_queryset(root, query_context), page_size)
    try:
        cards = list(paginator.page(page))
    except EmptyPage:
        cards = []
    prefetch_related_objects(cards, *card_prefetches(user))

    preferred_set = get_preferred_set(root)
    return SearchOutcome(
        results=[SearchResult(card, selected_set=preferred_set) for card in cards],
        count=paginator.count,
        page=page,
        num_pages=paginator.num_pages,
        pretty_query=root.get_pretty_str(query_context),
    )
