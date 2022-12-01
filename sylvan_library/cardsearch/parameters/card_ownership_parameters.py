"""
Card ownership parameters
"""
from django.contrib.auth import get_user_model
from django.db.models import Q

from cards.models.card import Card
from cardsearch.parameters.base_parameters import (
    CardNumericalParam,
    CardSearchParam,
)


class CardOwnershipCountParam(CardNumericalParam):
    """
    The parameter for searching by how many a user owns of it
    """

    def __init__(self, user: get_user_model(), operator: str, number: int):
        super().__init__(number, operator)
        self.user = user

    def query(self) -> Q:
        """
        Gets the Q query object
        :return: The Q object
        """
        assert self.operator in ("<", "<=", "=", ">=", ">")
        raw = Card.objects.raw(
            f"""
SELECT cards_card.id
FROM cards_card
JOIN cards_cardprinting
  ON cards_cardprinting.card_id = cards_card.id
JOIN cards_cardlocalisation
  ON cards_cardprinting.id = cards_cardlocalisation.card_printing_id
LEFT JOIN cards_userownedcard
  ON cards_userownedcard.card_localisation_id = cards_cardlocalisation.id
  AND cards_userownedcard.owner_id = %s
GROUP BY cards_card.id
HAVING SUM(COALESCE(cards_userownedcard.count, 0)) {self.operator} %s
        """,
            [self.user.id, self.number],
        )
        return Q(card_id__in=raw)

    def get_pretty_str(self) -> str:
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


class CardUsageCountParam(CardNumericalParam):
    """
    The parameter for searching by how many times it has been used in a deck
    """

    def __init__(self, user: get_user_model(), operator: str, number: int):
        super().__init__(number, operator)
        self.user = user

    def query(self) -> Q:
        """
        Gets the Q query object
        :return: The Q object
        """
        raw = Card.objects.raw(
            f"""
SELECT cards_card.id
FROM cards_card
LEFT JOIN cards_deckcard ON cards_deckcard.card_id = cards_card.id
LEFT JOIN cards_deck ON cards_deck.id = cards_deckcard.deck_id AND cards_deck.owner_id = %s
GROUP BY cards_card.id
HAVING COUNT(cards_deck.id) {self.operator} %s
""",
            [self.user.id, self.number],
        )
        return Q(card_id__in=raw)

    def get_pretty_str(self) -> str:
        """
        Returns a human readable version of this parameter
        (and all sub parameters for those with children)
        :return: The pretty version of this parameter
        """
        if self.operator == "=" and self.number == 0:
            return "you haven't used it in a deck"
        return f"you used it in {self.operator} {self.number} decks"


class CardMissingPauperParam(CardSearchParam):
    """
    A parameter for searching for cards that the user owns a rare version of,
    but doesn't own a common or uncommon variant that they can use in pauper
    """

    def __init__(self, user: get_user_model()):
        super().__init__()
        self.user = user

    def query(self) -> Q:
        """
        Gets the Q query object
        :return: The Q object
        """
        raw = Card.objects.raw(
            f"""
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
WHERE cards_userownedcard.owner_id = %s
AND cards_rarity.symbol IN ('R', 'M')
AND cards_set.release_date >= (SELECT release_date FROM cards_set WHERE cards_set.code = 'EXO')

INTERSECT 

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
AND cards_set.release_date >= (SELECT release_date FROM cards_set WHERE cards_set.code = 'EXO')

EXCEPT

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
WHERE cards_userownedcard.owner_id = %s
AND cards_rarity.symbol IN ('U', 'C')
""",
            [self.user.id, self.user.id],
        )
        return ~Q(card_id__in=raw) if self.negated else Q(card_id__in=raw)

    def get_pretty_str(self) -> str:
        """
        Returns a human-readable version of this parameter
        (and all sub parameters for those with children)
        :return: The pretty version of this parameter
        """
        return "you are missing pauper variant of it"
