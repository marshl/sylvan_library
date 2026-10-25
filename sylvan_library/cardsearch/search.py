"""
Running a card search from a query string
"""

import dataclasses
from typing import List, Optional

from django.contrib.auth.models import AbstractBaseUser
from django.core.paginator import EmptyPage, Paginator
from django.db.models import QuerySet, prefetch_related_objects

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


def build_queryset(root: CardSearchTreeNode, query_context: QueryContext) -> QuerySet:
    """
    The sorted queryset of cards that match the parameter tree
    """
    query = root.query(query_context)
    sort_params: List[CardSortParam] = root.get_sort_parameters() + [
        CardNameSortParam(ParameterArgs(keyword="sort", operator=":", value="name"))
    ]

    distinct_fields = [
        key.strip("-")
        for sort_param in sort_params
        for key in sort_param.get_sort_keys(CardSearchContext.CARD)
    ]
    if "name" in distinct_fields:
        distinct_fields.append("scryfall_oracle_id")

    if query_context.search_mode == CardSearchContext.CARD:
        queryset = Card.objects.filter(query)
    else:
        queryset = Card.objects.filter(printings__in=CardPrinting.objects.filter(query))

    if "?" not in distinct_fields:
        queryset = queryset.distinct(*distinct_fields)

    for sort_param in sort_params:
        queryset = sort_param.annotate_queryset(
            queryset, search_context=CardSearchContext.CARD
        )

    return queryset.order_by(
        *[
            order
            for sort_param in sort_params
            for order in sort_param.get_sort_list(CardSearchContext.CARD)
        ]
    )


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

    query_context = QueryContext(
        user=user, search_mode=root.get_default_search_context()
    )
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
