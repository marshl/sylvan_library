"""
The module for the base search classes
"""
from typing import List, Optional

from django.core.paginator import Paginator, EmptyPage
from django.db.models import prefetch_related_objects, QuerySet

from cardsearch.parameters import (
    CardSortParam,
    CardNameSortParam,
    CardColourSortParam,
    CardPowerSortParam,
    AndParam,
    OrParam,
    BranchParam,
    SearchMode,
)

from cards.models import Card, CardPrinting, Set


# pylint: disable=too-few-public-methods
class SearchResult:
    """
    A single search result including the card and it's selected printing
    """

    def __init__(
        self,
        card: Card,
        selected_printing: CardPrinting = None,
        selected_set: Set = None,
    ):
        self.card = card
        self.selected_printing = selected_printing

        if self.card and selected_set and not self.selected_printing:
            self.selected_printing = next(
                (p for p in self.card.printings.all() if p.set == selected_set), None
            )

        if self.card and not self.selected_printing:
            sorted_printings = sorted(
                self.card.printings.all(), key=lambda x: x.set.release_date
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

    def is_planeswalker(self) -> bool:
        """
        Returns true if this card result is a planeswalker card
        :return: True if this result is a planeswalker, otherwise False
        """
        return self.card.type and "Planeswalker" in self.card.type

    def is_saga(self) -> bool:
        """
        Returns true if this card result is an Enchantment - Saga
        :return: True if this result is a saga, otherwise False
        """
        return bool(self.card.subtype and "Saga" in self.card.subtype)

    def can_rotate(self) -> bool:
        """
        Returns whether or not this card should have be able to rotate its image
        :return: True if this card can rotate, otherwise False
        """
        return self.card.layout in ("split", "aftermath", "planar")


def create_colour_param(
    colour_params: List[int],
    param_class: type,
    match_colours: bool,
    exclude_colours: bool,
) -> AndParam:
    """
    Creates a series of colour parameters based on the given colours
    :param colour_params: A list of bits flags that should be searched for
    :param param_class: The colour parameter class (either Colour of ColourIdentity)
    :param match_colours: Whether the colours should match exactly or not
    :param exclude_colours: Whether unselected colours should be excluded or not
    :return: A root AndParam with a series of colour parameters underneath
    """
    root_param = AndParam()
    if match_colours:
        colour_root = AndParam()
    else:
        colour_root = OrParam()
    root_param.add_parameter(colour_root)

    for colour in colour_params:
        colour_root.add_parameter(param_class(colour))

    if exclude_colours:
        exclude_param = OrParam()
        exclude_param.negated = True
        for colour in [c for c in Card.colour_flags.values() if c not in colour_params]:
            param = param_class(colour)
            exclude_param.add_parameter(param)

        if exclude_param.child_parameters:
            root_param.add_parameter(exclude_param)

    return root_param


class BaseSearch:
    """
    The core searching object. This can be extended to have different fields, but they should
    all use a single root node with parameters haning off of it
    """

    def __init__(self) -> None:
        self.root_parameter: BranchParam = AndParam()
        self.sort_params: List[CardSortParam] = []
        self.paginator: Optional[Paginator] = None
        self.results: List[SearchResult] = []
        self.page: Optional[int] = None

    # pylint: disable=no-self-use
    def build_parameters(self) -> None:
        """
        Build the parameters tree for this search object
        """
        raise NotImplementedError()

    def get_queryset(self) -> QuerySet:
        """
        Gets the queryset of the search
        :return: The search queryset
        """
        query = self.root_parameter.query()
        queryset = CardPrinting.objects.filter(query).distinct()
        # TODO: Need to handle printing and card searches separately somehow
        queryset = Card.objects.filter(printings__in=queryset).distinct()
        # print(str(queryset.query))
        # Add some default sort params to ensure stable ordering
        self.add_sort_param(CardNameSortParam())
        # self.add_sort_param(CardColourSortParam())
        # self.add_sort_param(CardPowerSortParam())

        queryset = queryset.order_by(
            *[
                order
                for sort_param in self.sort_params
                for order in sort_param.get_sort_list(SearchMode.SEARCH_MODE_CARD)
            ]
        )
        return queryset
        queryset = queryset.distinct()
        # card_ids = queryset.values_list("card", flat=True)
        # queryset = Card.objects.filter(id__in=card_ids)
        queryset = Card.objects.filter(printings__in=queryset)  # .distinct()
        # queryset = queryset.select_related("card")

    def search(self, page_number: int = 1, page_size: int = 25) -> None:
        """
        Runs the search for this search and constructs
        :param page_number: The result page
        :param page_size: The number of items per page
        """
        queryset = self.get_queryset()
        print(str(queryset.query))
        self.paginator = Paginator(queryset, page_size)
        try:
            self.page = self.paginator.page(page_number)
        except EmptyPage:
            return
        cards = list(self.page)
        prefetch_related_objects(cards, "printings__face_printings")
        prefetch_related_objects(cards, "printings__localisations__ownerships")
        prefetch_related_objects(cards, "printings__localisations__language")
        prefetch_related_objects(cards, "printings__localisations__localised_faces")
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

    def add_sort_param(self, sort_param: CardSortParam) -> None:
        """
        Adds a sort parameter
        :param sort_param:
        :return:
        """
        self.sort_params.append(sort_param)

    def get_pretty_str(self) -> str:
        """
        Gets the human readable version of the search query
        :return: The human readable string
        """
        return self.root_parameter.get_pretty_str()
