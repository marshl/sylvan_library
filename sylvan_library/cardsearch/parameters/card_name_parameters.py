"""
Card name parameters
"""

from typing import List

from django.db.models.query import Q

from sylvan_library.cardsearch.parameters.base_parameters import (
    OPERATOR_MAPPING,
    ParameterArgs,
    QueryContext,
    CardSearchParameter,
)


class CardNameParam(CardSearchParameter):
    """
    The parameter for searching by a card's name
    """

    @classmethod
    def get_parameter_name(cls) -> str:
        return "name"

    @classmethod
    def get_search_operators(cls) -> List[str]:
        return [":", "=", ">", ">=", "<", "<="]

    @classmethod
    def get_search_keywords(cls) -> List[str]:
        return ["name", "n"]

    def __init__(self, param_args: ParameterArgs, negated: bool = False):
        super().__init__(param_args, negated)
        match_exact = self.operator == "="
        if self.value.startswith("!"):
            match_exact = True
            self.value = self.value[1:]

        self.match_exact = match_exact
        self.regex_match: bool = param_args.is_regex

    def query(self, query_context: QueryContext) -> Q:
        name_column = "card__name"
        if self.regex_match:
            query = Q(**{f"{name_column}__iregex": self.value})
        elif self.match_exact:
            query = Q(**{f"{name_column}__iexact": self.value})
        elif self.operator == ":":
            query = Q(**{f"{name_column}__icontains": self.value})
        else:
            django_op = OPERATOR_MAPPING[self.operator]
            query = Q(**{name_column + django_op: self.value})

        return ~query if self.negated else query

    def get_pretty_str(self, query_context: QueryContext) -> str:
        """
        Returns a human-readable version of this parameter
        (and all sub parameters for those with children)
        :return: The pretty version of this parameter
        """
        if self.match_exact:
            verb = "isn't" if self.negated else "is"
        else:
            verb = "does not contain" if self.negated else "contains"
        return f'the name {verb} "{self.value}"'
