"""
Module for custom template filters to get the image paths of different card models
"""

from django import template
from django.db.models import QuerySet, Sum

# pylint: disable=invalid-name
register = template.Library()


@register.filter(name="deck_group_count")
def deck_card_group_count(cards: QuerySet) -> int:
    """
    Gets the total number of cards in the given list of deck cards
    :param cards: A QuerySet of DeckCards
    :return: The total number of cards
    """
    return cards.aggregate(sum=Sum("count"))["sum"]
