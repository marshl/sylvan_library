"""
Module for custom template filters to get the image paths of different card models
"""


from os import path
from django import template
from cards.models import (
    Card,
    CardPrinting,
    CardPrintingLanguage,
    Language,
)

# pylint: disable=invalid-name
register = template.Library()


@register.filter(name='card_printing_language_image_url')
def card_printing_language_image_url(printed_language: CardPrintingLanguage) -> str:
    """
    Gets the image path for the given CardPrintingLanguage
    :param printed_language: The printed language to get an image for
    :return: The relative image path
    """
    return printed_language.get_image_path()


@register.filter(name='card_printing_image_url')
def card_printing_image_url(card_printing: CardPrinting) -> str:
    """
    Gets the image path for the given CardPrinting
    :param card_printing: The card printing to get the image for
    :return: The relative image path
    """
    printed_language = card_printing.printed_languages.get(
        language=Language.objects.get(name='English'))
    return printed_language.get_image_path()


@register.filter(name='card_image_url')
def card_image_url(card: Card) -> str:
    """
    Gets the image path for the given Card
    :param card: The card to get an image for
    :return: The relative image path
    """
    printing = card.printings.order_by('-set__release_date').first()

    if not printing:
        return path.join('static', 'card_images', 'card_back.jpg')

    return card_printing_image_url(printing)
