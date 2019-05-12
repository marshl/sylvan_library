"""
Module for custom template filters to get the image paths of different card models
"""

from django import template
from django.db.models import QuerySet, Sum

# pylint: disable=invalid-name
register = template.Library()


@register.filter(name="deck_group_count")
def deck_card_group_count(cards: QuerySet) -> int:
    return cards.aggregate(sum=Sum("count"))["sum"]
