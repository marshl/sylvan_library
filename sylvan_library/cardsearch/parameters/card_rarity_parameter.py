"""
Card rarity parameters
"""
from django.db.models.query import Q

from cards.models import Rarity
from .base_parameters import CardSearchParam


class CardRarityParam(CardSearchParam):
    """
    The parameter for searching by a card's rarity
    """

    def __init__(self, rarity: Rarity):
        super().__init__()
        self.rarity = rarity

    def query(self) -> Q:
        return Q(rarity=self.rarity)

    def get_pretty_str(self, within_or_block: bool = False) -> str:
        return "rarity " + ("isn't" if self.negated else "is") + " " + self.rarity.name
