"""
Card ownership parameters
"""
from django.contrib.auth.models import User
from django.db.models import Sum, Case, When, IntegerField, Q

from cards.models import Card, CardPrinting
from .base_parameters import CardSearchParam
from .base_parameters import OPERATOR_MAPPING, CardNumericalParam


class CardOwnerParam(CardSearchParam):
    """
    The parameter for searching by whether it is owned by a given user
    """

    def __init__(self, user: User):
        super().__init__()
        self.user = user

    def query(self) -> Q:
        return Q(localisations__ownerships__owner=self.user)

    def get_pretty_str(self) -> str:
        verb = "don't own" if self.negated else "own"
        return f"{verb} the card"


class CardOwnershipCountParam(CardNumericalParam):
    """
    The parameter for searching by how many a user owns of it
    """

    def __init__(self, user: User, operator: str, number: int):
        super().__init__(number, operator)
        self.user = user

    def query(self) -> Q:
        """
        Gets the Q query object
        :return: The Q object
        """
        annotated_result = CardPrinting.objects.annotate(
            ownership_count=Sum(
                "localisations__ownerships__count",
                filter=Q(localisations__ownerships__owner=self.user),
            )
        )
        kwargs = {f"ownership_count{OPERATOR_MAPPING[self.operator]}": self.number}
        query = Q(**kwargs)
        return Q(id__in=annotated_result.filter(query))
        annotated_result = Card.objects.annotate(
            ownership_count=Sum(
                Case(
                    When(
                        printings__localisations__ownerships__owner=self.user,
                        then="printings__localisations__ownerships__count",
                    ),
                    output_field=IntegerField(),
                    default=0,
                )
            )
        )

        kwargs = {f"ownership_count{OPERATOR_MAPPING[self.operator]}": self.number}
        query = Q(**kwargs)
        return Q(card_id__in=annotated_result.filter(query))

    def get_pretty_str(self) -> str:
        """
        Returns a human readable version of this parameter
        (and all sub parameters for those with children)
        :return: The pretty version of this parameter
        """
        if self.operator in ("<", "<=", "=") and self.number <= 0:
            return f"you you don't own any"

        if (self.operator == ">" and self.number == 0) or (
            self.operator == ">=" and self.number == 1
        ):
            return f"you own it"

        return f"you own {self.operator} {self.number}"


class CardUsageCountParam(CardNumericalParam):
    """
    The parameter for searching by how many times it has been used in a deck
    """

    def __init__(self, user: User, operator: str, number: int):
        super().__init__(number, operator)
        self.user = user

    def query(self) -> Q:
        """
        Gets the Q query object
        :return: The Q object
        """
        annotated_result = Card.objects.annotate(
            usage_count=Sum(
                Case(
                    When(deck_cards__deck__owner=self.user, then=1),
                    output_field=IntegerField(),
                    default=0,
                )
            )
        )

        kwargs = {f"usage_count{OPERATOR_MAPPING[self.operator]}": self.number}
        query = Q(**kwargs)
        return Q(card_id__in=annotated_result.filter(query))

    def get_pretty_str(self) -> str:
        """
        Returns a human readable version of this parameter
        (and all sub parameters for those with children)
        :return: The pretty version of this parameter
        """
        return f"the card was used in {self.operator} {self.number} decks"
