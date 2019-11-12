"""
Module for the update_printing_uids command
"""
import logging
from typing import Dict, List

from django.core.management.base import BaseCommand
from django.db import transaction

from _query import query_yes_no
from cards.models import CardPrinting
from data_import.staging import StagedCard, StagedCardPrinting
from data_import.management.commands import get_all_set_data

logger = logging.getLogger("django")


class Command(BaseCommand):
    help = (
        "Finds printings that may have had their UID (printing.json_id) changed, "
        "and the prompts the user to fix them."
    )

    existing_card_printings = {}  # type: Dict[str, CardPrinting]

    cards_parsed = set()

    card_printings_to_create = {}  # type: Dict[str, List[StagedCardPrinting]]
    card_printings_parsed = set()
    card_printings_to_delete = set()

    force_update = False

    def add_arguments(self, parser):

        parser.add_argument(
            "-y",
            "--yes",
            action="store_true",
            dest="yes_to_all",
            default=False,
            help="Update every UId without prompt",
        )

    def handle(self, *args, **options):
        logger.info("Getting existing printings")
        self.existing_card_printings = {
            cp.json_id: cp for cp in CardPrinting.objects.all()
        }

        for set_data in get_all_set_data():
            logger.info(
                "Parsing set %s (%s)", set_data.get("code"), set_data.get("name")
            )
            self.process_set_cards(set_data)

        self.card_printings_to_delete = set(
            self.existing_card_printings.keys()
        ).difference(self.card_printings_parsed)

        with transaction.atomic():
            for printing_json_id in self.card_printings_to_delete:
                printing_to_delete = CardPrinting.objects.get(json_id=printing_json_id)
                card_name = printing_to_delete.card.name
                if card_name not in self.card_printings_to_create:
                    continue

                for printing_to_create in self.card_printings_to_create[card_name]:
                    if (
                        printing_to_create.set_code != printing_to_delete.set.code
                        or printing_to_create.number != printing_to_delete.number
                    ):
                        continue

                    if not options["yes_to_all"]:
                        query = (
                            f"Card {printing_to_delete} might have had its UID changed "
                            f"from {printing_json_id} to {printing_to_create.json_id} "
                            f"({printing_to_create.card_name} in {printing_to_create.set_code})."
                            f" Change UID?"
                        )
                        if not query_yes_no(query, "no"):
                            continue
                    else:
                        logger.info(
                            f"Updating {printing_to_delete} from {printing_json_id} "
                            f"to {printing_to_create.json_id}"
                        )
                    printing_to_delete.json_id = printing_to_create.json_id
                    printing_to_delete.clean()
                    printing_to_delete.save()

    def process_set_cards(self, set_data: dict) -> None:
        for card_data in set_data.get("cards", []):
            staged_card = self.process_card(card_data, False)
            self.process_card_printing(staged_card, set_data, card_data)

        for card_data in set_data.get("tokens", []):
            staged_card = self.process_card(card_data, True)
            self.process_card_printing(staged_card, set_data, card_data)

    def process_card(self, card_data: dict, is_token: bool) -> StagedCard:
        staged_card = StagedCard(card_data, is_token=is_token)
        if staged_card.name in self.cards_parsed:
            return staged_card

        self.cards_parsed.add(staged_card.name)
        return staged_card

    def process_card_printing(
        self, staged_card: StagedCard, set_data: dict, card_data: dict
    ) -> None:
        staged_card_printing = StagedCardPrinting(staged_card.name, card_data, set_data)
        uuid = staged_card_printing.json_id

        if uuid not in self.existing_card_printings:
            card_name = staged_card_printing.card_name
            if card_name not in self.card_printings_to_create:
                self.card_printings_to_create[card_name] = []
            self.card_printings_to_create[card_name].append(staged_card_printing)

        self.card_printings_parsed.add(staged_card_printing.json_id)
