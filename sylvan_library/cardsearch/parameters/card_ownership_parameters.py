"""
Card ownership parameters
"""

from typing import List

from django.db import connection
from django.db.models import Q

from cards.models.card import Card
from cardsearch.parameters.base_parameters import (
    CardSearchNumericalParameter,
    CardSearchContext,
    QueryContext,
    ParameterArgs,
    QueryValidationError,
    CardSearchBinaryParameter,
)


class CardOwnershipCountParam(CardSearchNumericalParameter):
    """
    The parameter for searching by how many a user owns of it
    """

    @classmethod
    def get_parameter_name(cls) -> str:
        return "ownership"

    @classmethod
    def get_search_keywords(cls) -> List[str]:
        return ["have", "own"]

    def get_default_search_context(self) -> CardSearchContext:
        return CardSearchContext.CARD

    def validate(self, query_context: QueryContext) -> None:
        if not query_context.user or query_context.user.is_anonymous:
            raise QueryValidationError("Can't search by ownership when not logged in")

        if self.operator == ":":
            if self.value == "any":
                self.operator = ">="
                self.number = 1
            elif self.value == "none":
                self.operator = "="
                self.number = 0
            else:
                self.operator = ">="

        super().validate(query_context)

    def __init__(self, param_args: ParameterArgs, negated: bool = False):
        super().__init__(param_args, negated)

    def query(self, query_context: QueryContext) -> Q:
        assert self.operator in ("<", "<=", "=", ">=", ">")

        with connection.cursor() as cursor:
            cursor.execute(
                # raw = Card.objects.raw(
                f"""
SELECT cards_card.id
FROM cards_card
JOIN cards_cardprinting
  ON cards_cardprinting.card_id = cards_card.id
JOIN cards_cardlocalisation
  ON cards_cardprinting.id = cards_cardlocalisation.card_printing_id
LEFT JOIN cards_userownedcard
  ON cards_userownedcard.card_localisation_id = cards_cardlocalisation.id
  AND cards_userownedcard.owner_id = %(user_id)s
GROUP BY cards_card.id
HAVING SUM(COALESCE(cards_userownedcard.count, 0)) {self.operator} %(number)s
        """,
                {"user_id": query_context.user.id, "number": self.number},
            )
            rows = cursor.fetchall()
            ids = list(sum(rows, ()))
        if query_context.search_mode == CardSearchContext.CARD:
            return Q(id__in=ids, _negated=self.negated)
        return Q(card_id__in=ids, _negated=self.negated)

    def get_pretty_str(self, query_context: QueryContext) -> str:
        """
        Returns a human-readable version of this parameter
        (and all sub parameters for those with children)
        :return: The pretty version of this parameter
        """
        if self.operator in ("<", "<=", "=") and self.number <= 0:
            return "you don't own any"

        if (self.operator == ">" and self.number == 0) or (
            self.operator == ">=" and self.number == 1
        ):
            return "you own it"

        return f"you own {self.operator} {self.number}"


class CardUsageCountParam(CardSearchNumericalParameter):
    """
    The parameter for searching by how many times it has been used in a deck
    """

    @classmethod
    def get_parameter_name(cls) -> str:
        return "usage"

    @classmethod
    def get_search_keywords(cls) -> List[str]:
        return ["used", "decks", "deck"]

    def get_default_search_context(self) -> CardSearchContext:
        return CardSearchContext.CARD

    def validate(self, query_context: QueryContext) -> None:
        if not query_context.user or query_context.user.is_anonymous:
            raise QueryValidationError("Can't search by deck usage if not logged in")

        if self.operator == ":":
            if self.value in ("any", "ever"):
                self.operator = ">="
                self.number = 1
            elif self.value == "never":
                self.operator = "="
                self.number = 0

        super().validate(query_context)

    def query(self, query_context: QueryContext) -> Q:
        """
        Gets the Q query object
        :return: The Q object
        """
        # raw = Card.objects.raw(

        with connection.cursor() as cursor:
            cursor.execute(
                f"""
SELECT cards_card.id
FROM cards_card
LEFT JOIN cards_deckcard ON cards_deckcard.card_id = cards_card.id
LEFT JOIN cards_deck ON cards_deck.id = cards_deckcard.deck_id AND cards_deck.owner_id = %(user_id)s
GROUP BY cards_card.id
HAVING COUNT(cards_deck.id) {self.operator} %(number)s
""",
                {"user_id": query_context.user.id, "number": self.number},
            )
            ids = cursor.fetchall()
            ids = list(sum(ids, ()))
        if query_context.search_mode == CardSearchContext.CARD:
            return Q(id__in=ids, _negated=self.negated)
        return Q(card_id__in=ids, _negated=self.negated)

    def get_pretty_str(self, query_context: QueryContext) -> str:
        """
        Returns a human-readable version of this parameter
        (and all sub parameters for those with children)
        :return: The pretty version of this parameter
        """
        if self.operator == "=" and self.number == 0:
            return "you haven't used it in a deck"
        return f"you used it in {self.operator} {self.number} decks"


