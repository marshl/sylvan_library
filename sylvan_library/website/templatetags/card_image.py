"""
Module for custom template filters to get the image paths of different card models
"""

import os
from typing import Optional

from django import template
from cards.models import Card, CardPrinting, CardPrintingLanguage, Language

# pylint: disable=invalid-name
register = template.Library()


def does_image_exist(path: Optional[str]) -> bool:
    """
    Returns whether the given image path exists or not
    :param path:  The path of the image
    :return:  True if the image file exists, otherwise False
    """
    return path is not None and os.path.exists(os.path.join("website", "static", path))


def get_default_image() -> str:
    """
    Gets the oath of the default iimage to use if one can't be found
    :return: A path to an image in the static folder
    """
    return "card_back.jpg"


@register.filter(name="card_printing_language_image_url")
def card_printing_language_image_url(printed_language: CardPrintingLanguage) -> str:
    """
    Gets the image path for the given CardPrintingLanguage
    :param printed_language: The printed language to get an image for
    :return: The relative image path
    """
    path = printed_language.get_image_path()

    if not path or not does_image_exist(path):
        return get_default_image()

    return path


@register.filter(name="card_printing_image_url")
def card_printing_image_url(card_printing: CardPrinting) -> str:
    """
    Gets the image path for the given CardPrinting
    :param card_printing: The card printing to get the image for
    :return: The relative image path
    """
    printed_language = next(
        pl
        for pl in card_printing.printed_languages.all()
        if pl.language_id == Language.english().id
    )
    path = printed_language.get_image_path()
    if does_image_exist(path):
        return path

    for pl in card_printing.printed_languages.all():
        path = pl.get_image_path()
        if does_image_exist(path):
            return path

    return get_default_image()


@register.filter(name="card_image_url")
def card_image_url(card: Card) -> str:
    """
    Gets the image path for the given Card
    :param card: The card to get an image for
    :return: The relative image path
    """
    non_promo_printings = card.printings.exclude(set__type="promo")
    if non_promo_printings.exists():
        printing = non_promo_printings.order_by("-set__release_date").first()
    else:
        printing = card.printings.order_by("-set__release_date").first()

    if not printing:
        return get_default_image()

    return card_printing_image_url(printing)
