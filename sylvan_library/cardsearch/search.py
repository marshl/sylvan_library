"""
Running a card search from a query string
"""

import copy
import dataclasses
from collections import defaultdict
from typing import Callable, Collection, Dict, List, Optional, Set, Union

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
from sylvan_library.cards.serializers import card_prefetches
from sylvan_library.cardsearch.parameters.base_parameters import (
    CardSearchAnd,
    CardSearchContext,
    CardSearchTreeNode,
    ParameterArgs,
    QueryContext,
    QueryValidationError,
    SortKey,
)
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

    def __init__(self, card: Card, printing_ids: Collection[int]):
        """
        :param card: The card, with its printings prefetched
        :param printing_ids: The printings that can be shown, from which the newest
        non-promotional printing is picked
        """
        self.card = card
        printings = sorted(
            (p for p in card.printings.all() if p.id in printing_ids),
            key=lambda p: (p.set.release_date, -(p.numerical_number or 0)),
        )
        non_promo = [p for p in printings if p.set.type != "promo"]
        self.selected_printing: Optional[CardPrinting] = (
            (non_promo or printings)[-1] if printings else None
        )


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


def field_paths(expression: Expression) -> List[str]:
    """
    The field paths used by an expression
    """
    if isinstance(expression, F):
        return [expression.name]
    return [part.name for part in expression.flatten() if isinstance(part, F)]


def rename_fields(
    expression: Union[Expression, Q], rename: Callable[[str], str]
) -> Union[Expression, Q]:
    """
    A copy of an expression or Q object, with every field path in it renamed
    """
    if isinstance(expression, F):
        return F(rename(expression.name))
    if isinstance(expression, Q):
        clone = copy.copy(expression)
        clone.children = [
            (
                rename_fields(child, rename)
                if isinstance(child, Q)
                else (rename(child[0]), child[1])
            )
            for child in expression.children
        ]
        return clone
    clone = expression.copy()
    clone.set_source_expressions(
        [rename_fields(e, rename) for e in expression.get_source_expressions()]
    )
    return clone


def sort_value(
    key: SortKey,
    descending: bool,
    search_mode: CardSearchContext,
    matching_printings: QuerySet,
):
    """
    The value to sort each result by for a sort key. When a result has more than one
    value for the key, the lowest is used (or the highest in descending order). For cards,
    that's over their matching printings.
    """
    expression = key.expression
    if isinstance(expression, str):
        expression = F(expression)

    paths = field_paths(expression)
    if key.filter is None and all(is_single_valued(path) for path in paths):
        if search_mode == CardSearchContext.PRINTING:
            return expression
        if all(path.startswith("card__") for path in paths):
            return rename_fields(expression, lambda path: path.removeprefix("card__"))

    aggregate = Max if descending else Min
    if search_mode == CardSearchContext.PRINTING:
        return aggregate(expression, filter=key.filter)

    def on_printings(path: str) -> str:
        return "printings__" + path

    printing_filter = Q(printings__in=matching_printings)
    if key.filter is not None:
        printing_filter &= rename_fields(key.filter, on_printings)
    return aggregate(rename_fields(expression, on_printings), filter=printing_filter)


def build_queryset(
    root: CardSearchTreeNode,
    query_context: QueryContext,
    matching_printings: QuerySet,
) -> QuerySet:
    """
    The sorted queryset of results: either the matching printings, or the cards with at
    least one matching printing
    """
    if query_context.search_mode == CardSearchContext.PRINTING:
        # Filtering by id stops printings appearing once for each card face (or other
        # related row) that the query matched
        queryset = CardPrinting.objects.filter(
            id__in=matching_printings.values("id")
        ).select_related("card")
    else:
        queryset = Card.objects.filter(id__in=matching_printings.values("card_id"))

    sort_params: List[CardSortParam] = root.get_sort_parameters() + [
        CardNameSortParam(ParameterArgs(keyword="sort", operator=":", value="name"))
    ]
    ordering = []
    for sort_param in sort_params:
        for key in sort_param.get_sort_keys(query_context):
            descending = key.descending != sort_param.negated
            alias = f"sort_value_{len(ordering)}"
            value = sort_value(
                key, descending, query_context.search_mode, matching_printings
            )
            queryset = queryset.alias(**{alias: value})
            ordering.append(OrderBy(F(alias), descending=descending, nulls_last=True))

    # Cards can share a name, so these keep the order the same from one page to the next
    if query_context.search_mode == CardSearchContext.PRINTING:
        ordering += [
            F("card__scryfall_oracle_id").asc(),
            F("set__release_date").desc(),
            F("numerical_number").asc(nulls_last=True),
            F("id").asc(),
        ]
    else:
        ordering.append(F("scryfall_oracle_id").asc())
    return queryset.order_by(*ordering)


def get_results(
    page_items: List[Union[Card, CardPrinting]],
    query_context: QueryContext,
    matching_printings: QuerySet,
) -> List[SearchResult]:
    """
    The search results for one page of cards or printings
    """
    if query_context.search_mode == CardSearchContext.PRINTING:
        # Each printing has its own copy of its card, so this prefetches each card once
        cards = {printing.card_id: printing.card for printing in page_items}
        prefetch_related_objects(
            list(cards.values()), *card_prefetches(query_context.user)
        )
        return [
            SearchResult(cards[printing.card_id], [printing.id])
            for printing in page_items
        ]

    prefetch_related_objects(page_items, *card_prefetches(query_context.user))
    printing_ids: Dict[int, Set[int]] = defaultdict(set)
    for card_id, printing_id in matching_printings.filter(
        card_id__in=[card.id for card in page_items]
    ).values_list("card_id", "id"):
        printing_ids[card_id].add(printing_id)
    return [SearchResult(card, printing_ids[card.id]) for card in page_items]


def run_search(
    query_string: str,
    user: Optional[AbstractBaseUser] = None,
    page: int = 1,
    page_size: int = 25,
    search_mode: CardSearchContext = CardSearchContext.CARD,
) -> SearchOutcome:
    """
    Parses, validates and runs a search, returning one page of results
    """
    try:
        root = parse_query(query_string)
    except (ParseError, ValueError) as error:
        return SearchOutcome(results=[], count=0, page=1, num_pages=1, error=str(error))

    query_context = QueryContext(user=user, search_mode=search_mode)
    try:
        root.validate(query_context)
    except QueryValidationError as error:
        return SearchOutcome(results=[], count=0, page=1, num_pages=1, error=str(error))

    matching_printings = CardPrinting.objects.filter(root.query(query_context))
    paginator = Paginator(
        build_queryset(root, query_context, matching_printings), page_size
    )
    try:
        page_items = list(paginator.page(page))
    except EmptyPage:
        page_items = []

    return SearchOutcome(
        results=get_results(page_items, query_context, matching_printings),
        count=paginator.count,
        page=page,
        num_pages=paginator.num_pages,
        pretty_query=root.get_pretty_str(query_context),
    )
