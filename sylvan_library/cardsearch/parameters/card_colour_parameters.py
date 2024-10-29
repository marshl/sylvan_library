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
    CardSearchBinaryParameter,
    CardSearchContext,
    QueryContext,
    CardSearchParameter,
    ParameterArgs,
)


class CardComplexColourParam(CardSearchParameter):
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

    def __init__(self, param_args: ParameterArgs, negated: bool = False):
        super().__init__(param_args, negated)
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

        prefix = (
            "card__" if query_context.search_mode == CardSearchContext.PRINTING else ""
        )

        if self.operator == "=":
            result = Q(**{f"{prefix}{self.field_name}": colour_flags})
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
            if query_context.search_mode == CardSearchContext.CARD:
                result = Q(id__in=annotated_result.values_list("id"))
            else:
                result = Q(card__in=annotated_result)

        return ~result if self.negated else result

    def get_pretty_str(self, query_context: QueryContext) -> str:
        if self.colours == 0:
            return (
                "is cards have colourless identity"
                if self.search_by_identity
                else "the cards are colourless"
            )

        if self.search_by_identity:
            param_type = "colour identity"
            if self.operator == "=":
                operator_text = "is not" if self.negated else "is"
            else:
                operator_text = self.operator
        else:
            param_type = "colours"
            if self.operator == "=":
                operator_text = "are not" if self.negated else "are"
            else:
                operator_text = self.operator

        return f"the {param_type} {operator_text} {colours_to_symbols(self.colours)}"


class CardMulticolouredOnlyParam(CardSearchBinaryParameter):
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
        if query_context.search_mode == CardSearchContext.CARD:
            return Q(faces__colour_count__gte=2, _negated=self.negated)
        return Q(card__faces__colour_count__gte=2, _negated=self.negated)

    def get_pretty_str(self, query_context: QueryContext) -> str:
        verb = "isn't" if self.negated else "is"
        return f"card {verb} multicoloured"
