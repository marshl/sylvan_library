"""
Card rules text parameters
"""

from typing import List

from django.db.models import F, Value
from django.db.models.functions import Concat
from django.db.models.query import Q

from cards.models import colour
from cards.models.colour import Colour, colours_to_symbols
from cardsearch.parameters.base_parameters import (
    and_group_queries,
    or_group_queries,
    CardSearchContext,
    QueryContext,
    CardSearchParameter,
    ParameterArgs,
)


class CardRulesTextParam(CardSearchParameter):
    """
    The parameter for searching by a card's rules text
    """

    @classmethod
    def get_parameter_name(cls) -> str:
        return "rules text"

    @classmethod
    def get_search_operators(cls) -> List[str]:
        return [":", "="]

    @classmethod
    def get_search_keywords(cls) -> List[str]:
        return ["oracle", "rules", "text", "o"]

    def get_default_search_context(self) -> CardSearchContext:
        return CardSearchContext.CARD

    def __init__(self, param_args: ParameterArgs, negated: bool = False):
        super().__init__(param_args, negated)
        self.exact_match = self.operator == "="
        self.regex_match = param_args.is_regex

    def query(self, query_context: QueryContext) -> Q:
        if query_context.search_mode == CardSearchContext.CARD:
            return self.get_query("faces__rules_text", query_context)
        return self.get_query("card__faces__rules_text", query_context)

    def get_query(self, column_name: str, query_context: QueryContext):
        if "~" not in self.value:
            if self.regex_match:
                query = Q(**{f"{column_name}__iregex": self.value})
            elif self.exact_match:
                query = Q(**{f"{column_name}__iexact": self.value})
            else:
                query = Q(**{f"{column_name}__icontains": self.value})
            return ~query if self.negated else query

        name_column = (
            "card__name"
            if query_context.search_mode == CardSearchContext.PRINTING
            else "name"
        )
        chunks = [Value(c) for c in self.value.split("~")]
        params = [F(name_column)] * (len(chunks) * 2 - 1)
        params[0::2] = chunks
        if self.regex_match:
            query = Q(**{f"{column_name}__iregex": Concat(*params)})
        elif self.exact_match:
            query = Q(**{f"{column_name}__iexact": Concat(*params)})
        else:
            query = Q(**{f"{column_name}__icontains": Concat(*params)})

        params = [Value("this spell")] * (len(chunks) * 2 - 1)
        params[0::2] = chunks
        if self.regex_match:
            query |= Q(**{f"{column_name}__iregex": Concat(*params)})
        elif self.exact_match:
            query |= Q(**{f"{column_name}__iexact": Concat(*params)})
        else:
            query |= Q(**{f"{column_name}__icontains": Concat(*params)})

        return ~query if self.negated else query

    def get_pretty_str(self, query_context: QueryContext) -> str:
        if self.is_regex:
            if self.negated:
                modifier = "doesn't match the regex"
            else:
                modifier = "matches the regex"
        else:
            if self.negated:
                modifier = "is not" if self.exact_match else "does not contain"
            else:
                modifier = "is" if self.exact_match else "contains"
        return f'the rules text {modifier} "{self.value}"'


class CardOriginalRulesTextParam(CardRulesTextParam):
    """
    The parameter for searching by a card's original printing rules text
    """

    @classmethod
    def get_parameter_name(cls) -> str:
        return "original rules text"

    @classmethod
    def get_search_keywords(cls) -> List[str]:
        return ["otext", "orules"]

    def get_default_search_context(self) -> CardSearchContext:
        return CardSearchContext.PRINTING

    def query(self, query_context: QueryContext) -> Q:
        return self.get_query(
            (
                "card__faces__face_printings__original_text"
                if query_context.search_mode == CardSearchContext.PRINTING
                else "faces__face_printings__original_text"
            ),
            query_context,
        )

    def get_pretty_str(self, query_context: QueryContext) -> str:
        if self.negated:
            modifier = "is not" if self.exact_match else "does not contain"
        else:
            modifier = "is" if self.exact_match else "contains"
        return f'the original rules text {modifier} "{self.value}"'


class CardProducesManaParam(CardSearchParameter):
    """
    Parameter for the mana that a card can produce
    """

    @classmethod
    def get_parameter_name(cls) -> str:
        return "produces"

    @classmethod
    def get_search_operators(cls) -> List[str]:
        return [":", "=", "<", "<=", ">", ">="]

    @classmethod
    def get_search_keywords(cls) -> List[str]:
        return ["p", "produce", "produces"]

    def get_default_search_context(self) -> CardSearchContext:
        return CardSearchContext.CARD

    def __init__(self, param_args: ParameterArgs, negated: bool = False):
        super().__init__(param_args, negated)
        self.any_colour = "any"
        if self.any_colour:
            self.colours = []
        else:
            self.colours = colour.get_colours_for_nickname(self.value)
        self.operator = ">=" if self.operator == ":" else self.operator

    def query(self, query_context: QueryContext) -> Q:

        prefix = (
            "card__" if query_context.search_mode == CardSearchContext.PRINTING else ""
        )
        if self.any_colour:
            query = Q(**{f"{prefix}faces__rules_text__iregex": r"adds?\W"})
            return ~query if self.negated else query

        included_colours: List[Q] = []
        excluded_colours: List[Q] = []

        for c in Colour.objects.all():
            query_part = Q(
                **{
                    f"{prefix}faces__search_metadata__produces_"
                    + c.symbol.lower(): True
                }
            )
            included = c in self.colours

            if included:
                included_colours.append(query_part)
            else:
                excluded_colours.append(query_part)

        if self.operator in ("<", "<="):
            # pylint: disable=invalid-unary-operand-type
            query = or_group_queries(included_colours) & ~or_group_queries(
                included_colours
            )

            if self.operator == "<":
                query &= ~and_group_queries(included_colours)
        else:
            query = and_group_queries(included_colours)
            if self.operator == "=":
                # pylint: disable=invalid-unary-operand-type
                query &= ~or_group_queries(excluded_colours)
            elif self.operator == ">":
                query &= or_group_queries(excluded_colours)

        return ~query if self.negated else query

    def get_pretty_str(self, query_context: QueryContext) -> str:
        verb = "doesn't produce" if self.negated else "produces"
        if self.any_colour:
            colour_names = "any colour"
        else:
            colour_names = f"{self.operator} {colours_to_symbols(self.colours)}"
        return f"card {verb} {colour_names}"


class CardWatermarkParam(CardSearchParameter):
    """
    Parameter for whether a printing has a watermark or not
    """

    def get_default_search_context(self) -> CardSearchContext:
        return CardSearchContext.PRINTING

    @classmethod
    def get_parameter_name(cls) -> str:
        return "watermark"

    @classmethod
    def get_search_operators(cls) -> List[str]:
        return [":", "="]

    @classmethod
    def get_search_keywords(cls) -> List[str]:
        return ["watermark", "wm", "w"]

    def query(self, query_context: QueryContext) -> Q:
        return Q(face_printings__watermark__iexact=self.value)

    def get_pretty_str(self, query_context: QueryContext) -> str:
        return "card {} a {} watermark".format(
            "doesn't have " if self.negated else "has", self.value
        )
