"""
Miscellaneous card parameters (mostly the "is" and "has" parameters)
"""

from typing import List

from django.db.models import Q

from cardsearch.parameters.base_parameters import (
    CardSearchNumericalParameter,
    CardSearchContext,
    QueryContext,
    CardSearchParameter,
    CardSearchBinaryParameter,
)


class CardLayoutParameter(CardSearchParameter):
    """
    Parameter for whether a card has any phyrexian mana symbols or not
    """

    def get_default_search_context(self) -> CardSearchContext:
        return CardSearchContext.CARD

    @classmethod
    def get_parameter_name(cls) -> str:
        return "layout"

    @classmethod
    def get_search_operators(cls) -> List[str]:
        return [":", "="]

    @classmethod
    def get_search_keywords(cls) -> List[str]:
        return ["layout", "l"]

    def query(self, query_context: QueryContext) -> Q:
        return Q(card__layout=self.value, _negated=self.negated)

    def get_pretty_str(self, query_context: QueryContext) -> str:
        return f"card layout " + ("isn't" if self.negated else "is") + f" {self.value}"


class CardIsPhyrexianParam(CardSearchBinaryParameter):
    """
    Parameter for whether a card has any phyrexian mana symbols or not
    """

    @classmethod
    def get_is_keywords(cls) -> str:
        return "phyrexian"

    @classmethod
    def get_parameter_name(cls) -> str:
        return "is phyrexian"

    def get_default_search_context(self) -> CardSearchContext:
        return CardSearchContext.CARD

    def query(self, query_context: QueryContext) -> Q:
        query = Q(card__faces__mana_cost__icontains="/p") | Q(
            card__faces__rules_text__icontains="/p"
        )
        return ~query if self.negated else query

    def get_pretty_str(self, query_context: QueryContext) -> str:
        return "card " + ("isn't" if self.negated else "is") + " phyrexian"


class CardHasWatermarkParam(CardSearchBinaryParameter):
    """
    Parameter for whether a printing has a watermark or not
    """

    @classmethod
    def get_parameter_name(cls) -> str:
        return "has watermark"

    def get_default_search_context(self) -> CardSearchContext:
        return CardSearchContext.PRINTING

    @classmethod
    def get_is_keywords(cls) -> str:
        return "watermark"

    def query(self, query_context: QueryContext) -> Q:
        return Q(face_printings__watermark__isnull=self.negated)

    def get_pretty_str(self, query_context: QueryContext) -> str:
        return "card " + ("doesn't have " if self.negated else "has") + " a watermark"


class CardIsReprintParam(CardSearchBinaryParameter):
    """
    Parameter for whether a printing has been printed before
    """

    @classmethod
    def get_is_keywords(cls) -> str:
        return "reprint"

    @classmethod
    def get_parameter_name(cls) -> str:
        return "reprint"

    def get_default_search_context(self) -> CardSearchContext:
        return CardSearchContext.PRINTING

    def query(self, query_context: QueryContext) -> Q:
        return Q(is_reprint=not self.negated)

    def get_pretty_str(self, query_context: QueryContext) -> str:
        return "card " + ("isn't" if self.negated else "is") + " a reprint"


class CardHasColourIndicatorParam(CardSearchBinaryParameter):
    """
    Parameter for whether a card has a colour indicator or not
    """

    @classmethod
    def get_is_keywords(cls) -> str:
        return "indicator"

    @classmethod
    def get_parameter_name(cls) -> str:
        return "colour indicator"

    def get_default_search_context(self) -> CardSearchContext:
        return CardSearchContext.CARD

    def query(self, query_context: QueryContext) -> Q:
        query = Q(card__faces__colour_indicator=0)
        return query if self.negated else ~query

    def get_pretty_str(self, query_context: QueryContext) -> str:
        return (
            "card "
            + ("doesn't have" if self.negated else "has")
            + " a colour indicator"
        )


class CardIsHybridParam(CardSearchBinaryParameter):
    """
    Parameter for whether a card has hybrid mana in its cost
    """

    @classmethod
    def get_is_keywords(cls) -> str:
        return "hybrid"

    @classmethod
    def get_parameter_name(cls) -> str:
        return "is hybrid"

    def get_default_search_context(self) -> CardSearchContext:
        return CardSearchContext.CARD

    def query(self, query_context: QueryContext) -> Q:
        query = Q(card__faces__mana_cost__iregex=r"\/[wubrg]")
        return ~query if self.negated else query

    def get_pretty_str(self, query_context: QueryContext) -> str:
        return (
            "the cards " + ("don't have" if self.negated else "have") + " hybrid mana"
        )


class CardIsCommanderParam(CardSearchBinaryParameter):
    """
    Parameter for whether this card can be yor commander
    """

    @classmethod
    def get_is_keywords(cls) -> List[str]:
        return ["commander", "general"]

    @classmethod
    def get_parameter_name(cls) -> str:
        return "is commander"

    def get_default_search_context(self) -> CardSearchContext:
        return CardSearchContext.CARD

    def query(self, query_context: QueryContext) -> Q:
        query = (
            (
                Q(card__faces__supertypes__name="Legendary")
                & Q(card__faces__types__name="Creature")
                & ~Q(card__faces__types__name="Token")
            )
            | Q(card__faces__rules_text__contains="can be your commander")
            | Q(card__faces__subtypes__name="Background")
        )
        return ~query if self.negated else query

    def get_pretty_str(self, query_context: QueryContext) -> str:
        return (
            "the cards " + ("can't" if self.negated else "can") + " be your commander"
        )


class CardIsVanillaParam(CardSearchBinaryParameter):
    @classmethod
    def get_is_keywords(cls) -> List[str]:
        return ["vanilla"]

    @classmethod
    def get_parameter_name(cls) -> str:
        return "vanilla"

    def get_default_search_context(self) -> CardSearchContext:
        return CardSearchContext.CARD

    def query(self, query_context: QueryContext) -> Q:
        query = Q(card__faces__rules_text__isnull=True) & Q(
            card__faces__types__name="Creature"
        )
        return ~query if self.negated else query

    def get_pretty_str(self, query_context: QueryContext):
        return "the card " + ("isn't" if self.negated else "is") + " vanilla"


class CardCollectorNumberParam(CardSearchNumericalParameter):
    """
    The parameter for searching by a card's numerical power
    """

    @classmethod
    def get_parameter_name(cls) -> str:
        return "collector number"

    @classmethod
    def get_search_keywords(cls) -> List[str]:
        return ["number", "cnum", "num"]

    def get_default_search_context(self) -> CardSearchContext:
        return CardSearchContext.PRINTING

    def query(self, query_context: QueryContext) -> Q:
        args = self.get_args("card__printings__numerical_number")
        query = Q(**args)
        return ~query if self.negated else query

    def get_pretty_str(self, query_context: QueryContext) -> str:
        return f"the printing's collector number {'is not ' if self.negated else ''}{self.operator} {self.number}"
