"""
The module for the field search class
"""
import logging
from typing import Optional

from cards.models import Set

from cardsearch.parameters import (
    CardNameParam,
)
from cardsearch.base_search import BaseSearch

logger = logging.getLogger('django')


class NameSearch(BaseSearch):
    """
    The search form for a series of different fields
    """

    def __init__(self):
        super().__init__()

        self.card_name = None

    def build_parameters(self):
        if self.card_name:
            self.root_parameter.add_parameter(CardNameParam(self.card_name))

    def get_preferred_set(self) -> Optional[Set]:
        return None
