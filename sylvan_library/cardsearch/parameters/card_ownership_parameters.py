"""
Card ownership parameters
"""
from django.contrib.auth.models import User
from django.db.models import Q

from cards.models import Card
from .base_parameters import CardNumericalParam
from .base_parameters import CardSearchParam


class CardOwnerParam(CardSearchParam):
    """
    The parameter for searching by whether it is owned by a given user
    """

    def __init__(self, user: User):
        super().__init__()
        self.user = user

    def query(self) -> Q:
        return Q(localisations__ownerships__owner=self.user)

    def get_pretty_str(self) -> str:
        verb = "don't own" if self.negated else "own"
        return f"{verb} the card"


class CardOwnershipCountParam(CardNumericalParam):
    """
    The parameter for searching by how many a user owns of it
    """

    def __init__(self, user: User, operator: str, number: int):
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
JOIN cards_cardprinting ON cards_cardprinting.card_id = cards_card.id
JOIN cards_cardlocalisation ON cards_cardprinting.id = cards_cardlocalisation.card_printing_id
LEFT JOIN cards_userownedcard ON cards_userownedcard.card_localisation_id = cards_cardlocalisation.id
AND cards_userownedcard.owner_id = %s
GROUP BY cards_card.id
HAVING SUM(COALESCE(cards_userownedcard.count, 0)) {self.operator} %s
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
        if self.operator in ("<", "<=", "=") and self.number <= 0:
            return "you you don't own any"

        if (self.operator == ">" and self.number == 0) or (
            self.operator == ">=" and self.number == 1
        ):
            return "you own it"

        return f"you own {self.operator} {self.number}"


class CardUsageCountParam(CardNumericalParam):
    """
    The parameter for searching by how many times it has been used in a deck
    """

    def __init__(self, user: User, operator: str, number: int):
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
HAVING COUNT(cards_deckcard.id) {self.operator} %s
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
