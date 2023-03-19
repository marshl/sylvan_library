"""
Module for the update_prices command
"""
import logging
from decimal import Decimal
from typing import Any

import ijson
from django.core.management.base import BaseCommand

from cards.models.card import CardPrinting, Card
from data_import import _paths

logger = logging.getLogger("django")


class Command(BaseCommand):
    """
    Command for updating card prices from the MTGJSON price files
    """

    help = (
        "Finds printings that may have had their UID (printing.json_id) changed, "
        "and the prompts the user to fix them."
    )

    def handle(self, *args: Any, **options: Any) -> None:
        printing = CardPrinting.objects.get(
            card=Card.objects.get(name="Multani, Maro-Sorcerer")
        )

        face_printing = printing.face_printings.first()

        with open(_paths.PRICES_JSON_PATH, "r", encoding="utf8") as prices_file:
            cards = ijson.kvitems(prices_file, "data")
            for uuid, price_data in cards:
                if uuid == face_printing.uuid:
                    print(price_data)
                    break
