"""
Module for custom template filters to get the image paths of different card models
"""

from django import template
from django.contrib.auth.models import User

from cards.models import Card, CardPrinting, CardLocalisation

register = template.Library()


@register.filter
def user_card_ownership_count(card: Card, user: User) -> int:
    """
    Returns the total number of cards that given user owns of the given card
    :param card: The card to find all ownerships for
    :param user: The user who should own the card
    :return: The ownership total
    """
    return card.get_user_ownership_count(user, prefetched=True)


@register.filter
def user_cardprinting_ownership_count(card_printing: CardPrinting, user: User) -> int:
    """
    Returns the total number of cards that given user owns of the given card printed in a set
    :param card_printing: The card to find all ownerships for
    :param user: The user who should own the card
    :return: The ownership total
    """
    return card_printing.get_user_ownership_count(user, prefetched=True)


@register.filter
def user_printedlanguage_ownership_count(
    printed_language: CardLocalisation, user: User
) -> int:
    """
    Returns the total number of cards that given user owns of the
        given card printed in a specific set with a specific language
    :param printed_language: The card to find all ownerships for
    :param user: The user who should own the card
    :return: The ownership total
    """
    return printed_language.get_user_ownership_count(user, prefetched=True)
