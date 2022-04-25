"""
The module for all search parameters
"""
from enum import Enum
from typing import List

from django.db.models import F


class SearchMode(Enum):
    SEARCH_MODE_CARD = "SEARCH_MODE_CARD"
    SEARCH_MODE_PRINTING = "SEARCH_MODE_PRINTING"


class CardSortParam:
    """
    The base sorting parameter
    """

    def __init__(self, negated: bool = False):
        super().__init__()
        self.negated = negated

    def get_sort_list(self, search_mode: SearchMode) -> List[str]:
        """
        Gets the sort list taking order into account
        :return:
        """
        sort_keys = self.get_sort_keys(search_mode)
        return [
            F(key).desc(nulls_last=True)
            if self.negated
            else F(key).asc(nulls_last=True)
            for key in sort_keys
        ]

    def get_sort_keys(self, search_mode: SearchMode) -> List[str]:
        """
        Gets the list of attributes to be sorted by
        :return:
        """
        raise NotImplementedError()


class CardNameSortParam(CardSortParam):
    """
    THe sort parameter for a card's name
    """

    def get_sort_keys(self, search_mode: SearchMode) -> list:
        """
        Gets the list of attributes to be sorted by
        """
        if search_mode == SearchMode.SEARCH_MODE_CARD:
            return ["name"]

        return ["card__name"]


class CardPowerSortParam(CardSortParam):
    """
    THe sort parameter for a card's numerical power
    """

    def get_sort_keys(self, search_mode: SearchMode) -> list:
        """
        Gets the list of attributes to be sorted by
        """
        if search_mode == SearchMode.SEARCH_MODE_CARD:
            return ["faces__num_power"]
        return ["card__faces__num_power"]


class CardPriceSortParam(CardSortParam):
    """
    THe sort parameter for a card's latest price
    """

    def get_sort_keys(self, search_mode: SearchMode) -> list:
        """
        Gets the list of attributes to be sorted by
        """
        if search_mode == SearchMode.SEARCH_MODE_CARD:
            return ["printings__latest_price__paper_value"]
        return ["latest_price__paper_value"]


class CardManaValueSortParam(CardSortParam):
    """
    THe sort parameter for a card's mana value
    """

    def get_sort_keys(self, search_mode: SearchMode) -> list:
        """
        Gets the list of attributes to be sorted by
        """
        if search_mode == SearchMode.SEARCH_MODE_CARD:
            return ["mana_value", "faces__colour_weight"]
        return ["card__mana_value", "card__colour_weight"]


class CardCollectorNumSortParam(CardSortParam):
    """
    The sort parameter for a card's collector number
    """

    def get_sort_keys(self, search_mode: SearchMode) -> list:
        if search_mode == SearchMode.SEARCH_MODE_CARD:
            return ["printings__numerical_number", "printings__number"]
        return ["numerical_number", "number"]


class CardColourSortParam(CardSortParam):
    """
    The sort parameter for a card's colour key
    """

    def get_sort_keys(self, search_mode: SearchMode) -> List[str]:
        if search_mode == SearchMode.SEARCH_MODE_CARD:
            return ["faces__colour_sort_key"]
        return ["card__faces__colour_sort_key"]


class CardColourWeightSortParam(CardSortParam):
    """
    The sort parameter for a card's colour weight
    """

    def get_sort_keys(self, search_mode: SearchMode) -> list:
        if search_mode == SearchMode.SEARCH_MODE_CARD:
            return [
                "mana_value",
                "faces__colour_sort_key",
                "faces__colour_weight",
            ]
        return [
            "card__mana_value",
            "card__faces__colour_sort_key",
            "card__faces__colour_weight",
        ]
