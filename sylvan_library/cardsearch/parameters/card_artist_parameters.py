"""
Card artist parameters
"""

from typing import List

from django.db.models.query import Q

from cardsearch.parameters.base_parameters import (
    CardSearchParameter,
    CardSearchContext,
    QueryContext,
)


class CardArtistParam(CardSearchParameter):
    """
    The parameter for searching by a card printings artist
    """

    @classmethod
    def get_parameter_name(cls) -> str:
        return "artist"

    @classmethod
    def get_search_operators(cls) -> List[str]:
        return [":", "="]

    @classmethod
    def get_search_keywords(cls) -> List[str]:
        return ["artist", "art"]

    def get_default_search_context(self) -> CardSearchContext:
        return CardSearchContext.PRINTING

    def query(self, query_context: QueryContext) -> Q:
        return Q(face_printings__artist__icontains=self.value)

    def get_pretty_str(self, query_context: QueryContext) -> str:
        return "artist " + ("isn't" if self.negated else "is") + " " + self.value
