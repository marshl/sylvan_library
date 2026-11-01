"""
Card ownership parameters
"""

import operator
from typing import List

from django.db import connection
from django.db.models import Aggregate, Count, Exists, OuterRef, Q, QuerySet, Sum

from sylvan_library.cards.models.card import UserOwnedCard
from sylvan_library.cards.models.decks import DeckCard
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


def count_query(
    rows: QuerySet,
    row_field: str,
    outer_field: str,
    total: Aggregate,
    operator_str: str,
    number: float,
    negated: bool,
) -> Q:
    """
    A filter on CardPrinting for comparing how many of the given rows each printing
    (or card) has
    :param rows: The user's rows to count, such as their ownerships
    :param row_field: The field on the rows that links them to the printing or card
    :param outer_field: The field on CardPrinting that row_field is matched against
    :param total: How to total up the rows for each printing or card. Having no rows
    must mean a total of 0, and having any rows a total of at least 1
    :param operator_str: The comparison operator
    :param number: The number to compare the total to
    :param negated: Whether to negate the comparison
    """
    # "Any" and "none" are the common searches, and checking whether a row exists is
    # much cheaper than totalling them up
    exists = Exists(rows.filter(**{row_field: OuterRef(outer_field)}))
    if (operator_str, number) in ((">=", 1), (">", 0)):
        return Q(exists, _negated=negated)
    if (operator_str, number) in (("=", 0), ("<=", 0), ("<", 1)):
        return Q(exists, _negated=not negated)

    # Otherwise total up the user's rows once, which only touches the rows they have.
    # Anything without rows has a total of 0, so when 0 matches the condition, search
    # for everything except the totals that don't match.
    totals = rows.order_by().values(row_field).annotate(total=total).values(row_field)
    condition = {f"total{OPERATOR_MAPPING[operator_str]}": number}
    if OPERATOR_FUNCTIONS[operator_str](0, number):
        return Q(
            **{f"{outer_field}__in": totals.exclude(**condition)},
            _negated=not negated,
        )
    return Q(**{f"{outer_field}__in": totals.filter(**condition)}, _negated=negated)


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
            row_field = "card_localisation__card_printing_id"
        else:
            outer_field = "card_id"
            row_field = "card_localisation__card_printing__card_id"

        return count_query(
            rows=UserOwnedCard.objects.filter(owner=query_context.user, count__gt=0),
            row_field=row_field,
            outer_field=outer_field,
            total=Sum("count"),
            operator_str=self.operator,
            number=self.number,
            negated=self.negated,
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
            else:
                self.operator = ">="

        super().validate(query_context)

    def query(self, query_context: QueryContext) -> Q:
        """
        Gets the Q query object
        :return: The Q object
        """
        assert self.operator in ("<", "<=", "=", ">=", ">")
        deck_cards = DeckCard.objects.filter(deck__owner=query_context.user)
        if self.only_commanders:
            deck_cards = deck_cards.filter(is_commander=True)

        # Deck cards are per card rather than per printing, so both search modes match
        # them on the card
        return count_query(
            rows=deck_cards,
            row_field="card_id",
            outer_field="card_id",
            total=Count("deck", distinct=True),
            operator_str=self.operator,
            number=self.number,
            negated=self.negated,
        )

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
