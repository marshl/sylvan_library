"""
Card power, toughness and loyalty parameters
"""
from django.db.models.query import Q

from .base_parameters import CardNumericalParam


class CardNumPowerParam(CardNumericalParam):
    """
    The parameter for searching by a card's numerical power
    """

    def query(self) -> Q:
        args = self.get_args("card__faces__num_power")
        query = Q(**args) & Q(card__faces__power__isnull=False)
        return ~query if self.negated else query

    def get_pretty_str(self) -> str:
        return f"the power {'is not ' if self.negated else ''}{self.operator} {self.number}"


class CardNumToughnessParam(CardNumericalParam):
    """
    The parameter for searching by a card's numerical toughness
    """

    def query(self) -> Q:
        args = self.get_args("card__faces__num_toughness")
        return Q(**args) & Q(card__faces__toughness__isnull=False)

    def get_pretty_str(self) -> str:
        return f"the toughness {self.operator} {self.number}"


class CardNumLoyaltyParam(CardNumericalParam):
    """
    The parameter for searching by a card's numerical loyalty
    """

    def query(self) -> Q:
        args = self.get_args("card__faces__num_loyalty")
        return Q(**args) & Q(card__faces__loyalty__isnull=False)

    def get_pretty_str(self) -> str:
        return f"the loyalty {self.operator} {self.number}"
