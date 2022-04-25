"""
Card name parameters
"""
from django.db.models.query import Q

from cardsearch.parameters.base_parameters import CardSearchParam


class CardNameParam(CardSearchParam):
    """
    The parameter for searching by a card's name
    """

    def __init__(self, card_name, match_exact: bool = False) -> None:
        super().__init__()
        self.card_name = card_name
        self.match_exact = match_exact
        self.regex_match: bool = False
        if self.card_name.startswith("/") and self.card_name.endswith("/"):
            self.regex_match = True
            self.card_name = self.card_name.strip("/")
            if self.match_exact:
                self.card_name = "^" + self.card_name + "$"

    def query(self) -> Q:
        if self.regex_match:
            query = Q(card__name__iregex=self.card_name)
        elif self.match_exact:
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
