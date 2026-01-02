"""
The module for the base search classes
"""

from typing import List, Optional

from django.contrib.auth import get_user_model
from django.core.paginator import Paginator, EmptyPage
from django.db.models import prefetch_related_objects, QuerySet

from sylvan_library.cards.models.card import CardPrinting, Card
from sylvan_library.cards.models.sets import Set

from sylvan_library.cardsearch.parameters.base_parameters import (
    CardSearchAnd,
    CardSearchBranchNode,
    QueryContext,
    ParameterArgs,
    CardSearchContext,
)
from sylvan_library.cardsearch.parameters.sort_parameters import (
    CardSortParam,
    CardNameSortParam,
)

User = get_user_model()


class SearchResult:
    """
    A single search result including the card and its selected printing
    """

    def __init__(
        self,
        card: Card,
        selected_printing: Optional[CardPrinting] = None,
        selected_set: Optional[Set] = None,
    ):
        self.card = card
        self.selected_printing = selected_printing

        if self.card and selected_set and not self.selected_printing:
            self.selected_printing = next(
                (p for p in self.card.printings.all() if p.set == selected_set), None
            )

        if self.card and not self.selected_printing:
            sorted_printings = sorted(
                self.card.printings.all(),
                key=lambda x: (x.set.release_date, -x.numerical_number),
            )
            # Prefer non-promotional cards if possible
            non_promo_prints = [p for p in sorted_printings if p.set.type != "promo"]
            if non_promo_prints:
                self.selected_printing = non_promo_prints[-1]
            else:
                self.selected_printing = sorted_printings[-1]

        assert (
            self.selected_printing is None
            or self.card is None
            or self.selected_printing in self.card.printings.all()
        )

    def can_rotate(self) -> bool:
        """
        Returns whether this card should be able to rotate its image
        :return: True if this card can rotate, otherwise False
        """
        return self.card.layout in ("split", "aftermath", "planar")


class BaseSearch:
    """
    The core searching object. This can be extended to have different fields, but they should
    all use a single root node with parameters hanging off of it
    """

    def __init__(self, user: User = None) -> None:
        self.user: User = user
        self.root_parameter: CardSearchBranchNode = CardSearchAnd()
        self.sort_params: List[CardSortParam] = []
        self.paginator: Optional[Paginator] = None
        self.results: List[SearchResult] = []
        self.page: Optional[int] = None

    def build_parameters(self) -> None:
        """
        Build the parameters tree for this search object
        """
        raise NotImplementedError()

    def get_queryset(self, query_context: QueryContext) -> QuerySet:
        """
        Gets the queryset of the search
        :return: The search queryset
        """
        query = self.root_parameter.query(query_context)
        print(query)
        self.sort_params.append(
            CardNameSortParam(
                param_args=ParameterArgs(keyword="sort", operator=":", value="name"),
            )
        )

        distinct_fields = [
            k.strip("-")
            for p in self.sort_params
            for k in p.get_sort_keys(CardSearchContext.CARD)
        ]
        if "name" in distinct_fields:
            # idx = distinct_fields.index("name")
            # distinct_fields.remove("name")
            distinct_fields.append("scryfall_oracle_id")

        if query_context.search_mode == CardSearchContext.CARD:
            queryset = Card.objects.filter(query)
            print(str(queryset.query))
        else:
            queryset = CardPrinting.objects.filter(query)  # .distinct()
            print(str(queryset.query))
            queryset = Card.objects.filter(printings__in=queryset)

        if "?" not in distinct_fields:
            queryset = queryset.distinct(*distinct_fields)

        queryset = queryset.order_by(
            *[
                order
                for sort_param in self.sort_params
                for order in sort_param.get_sort_list(CardSearchContext.CARD)
            ]
        )
        return queryset

    def search(
        self, query_context: QueryContext, page_number: int = 1, page_size: int = 25
    ) -> None:
        """
        Runs the search for this search and constructs
        :param page_number: The result page
        :param page_size: The number of items per page
        """
        queryset = self.get_queryset(query_context)
        print(str(queryset.query))
        self.paginator = Paginator(queryset, page_size)
        try:
            self.page = self.paginator.page(page_number)
        except EmptyPage:
            return
        cards = list(self.page)

        prefetch_related_objects(cards, "printings__localisations__ownerships")
        prefetch_related_objects(cards, "printings__localisations__language")
        prefetch_related_objects(
            cards, "printings__localisations__localised_faces__image"
        )
        prefetch_related_objects(
            cards, "printings__face_printings__localised_faces__image"
        )
        prefetch_related_objects(
            cards, "printings__face_printings__localised_faces__localisation"
        )
        prefetch_related_objects(cards, "faces")
        prefetch_related_objects(cards, "printings__set")
        prefetch_related_objects(cards, "printings__rarity")

        preferred_set = self.get_preferred_set()
        self.results = [
            SearchResult(card, selected_set=preferred_set) for card in cards
        ]

    def get_preferred_set(self) -> Optional[Set]:
        """
        Gets the set that would be preferred for each card result (this should be overridden)
        :return:
        """
        raise NotImplementedError()

    def get_pretty_str(self, query_context: QueryContext) -> str:
        """
        Gets the human readable version of the search query
        :return: The human readable string
        """
        return self.root_parameter.get_pretty_str(query_context)
