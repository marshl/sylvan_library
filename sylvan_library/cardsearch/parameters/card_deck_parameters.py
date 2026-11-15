"""
Card deck parameters
"""

from typing import List

from django.db.models.query import Q

from sylvan_library.cards.models.decks import DeckCard
from sylvan_library.cardsearch.parameters.base_parameters import (
    QueryContext,
    CardSearchParameter,
    QueryValidationError,
)


class CardDeckParam(CardSearchParameter):
    """
    The parameter for searching for cards within one of the user's decks, by its ID.
    Other users' decks match nothing.
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

    def validate(self, query_context: QueryContext) -> None:
        if not query_context.user or query_context.user.is_anonymous:
            raise QueryValidationError("Can't search by deck when not logged in")
        if not self.value.isdigit():
            raise QueryValidationError(f'"{self.value}" isn\'t a deck ID')

    def query(self, query_context: QueryContext) -> Q:
        deck_cards = DeckCard.objects.filter(
            deck_id=self.value, deck__owner=query_context.user
        )
        return Q(card_id__in=deck_cards.values("card_id"), _negated=self.negated)

    def get_pretty_str(self, query_context: QueryContext) -> str:
        return (
            "the card " + ("isn't" if self.negated else "is") + f" in deck {self.value}"
        )
