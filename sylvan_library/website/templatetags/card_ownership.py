"""
Module for custom template filters to get the image paths of different card models
"""

from django import template
from cards.models import (
    Card,
    CardPrinting,
    CardPrintingLanguage,
)

from django.contrib.auth.models import User

register = template.Library()


@register.filter
def user_card_ownership_count(card: Card, user: User) -> int:
    """
    Returns the total number of cards that given user owns of the given card
    :param card: The card to find all ownerships for
    :param user: The user who should own the card
    :return: The ownership total
    """
    return sum(
        ownership.count
        for card_printing in card.printings.all()
        for printed_language in card_printing.printed_languages.all()
        for physical_card in printed_language.physical_cards.all()
        for ownership in physical_card.ownerships.all()
        if ownership.owner_id == user.id
    )


@register.filter
def user_cardprinting_ownership_count(card_printing: CardPrinting, user: User) -> int:
    """
    Returns the total number of cards that given user owns of the given card printed in a set
    :param card_printing: The card to find all ownerships for
    :param user: The user who should own the card
    :return: The ownership total
    """
    return sum(
        ownership.count
        for printed_language in card_printing.printed_languages.all()
        for physical_card in printed_language.physical_cards.all()
        for ownership in physical_card.ownerships.all()
        if ownership.owner_id == user.id
    )


@register.filter
def user_printedlanguage_ownership_count(printed_language: CardPrintingLanguage, user: User) -> int:
    """
    Returns the total number of cards that given user owns of the
        given card printed in a specific set with a specific language
    :param printed_language: The card to find all ownerships for
    :param user: The user who should own the card
    :return: The ownership total
    """
    return sum(
        ownership.count
        for physical_card in printed_language.physical_cards.all()
        for ownership in physical_card.ownerships.all()
        if ownership.owner_id == user.id
    )
