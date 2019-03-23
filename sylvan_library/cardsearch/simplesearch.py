"""
The module for the simple search form
"""
from cardsearch.base_search import BaseSearch, create_colour_param

from cardsearch.parameters import (
    OrParam,
    CardNameParam,
    CardColourParam,
    CardRulesTextParam,
    CardTypeParam,
    CardSubtypeParam,
    CardSetParam,
    CardMulticolouredOnlyParam,
)


# pylint: disable=too-many-instance-attributes
class SimpleSearch(BaseSearch):
    """
    A simple flat search
    """

    def __init__(self):
        super().__init__()
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

    def get_preferred_set(self):
        return None

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
            self.root_parameter.add_parameter(
                create_colour_param(self.colours,
                                    CardColourParam,
                                    match_colours=self.match_colours,
                                    exclude_colours=self.exclude_colours)
            )

        if self.set:
            root_param.add_parameter(CardSetParam(self.set))

        if self.multicoloured_only:
            root_param.add_parameter(CardMulticolouredOnlyParam())

        if self.card_type:
            root_param.add_parameter(CardTypeParam(self.card_type))
