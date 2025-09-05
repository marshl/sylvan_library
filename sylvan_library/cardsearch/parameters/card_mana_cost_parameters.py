"""
Card mana cost parameters
"""

from collections import Counter

import typing
from typing import List

from django.db.models.query import Q

from cardsearch.parameters.base_parameters import (
    OPERATOR_MAPPING,
    CardSearchNumericalParameter,
    CardSearchContext,
    ParameterArgs,
    QueryContext,
    QueryValidationError,
    CardSearchParameter,
)


SYMBOL_REMAPPING = {
    "w/r": "r/w",
    "u/g": "g/u",
    "b/w": "w/b",
    "r/u": "u/r",
    "g/b": "b/g",
}


class CardManaCostComplexParam(CardSearchParameter):
    """
    Parameter for complex mana cost checking
    """

    def get_default_search_context(self) -> CardSearchContext:
        return CardSearchContext.CARD

    @classmethod
    def get_parameter_name(cls) -> str:
        return "mana cost"

    @classmethod
    def get_search_operators(cls) -> List[str]:
        return [":", "=", "<", "<=", ">", ">="]

    @classmethod
    def get_search_keywords(cls) -> List[str]:
        return ["mana", "m"]

    @classmethod
    def matches_param_args(cls, param_args: ParameterArgs) -> bool:
        if not super().matches_param_args(param_args):
            return False

        try:
            int(param_args.value)
            return False
        except (TypeError, ValueError):
            pass

        return True

    symbols = [
        "W",
        "U",
        "B",
        "R",
        "G",
        "C",
        "X",
        "S",
        "W/U",
        "U/B",
        "B/R",
        "R/G",
        "G/W",
        "W/B",
        "U/R",
        "B/G",
        "R/W",
        "G/U",
        "2/W",
        "2/U",
        "2/B",
        "2/R",
        "2/G",
        "W/P",
        "U/P",
        "B/P",
        "R/P",
        "G/P",
    ]

    def __init__(self, param_args: ParameterArgs, negated: bool = False) -> None:
        super().__init__(param_args, negated)
        self.cost_text: str = self.value.lower()
        self.operator: str = ">=" if self.operator == ":" else self.operator
        self.symbol_counts: typing.Counter[str] = Counter()
        self.generic_mana = 0

    def validate(self, query_context: QueryContext) -> None:
        self.symbol_counts = Counter()
        pos: int = 0
        current_symbol: str = ""
        in_symbol: bool = False
        while True:
            if pos >= len(self.cost_text):
                break
            char: str = self.cost_text[pos]
            if char == "{":
                if in_symbol:
                    raise ValueError(
                        f"Could not parse {self.cost_text}: unexpected '{{'"
                    )
                in_symbol = True
                current_symbol = ""
            elif char == "}":
                if in_symbol:
                    self.symbol_counts[
                        SYMBOL_REMAPPING.get(current_symbol, current_symbol)
                    ] += 1

                    in_symbol = False
                else:
                    raise QueryValidationError(
                        f"Could not parse {self.cost_text}: unexpected '{{'"
                    )
            elif in_symbol:
                current_symbol += char
            elif not in_symbol:
                self.symbol_counts[char] += 1

            pos += 1

        if in_symbol:
            raise QueryValidationError(
                f"Could not parse {self.cost_text}: expected '}}'"
            )

        self.generic_mana = 0
        for symbol, _ in dict(self.symbol_counts).items():
            try:
                self.generic_mana = int(symbol)
                del self.symbol_counts[symbol]
            except (TypeError, ValueError):
                continue

    def query(self, query_context: QueryContext) -> Q:
        query = Q()

        prefix = (
            "card__" if query_context.search_mode == CardSearchContext.PRINTING else ""
        )
        for symbol, count in dict(self.symbol_counts).items():
            if symbol.upper() not in self.symbols:
                raise ValueError(f'Unknown symbol "{symbol}"')

            query &= Q(
                **{
                    prefix
                    + "faces__search_metadata__symbol_count_"
                    + symbol.lower().replace("/", "_")
                    + OPERATOR_MAPPING[self.operator]: count
                }
            )

        if self.generic_mana:
            query &= Q(
                **{
                    prefix
                    + "faces__search_metadata__symbol_count_generic"
                    + OPERATOR_MAPPING[self.operator]: self.generic_mana
                }
            )

        # If we are in "less than" mode
        if self.operator in ("<", "<=", "="):
            # Exclude cards with any other symbol
            for symbol in self.symbols:
                if symbol.lower() in self.symbol_counts:
                    continue
                query &= Q(
                    **{
                        prefix
                        + "faces__search_metadata__symbol_count_"
                        + symbol.lower().replace("/", "_"): 0
                    }
                )

            # Only include cards with no generic mana
            if not self.generic_mana:
                query &= Q(
                    **{
                        prefix
                        + "faces__search_metadata__symbol_count_generic"
                        + OPERATOR_MAPPING[self.operator]: 0
                    }
                )
        query.negated = self.negated
        return query

    def get_pretty_str(self, query_context: QueryContext) -> str:
        """
        Returns a human-readable version of this parameter
        (and all sub parameters for those with children)
        :return: The pretty version of this parameter
        """
        return f"mana cost {'does not contain' if self.negated else 'contains'} {self.cost_text}"


