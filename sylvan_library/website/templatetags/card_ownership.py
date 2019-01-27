"""
Module for custom template filters to get the image paths of different card models
"""

from django import template
from cards.models import (
    Card,
    CardPrinting,
    CardPrintingLanguage,
)

from django.db.models import Sum, IntegerField, Case, When
from django.contrib.auth.models import User

# pylint: disable=invalid-name
register = template.Library()


@register.filter
def user_card_ownership_count(card: Card, user: User):
    return card.printings.aggregate(
        card_count=Sum(
            Case(
                When(
                    printed_languages__physical_cards__ownerships__owner=user,
                    then='printed_languages__physical_cards__ownerships__count'),
                output_field=IntegerField(),
                default=0
            )
        )
    )['card_count']


@register.filter
def user_cardprinting_ownership_count(card_printing: CardPrinting, user: User):
    return card_printing.printed_languages.aggregate(
        card_count=Sum(
            Case(
                When(
                    physical_cards__ownerships__owner=user,
                    then='physical_cards__ownerships__count'),
                output_field=IntegerField(),
                default=0
            )
        )
    )['card_count']


@register.filter
def user_printedlanguage_ownership_count(printed_language: CardPrintingLanguage, user: User):
    return printed_language.physical_cards.aggregate(
        card_count=Sum(
            Case(
                When(
                    ownerships__owner=user,
                    then='ownerships__count'),
                output_field=IntegerField(),
                default=0
            )
        )
    )['card_count']
