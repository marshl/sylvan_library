"""
The module for all search parameters
"""

from typing import List

from sylvan_library.cardsearch.parameters.base_parameters import (
    CardSortParam,
    CardSearchContext,
    # SearchMode,
)


class CardNameSortParam(CardSortParam):
    """
    THe sort parameter for a card's name
    """

    @classmethod
    def get_sort_keywords(cls) -> List[str]:
        return ["name"]

    @classmethod
    def get_parameter_name(cls) -> str:
        return "sort by name"

    def get_sort_keys(self, search_context: CardSearchContext) -> list:
        """
        Gets the list of attributes to be sorted by
        """
        if search_context == CardSearchContext.CARD:
            return ["name"]

        return ["card__name"]


class CardPowerSortParam(CardSortParam):
    """
    THe sort parameter for a card's numerical power
    """

    @classmethod
    def get_sort_keywords(cls) -> List[str]:
        return ["power"]

    @classmethod
    def get_parameter_name(cls) -> str:
        return "sort by power"

    def get_sort_keys(self, search_context: CardSearchContext) -> list:
        """
        Gets the list of attributes to be sorted by
        """
        if search_context == CardSearchContext.CARD:
            return ["faces__num_power"]
        return ["card__faces__num_power"]


class CardPriceSortParam(CardSortParam):
    """
    THe sort parameter for a card's latest price
    """

    @classmethod
    def get_sort_keywords(cls) -> List[str]:
        return ["price", "cost"]

    @classmethod
    def get_parameter_name(cls) -> str:
        return "sort by price"

    def get_sort_keys(self, search_context: CardSearchContext) -> list:
        """
        Gets the list of attributes to be sorted by
        """
        if search_context == CardSearchContext.CARD:
            return ["cheapest_price__paper_value"]
        return ["latest_price__paper_value"]


class CardManaValueSortParam(CardSortParam):
    """
    THe sort parameter for a card's mana value
    """

    @classmethod
    def get_sort_keywords(cls) -> List[str]:
        return ["cmc", "mv", "manavalue"]

    @classmethod
    def get_parameter_name(cls) -> str:
        return "sort by mana value"

    def get_sort_keys(self, search_context: CardSearchContext) -> list:
        """
        Gets the list of attributes to be sorted by
        """
        if search_context == CardSearchContext.CARD:
            return ["mana_value"]
        return ["card__mana_value"]


class CardCollectorNumSortParam(CardSortParam):
    """
    The sort parameter for a card's collector number
    """

    @classmethod
    def get_sort_keywords(cls) -> List[str]:
        return ["num", "number", "cnum"]

    @classmethod
    def get_parameter_name(cls) -> str:
        return "sort by number"

    def get_sort_keys(self, search_context: CardSearchContext) -> list:
        if search_context == CardSearchContext.CARD:
            return ["printings__numerical_number", "printings__number"]
        return ["numerical_number", "number"]


class CardColourSortParam(CardSortParam):
    """
    The sort parameter for a card's colour key
    """

    @classmethod
    def get_sort_keywords(cls) -> List[str]:
        return ["colour", "color"]

    @classmethod
    def get_parameter_name(cls) -> str:
        return "sort by colour"

    def get_sort_keys(self, search_context: CardSearchContext) -> List[str]:
        if search_context == CardSearchContext.CARD:
            return ["faces__colour_sort_key"]
        return ["card__faces__colour_sort_key"]


class CardRaritySortParam(CardSortParam):
    """
    The sort parameter for a card's rarity
    """

    @classmethod
    def get_sort_keywords(cls) -> List[str]:
        return ["rarity"]

    @classmethod
    def get_parameter_name(cls) -> str:
        return "sort by rarity"

    def get_sort_keys(self, search_context: CardSearchContext) -> List[str]:
        if search_context == CardSearchContext.CARD:
            return ["-printings__rarity__display_order"]
        return ["-rarity__display_order"]


class CardRandomSortParam(CardSortParam):
    """
    A "sort" parameter to order the results randomly
    This overrides get_sort_list() instead of get_sort_keys() as the "?" sort is not a column
    """

    @classmethod
    def get_sort_keywords(cls) -> List[str]:
        return ["random", "shuffle"]

    @classmethod
    def get_parameter_name(cls) -> str:
        return "sort randomly"

    def get_sort_list(self, search_context: CardSearchContext) -> List[str]:
        return ["?"]

    def get_sort_keys(self, search_context: CardSearchContext) -> List[str]:
        return ["?"]


class CardColourWeightSortParam(CardSortParam):
    """
    The sort parameter for a card's colour weight
    """

    @classmethod
    def get_sort_keywords(cls) -> List[str]:
        return ["cweight", "cw", "colourweight"]

    @classmethod
    def get_parameter_name(cls) -> str:
        return "sort by colour weight"

    def get_sort_keys(self, search_context: CardSearchContext) -> list:
        if search_context == CardSearchContext.CARD:
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


class CardReleaseDateSortParam(CardSortParam):
    @classmethod
    def get_sort_keywords(cls) -> List[str]:
        return ["date", "release_date"]

    @classmethod
    def get_parameter_name(cls) -> str:
        return "sort by release date"

    def get_sort_keys(self, search_context: CardSearchContext) -> List[str]:
        if search_context == CardSearchContext.CARD:
            return ["printings__set__release_date"]
        return ["set__release_date"]


class CardSuperKeySortParam(CardSortParam):
    @classmethod
    def get_sort_keywords(cls) -> List[str]:
        return ["key", "superkey"]

    @classmethod
    def get_parameter_name(cls) -> str:
        return "sort by super key"

    def get_sort_keys(self, search_context: CardSearchContext) -> List[str]:
        if search_context == CardSearchContext.CARD:
            return ["search_metadata__super_sort_key"]
        return ["card__search_metadata__super_sort_key"]