class CardColourCountParam(CardSearchNumericalParameter):
    """
    Parameter for the number of colours a card has
    """

    def get_default_search_context(self) -> CardSearchContext:
        return CardSearchContext.CARD

    @classmethod
    def get_parameter_name(cls) -> str:
        return "colour"

    @classmethod
    def get_search_operators(cls) -> List[str]:
        return [":", "=", "<", "<=", ">", ">="]

    @classmethod
    def get_search_keywords(cls) -> List[str]:
        return ["colour", "color", "col", "c", "identity", "ci", "id"]

    @classmethod
    def matches_param_args(cls, param_args: ParameterArgs) -> bool:
        if not super().matches_param_args(param_args):
            return False

        try:
            int(param_args.value)
            return True
        except (TypeError, ValueError):
            return False

    def __init__(self, param_args: ParameterArgs, negated: bool = False):
        super().__init__(param_args, negated)
        self.in_identity_mode = param_args.keyword in ["identity", "di", "id"]
        if self.in_identity_mode and self.operator == ":":
            self.operator = "="

    def query(self, query_context: QueryContext) -> Q:
        """
        Gets the Q query object
        :return: The Q query object
        """
        prefix = (
            "card__" if query_context.search_mode == CardSearchContext.PRINTING else ""
        )
        args = (
            self.get_args(f"{prefix}colour_identity_count", query_context)
            if self.in_identity_mode
            else self.get_args(f"{prefix}faces__colour_count", query_context)
        )
        args["_negated"] = self.negated
        return Q(**args)

    def get_pretty_str(self, query_context: QueryContext) -> str:
        """
        Returns a human-readable version of this parameter
        (and all sub parameters for those with children)
        :return: The pretty version of this parameter
        """
        operator_text = "" if self.operator == "=" else self.operator
        return (
            "card "
            + ("doesn't have" if self.negated else "has")
            + f" {operator_text} {self.value} colours"
        )


class CardManaValueParam(CardSearchNumericalParameter):
    """
    The parameter for searching by a card's numerical mana value
    """

    @classmethod
    def get_parameter_name(cls) -> str:
        return "mana value"

    @classmethod
    def get_search_keywords(cls) -> List[str]:
        return ["cmc", "manavalue", "mv"]

    def get_default_search_context(self) -> CardSearchContext:
        return CardSearchContext.CARD

    def query(self, query_context: QueryContext) -> Q:
        prefix = (
            "card__" if query_context.search_mode == CardSearchContext.PRINTING else ""
        )
        args = self.get_args(f"{prefix}mana_value", query_context)
        query = Q(**args)
        return query

    def get_pretty_str(self, query_context: QueryContext) -> str:
        return (
            "mana value "
            + ("isn't " if self.negated else "")
            + f"{self.operator} {self.value}"
        )
