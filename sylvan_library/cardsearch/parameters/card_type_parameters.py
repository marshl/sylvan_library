"""
Card type parameters
"""

from typing import List

from django.db.models.query import Q

from cards.models.card import (
    CardSubtype,
    CardSupertype,
    CardType,
    CardFacePrinting,
    Card,
)
from cardsearch.parameters.base_parameters import (
    CardSearchContext,
    QueryContext,
    CardSearchParameter,
    ParameterArgs,
)


class CardGenericTypeParam(CardSearchParameter):
    """
    Parameter for searching both types and subtypes
    """

    def get_default_search_context(self) -> CardSearchContext:
        return CardSearchContext.CARD

    @classmethod
    def get_parameter_name(cls) -> str:
        return "type"

    @classmethod
    def get_search_operators(cls) -> List[str]:
        return [":", "="]

    @classmethod
    def get_search_keywords(cls) -> List[str]:
        return ["type", "t"]

    @classmethod
    def matches_param_args(cls, param_args: ParameterArgs) -> bool:
        if param_args.keyword == "is" and param_args.value == "token":
            return True

        return super().matches_param_args(param_args)

    def query(self, query_context: QueryContext) -> Q:
        """
        Gets the query object
        :return: The search Q object
        """
        if self.operator == "=":
            types = CardType.objects.filter(name__iexact=self.value)
            subtypes = CardSubtype.objects.filter(name__iexact=self.value)
            supertypes = CardSupertype.objects.filter(name__iexact=self.value)
        else:
            types = CardType.objects.filter(name__icontains=self.value)
            subtypes = CardSubtype.objects.filter(name__icontains=self.value)
            supertypes = CardSupertype.objects.filter(name__icontains=self.value)

        face_filter = (
            Q(faces__types__in=types)
            | Q(faces__subtypes__in=subtypes)
            | Q(faces__supertypes__in=supertypes)
        )
        result = Q(card__in=Card.objects.filter(face_filter))

        return ~result if self.negated else result

    def get_pretty_str(self, query_context: QueryContext) -> str:
        """
        Returns a human-readable version of this parameter
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
        return f'the card types {inclusion} "{self.value}"'


class CardOriginalTypeParam(CardSearchParameter):
    """
    A parameter for querying the original type line of a card
    """

    def get_default_search_context(self) -> CardSearchContext:
        return CardSearchContext.PRINTING

    @classmethod
    def get_parameter_name(cls) -> str:
        return "original type"

    @classmethod
    def get_search_operators(cls) -> List[str]:
        return [":", "="]

    @classmethod
    def get_search_keywords(cls) -> List[str]:
        return ["originaltype", "ot"]

    def query(self, query_context: QueryContext) -> Q:
        """
        Gets the query object
        :return: The search Q object
        """
        if self.negated:
            return ~Q(
                face_printings__in=CardFacePrinting.objects.filter(
                    Q(original_type__isnull=True)
                    | Q(original_type__icontains=self.value)
                )
            )
        return Q(
            face_printings__in=CardFacePrinting.objects.filter(
                original_type__icontains=self.value
            )
        )

    def get_pretty_str(self, query_context: QueryContext) -> str:
        """
        Returns a human-readable version of this parameter
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
        return f'the card types {inclusion} "{self.value}"'
