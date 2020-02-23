"""
Module for the build_metadata command
"""
import logging
import re
from typing import Any

from django.core.management.base import BaseCommand
from django.db import transaction

from cards.models import Card
from cardsearch.models import CardSearchMetadata

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
    symbol: re.compile(r"adds?\W[^\n.]*?{" + symbol + "}", re.IGNORECASE)
    for symbol in ["W", "U", "B", "R", "G", "C"]
}

RE_PRODUCES_ANY = re.compile(
    r"adds?\W[^\n.]*?any (combination of )?color", re.IGNORECASE
)


def build_card_symbol_counts(metadata: CardSearchMetadata) -> None:
    """
    Builds the counts of symbols in the costs of the given card
    :param metadata: The metadata record to build symbol counts for
    """
    for symbol in MANA_SYMBOLS:
        if metadata.card.cost:
            count = metadata.card.cost.count("{" + symbol + "}")
        else:
            count = 0

        attr_name = "symbol_count_" + symbol.lower().replace("/", "_")
        assert hasattr(metadata, attr_name)
        setattr(metadata, attr_name, count)

    metadata.symbol_count_generic = get_card_generic_mana(metadata.card)


def get_card_generic_mana(card: Card) -> int:
    """
    Gets the number for the generic mana symbol in a cards cost
    (if there is one, otherwise 0)
    :return: The amount of generic mana required to cast this card
    """
    if not card.cost:
        return 0

    generic_mana = RE_GENERIC_MANA.search(card.cost)
    if generic_mana:
        return int(generic_mana.group(1))
    return 0


def build_produces_counts(metadata: CardSearchMetadata) -> None:
    """
    Computes what colours a card can produce
    :param metadata: The card to build "produces" data for
    """
    if not metadata.card.rules_text:
        metadata.produces_w = (
            metadata.produces_u
        ) = (
            metadata.produces_b
        ) = metadata.produces_r = metadata.produces_g = metadata.produces_c = False
        return

    produces_any = bool(RE_PRODUCES_ANY.search(metadata.card.rules_text))
    for symbol, regex in RE_PRODUCES_MAP.items():
        produces = (
            symbol != "C"
            if produces_any
            else bool(regex.search(metadata.card.rules_text))
        )
        setattr(metadata, "produces_" + symbol.lower(), produces)


def build_metadata_for_card(card: Card) -> None:
    """
    Constructs (or repopulates) the search metadata for the given card
    :param card: The card to build the metadata for
    """
    if hasattr(card, "search_metadata"):
        metadata = card.search_metadata
    else:
        metadata = CardSearchMetadata(card=card)

    if card.rules_text and "(" in card.rules_text:
        metadata.rules_without_reminders = RE_REMINDER_TEXT.sub("", card.rules_text)

    build_card_symbol_counts(metadata)
    build_produces_counts(metadata)
    metadata.save()


class Command(BaseCommand):
    """
    The command for updating search metadata
    """

    help = "Rebuilds the search metadata. This should be run after each call to apply_changes"

    def handle(self, *args: Any, **options: Any):
        card_count = Card.objects.count()
        with transaction.atomic():
            for idx, card in enumerate(
                Card.objects.prefetch_related("search_metadata").all()
            ):
                build_metadata_for_card(card)
                if idx % (card_count // 10) == 0:
                    logger.info("Indexed %s of %s cards", idx + 1, card_count)
