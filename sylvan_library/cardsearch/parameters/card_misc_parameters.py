"""
Miscellaneous card parameters (mostly the "is" and "has" parameters)
"""
from django.db.models import Q

from .base_parameters import CardSearchParam


class CardLayoutParameter(CardSearchParam):
    """
    Parameter for whether a card has any phyrexian mana symbols or not
    """

    def __init__(self, layout: str):
        super().__init__()
        self.layout = layout

    def query(self) -> Q:
        query = Q(card__layout=self.layout)
        return ~query if self.negated else query

    def get_pretty_str(self) -> str:
        return "card layout " + ("isn't" if self.negated else "is") + " " + self.layout


class CardIsPhyrexianParam(CardSearchParam):
    """
    Parameter for whether a card has any phyrexian mana symbols or not
    """

    def query(self) -> Q:
        query = Q(card__faces__mana_cost__icontains="/p") | Q(
            card__faces__rules_text__icontains="/p"
        )
        return ~query if self.negated else query

    def get_pretty_str(self) -> str:
        return "card " + ("isn't" if self.negated else "is") + " phyrexian"


class CardHasWatermarkParam(CardSearchParam):
    """
    Parameter for whether a printing has a watermark or not
    """

    def query(self) -> Q:
        return Q(face_printings__watermark__isnull=self.negated)

    def get_pretty_str(self) -> str:
        return "card " + ("doesn't have " if self.negated else "has") + " a watermark"


class CardIsReprintParam(CardSearchParam):
    """
    Parameter for whether a printing has been printed before
    """

    def query(self) -> Q:
        return Q(is_reprint=not self.negated)

    def get_pretty_str(self) -> str:
        return "card " + ("isn't" if self.negated else "is") + " a reprint"


class CardHasColourIndicatorParam(CardSearchParam):
    """
    Parameter for whether a card has a colour indicator or not
    """

    def query(self) -> Q:
        query = Q(card__faces__colour_indicator=0)
        return query if self.negated else ~query

    def get_pretty_str(self) -> str:
        return (
            "card "
            + ("doesn't have" if self.negated else "has")
            + " a colour indicator"
        )


class CardIsHybridParam(CardSearchParam):
    """
    Parameter for whether a card has hybrid mana in its cost
    """

    def query(self) -> Q:
        query = Q(card__faces__mana_cost__iregex=r"\/[wubrg]")
        return ~query if self.negated else query

    def get_pretty_str(self) -> str:
        return "card " + ("isn't" if self.negated else "is") + " hybrid"
