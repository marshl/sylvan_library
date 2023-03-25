"""
Module for custom template filters to get the image paths of different card models
"""
import logging
from typing import Optional

from django import template
from django.contrib.staticfiles import finders

from cards.models.card import (
    CardLocalisation,
    CardFacePrinting,
    CardFaceLocalisation,
    CardPrinting,
    Card,
)
from cards.models.language import Language

logger = logging.getLogger("django")

# pylint: disable=invalid-name
register = template.Library()


def does_image_exist(path: Optional[str]) -> bool:
    """
    Returns whether the given image path exists or not
    :param path: The path of the image
    :return: True if the image file exists, otherwise False
    """
    return path and bool(finders.find(path))


def get_default_image() -> str:
    """
    Gets the oath of the default image to use if one can't be found
    :return: A path to an image in the static folder
    """
    return "card_back.jpg"


@register.filter(name="card_printing_language_image_url")
def card_printing_language_image_url(printed_language: CardLocalisation) -> str:
    """
    Gets the image path for the given CardLocalisation
    :param printed_language: The printed language to get an image for
    :return: The relative image path
    """
    path = printed_language.get_image_path()

    if not path or not does_image_exist(path):
        return get_default_image()

    return path


@register.filter(name="card_face_printing_image_url")
def card_face_printing_image_url(card_face_printing: CardFacePrinting) -> str:
    """
    Gets the image URL of the given CardFacePrinting
    :param card_face_printing: The CardFacePrinting to get the image URL for
    :return: The image URL
    """
    assert isinstance(card_face_printing, CardFacePrinting)
    face_localisation: CardFaceLocalisation = next(
        face_localisation
        for face_localisation in card_face_printing.localised_faces.all()
        if face_localisation.localisation.language_id == Language.english().id
    )
    path = face_localisation.get_image_path()
    if does_image_exist(path):
        return path

    for face_localisation in card_face_printing.localised_faces.all():
        path = face_localisation.get_image_path()
        if does_image_exist(path):
            return path

    return get_default_image()


@register.filter(name="card_printing_image_url")
def card_printing_image_url(card_printing: CardPrinting) -> str:
    """
    Gets the image path for the given CardPrinting
    :param card_printing: The card printing to get the image for
    :return: The relative image path
    """
    localisation: CardLocalisation = next(
        localisation
        for localisation in card_printing.localisations.all()
        if localisation.language_id == Language.english().id
    )

    path = localisation.get_image_path()
    if does_image_exist(path):
        return path

    for localisation in card_printing.localisations.all():
        try:
            path = localisation.localised_faces.all()[0].get_image_path()
        except IndexError:
            logging.exception("Failed to find image path for %s", localisation)
            return get_default_image()
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