class CardMissingPauperParam(CardSearchBinaryParameter):
    """
    A parameter for searching for cards that the user owns a rare version of,
    but doesn't own a common or uncommon variant that they can use in pauper
    """

    @classmethod
    def get_is_keywords(cls) -> List[str]:
        return ["missing-pauper", "missingpauper", "nopauper"]

    @classmethod
    def get_parameter_name(cls) -> str:
        return "missing pauper"

    def get_default_search_context(self) -> CardSearchContext:
        return CardSearchContext.CARD

    def validate(self, query_context: QueryContext) -> None:
        if not query_context.user or query_context.user.is_anonymous:
            raise QueryValidationError(
                "Can't search by missing pauper cards when not logged in"
            )

    def query(self, query_context: QueryContext) -> Q:
        """
        Gets the Q query object
        :return: The Q object
        """
        with connection.cursor() as cursor:
            cursor.execute(
                f"""
-- Find cards where I have a rare or mythic version of it
SELECT DISTINCT(cards_card.id)
FROM cards_card
JOIN cards_cardprinting
  ON cards_cardprinting.card_id = cards_card.id
JOIN cards_set
  ON cards_set.id = cards_cardprinting.set_id
JOIN cards_rarity
  ON cards_rarity.id = cards_cardprinting.rarity_id
JOIN cards_cardlocalisation
  ON cards_cardprinting.id = cards_cardlocalisation.card_printing_id
JOIN cards_userownedcard
  ON cards_userownedcard.card_localisation_id = cards_cardlocalisation.id
WHERE cards_userownedcard.owner_id = %(user_id)s
AND cards_rarity.symbol IN ('R', 'M')
AND cards_set.release_date >= (SELECT release_date FROM cards_set WHERE cards_set.code = 'EXO')

INTERSECT 

-- And there exists a common or uncommon version of it
SELECT DISTINCT(cards_card.id)
FROM cards_card
JOIN cards_cardprinting
  ON cards_cardprinting.card_id = cards_card.id
JOIN cards_set
  ON cards_set.id = cards_cardprinting.set_id
JOIN cards_rarity
  ON cards_rarity.id = cards_cardprinting.rarity_id
JOIN cards_cardlocalisation
  ON cards_cardprinting.id = cards_cardlocalisation.card_printing_id
WHERE cards_rarity.symbol IN ('U', 'C')
AND NOT cards_set.is_online_only
AND cards_set.code NOT IN ('30A')
AND cards_set.release_date >= (SELECT release_date FROM cards_set WHERE cards_set.code = 'EXO')

EXCEPT

-- And I don't already have a common or uncommon version of it
SELECT DISTINCT(cards_card.id)
FROM cards_card
JOIN cards_cardprinting
  ON cards_cardprinting.card_id = cards_card.id
JOIN cards_set
  ON cards_set.id = cards_cardprinting.set_id
JOIN cards_rarity
  ON cards_rarity.id = cards_cardprinting.rarity_id
JOIN cards_cardlocalisation
  ON cards_cardprinting.id = cards_cardlocalisation.card_printing_id
JOIN cards_userownedcard
  ON cards_userownedcard.card_localisation_id = cards_cardlocalisation.id
WHERE cards_userownedcard.owner_id = %(user_id)s
AND cards_rarity.symbol IN ('U', 'C')
""",
                {"user_id": query_context.user.id},
            )
            rows = cursor.fetchall()
            ids = list(sum(rows, ()))
        q = (
            Q(id__in=ids)
            if query_context.search_mode == CardSearchContext.CARD
            else Q(card_id__in=ids)
        )
        return ~q if self.negated else q

    def get_pretty_str(self, query_context: QueryContext) -> str:
        """
        Returns a human-readable version of this parameter
        (and all sub parameters for those with children)
        :return: The pretty version of this parameter
        """
        return "you are missing pauper variant of it"
