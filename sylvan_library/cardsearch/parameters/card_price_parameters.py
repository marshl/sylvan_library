"""
Card rarity parameters
"""

from typing import List

from django.db.models.query import Q

from sylvan_library.cardsearch.parameters.base_parameters import (
    CardSearchNumericalParameter,
    QueryContext,
    CardSearchContext,
)


class CardPriceParam(CardSearchNumericalParameter):
    """
    The parameter for searching by how many a user owns of it
    """

    @classmethod
    def get_parameter_name(cls) -> str:
        return "price"

    @classmethod
    def get_search_keywords(cls) -> List[str]:
        return ["price", "cost"]

    @classmethod
    def get_search_operators(cls) -> List[str]:
        return ["<", "<=", ">=", ">"]

    def get_default_search_context(self) -> CardSearchContext:
        return CardSearchContext.CARD

    def query(self, query_context: QueryContext) -> Q:
        args = self.get_args(
            (
                "card__cheapest_price__paper_value"
                if query_context.search_mode == CardSearchContext.PRINTING
                else "cheapest_price__paper_value"
            ),
            query_context=query_context,
        )
        return Q(**args)

    def get_pretty_str(self, query_context: QueryContext) -> str:
        return f"is worth {self.operator} ${self.value}"
