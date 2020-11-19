"""
Card type parameters
"""
from django.db.models.query import Q

from .base_parameters import CardSearchParam


class CardTypeParam(CardSearchParam):
    """
    The parameter for searching by a card's type or supertypes
    """

    def __init__(self, card_type):
        super().__init__()
        self.card_type = card_type

    def query(self) -> Q:
        return Q(card__type__icontains=self.card_type)

    def get_pretty_str(self) -> str:
        verb = "isn't" if self.negated else "is"
        return f'card type {verb} "{self.card_type}"'


class CardSubtypeParam(CardSearchParam):
    """
    The parameter for searching by a card's subtypes
    """

    def __init__(self, card_subtype):
        super().__init__()
        self.card_subtype = card_subtype

    def query(self) -> Q:
        return Q(card__subtype__icontains=self.card_subtype)

    def get_pretty_str(self) -> str:
        verb = "isn't" if self.negated else "is"
        return f'card subtype {verb} "{self.card_subtype}"'


class CardGenericTypeParam(CardSearchParam):
    """
    Parameter for searching both types and subtypes
    """

    def __init__(self, card_type: str, operator: str):
        super().__init__()
        self.card_type = card_type
        self.operator = operator

    def query(self) -> Q:
        """
        Gets the query object
        :return: The search Q object
        """
        if self.operator == "=":
            result = Q(card__type__iexact=self.card_type) | Q(
                card__subtype__iexact=self.card_type
            )
        else:
            result = Q(card__type__icontains=self.card_type) | Q(
                card__subtype__icontains=self.card_type
            )
        return ~result if self.negated else result

    def get_pretty_str(self) -> str:
        """
        Returns a human readable version of this parameter
        (and all sub parameters for those with children)
        :return: The pretty version of this parameter
        """
        if self.negated:
            if self.operator == "=":
                inclusion = "don't match"
            else:
                inclusion = "exclude"
        else:
            if self.operator == "=":
                inclusion = "match"
            else:
                inclusion = "include"
        return f'the card types {inclusion} "{self.card_type}"'
