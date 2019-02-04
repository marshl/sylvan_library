"""
The module for the simple search form
"""
from cards.models import Card
from cardsearch.base_search import BaseSearch

from cardsearch.parameters import (
    OrParam,
    CardNameParam,
    CardRulesTextParam,
    CardTypeParam,
    CardSubtypeParam,
    CardColourParam,
    NotParam,
    CardSetParam,
    CardMulticolouredOnlyParam,
)


class SimpleSearch(BaseSearch):
    """
    A simple flat search
    """

    def __init__(self):
        self.text = None
        self.colours = list()
        self.include_name = False
        self.include_types = False
        self.include_rules = False
        self.set = None
        self.format = None
        self.match_colours = False
        self.multicoloured_only = False
        self.exclude_colours = False
        self.card_type = False
        self.sort_order = None

    def build_parameters(self):

        root_param = self.root_parameter

        if self.text:
            text_root = root_param.add_parameter(OrParam())
            if self.include_name:
                text_root.add_parameter(CardNameParam(self.text))

            if self.include_rules:
                text_root.add_parameter(CardRulesTextParam(self.text))

            if self.include_types:
                text_root.add_parameter(CardTypeParam(self.text))
                text_root.add_parameter(CardSubtypeParam(self.text))

        if self.colours:
            if self.match_colours:
                colour_root = root_param
            else:
                colour_root = OrParam()
                root_param.add_parameter(colour_root)

            for colour in self.colours:
                colour_root.add_parameter(CardColourParam(colour))

            if self.exclude_colours:
                exclude_param = NotParam()
                root_param.add_parameter(exclude_param)
                for colour in [c for c in Card.colour_flags.values() if c not in self.colours]:
                    param = CardColourParam(colour)
                    exclude_param.add_parameter(param)

        if self.set:
            root_param.add_parameter(CardSetParam(self.set))

        if self.multicoloured_only:
            root_param.add_parameter(CardMulticolouredOnlyParam())

        if self.card_type:
            root_param.add_parameter(CardTypeParam(self.card_type))
