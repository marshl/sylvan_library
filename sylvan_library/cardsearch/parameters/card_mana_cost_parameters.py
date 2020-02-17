"""
Card mana cost parameters
"""
from collections import Counter

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

    def __init__(self, cost: str, operator: str) -> None:
        super().__init__()
        self.cost_text: str = cost.lower()
        self.operator: str = operator

        self.symbol_counts: Counter[int] = Counter()
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

    def query(self) -> Q:
        query = Q()

        for symbol, count in dict(self.symbol_counts).items():
            num = None
            try:
                num = int(symbol)
            except (TypeError, ValueError):
                pass

            if num is not None:
                query &= Q(
                    **{
                        "card__generic_mana_count"
                        + OPERATOR_MAPPING[self.operator]: num
                    }
                )
            else:
                query &= Q(card__cost__icontains=("{" + symbol + "}") * count)
                if self.operator == "=":
                    query &= ~Q(
                        card__cost__icontains=("{" + symbol + "}") * (count + 1)
                    )

        return query

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
            else self.get_args("card__colour_count")
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


class CardCmcParam(CardNumericalParam):
    """
    The parameter for searching by a card's numerical converted mana cost
    """

    def query(self) -> Q:
        args = self.get_args("card__cmc")
        query = Q()
        if isinstance(self.number, F):
            query &= Q(**{"toughness__isnull": False})
        return query & Q(**args)

    def get_pretty_str(self) -> str:
        return (
            "cmd "
            + ("isn't " if self.negated else "")
            + f"{self.operator} {self.number}"
        )
