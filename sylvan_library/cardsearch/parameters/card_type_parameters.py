"""
Card type parameters
"""

from typing import List

from django.db.models.query import Q

from sylvan_library.cards.models.card import (
    CardSubtype,
    CardSupertype,
    CardType,
    CardFace,
    CardFacePrinting,
)
from sylvan_library.cardsearch.parameters.base_parameters import (
    QueryContext,
    CardSearchParameter,
    ParameterArgs,
    or_group_queries,
)


class CardGenericTypeParam(CardSearchParameter):
    """
    Parameter for searching both types and subtypes
    """

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

        # A separate subquery for each kind of type is much faster than one subquery
        # that joins all three
        matching_faces = [
            CardFace.objects.filter(types__in=types),
            CardFace.objects.filter(subtypes__in=subtypes),
            CardFace.objects.filter(supertypes__in=supertypes),
        ]
        result = or_group_queries(
            [Q(card_id__in=faces.values("card_id")) for faces in matching_faces]
        )
        result.negated = self.negated
        return result

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

    @classmethod
    def get_parameter_name(cls) -> str:
        return "original type"

    @classmethod
    def get_search_operators(cls) -> List[str]:
        return [":", "="]

    @classmethod
    def get_search_keywords(cls) -> List[str]:
        return ["originaltype", "otype", "ot"]

    def query(self, query_context: QueryContext) -> Q:
        """
        Gets the query object
        :return: The search Q object
        """
        return Q(
            face_printings__in=CardFacePrinting.objects.filter(
                original_type__icontains=self.value
            ),
            _negated=self.negated,
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
        return f'the card\'s original types {inclusion} "{self.value}"'
