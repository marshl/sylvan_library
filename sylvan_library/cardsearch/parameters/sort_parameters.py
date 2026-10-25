"""
The module for all search parameters
"""

from typing import List

from django.db.models import F, Q
from django.db.models.functions import Coalesce, Random

from sylvan_library.cardsearch.parameters.base_parameters import (
    CardSearchContext,
    CardSortParam,
    QueryContext,
    SortKey,
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

    def get_sort_keys(self, query_context: QueryContext) -> List[SortKey]:
        return [SortKey("card__name")]


class CardPowerSortParam(CardSortParam):
    """
    THe sort parameter for a card's numerical power. Cards without a power go last.
    """

    @classmethod
    def get_sort_keywords(cls) -> List[str]:
        return ["power"]

    @classmethod
    def get_parameter_name(cls) -> str:
        return "sort by power"

    def get_sort_keys(self, query_context: QueryContext) -> List[SortKey]:
        return [
            SortKey(
                "card__faces__num_power", filter=Q(card__faces__power__isnull=False)
            )
        ]


class CardPriceSortParam(CardSortParam):
    """
    The sort parameter for price: the cheapest printing of each card, or each printing's
    latest price. Most expensive first, unless it's reversed.
    """

    @classmethod
    def get_sort_keywords(cls) -> List[str]:
        return ["price", "cost"]

    @classmethod
    def get_parameter_name(cls) -> str:
        return "sort by price"

    def get_sort_keys(self, query_context: QueryContext) -> List[SortKey]:
        if query_context.search_mode == CardSearchContext.CARD:
            return [SortKey("card__cheapest_price__paper_value", descending=True)]
        return [SortKey("latest_price__paper_value", descending=True)]


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

    def get_sort_keys(self, query_context: QueryContext) -> List[SortKey]:
        return [SortKey("card__mana_value")]


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

    def get_sort_keys(self, query_context: QueryContext) -> List[SortKey]:
        return [SortKey("numerical_number"), SortKey("number")]


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

    def get_sort_keys(self, query_context: QueryContext) -> List[SortKey]:
        return [SortKey("card__faces__colour_sort_key")]


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

    def get_sort_keys(self, query_context: QueryContext) -> List[SortKey]:
        return [SortKey("rarity__display_order", descending=True)]


class CardRandomSortParam(CardSortParam):
    """
    A "sort" parameter to order the results randomly
    """

    @classmethod
    def get_sort_keywords(cls) -> List[str]:
        return ["random", "shuffle"]

    @classmethod
    def get_parameter_name(cls) -> str:
        return "sort randomly"

    def get_sort_keys(self, query_context: QueryContext) -> List[SortKey]:
        return [SortKey(Random())]


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

    def get_sort_keys(self, query_context: QueryContext) -> List[SortKey]:
        return [
            SortKey("card__mana_value"),
            SortKey("card__faces__colour_sort_key"),
            SortKey("card__faces__colour_weight"),
        ]


class CardReleaseDateSortParam(CardSortParam):
    @classmethod
    def get_sort_keywords(cls) -> List[str]:
        return ["date", "release_date"]

    @classmethod
    def get_parameter_name(cls) -> str:
        return "sort by release date"

    def get_sort_keys(self, query_context: QueryContext) -> List[SortKey]:
        return [SortKey(Coalesce(F("original_release_date"), F("set__release_date")))]


class CardSuperKeySortParam(CardSortParam):
    @classmethod
    def get_sort_keywords(cls) -> List[str]:
        return ["key", "superkey"]

    @classmethod
    def get_parameter_name(cls) -> str:
        return "sort by super key"

    def get_sort_keys(self, query_context: QueryContext) -> List[SortKey]:
        return [SortKey("card__search_metadata__super_sort_key")]


class CardOwnershipSortParam(CardSortParam):
    @classmethod
    def get_sort_keywords(cls) -> List[str]:
        return ["bought", "owned"]

    @classmethod
    def get_parameter_name(cls) -> str:
        return "sort by date first owned"

    def get_sort_keys(self, query_context: QueryContext) -> List[SortKey]:
        return [
            SortKey(
                "localisations__user_changes__date",
                filter=Q(localisations__user_changes__owner=query_context.user),
            )
        ]
