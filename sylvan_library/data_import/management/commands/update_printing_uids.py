"""
Module for the update_printing_uids command
"""
import logging
from typing import Dict, List, Any

import typing
from django.core.management.base import BaseCommand
from django.db import transaction

from _query import query_yes_no
from cards.models import CardPrinting
from data_import.management.commands import get_all_set_data
from data_import.staging import StagedCard, StagedCardPrinting

logger = logging.getLogger("django")


class Command(BaseCommand):
    """
    Command for updating the UIDs of card printings that changed in the json
    """

    help = (
        "Finds printings that may have had their UID (printing.json_id) changed, "
        "and the prompts the user to fix them."
    )

    existing_card_printings: Dict[str, CardPrinting] = {}

    cards_parsed: typing.Set[str] = set()

    card_printings_to_create: Dict[str, List[StagedCardPrinting]] = {}
    card_printings_parsed: typing.Set[str] = set()

    force_update = False

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
        """
        Fixes printing UIDs of cards that might have been broken by having multiple printings
        of the same multiple faced cards in the same set
        :param args: Command arguments
        :param options: Command keyword arguments
        """
        logger.info("Getting existing printings")
        self.existing_card_printings = {
            cp.json_id: cp for cp in CardPrinting.objects.all()
        }

        for set_data in get_all_set_data():
            logger.info(
                "Parsing set %s (%s)", set_data.get("code"), set_data.get("name")
            )
            self.process_set_cards(set_data)

        card_printing_differences = set(self.existing_card_printings.keys()).difference(
            self.card_printings_parsed
        )

        if not card_printing_differences:
            return

        with transaction.atomic():
            for printing_json_id in card_printing_differences:
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
                            f'Card "{printing_to_delete}" might have had its UID changed '
                            f'from "{printing_json_id}" to "{printing_to_create.json_id}" '
                            f"({printing_to_create.card_name} in {printing_to_create.set_code})."
                            f"\nChange UID?"
                        )
                        if not query_yes_no(query, "no"):
                            continue
                    else:
                        logger.info(
                            "Updating %s from %s to %s",
                            printing_to_delete,
                            printing_json_id,
                            printing_to_create.json_id,
                        )
                    printing_to_delete.json_id = printing_to_create.json_id
                    printing_to_delete.clean()
                    printing_to_delete.save()
            if options["yes_to_all"] and not query_yes_no("Save all changes?", "no"):
                raise Exception("Change application aborted")

    def process_set_cards(self, set_data: Dict[str, Any]) -> None:
        """
        Processes all the cards within a set,
        creating Cards, CardPrintings and CardLocalisations
        :param set_data: The JSON set data dict
        """
        for card_data in set_data.get("cards", []):
            staged_card = self.process_card(card_data, False)
            self.process_card_printing(
                staged_card, set_data, card_data, for_tokens=False
            )

        for card_data in set_data.get("tokens", []):
            staged_card = self.process_card(card_data, True)
            self.process_card_printing(
                staged_card, set_data, card_data, for_tokens=True
            )

    def process_card(self, card_data: Dict[str, Any], is_token: bool) -> StagedCard:
        """
        Processes a single Card
        :param card_data: The JSON data for a card
        :param is_token: whether or not this is a token
        :return: The new or existing StagedCard
        """
        staged_card = StagedCard(card_data, is_token=is_token)
        if staged_card.name in self.cards_parsed:
            return staged_card

        self.cards_parsed.add(staged_card.name)
        return staged_card

    def process_card_printing(
        self,
        staged_card: StagedCard,
        set_data: Dict[str, Any],
        card_data: dict,
        for_tokens: bool,
    ) -> None:
        """
        Process a card printing
        :param staged_card: The staged card
        :param set_data: The set data dict
        :param card_data: The card data dict
        :param for_tokens:
        """
        staged_card_printing = StagedCardPrinting(
            staged_card.name, card_data, set_data, for_tokens
        )
        uuid = staged_card_printing.json_id

        if uuid not in self.existing_card_printings:
            card_name = staged_card_printing.card_name
            if card_name not in self.card_printings_to_create:
                self.card_printings_to_create[card_name] = []
            self.card_printings_to_create[card_name].append(staged_card_printing)

        self.card_printings_parsed.add(staged_card_printing.json_id)
