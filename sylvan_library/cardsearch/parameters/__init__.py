"""
The module for all search parameters
"""
from typing import List

from .base_parameters import OrParam, AndParam, CardSearchParam, BranchParam
from .card_colour_parameters import (
    CardComplexColourParam,
    CardColourParam,
    CardColourIdentityParam,
    CardMulticolouredOnlyParam,
)
from .card_mana_cost_parameters import (
    CardManaCostComplexParam,
    CardCmcParam,
    CardManaCostParam,
    CardColourCountParam,
)
from .card_misc_parameters import (
    CardIsReprintParam,
    CardHasWatermarkParam,
    CardIsPhyrexianParam,
    CardHasColourIndicatorParam,
    CardIsHybridParam,
)
from .card_ownership_parameters import CardOwnershipCountParam, CardOwnerParam
from .card_power_toughness_parameters import (
    CardNumLoyaltyParam,
    CardNumToughnessParam,
    CardNumPowerParam,
)
from .card_rarity_parameter import CardRarityParam
from .card_set_parameters import CardSetParam, CardBlockParam
from .card_type_parameters import CardGenericTypeParam, CardSubtypeParam, CardTypeParam
from .card_flavour_text_parameter import CardFlavourTextParam
from .card_name_parameters import CardNameParam
from .card_rules_text_parameter import CardRulesTextParam, CardProducesManaParam


class CardSortParam:
    """
    The base sorting parameter
    """

    def __init__(self, descending: bool = False):
        super().__init__()
        self.sort_descending = descending

    def get_sort_list(self) -> List[str]:
        """
        Gets the sort list taking order into account
        :return:
        """
        return [
            "-" + arg if self.sort_descending else arg for arg in self.get_sort_keys()
        ]

    def get_sort_keys(self) -> List[str]:
        """
        Gets the list of attributes to be sorted by
        :return:
        """
        raise NotImplementedError()


class CardNameSortParam(CardSortParam):
    """
    THe sort parameter for a card's name
    """

    def get_sort_keys(self) -> list:
        """
        Gets the list of attributes to be sorted by
        """
        return ["name"]


class CardPowerSortParam(CardSortParam):
    """
    THe sort parameter for a card's numerical power
    """

    def get_sort_keys(self) -> list:
        """
        Gets the list of attributes to be sorted by
        """
        return ["num_power"]


class CardCollectorNumSortParam(CardSortParam):
    """
    The sort parameter for a card's collector number
    """

    def get_sort_keys(self) -> list:
        return ["printings__number"]


class CardColourSortParam(CardSortParam):
    """
    The sort parameter for a card's colour key
    """

    def get_sort_keys(self) -> List[str]:
        return ["colour_sort_key"]


class CardColourWeightSortParam(CardSortParam):
    """
    The sort parameter for a card's colour weight
    """

    def get_sort_keys(self) -> list:
        return ["cmc", "colour_sort_key", "colour_weight"]
