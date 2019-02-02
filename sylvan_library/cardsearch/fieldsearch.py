"""
The module for the field search class
"""
import logging

from cards.models import Card
from cardsearch.parameters import (
    CardFlavourTextParam,
    CardNameParam,
    CardRulesTextParam,
    CardCmcParam,
    OrParam,
    CardColourParam,
    NotParam,
    CardColourIdentityParam,
    CardTypeParam,
    CardSubtypeParam
)
from cardsearch.base_search import BaseSearch

logger = logging.getLogger('django')


class FieldSearch(BaseSearch):
    """
    The search form for a series of different fields
    """

    def __init__(self):
        super().__init__()

        self.card_name = None
        self.rules_text = None
        self.flavour_text = None
        self.type_text = None
        self.subtype_text = None
        self.cmc = None
        self.cmc_operator = None

        self.colours = []
        self.colour_identities = []

        self.exclude_unselected_colours = False
        self.match_colours_exactly = False
        self.exclude_unselected_colour_identities = False
        self.match_colour_identities_exactly = False

    def build_parameters(self):

        root_param = self.root_parameter

        if self.card_name:
            logger.info('Searching for card name %s', self.card_name)
            root_param.add_parameter(CardNameParam(self.card_name))

        if self.rules_text:
            logger.info('Searching for rules text %s', self.rules_text)
            root_param.add_parameter(CardRulesTextParam(self.rules_text))

        if self.flavour_text:
            root_param.add_parameter(CardFlavourTextParam(self.flavour_text))

        if self.type_text:
            root_param.add_parameter(CardTypeParam(self.type_text))

        if self.subtype_text:
            root_param.add_parameter(CardSubtypeParam(self.subtype_text))

        if self.cmc is not None:
            logger.info('Searching for CMC %s/%s', self.cmc, self.cmc_operator)
            root_param.add_parameter(CardCmcParam(self.cmc, self.cmc_operator))

        if self.colours:
            if self.match_colours_exactly:
                colour_root = root_param
            else:
                colour_root = OrParam()
                root_param.add_parameter(colour_root)

            for colour in self.colours:
                colour_root.add_parameter(CardColourParam(colour))

            if self.exclude_unselected_colours:
                exclude_param = NotParam()
                root_param.add_parameter(exclude_param)
                for colour in [c for c in Card.colour_flags.values() if c not in self.colours]:
                    param = CardColourParam(colour)
                    exclude_param.add_parameter(param)

        if self.colour_identities:
            if self.match_colour_identities_exactly:
                colour_id_root = root_param
            else:
                colour_id_root = OrParam()
                root_param.add_parameter(colour_id_root)

            for colour in self.colour_identities:
                colour_id_root.add_parameter(CardColourIdentityParam(colour))

            if self.exclude_unselected_colour_identities:
                exclude_param = NotParam()
                root_param.add_parameter(exclude_param)
                for colour in [c for c in Card.colour_flags.values()
                               if c not in self.colour_identities]:
                    param = CardColourIdentityParam(colour)
                    exclude_param.add_parameter(param)
