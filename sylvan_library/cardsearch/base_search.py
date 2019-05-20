"""
The module for the base search classes
"""
from typing import List, Optional
from bitfield.types import Bit

from django.core.paginator import Paginator, EmptyPage
from django.db.models import prefetch_related_objects

from cardsearch.parameters import (
    CardSortParam,
    CardNameSortParam,
    CardColourSortParam,
    CardPowerSortParam,
    AndParam,
    OrParam,
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
            self.selected_printing = sorted(
                self.card.printings.all(), key=lambda x: x.set.release_date
            )[-1]

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


def create_colour_param(
    colour_params: List[Bit],
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
        exclude_param = OrParam(inverse=True)
        root_param.add_parameter(exclude_param)
        for colour in [c for c in Card.colour_flags.values() if c not in colour_params]:
            param = param_class(colour)
            exclude_param.add_parameter(param)

    return root_param


class BaseSearch:
    """
    The core searching object. This can be extended to have different fields, but they should
    all use a single root node with parameters haning off of it
    """

    def __init__(self):
        self.root_parameter = AndParam()
        self.sort_params = list()
        self.paginator = None
        self.results = []
        self.page = None

    # pylint: disable=no-self-use
    def build_parameters(self):
        """
        Build the parameters tree for this search object
        :return:
        """
        return

    def search(self, page_number: int = 1, page_size: int = 25):
        """
        Runs the search for this search and constructs
        :param page_number: The result page
        :param page_size: The number of items per page
        """
        queryset = Card.objects.filter(self.root_parameter.query()).distinct()
        self.add_sort_param(CardNameSortParam())
        self.add_sort_param(CardColourSortParam())
        self.add_sort_param(CardPowerSortParam())
        queryset = queryset.order_by(
            *[
                order
                for sort_param in self.sort_params
                for order in sort_param.get_sort_list()
            ]
        )

        self.paginator = Paginator(queryset, page_size)
        try:
            self.page = self.paginator.page(page_number)
        except EmptyPage:
            return
        cards = list(self.page)
        prefetch_related_objects(
            cards, "printings__printed_languages__physical_cards__ownerships"
        )
        prefetch_related_objects(cards, "printings__printed_languages__language")
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
