"""
Module for the update_database command
"""

import logging

from django.core.management.base import BaseCommand
from django.urls import reverse

from cards.models.card import (
    CardPrinting,
)
from data_import.management.commands import get_all_set_data

logger = logging.getLogger("django")


def get_admin_link(scryfall_id):
    obj = CardPrinting.objects.get(scryfall_id=scryfall_id)
    return "http://localhost:8000" + reverse(
        "admin:cards_cardprinting_change", args=(obj.id,)
    )


class Command(BaseCommand):
    """
    The command for updating hte database
    """

    help = (
        "Uses the downloaded JSON files to update the database, "
        "including creating cards, set and rarities\n"
    )

    def __init__(self, stdout=None, stderr=None, no_color=False):
        super().__init__(stdout=stdout, stderr=stderr, no_color=no_color)

    def handle(self, *args, **options):
        existing_scryfall_ids = {
            c[0]: c[1]
            for c in CardPrinting.objects.values_list("scryfall_id", "set__code")
        }
        for set_data in get_all_set_data(options.get("set_codes")):
            set_code = set_data["code"]
            for card in set_data["cards"]:
                scryfall_id = card["identifiers"]["scryfallId"]
                if scryfall_id not in existing_scryfall_ids:
                    existing_scryfall_ids[scryfall_id] = set_code
                    continue

                if existing_scryfall_ids[scryfall_id] != set_code:
                    logger.info(
                        "Printing %s (%s) in %s is already in %s %s",
                        card["name"],
                        scryfall_id,
                        existing_scryfall_ids[scryfall_id],
                        set_code,
                        get_admin_link(scryfall_id),
                    )
        for set_data in get_all_set_data(options.get("set_codes")):
            for card in set_data["cards"]:
                scryfall_id = card["identifiers"]["scryfallId"]
                try:
                    existing_scryfall_ids.pop(scryfall_id)
                except KeyError:
                    pass

        for scryfall_id, set_code in existing_scryfall_ids.items():
            logger.info("Leftover scryfall ID %s in set %s", scryfall_id, set_code)
