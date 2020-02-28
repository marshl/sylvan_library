"""
Module for the update_printing_uids command
"""
import logging
import typing
from typing import Any

from django.core.management.base import BaseCommand
from django.db import transaction

from cards.models import CardPrice
from cards.models import CardPrinting
from data_import.management.commands import get_all_set_data

logger = logging.getLogger("django")


class Command(BaseCommand):
    """
    Command for updating the UIDs of card printings that changed in the json
    """

    help = (
        "Finds printings that may have had their UID (printing.json_id) changed, "
        "and the prompts the user to fix them."
    )

    def handle(self, *args: Any, **options: Any) -> None:
        total_created = 0
        total_skipped = 0

        with transaction.atomic():
            for set_data in get_all_set_data():
                logger.info(
                    "Parsing set %s (%s)", set_data.get("code"), set_data.get("name")
                )

                for card_data in set_data.get("cards", []):
                    if "prices" not in card_data:
                        continue
                    created, skipped = update_card_prices(card_data)
                    total_created += created
                    total_skipped += skipped

                logger.info(
                    "Created %s prices, skipped %s", total_created, total_skipped
                )


def update_card_prices(card_data) -> typing.Tuple[int, int]:
    created = skipped = 0

    card_printing = CardPrinting.objects.get(json_id=card_data["uuid"])
    for price_type, price_dates in card_data.get("prices", {}).items():
        if not price_dates:
            continue
        for price_date, cost in price_dates.items():
            if cost is None:
                continue
            price_obj, created = CardPrice.objects.get_or_create(
                date=price_date,
                price=cost,
                printing=card_printing,
                price_type=price_type,
            )
            if created:
                created += 1
            else:
                skipped += 1

    return created, skipped
