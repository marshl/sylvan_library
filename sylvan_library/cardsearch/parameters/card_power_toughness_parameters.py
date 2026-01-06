"""
Card power, toughness and loyalty parameters
"""

from typing import List

from django.db.models import F
from django.db.models.query import Q

from sylvan_library.cardsearch.parameters.base_parameters import (
    CardSearchNumericalParameter,
    CardSearchContext,
    QueryContext,
)


class CardNumPowerParam(CardSearchNumericalParameter):
    """
    The parameter for searching by a card's numerical power
    """

    @classmethod
    def get_parameter_name(cls) -> str:
        return "power"

    @classmethod
    def get_search_keywords(cls) -> List[str]:
        return ["power", "pow"]

    def get_default_search_context(self) -> CardSearchContext:
        return CardSearchContext.CARD

    def query(self, query_context: QueryContext) -> Q:
        prefix = (
            "card__" if query_context.search_mode == CardSearchContext.PRINTING else ""
        )
        args = self.get_args(
            f"{prefix}faces__num_power",
            query_context,
        )
        query = Q(**args) & Q(**{f"{prefix}faces__power__isnull": False})
        return ~query if self.negated else query

    def get_pretty_str(self, query_context: QueryContext) -> str:
        return (
            f"the power {'is not ' if self.negated else ''}{self.operator} {self.value}"
        )


class CardNumToughnessParam(CardSearchNumericalParameter):
    """
    The parameter for searching by a card's numerical toughness
    """

    @classmethod
    def get_parameter_name(cls) -> str:
        return "toughness"

    @classmethod
    def get_search_keywords(cls) -> List[str]:
        return ["tou", "toughness", "tough", "tuff"]

    def get_default_search_context(self) -> CardSearchContext:
        return CardSearchContext.CARD

    def query(self, query_context: QueryContext) -> Q:
        prefix = (
            "card__" if query_context.search_mode == CardSearchContext.PRINTING else ""
        )
        args = self.get_args(f"{prefix}faces__num_toughness", query_context)
        return Q(**args) & Q(**{f"{prefix}faces__toughness__isnull": False})

    def get_pretty_str(self, query_context: QueryContext) -> str:
        if isinstance(self.value, F):
            return f"the toughness {self.operator} "
        return f"the toughness {self.operator} {self.value}"


class CardNumLoyaltyParam(CardSearchNumericalParameter):
    """
    The parameter for searching by a card's numerical loyalty
    """

    @classmethod
    def get_parameter_name(cls) -> str:
        return "loyalty"

    @classmethod
    def get_search_keywords(cls) -> List[str]:
        return ["loyalty", "loy", "l"]

    def get_default_search_context(self) -> CardSearchContext:
        return CardSearchContext.CARD

    def query(self, query_context: QueryContext) -> Q:
        prefix = (
            "card__" if query_context.search_mode == CardSearchContext.PRINTING else ""
        )
        args = self.get_args(f"{prefix}faces__num_loyalty", query_context)
        return Q(**args) & Q(**{f"{prefix}faces__loyalty__isnull": False})

    def get_pretty_str(self, query_context: QueryContext) -> str:
        return f"the loyalty {self.operator} {self.value}"
