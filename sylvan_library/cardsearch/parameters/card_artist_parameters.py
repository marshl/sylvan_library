"""
Card artist parameters
"""

from typing import List

from django.db.models.query import Q

from sylvan_library.cardsearch.parameters.base_parameters import (
    CardSearchParameter,
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

    def query(self, query_context: QueryContext) -> Q:
        return Q(face_printings__artist__icontains=self.value, _negated=self.negated)

    def get_pretty_str(self, query_context: QueryContext) -> str:
        return "the artist name {0} {1}".format(
            ("doesn't include" if self.negated else "includes"), self.value
        )
