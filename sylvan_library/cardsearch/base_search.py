"""
The module for the base search classes
"""
import abc
from typing import List
from bitfield.types import Bit

from django.core.paginator import Paginator, EmptyPage
from django.db.models import prefetch_related_objects

from cardsearch.parameters import (
    CardSortParam,
    CardNameSortParam,
    AndParam,
    OrParam,
)

from cards.models import (
    Card,
    CardPrinting,
    Set,
)


class PageButton:
    """
    Information about a single page button
    """

    def __init__(self, number, is_enabled, is_active=False, is_previous=False, is_next=False,
                 is_spacer=False):
        self.number = number
        self.enabled = is_enabled
        self.is_active = is_active
        self.is_previous = is_previous
        self.is_next = is_next
        self.is_spacer = is_spacer


class SearchResult:
    """
    A single search result including the card and it's selected printing
    """

    def __init__(self, card: Card, selected_printing: CardPrinting = None,
                 selected_set: Set = None):
        self.card = card
        self.selected_printing = selected_printing

        if self.card and selected_set and not self.selected_printing:
            self.selected_printing = self.card.printings.filter(set=selected_set).first()

        if self.card and not self.selected_printing:
            self.selected_printing = self.card.printings.order_by('set__release_date').last()

        assert self.selected_printing is None or self.card is None \
               or self.selected_printing in self.card.printings.all()


class BaseSearch:
    """
    The core searching object. This can be extended to have different fields, but they should
    all use a single root node with parameters haning off of it
    """
    __metaclass__ = abc.ABCMeta

    def __init__(self):
        self.root_parameter = AndParam()
        self.sort_params = list()
        self.paginator = None
        self.results = []
        self.page = None

    @abc.abstractmethod
    def build_parameters(self):
        return

    def search(self, page_number: int = 1, page_size: int = 25) -> None:
        queryset = Card.objects.filter(self.root_parameter.query())
        self.add_sort_param(CardNameSortParam())
        queryset = queryset.order_by(
            *[order for sort_param in self.sort_params for order in sort_param.get_sort_list()])

        self.paginator = Paginator(queryset, page_size)
        try:
            self.page = self.paginator.page(page_number)
        except EmptyPage:
            return
        cards = list(self.page)
        prefetch_related_objects(cards, 'printings__printed_languages__physical_cards__ownerships')
        prefetch_related_objects(cards, 'printings__printed_languages__language')
        prefetch_related_objects(cards, 'printings__set')
        prefetch_related_objects(cards, 'printings__rarity')

        self.results = [SearchResult(card) for card in cards]

    def get_page_info(self, current_page, page_span):
        page_info = [PageButton(page_number, True, is_active=page_number == current_page)
                     for page_number in self.paginator.page_range
                     if abs(page_number - current_page) <= page_span]

        # if the current page is great enough
        # put a  link to the first page at the start followed by a spacer
        if current_page - page_span > 1:
            page_info.insert(0, PageButton(None, False, is_spacer=True))
            page_info.insert(0, PageButton(1, True))

        if current_page + page_span <= self.paginator.num_pages - 1:
            page_info.append(PageButton(None, False, is_spacer=True))
            page_info.append(PageButton(self.paginator.num_pages, True))

        page_info.insert(0,
                         PageButton(max(current_page - 1, 1), current_page != 1, is_previous=True))
        page_info.append(PageButton(current_page + 1,
                                    current_page != self.paginator.num_pages, is_next=True))

        return page_info

    def add_sort_param(self, sort_param: CardSortParam) -> None:
        """
        Adds a sort parameter
        :param sort_param:
        :return:
        """
        self.sort_params.append(sort_param)

    def create_colour_param(self, colour_params: List[Bit], param_class: type, match_colours: bool,
                            exclude_colours: bool):
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
