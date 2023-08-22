"""
Card name parameters
"""
from typing import List

from django.db.models.query import Q

from cardsearch.parameters.base_parameters import (
    OPERATOR_MAPPING,
    CardSearchContext,
    ParameterArgs,
    QueryContext,
    CardTextParameter,
)


class CardNameParam(CardTextParameter):
    """
    The parameter for searching by a card's name
    """

    def get_default_search_context(self) -> CardSearchContext:
        return CardSearchContext.CARD

    @classmethod
    def get_parameter_name(cls) -> str:
        return "name"

    @classmethod
    def get_search_operators(cls) -> List[str]:
        return [":", "=", ">", ">=", "<", "<="]

    @classmethod
    def get_search_keywords(cls) -> List[str]:
        return ["name", "n"]

    def __init__(self, negated: bool, param_args: ParameterArgs):
        super().__init__(negated, param_args)
        match_exact = self.operator == "="
        if self.value.startswith("!"):
            match_exact = True
            self.value = self.value[1:]

        self.match_exact = match_exact
        self.regex_match: bool = False

        if self.value.startswith("/") and self.value.endswith("/"):
            self.regex_match = True
            self.card_name = self.value.strip("/")
            if self.match_exact:
                self.card_name = "^" + self.card_name + "$"

    def query(self, query_context: QueryContext) -> Q:
        if self.regex_match:
            query = Q(card__name__iregex=self.card_name)
        elif self.match_exact:
            query = Q(card__name__iexact=self.card_name)
        elif self.operator == ":":
            query = Q(card__name__icontains=self.card_name)
        else:
            django_op = OPERATOR_MAPPING[self.operator]
            query = Q(**{"card__name" + django_op: self.card_name})

        return ~query if self.negated else query

    def get_pretty_str(self, query_context: QueryContext) -> str:
        """
        Returns a human-readable version of this parameter
        (and all sub parameters for those with children)
        :return: The pretty version of this parameter
        """
        if self.negated:
            return f'the name does not contain "{self.card_name}"'
        return f'the name contains "{self.card_name}"'
