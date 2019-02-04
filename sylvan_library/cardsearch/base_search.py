import abc

from django.core.paginator import Paginator, EmptyPage
from cardsearch.search_result import SearchResult

from cardsearch.parameters import AndParam, CardSortParam, CardNameSortParam

class PageInfo:
    def __init__(self, number, is_enabled, is_active=False, is_previous=False, is_next=False,
                 is_spacer=False):
        self.number = number
        self.enabled = is_enabled
        self.is_active = is_active
        self.is_previous = is_previous
        self.is_next = is_next
        self.is_spacer = is_spacer


class BaseSearch:
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
        queryset = self.root_parameter.query()
        self.add_sort_param(CardNameSortParam())
        ordered_query = queryset.order_by(
            *[order for sort_param in self.sort_params for order in sort_param.get_sort_list()])

        self.paginator = Paginator(ordered_query, page_size)
        try:
            self.page = self.paginator.page(page_number)
        except EmptyPage:
            return
        self.results = [SearchResult(card) for card in self.page]

    def get_page_info(self, current_page, page_span):
        page_info = [PageInfo(page_number, True,
                              is_active=page_number == current_page)
                     for page_number in self.paginator.page_range
                     if abs(page_number - current_page) <= page_span]

        # if the current page is great enough
        # put a  link to the first page at the start followed by a spacer
        if current_page - page_span > 1:
            page_info.insert(0, PageInfo(None, False, is_spacer=True))
            page_info.insert(0, PageInfo(1, True))

        if current_page + page_span <= self.paginator.num_pages - 1:
            page_info.append(PageInfo(None, False, is_spacer=True))
            page_info.append(PageInfo(self.paginator.num_pages, True))

        page_info.insert(0, PageInfo(max(current_page - 1, 1), current_page != 1, is_previous=True))
        page_info.append(PageInfo(current_page + 1,
                                  current_page != self.paginator.num_pages, is_next=True))

        return page_info

    def add_sort_param(self, sort_param: CardSortParam) -> None:
        """
        Adds a sort parameter
        :param sort_param:
        :return:
        """
        self.sort_params.append(sort_param)
