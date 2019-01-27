import abc

from django.core.paginator import Paginator
from cardsearch.search_result import SearchResult
from django.db.models.query import QuerySet

from cardsearch.parameters import AndParam, CardSortParam, CardNameSortParam

from typing import List


class BaseSearch:
    __metaclass__ = abc.ABCMeta

    def __init__(self):
        self.root_parameter = AndParam()
        self.sort_params = list()

    @abc.abstractmethod
    def build_parameters(self):
        return

    def get_results(self, page_number: int = 1, page_size: int = 25) -> List[SearchResult]:
        queryset = self.root_parameter.query()
        paginator = Paginator(queryset, page_size)
        page = paginator.page(page_number)
        results = [SearchResult(card) for card in page]
        return results

    def add_sort_param(self, sort_param: CardSortParam) -> None:
        """
        Adds a sort parameter
        :param sort_param:
        :return:
        """
        self.sort_params.append(sort_param)

    def result_search(self) -> QuerySet:
        """
        Creates and returns the search tree
        :return:
        """
        result = self.root_parameter.query()
        self.add_sort_param(CardNameSortParam())
        result = result.order_by(
            *[order for sort_param in self.sort_params for order in sort_param.get_sort_list()])
        return result
