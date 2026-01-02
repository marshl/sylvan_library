"""
Card rarity parameters
"""

from typing import List, Optional

from django.db.models.query import Q

from sylvan_library.cards.models.rarity import Rarity
from sylvan_library.cardsearch.parameters.base_parameters import (
    OPERATOR_MAPPING,
    OPERATOR_TO_WORDY_MAPPING,
    CardSearchParameter,
    CardSearchContext,
    ParameterArgs,
    QueryContext,
    QueryValidationError,
)


class CardRarityParam(CardSearchParameter):
    """
    The parameter for searching by a card's rarity
    """

    @classmethod
    def get_parameter_name(cls) -> str:
        return "rarity"

    @classmethod
    def get_search_operators(cls) -> List[str]:
        return [":", "=", "<=", "<", ">", ">="]

    @classmethod
    def get_search_keywords(cls) -> List[str]:
        return ["rarity", "r"]

    def get_default_search_context(self) -> CardSearchContext:
        return CardSearchContext.PRINTING

    def __init__(self, param_args: ParameterArgs, negated: bool = False):
        super().__init__(param_args, negated)
        self.rarity: Optional[Rarity] = None
        if self.operator == ":":
            self.operator = "="

    def validate(self, query_context: QueryContext) -> None:
        try:
            self.rarity = Rarity.objects.get(
                Q(symbol__iexact=self.value) | Q(name__iexact=self.value)
            )
        except Rarity.DoesNotExist as ex:
            raise QueryValidationError(f'Couldn\'t find rarity "{self.value}"') from ex

    def query(self, query_context: QueryContext) -> Q:
        if self.operator == "=":
            query = Q(rarity=self.rarity)
        else:
            filter_ = f"rarity__display_order{OPERATOR_MAPPING[self.operator]}"
            query = Q(**{filter_: self.rarity.display_order})
        return ~query if self.negated else query

    def get_pretty_str(self, query_context: QueryContext) -> str:
        return (
            "the rarity "
            + ("isn't" if self.negated else "is")
            + (
                " " + OPERATOR_TO_WORDY_MAPPING[self.operator]
                if self.operator not in (":", "=")
                else ""
            )
            + f" {self.rarity.name.lower()}"
        )
