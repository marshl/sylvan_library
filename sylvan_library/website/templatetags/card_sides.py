"""
Module for custom template filters to get the image paths of different card models
"""

from django import template
from cards.models import CardPrinting

# pylint: disable=invalid-name
register = template.Library()


@register.filter(name="other_printing_side")
def other_card_printing_side(card_printing: CardPrinting) -> CardPrinting:
    """
    Returns the other side of a CardPrinting if it is a two-sided card
    :param card_printing: THe CardPrinting to find the other side of
    :return: The other half of this card

    Note that this won't work consistently for cards with more than one other side
    (such as meld cards and Who/What/When/Where/Why)
    """
    other_card = card_printing.card.links.exclude(printings=card_printing).first()
    if other_card is None:
        return None
    return other_card.printings.filter(set=card_printing.set).first()
