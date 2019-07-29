"""
Module for custom template filters to get the image paths of different card models
"""

import os
from django import template
from cards.models import Card, CardPrinting, CardPrintingLanguage, Language

# pylint: disable=invalid-name
register = template.Library()


@register.filter(name="other_printing_side")
def other_card_printing_side(card_printing: CardPrinting) -> CardPrinting:
    other_card = card_printing.card.links.exclude(printings=card_printing).first()
    return other_card.printings.filter(set=card_printing.set).first()
