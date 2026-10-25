"""
Card deck parameters
"""

from typing import List

from django.db.models.query import Q

from sylvan_library.cards.models.decks import DeckCard
from sylvan_library.cardsearch.parameters.base_parameters import (
    QueryContext,
    CardSearchParameter,
)


class CardDeckParam(CardSearchParameter):
    """
    The parameter for searching for cards within a specific deck
    """

    @classmethod
    def get_parameter_name(cls) -> str:
        return "deck"

    @classmethod
    def get_search_operators(cls) -> List[str]:
        return [":", "="]

    @classmethod
    def get_search_keywords(cls) -> List[str]:
        return ["deck", "d"]

    def query(self, query_context: QueryContext) -> Q:
        deck_cards = DeckCard.objects.filter(deck_id=self.value)
        return Q(card_id__in=deck_cards.values("card_id"), _negated=self.negated)

    def get_pretty_str(self, query_context: QueryContext) -> str:
        return (
            "the card " + ("isn't" if self.negated else "is") + f" in deck {self.value}"
        )
