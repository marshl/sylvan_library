"""
Card mana cost parameters
"""
from collections import Counter

import typing
from django.db.models import F
from django.db.models.query import Q

from .base_parameters import CardNumericalParam, CardSearchParam, OPERATOR_MAPPING


class CardManaCostParam(CardSearchParam):
    """
    The parameter for searching by a card's mana cost
    """

    def __init__(self, cost: str, exact_match: bool):
        super().__init__()
        self.cost = cost
        self.exact_match = exact_match

    def query(self) -> Q:
        return (
            Q(card__cost=self.cost)
            if self.exact_match
            else Q(card__cost__icontains=self.cost)
        )

    def get_pretty_str(self) -> str:
        verb = "isn't" if self.negated else "is"
        if self.exact_match:
            verb = f"{verb} exactly"
        return f"card colour {verb} {self.cost}"


SYMBOL_REMAPPING = {
    "w/r": "r/w",
    "u/g": "g/u",
    "b/w": "w/b",
    "r/u": "u/r",
    "g/b": "b/g",
}


class CardManaCostComplexParam(CardSearchParam):
    """
    Parameter for complex mana cost checking
    """

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

    def __init__(self, cost: str, operator: str) -> None:
        super().__init__()
        self.cost_text: str = cost.lower()
        self.operator: str = ">=" if operator == ":" else operator
        self.symbol_counts = {}

        self.symbol_counts: typing.Counter[str] = Counter()
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
                    raise ValueError(
                        f"Could not parse {self.cost_text}: unexpected '{{'"
                    )
            elif in_symbol:
                current_symbol += char
            elif not in_symbol:
                self.symbol_counts[char] += 1

            pos += 1

        if in_symbol:
            raise ValueError(f"Could not parse {self.cost_text}: expected '}}'")

        self.generic_mana = 0
        for symbol, _ in dict(self.symbol_counts).items():
            try:
                self.generic_mana = int(symbol)
                del self.symbol_counts[symbol]
            except (TypeError, ValueError):
                continue

    def query(self) -> Q:
        query = Q()

        for symbol, count in dict(self.symbol_counts).items():
            if symbol.upper() not in self.symbols:
                raise ValueError(f'Unknown symbol "{symbol}"')

            query &= Q(
                **{
                    "card__faces__search_metadata__symbol_count_"
                    + symbol.lower().replace("/", "_")
                    + OPERATOR_MAPPING[self.operator]: count
                }
            )

        if self.generic_mana:
            query &= Q(
                **{
                    "card__faces__search_metadata__symbol_count_generic"
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
                        "card__faces__search_metadata__symbol_count_"
                        + symbol.lower().replace("/", "_"): 0
                    }
                )

            # Only include cards with no generic mana
            if not self.generic_mana:
                query &= Q(
                    **{
                        "card__faces__search_metadata__symbol_count_generic"
                        + OPERATOR_MAPPING[self.operator]: 0
                    }
                )

        return ~query if self.negated else query

    def get_pretty_str(self) -> str:
        """
        Returns a human readable version of this parameter
        (and all sub parameters for those with children)
        :return: The pretty version of this parameter
        """
        return f"mana cost {'does not contain' if self.negated else 'contains'} {self.cost_text}"


class CardColourCountParam(CardNumericalParam):
    """
    Parameter for the number of colours a card has
    """

    def __init__(self, number: int, operator: str, identity: bool = False):
        super().__init__(number, operator)
        self.identity = identity
        self.operator = "=" if self.identity and operator == ":" else operator

    def query(self) -> Q:
        """
        Gets the Q query object
        :return: The Q query object
        """
        args = (
            self.get_args("card__colour_identity_count")
            if self.identity
            else self.get_args("card__faces__colour_count")
        )
        return Q(**args)

    def get_pretty_str(self) -> str:
        """
        Returns a human readable version of this parameter
        (and all sub parameters for those with children)
        :return: The pretty version of this parameter
        """
        return (
            "card "
            + ("doesn't have" if self.negated else "has")
            + f" {self.operator} {self.number} colours"
        )


class CardManaValueParam(CardNumericalParam):
    """
    The parameter for searching by a card's numerical mana value
    """

    def query(self) -> Q:
        args = self.get_args("card__mana_value")
        query = Q()
        if isinstance(self.number, F):
            query &= Q(**{"toughness__isnull": False})
        return query & Q(**args)

    def get_pretty_str(self) -> str:
        return (
            "mana value "
            + ("isn't " if self.negated else "")
            + f"{self.operator} {self.number}"
        )
