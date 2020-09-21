"""
Card rules text parameters
"""
from typing import List

from django.db.models import F, Value
from django.db.models.functions import Concat
from django.db.models.query import Q

from cards.models import Colour
from cards.models.colour import colours_to_symbols
from .base_parameters import CardSearchParam, or_group_queries, and_group_queries


class CardRulesTextParam(CardSearchParam):
    """
    The parameter for searching by a card's rules text
    """

    def __init__(self, card_rules: str, exact: bool = False):
        super().__init__()
        self.card_rules: str = card_rules
        self.exact_match: bool = exact
        if self.card_rules.startswith("/") and self.card_rules.endswith("/"):
            self.regex_match: bool = True
            # self.card_rules = "(?m)" + self.card_rules.strip("/")
            self.card_rules = self.card_rules.strip("/")
            if self.exact_match:
                self.card_rules = "^" + self.card_rules + "$"
        else:
            self.regex_match: bool = False

    def query(self) -> Q:
        if "~" not in self.card_rules:
            if self.regex_match:
                query = Q(card__rules_text__iregex=self.card_rules)
            elif self.exact_match:
                query = Q(card__rules_text__iexact=self.card_rules)
            else:
                query = Q(card__rules_text__icontains=self.card_rules)
            return ~query if self.negated else query

        chunks = [Value(c) for c in self.card_rules.split("~")]
        params = [F("card__name")] * (len(chunks) * 2 - 1)
        params[0::2] = chunks
        if self.regex_match:
            query = Q(card__rules_text__iregex=Concat(*params))
        elif self.exact_match:
            query = Q(card__rules_text__iexact=Concat(*params))
        else:
            query = Q(card__rules_text__icontains=Concat(*params))

        params = [Value("this spell")] * (len(chunks) * 2 - 1)
        params[0::2] = chunks
        if self.regex_match:
            query |= Q(card__rules_text__iregex=Concat(*params))
        elif self.exact_match:
            query |= Q(card__rules_text__iexact=Concat(*params))
        else:
            query |= Q(card__rules_text__icontains=Concat(*params))

        return ~query if self.negated else query

    def get_pretty_str(self) -> str:
        """
        Returns a human readable version of this parameter
        (and all sub parameters for those with children)
        :return: The pretty version of this parameter
        """
        if self.negated:
            modifier = "is not" if self.exact_match else "does not contain"
        else:
            modifier = "is" if self.exact_match else "contains"
        return f'the rules text {modifier} "{self.card_rules}"'


class CardProducesManaParam(CardSearchParam):
    """
    Parameter for the mana that a card can produce
    """

    def __init__(
        self, colours: List[Colour], operator: str = "=", any_colour: bool = False
    ):
        super().__init__()
        self.colours = colours
        self.operator = ">=" if operator == ":" else operator
        self.any_colour = any_colour

    def query(self) -> Q:
        if self.any_colour:
            query = Q(card__rules_text__iregex=r"adds?\W")
            return ~query if self.negated else query

        included_colours: List[Q] = []
        excluded_colours: List[Q] = []

        for colour in Colour.objects.all():
            query_part = Q(
                **{"card__search_metadata__produces_" + colour.symbol.lower(): True}
            )
            included = colour in self.colours

            if included:
                included_colours.append(query_part)
            else:
                excluded_colours.append(query_part)

        if self.operator in ("<", "<="):
            query = or_group_queries(included_colours) & ~or_group_queries(
                included_colours
            )

            if self.operator == "<":
                query &= ~and_group_queries(included_colours)
        else:
            query = and_group_queries(included_colours)
            if self.operator == "=":
                query &= ~or_group_queries(excluded_colours)
            elif self.operator == ">":
                query &= or_group_queries(excluded_colours)

        return ~query if self.negated else query

    def get_pretty_str(self) -> str:
        verb = "doesn't produce" if self.negated else "produces"
        if self.any_colour:
            colour_names = "any colour"
        else:
            colour_names = colours_to_symbols(self.colours)
        return f"card {verb} {self.operator} {colour_names}"


class CardWatermarkParam(CardSearchParam):
    """
    Parameter for whether a printing has a watermark or not
    """

    def __init__(self, watermark: str):
        super().__init__()
        self.watermark = watermark

    def query(self) -> Q:
        return Q(watermark__iexact=self.watermark)

    def get_pretty_str(self) -> str:
        return (
            "card "
            + ("doesn't have " if self.negated else "has")
            + " a "
            + self.watermark
            + " watermark"
        )
