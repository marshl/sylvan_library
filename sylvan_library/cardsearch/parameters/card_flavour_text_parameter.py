"""
Cardl flavour text parameters
"""

from django.db.models.query import Q

from .base_parameters import CardSearchParam


class CardFlavourTextParam(CardSearchParam):
    """
    The parameter for searching by a card's flavour text
    """

    def __init__(self, flavour_text):
        super().__init__()
        self.flavour_text = flavour_text

    def query(self) -> Q:
        return Q(flavour_text__icontains=self.flavour_text)

    def get_pretty_str(self, within_or_block: bool = False) -> str:
        verb = "isn't" if self.negated else "is"
        return f'flavour text {verb} "{self.flavour_text}"'
