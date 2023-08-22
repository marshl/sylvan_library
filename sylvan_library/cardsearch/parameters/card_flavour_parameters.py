"""
Module for flavour text parameters
"""
from typing import List

from django.db.models import Q

from cardsearch.parameters.base_parameters import (
    CardTextParameter,
    QueryContext,
    CardSearchContext,
)


class CardFlavourTextParam(CardTextParameter):
    """
    Parameter for the printing flavour text
    """

    @classmethod
    def get_parameter_name(cls) -> str:
        return "flavour text"

    @classmethod
    def get_search_operators(cls) -> List[str]:
        return [":", "="]

    @classmethod
    def get_search_keywords(cls) -> List[str]:
        return ["flavour", "flavor", "ft"]

    def get_default_search_context(self) -> CardSearchContext:
        return CardSearchContext.PRINTING

    def query(self, query_context: QueryContext) -> Q:
        query = Q(face_printings__flavour_text__icontains=self.value)
        return ~query if self.negated else query

    def get_pretty_str(self, query_context: QueryContext) -> str:
        return "flavour {} {}".format(
            "doesn't contain" if self.negated else "contains", self.value
        )
