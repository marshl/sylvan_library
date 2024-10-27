"""
Module for the build_metadata command
"""

import logging
import re
from typing import Any

from django.core.management.base import BaseCommand
from django.db import transaction

from cards.models.card import CardFace
from cardsearch.models import CardFaceSearchMetadata

logger = logging.getLogger("django")

RE_REMINDER_TEXT = re.compile(r"\(.+?\)")
RE_GENERIC_MANA = re.compile(r"{(\d+)}")

MANA_SYMBOLS = [
    "W",
    "U",
    "B",
    "R",
    "G",
    "C",
    "S",
    "X",
    "W/U",
    "U/B",
    "B/R",
    "R/G",
    "G/W",
    "W/B",
    "U/R",
    "B/G",
    "R/W",
    "G/U",
    "2/W",
    "2/U",
    "2/B",
    "2/R",
    "2/G",
    "W/P",
    "U/P",
    "B/P",
    "R/P",
    "G/P",
]

RE_PRODUCES_MAP = {
    symbol: re.compile(r"adds?\W[^\n.]*?{" + symbol.upper() + "}", re.IGNORECASE)
    for symbol in ["w", "u", "b", "r", "g", "c"]
}

RE_PRODUCES_ANY = re.compile(
    r"adds?\W[^\n.]*?any (combination of )?color", re.IGNORECASE
)


def build_card_symbol_counts(metadata: CardFaceSearchMetadata) -> bool:
    """
    Builds the counts of symbols in the costs of the given card
    :param metadata: The metadata record to build symbol counts for
    """
    changed = False
    for symbol in MANA_SYMBOLS:
        if metadata.card_face.mana_cost:
            count = metadata.card_face.mana_cost.count("{" + symbol + "}")
        else:
            count = 0

        attr_name = "symbol_count_" + symbol.lower().replace("/", "_")
        if getattr(metadata, attr_name) != count:
            setattr(metadata, attr_name, count)
            changed = True

    generic_count = get_card_generic_mana(metadata.card_face)
    if metadata.symbol_count_generic != generic_count:
        metadata.symbol_count_generic = generic_count
        changed = True

    return changed


def get_card_generic_mana(card_face: CardFace) -> int:
    """
    Gets the number for the generic mana symbol in a cards cost
    (if there is one, otherwise 0)
    :return: The amount of generic mana required to cast this card
    """
    if not card_face.mana_cost:
        return 0

    generic_mana = RE_GENERIC_MANA.search(card_face.mana_cost)
    if generic_mana:
        return int(generic_mana.group(1))
    return 0


def build_produces_counts(metadata: CardFaceSearchMetadata) -> bool:
    """
    Computes what colours a card can produce
    :param metadata: The card to build "produces" data for
    """
    if not metadata.card_face.rules_text:
        if any(getattr(metadata, "produces_" + c) for c in RE_PRODUCES_MAP.keys()):
            map(
                lambda c: setattr(metadata, "produces_" + c, False),
                RE_PRODUCES_MAP.keys(),
            )
            return True
        return False

    changed = False
    produces_every_colour = bool(RE_PRODUCES_ANY.search(metadata.card_face.rules_text))
    for symbol, regex in RE_PRODUCES_MAP.items():
        does_produce_colour = (
            symbol != "c"
            if produces_every_colour
            else bool(regex.search(metadata.card_face.rules_text))
        )
        attr_name = "produces_" + symbol
        if getattr(metadata, attr_name) != does_produce_colour:
            setattr(metadata, attr_name, does_produce_colour)
            changed = True
    return changed


def build_metadata_for_card_face(card_face: CardFace) -> None:
    """
    Constructs (or repopulates) the search metadata for the given card
    :param card_face: The card to build the metadata for
    """
    if hasattr(card_face, "search_metadata"):
        metadata = card_face.search_metadata
    else:
        metadata = CardFaceSearchMetadata(card_face=card_face)
    changed = False
    if card_face.rules_text and "(" in card_face.rules_text:
        new_text = RE_REMINDER_TEXT.sub("", card_face.rules_text)
        if metadata.rules_without_reminders != new_text:
            metadata.rules_without_reminders = new_text
            changed = True

    changed = build_card_symbol_counts(metadata) or changed
    changed = build_produces_counts(metadata) or changed

    if changed or not metadata.id:
        metadata.save()


class Command(BaseCommand):
    """
    The command for updating search metadata
    """

    help = "Rebuilds the search metadata. This should be run after each call to apply_changes"

    def handle(self, *args: Any, **options: Any):
        card_face_count = CardFace.objects.count()
        with transaction.atomic():
            for idx, card_face in enumerate(
                CardFace.objects.prefetch_related("search_metadata").all()
            ):
                build_metadata_for_card_face(card_face)
                if idx % (card_face_count // 10) == 0:
                    logger.info("Indexed %s of %s card faces", idx + 1, card_face_count)
