"""
Card colour parameters
"""
from bitfield.types import Bit
from django.db.models.query import Q

from cards.models import Colour
from .base_parameters import (
    CardSearchParam,
    validate_colour_flags,
    colour_flags_to_symbols,
)


class CardColourParam(CardSearchParam):
    """
    The parameter for searching by a card's colour
    """

    def __init__(self, card_colour: Bit):
        super().__init__()
        self.card_colour = card_colour

    def query(self) -> Q:
        return Q(card__colour_flags=self.card_colour)

    def get_pretty_str(self, within_or_block: bool = False) -> str:
        verb = "isn't" if self.negated else "is"
        return f"card colour {verb} {self.card_colour}"


class CardComplexColourParam(CardSearchParam):
    """
    Parameter for complex card parameters, including subset superset and colour identity handling
    """

    def __init__(self, colours: int, operator: str = "=", identity: bool = False):
        super().__init__()
        validate_colour_flags(colours)
        self.colours = colours
        if operator == ":":
            self.operator = "<=" if identity else ">="
        else:
            self.operator = operator
        self.identity = identity

    def query(self) -> Q:
        """
        Gets the Q query object
        :return: The Q query object
        """
        field = "card__colour_identity_flags" if self.identity else "card__colour_flags"
        if self.operator == ">=":
            return (
                ~Q(**{field: self.colours})
                if self.negated
                else Q(**{field: self.colours})
            )

        if self.operator == ">" or self.operator == "=":
            result = Q(**{field: self.colours})
            exclude = Q()

            for colour in Colour.objects.exclude(symbol="C"):
                if not colour.bit_value & self.colours:
                    exclude |= Q(**{field: colour.bit_value})
            if exclude:
                result &= exclude if self.operator == ">" else ~exclude
            return ~result if self.negated else result

        if self.operator == "<" or self.operator == "<=":
            include = Q()
            exclude = Q()
            for colour in Colour.objects.exclude(symbol="C"):
                if colour.bit_value & self.colours:
                    include |= Q(**{field: colour.bit_value})
                else:
                    exclude &= ~Q(**{field: colour.bit_value})

            if self.identity:
                include |= Q(card__colour_identity_flags=0)

            if self.operator == "<":
                result = include & exclude & ~Q(**{field: self.colours})
                return ~result if self.negated else result
            result = include & exclude
            return ~result if self.negated else result
        raise ValueError(f"Unsupported operator {self.operator}")

    def get_pretty_str(self, within_or_block: bool = False) -> str:
        """
        Returns a human readable version of this parameter
        (and all sub parameters for those with children)
        :param within_or_block: Whether this it being output inside an OR block
        :return: The pretty version of this parameter
        """
        if self.colours == 0:
            return (
                "is cards have colourless identity"
                if self.identity
                else "the cards are colourless"
            )

        param_type = "colour identity" if self.identity else "colours"
        return (
            f"the {param_type} {self.operator} {colour_flags_to_symbols(self.colours)}"
        )


class CardColourIdentityParam(CardSearchParam):
    """
    The parameter for searching by a card's colour identity
    """

    def __init__(self, colour_identity: Bit):
        super().__init__()
        self.colour_identity = colour_identity

    def query(self) -> Q:
        return Q(card__colour_identity_flags=self.colour_identity)

    def get_pretty_str(self, within_or_block: bool = False) -> str:
        verb = "isn't" if self.negated else "is"
        return f"card colour identity {verb} {self.colour_identity}"


class CardMulticolouredOnlyParam(CardSearchParam):
    """
    The parameter for searching by whether a card is multicoloured or not
    """

    def query(self) -> Q:
        return Q(card__colour_count__gt=1)

    def get_pretty_str(self, within_or_block: bool = False) -> str:
        verb = "isn't" if self.negated else "is"
        return f"card {verb} multicoloured"