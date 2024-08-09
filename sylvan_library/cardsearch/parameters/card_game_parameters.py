"""
Card game parameters
"""
from typing import List

from django.db.models.query import Q

from cardsearch.parameters.base_parameters import (
    CardSearchContext,
    QueryContext,
    QueryValidationError,
    CardSearchParameter,
)


class CardGameParam(CardSearchParameter):
    """
    The parameter for searching by a card's set
    """

    def get_default_search_context(self) -> CardSearchContext:
        return CardSearchContext.PRINTING

    @classmethod
    def get_parameter_name(cls) -> str:
        return "game"

    @classmethod
    def get_search_operators(cls) -> List[str]:
        return [":", "="]

    @classmethod
    def get_search_keywords(cls) -> List[str]:
        return ["game", "g"]

    def validate(self, query_context: QueryContext) -> None:
        if self.value not in ("paper", "online"):
            raise QueryValidationError(f'Unknown game "{self.value}"')

    def query(self, query_context: QueryContext) -> Q:
        if self.value == "paper":
            q = Q(is_online_only=False, set__is_online_only=False)
        else:
            q = Q(is_online_online=True, set__is_online_only=True)
        return ~q if self.negated else q

    def get_pretty_str(self, query_context: QueryContext) -> str:
        return "the card " + ("isn't" if self.negated else "is") + f" in {self.value}"
