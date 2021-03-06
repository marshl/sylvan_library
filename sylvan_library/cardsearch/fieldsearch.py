"""
The module for the field search class
"""
import logging
from typing import Optional

from cards.models import Set

from cardsearch.parameters import (
    AndParam,
    OrParam,
    CardManaCostParam,
    CardFlavourTextParam,
    CardNameParam,
    CardRulesTextParam,
    CardCmcParam,
    CardColourParam,
    CardColourIdentityParam,
    CardTypeParam,
    CardSubtypeParam,
    CardNumPowerParam,
    CardNumToughnessParam,
    CardRarityParam,
    CardSetParam,
    BranchParam,
)
from cardsearch.base_search import BaseSearch, create_colour_param

logger = logging.getLogger("django")


# pylint: disable=too-many-instance-attributes
class FieldSearch(BaseSearch):
    """
    The search form for a series of different fields
    """

    def __init__(self) -> None:
        super().__init__()

        self.card_name = None
        self.rules_text = None
        self.flavour_text = None
        self.type_text = None
        self.subtype_text = None
        self.min_cmc = None
        self.max_cmc = None
        self.min_toughness = None
        self.max_toughness = None
        self.min_power = None
        self.max_power = None
        self.mana_cost = None

        self.colours = []
        self.colour_identities = []

        self.exclude_unselected_colours = False
        self.match_colours_exactly = False
        self.exclude_unselected_colour_identities = False
        self.match_colour_identities_exactly = False

        self.rarities = []
        self.match_rarities_exactly = False

        self.sets = []
        self.match_sets_exactly = False

    # pylint: disable=too-many-branches
    def build_parameters(self) -> None:
        """
        Constructs the parameter list for this searching object
        """
        root_param = self.root_parameter

        if self.card_name:
            root_param.add_parameter(CardNameParam(self.card_name))

        if self.rules_text:
            root_param.add_parameter(CardRulesTextParam(self.rules_text))

        if self.flavour_text:
            root_param.add_parameter(CardFlavourTextParam(self.flavour_text))

        if self.type_text:
            root_param.add_parameter(CardTypeParam(self.type_text))

        if self.subtype_text:
            root_param.add_parameter(CardSubtypeParam(self.subtype_text))

        if self.min_cmc is not None:
            root_param.add_parameter(CardCmcParam(self.min_cmc, "GTE"))

        if self.max_cmc is not None:
            root_param.add_parameter(CardCmcParam(self.max_cmc, "LTE"))

        if self.min_power is not None:
            root_param.add_parameter(CardNumPowerParam(self.min_power, "GTE"))

        if self.max_power is not None:
            root_param.add_parameter(CardNumPowerParam(self.max_power, "LTE"))

        if self.min_toughness is not None:
            root_param.add_parameter(CardNumToughnessParam(self.min_toughness, "GTE"))

        if self.max_toughness is not None:
            root_param.add_parameter(CardNumToughnessParam(self.max_toughness, "LTE"))

        if self.mana_cost is not None and self.mana_cost != "":
            root_param.add_parameter(CardManaCostParam(self.mana_cost, False))

        if self.colours:
            self.root_parameter.add_parameter(
                create_colour_param(
                    self.colours,
                    CardColourParam,
                    match_colours=self.match_colours_exactly,
                    exclude_colours=self.exclude_unselected_colours,
                )
            )

        if self.colour_identities:
            self.root_parameter.add_parameter(
                create_colour_param(
                    self.colour_identities,
                    CardColourIdentityParam,
                    match_colours=self.match_colour_identities_exactly,
                    exclude_colours=self.exclude_unselected_colour_identities,
                )
            )

        if self.rarities:
            rarity_node: BranchParam = AndParam() if self.match_rarities_exactly else OrParam()
            self.root_parameter.add_parameter(rarity_node)
            for rarity in self.rarities:
                rarity_node.add_parameter(CardRarityParam(rarity))

        if self.sets:
            set_node: BranchParam = AndParam() if self.match_sets_exactly else OrParam()
            self.root_parameter.add_parameter(set_node)
            for set_obj in self.sets:
                set_node.add_parameter(CardSetParam(set_obj))

    def get_preferred_set(self) -> Optional[Set]:
        if self.sets:
            return (
                Set.objects.filter(id__in=self.sets).order_by("-release_date").first()
            )

        return None
