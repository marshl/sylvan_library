"""
Card name parameters
"""
from django.db.models.query import Q

from .base_parameters import CardSearchParam


class CardNameParam(CardSearchParam):
    """
    The parameter for searching by a card's name
    """

    def __init__(self, card_name, match_exact: bool = False):
        super().__init__()
        self.card_name = card_name
        self.match_exact = match_exact

    def query(self) -> Q:
        if self.match_exact:
            query = Q(card__name__iexact=self.card_name)
        else:
            query = Q(card__name__icontains=self.card_name)

        return ~query if self.negated else query

    def get_pretty_str(self) -> str:
        """
        Returns a human readable version of this parameter
        (and all sub parameters for those with children)
        :return: The pretty version of this parameter
        """
        if self.negated:
            return f'the name does not contain "{self.card_name}"'
        return f'the name contains "{self.card_name}"'
