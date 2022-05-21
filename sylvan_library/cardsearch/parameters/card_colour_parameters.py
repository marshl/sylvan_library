"""
Card colour parameters
"""
from typing import List

from django.db.models import F
from django.db.models.query import Q

from cards.models.card import Card
from cards.models.colour import (
    Colour,
    colours_to_int_flags,
    colours_to_symbols,
)
from cardsearch.parameters.base_parameters import CardSearchParam


class CardColourParam(CardSearchParam):
    """
    The parameter for searching by a card's colour
    """

    def __init__(self, card_colour: int):
        super().__init__()
        self.card_colour = card_colour

    def query(self) -> Q:
        return Q(card__face__colour_flags=self.card_colour)

    def get_pretty_str(self) -> str:
        verb = "isn't" if self.negated else "is"
        return f"card colour {verb} {self.card_colour}"


class CardComplexColourParam(CardSearchParam):
    """
    Parameter for complex card parameters, including subset superset and colour identity handling
    """

    def __init__(
        self, colours: List[Colour], operator: str = "=", identity: bool = False
    ) -> None:
        super().__init__()
        self.colours = colours
        if operator == ":":
            self.operator = "<=" if identity else ">="
        else:
            self.operator = operator
        self.identity = identity

    @property
    def field_name(self):
        """
        The field to use based on whether this is in colour identity mode or colour mode
        """
        return "colour_identity" if self.identity else "faces__colour"

    def query(self) -> Q:
        """
        Gets the Q query object
        :return: The Q query object
        """
        colour_flags = colours_to_int_flags(self.colours)

        if self.operator == "=":
            result = Q(**{f"card__{self.field_name}": colour_flags})
        else:
            if self.operator in (">=", ">"):
                annotated_result = Card.objects.annotate(
                    colour_filter=F(self.field_name).bitand(colour_flags)
                ).filter(colour_filter__gte=colour_flags)
                if self.operator == ">":
                    annotated_result = annotated_result.exclude(
                        **{self.field_name: colour_flags}
                    )
            elif self.operator in ("<=", "<"):
                # pylint: disable=invalid-unary-operand-type
                annotated_result = Card.objects.annotate(
                    colour_filter=F(self.field_name).bitand(~colour_flags)
                ).filter(colour_filter=0)
                if self.operator == "<":
                    annotated_result = annotated_result.exclude(
                        **{self.field_name: colour_flags}
                    )
            else:
                raise ValueError(f'Unsupported operator "{self.operator}"')
            result = Q(card__in=annotated_result)

        return ~result if self.negated else result

    def get_pretty_str(self) -> str:
        """
        Returns a human readable version of this parameter
        (and all sub parameters for those with children)
        :return: The pretty version of this parameter
        """
        if self.colours == 0:
            return (
                "is cards have colourless identity"
                if self.identity
                else "the cards are colourless"
            )

        param_type = "colour identity" if self.identity else "colours"
        operator_text = "is" if self.operator == "=" else self.operator
        return f"the {param_type} {operator_text} {colours_to_symbols(self.colours)}"


class CardColourIdentityParam(CardSearchParam):
    """
    The parameter for searching by a card's colour identity
    """

    def __init__(self, colour_identity: int):
        super().__init__()
        self.colour_identity = colour_identity

    def query(self) -> Q:
        return Q(card__colour_identity=self.colour_identity)

    def get_pretty_str(self) -> str:
        verb = "isn't" if self.negated else "is"
        return f"card colour identity {verb} {self.colour_identity}"


class CardMulticolouredOnlyParam(CardSearchParam):
    """
    The parameter for searching by whether a card is multicoloured or not
    """

    def query(self) -> Q:
        return Q(card__faces__colour_count__gte=2)

    def get_pretty_str(self) -> str:
        verb = "isn't" if self.negated else "is"
        return f"card {verb} multicoloured"
