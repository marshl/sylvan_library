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
    The parameter for searching by price: the card's cheapest printing in a card search,
    or each printing's latest price in a printing search
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

    def query(self, query_context: QueryContext) -> Q:
        field = (
            "latest_price__paper_value"
            if query_context.search_mode == CardSearchContext.PRINTING
            else "card__cheapest_price__paper_value"
        )
        return Q(**self.get_args(field, query_context=query_context))

    def get_pretty_str(self, query_context: QueryContext) -> str:
        return f"is worth {self.operator} ${self.value}"
