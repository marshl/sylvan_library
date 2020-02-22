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


def build_card_symbol_counts(metadata: CardSearchMetadata) -> None:
    """

    :param metadata:
    :return:
    """
    symbols = [
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
    for symbol in symbols:
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


def build_metadata_for_card(card: Card) -> None:
    """
    Constructs (or repopulates) the search metadata for the given card
    :param card: The card to build the metadata for
    """
    try:
        metadata = CardSearchMetadata.objects.get(card=card)
    except CardSearchMetadata.DoesNotExist:
        metadata = CardSearchMetadata(card=card)

    if card.rules_text and "(" in card.rules_text:
        metadata.rules_without_reminders = RE_REMINDER_TEXT.sub("", card.rules_text)

    build_card_symbol_counts(metadata)
    metadata.save()


class Command(BaseCommand):
    """
    The command for updating search metadata
    """

    help = "Rebuilds the search metadata. This should be run after each call to apply_changes"

    def handle(self, *args: Any, **options: Any):
        card_count = Card.objects.count()
        with transaction.atomic():
            for idx, card in enumerate(Card.objects.all()):
                build_metadata_for_card(card)
                if idx % int(card_count / 10) == 0:
                    logger.info("Indexed %s of %s cards" % (idx + 1, card_count))
