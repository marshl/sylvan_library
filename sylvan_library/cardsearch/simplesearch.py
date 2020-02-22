"""
The module for the simple search form
"""
from typing import Optional, List

from bitfield import Bit


from cards.models import Format, Set
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

    def __init__(self) -> None:
        super().__init__()
        self.text: Optional[str] = None
        self.colours: List[Bit] = list()
        self.include_name: bool = False
        self.include_types: bool = False
        self.include_rules: bool = False
        self.set: Optional[Set] = None
        self.format: Optional[Format] = None
        self.match_colours: bool = False
        self.multicoloured_only: bool = False
        self.exclude_colours: bool = False
        self.card_type: bool = False
        self.sort_order: Optional[str] = None

    def get_preferred_set(self) -> Optional[Set]:
        return None

    def build_parameters(self) -> None:
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
                create_colour_param(
                    self.colours,
                    CardColourParam,
                    match_colours=self.match_colours,
                    exclude_colours=self.exclude_colours,
                )
            )

        if self.set:
            root_param.add_parameter(CardSetParam(self.set))

        if self.multicoloured_only:
            root_param.add_parameter(CardMulticolouredOnlyParam())

        if self.card_type:
            root_param.add_parameter(CardTypeParam(self.card_type))
