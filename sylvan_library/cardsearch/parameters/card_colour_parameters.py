"""
Card colour parameters
"""
from typing import List

from django.db.models import F
from django.db.models.query import Q

from cards.models import colour
from cards.models.card import Card
from cards.models.colour import (
    colours_to_int_flags,
    colours_to_symbols,
)
from cardsearch.parameters.base_parameters import (
    CardIsParameter,
    CardSearchContext,
    QueryContext,
    CardTextParameter,
    ParameterArgs,
)


class CardComplexColourParam(CardTextParameter):
    """
    Parameter for complex card parameters, including subset superset and colour identity handling
    """

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
            return False
        except (TypeError, ValueError):
            return True

    def get_default_search_context(self) -> CardSearchContext:
        return CardSearchContext.CARD

    def __init__(self, negated: bool, param_args: ParameterArgs):
        super().__init__(negated, param_args)
        self.colours = colour.get_colours_for_nickname(self.value)
        self.search_by_identity = param_args.keyword in ["identity", "ci", "id"]
        if self.operator == ":":
            self.operator = "<=" if self.search_by_identity else ">="

    @property
    def field_name(self):
        """
        The field to use based on whether this is in colour identity mode or colour mode
        """
        return "colour_identity" if self.search_by_identity else "faces__colour"

    def query(self, query_context: QueryContext) -> Q:
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

    def get_pretty_str(self, query_context: QueryContext) -> str:
        if self.colours == 0:
            return (
                "is cards have colourless identity"
                if self.search_by_identity
                else "the cards are colourless"
            )

        param_type = "colour identity" if self.search_by_identity else "colours"
        operator_text = "is" if self.operator == "=" else self.operator
        return f"the {param_type} {operator_text} {colours_to_symbols(self.colours)}"


class CardMulticolouredOnlyParam(CardIsParameter):
    """
    The parameter for searching by whether a card is multicoloured or not
    """

    @classmethod
    def get_is_keywords(cls) -> List[str]:
        return ["multicoloured", "multicolored", "multi"]

    @classmethod
    def get_parameter_name(cls) -> str:
        return "is multicoloured"

    def get_default_search_context(self) -> CardSearchContext:
        return CardSearchContext.CARD

    def query(self, query_context: QueryContext) -> Q:
        return Q(card__faces__colour_count__gte=2, _negated=self.negated)

    def get_pretty_str(self, query_context: QueryContext) -> str:
        verb = "isn't" if self.negated else "is"
        return f"card {verb} multicoloured"
