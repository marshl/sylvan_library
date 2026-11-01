"""
Card ownership parameters
"""

import operator
from typing import List

from django.db import connection
from django.db.models import Exists, OuterRef, Q, Sum

from sylvan_library.cards.models.card import UserOwnedCard
from sylvan_library.cardsearch.parameters.base_parameters import (
    CardSearchNumericalParameter,
    CardSearchContext,
    QueryContext,
    QueryValidationError,
    CardSearchBinaryParameter,
    OPERATOR_MAPPING,
    ParameterArgs,
)


# The comparison function for each search operator
OPERATOR_FUNCTIONS = {
    "<": operator.lt,
    "<=": operator.le,
    "=": operator.eq,
    ">=": operator.ge,
    ">": operator.gt,
}


class CardOwnershipCountParam(CardSearchNumericalParameter):
    """
    The parameter for searching by how many a user owns of it: of the card in a card
    search, or of each printing in a printing search
    """

    @classmethod
    def get_parameter_name(cls) -> str:
        return "ownership"

    @classmethod
    def get_search_keywords(cls) -> List[str]:
        return ["have", "own"]

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

    def query(self, query_context: QueryContext) -> Q:
        assert self.operator in ("<", "<=", "=", ">=", ">")

        # Ownerships are matched to the printing in a printing search, or to any printing
        # of the card in a card search
        if query_context.search_mode == CardSearchContext.PRINTING:
            outer_field = "id"
            ownership_field = "card_localisation__card_printing_id"
        else:
            outer_field = "card_id"
            ownership_field = "card_localisation__card_printing__card_id"
        ownerships = UserOwnedCard.objects.filter(owner=query_context.user, count__gt=0)

        # Owning any and owning none are the common searches, and checking whether an
        # ownership exists for each row is much cheaper than adding up the counts
        exists = Exists(ownerships.filter(**{ownership_field: OuterRef(outer_field)}))
        if (self.operator, self.number) in ((">=", 1), (">", 0)):
            return Q(exists, _negated=self.negated)

        if (self.operator, self.number) in (("=", 0), ("<=", 0), ("<", 1)):
            return Q(exists, _negated=not self.negated)

        # Otherwise total up the user's ownerships once, which only touches the rows
        # they own. Anything they don't own has a total of 0, so when 0 matches the
        # condition, search for everything except the owned rows that don't match.
        compare = OPERATOR_FUNCTIONS[self.operator]
        totals = (
            ownerships.values(ownership_field)
            .annotate(total=Sum("count"))
            .values(ownership_field)
        )
        condition = {f"total{OPERATOR_MAPPING[self.operator]}": self.number}
        if compare(0, self.number):
            return Q(
                **{f"{outer_field}__in": totals.exclude(**condition)},
                _negated=not self.negated,
            )

        return Q(
            **{f"{outer_field}__in": totals.filter(**condition)},
            _negated=self.negated,
        )

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

    def __init__(self, param_args: ParameterArgs, negated: bool = False):
        super().__init__(param_args, negated)
        self.only_commanders = False

    @classmethod
    def get_parameter_name(cls) -> str:
        return "usage"

    @classmethod
    def get_search_keywords(cls) -> List[str]:
        return ["used"]

    def validate(self, query_context: QueryContext) -> None:
        if not query_context.user or query_context.user.is_anonymous:
            raise QueryValidationError("Can't search by deck usage if not logged in")

        if self.operator == ":":
            if self.value == "commander":
                self.operator = ">="
                self.number = 1
                self.only_commanders = True
            elif self.value in ("any", "ever"):
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
        with connection.cursor() as cursor:
            cursor.execute(
                f"""
SELECT cards_card.id
FROM cards_card
LEFT JOIN cards_deckcard 
ON cards_deckcard.card_id = cards_card.id
AND (cards_deckcard.is_commander OR NOT %(only_commanders)s)
LEFT JOIN cards_deck 
ON cards_deck.id = cards_deckcard.deck_id 
AND cards_deck.owner_id = %(user_id)s
GROUP BY cards_card.id
HAVING COUNT(cards_deck.id) {self.operator} %(number)s
""",
                {
                    "user_id": query_context.user.id,
                    "number": self.number,
                    "only_commanders": self.only_commanders,
                },
            )
            ids = cursor.fetchall()
            ids = list(sum(ids, ()))
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
        return [
            "missing-pauper",
            "missingpauper",
            "nopauper",
            "missing-peasant",
            "missingpeasant",
            "nopeasant",
        ]

    @classmethod
    def get_parameter_name(cls) -> str:
        return "missing pauper"

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

            include_rarities = ["C"]
            exclude_rarities = ["R", "M"]

            if self.value in ["missing-pauper", "missingpauper", "nopauper"]:
                exclude_rarities.append("U")
            else:
                include_rarities.append("U")

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
AND cards_rarity.symbol = ANY(%(exclude_rarities)s)
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
WHERE cards_rarity.symbol = ANY(%(include_rarities)s)
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
AND cards_rarity.symbol = ANY(%(include_rarities)s)
""",
                {
                    "user_id": query_context.user.id,
                    "include_rarities": include_rarities,
                    "exclude_rarities": exclude_rarities,
                },
            )
            rows = cursor.fetchall()
            ids = list(sum(rows, ()))
        return Q(card_id__in=ids, _negated=self.negated)

    def get_pretty_str(self, query_context: QueryContext) -> str:
        """
        Returns a human-readable version of this parameter
        (and all sub parameters for those with children)
        :return: The pretty version of this parameter
        """
        return "you are missing pauper variant of it"
