import itertools
import logging
from typing import Any

from django.core.management.base import BaseCommand
from django.db import transaction

from cards.models import CardPrinting
from data_import.management.commands import get_all_set_data

logger = logging.getLogger("django")


class Command(BaseCommand):

    help = ()

    def add_arguments(self, parser) -> None:
        """
        Add command line arguments
        :param parser: The argument parser
        """
        parser.add_argument(
            "-y",
            "--yes",
            action="store_true",
            dest="yes_to_all",
            default=False,
            help="Update every UId without prompt",
        )

    def handle(self, *args: Any, **options: Any) -> None:

        uid_mapping = {}

        for set_data in get_all_set_data():
            for card_data in itertools.chain(
                set_data.get("cards", []), set_data.get("tokens", [])
            ):
                old_uid = card_data.get("identifiers", {}).get("mtgjsonV4Id")
                new_uid = card_data.get("uuid")
                if old_uid in uid_mapping and card_data.get("layout") != "art_series":
                    logger.warning(
                        f"UID {old_uid} already maps to {uid_mapping[old_uid]}"
                        f", but also found {new_uid} ({card_data['name']})"
                    )
                uid_mapping[old_uid] = new_uid

        with transaction.atomic():
            for old_uid, new_uid in uid_mapping.items():
                CardPrinting.objects.filter(json_id=old_uid).update(json_id=new_uid)
