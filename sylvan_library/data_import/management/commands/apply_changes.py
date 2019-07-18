"""
Module for the update_database command
"""
import logging
import time
from typing import List, Optional, Dict, Tuple
from django.db import transaction
from django.core.exceptions import ValidationError

from django.core.management.base import BaseCommand
from cards.models import (
    Block,
    Card,
    CardLegality,
    CardPrinting,
    CardPrintingLanguage,
    CardRuling,
    Colour,
    Format,
    Language,
    PhysicalCard,
    Rarity,
    Set,
)
from data_import.importers import JsonImporter
from data_import.management.data_import_command import DataImportCommand

# from data_import.staging import StagedCard, StagedSet
import os
import _paths
import json
from datetime import date

logger = logging.getLogger("django")


class Command(BaseCommand):
    """
    The command for updating hte database
    """

    help = (
        "Uses the downloaded JSON files to update the database, "
        "including creating cards, set and rarities\n"
        "Use the update_rulings command to update rulings"
    )

    def add_arguments(self, parser):

        parser.add_argument(
            "--no-transaction",
            action="store_true",
            dest="no_transaction",
            default=False,
            help="Update the database without a transaction (unsafe)",
        )

    def handle(self, *args, **options):
        if not Colour.objects.exists() or not Rarity.objects.exists():
            logger.error(
                "No colours or rarities were found. "
                "Please run the update_metadata command first"
            )
            return

        transaction.atomic()
        with transaction.atomic():
            self.create_new_blocks()
            self.create_new_sets()
            self.update_sets()
            self.create_cards()
            self.update_cards()
            self.create_card_links()
            self.create_card_printings()
            self.create_printed_languages()
            self.create_physical_cards()
            self.create_rulings()
            self.delete_rulings()
            self.create_legalities()
            self.delete_legalities()

    def create_new_blocks(self) -> None:
        logger.info("Creating new blocks")
        with open(_paths.BLOCKS_TO_CREATE_PATH, "r", encoding="utf8") as block_file:
            block_list = json.load(block_file, encoding="utf8")

        for _, block_data in block_list.items():
            block = Block(
                name=block_data["name"], release_date=block_data["release_date"]
            )
            block.full_clean()
            block.save()

    def create_new_sets(self) -> None:
        logger.info("Creating new sets")
        with open(_paths.SETS_TO_CREATE_PATH, "r", encoding="utf8") as set_file:
            set_list = json.load(set_file, encoding="utf8")

        for _, set_data in set_list.items():
            set_obj = Set(
                code=set_data["code"],
                release_date=set_data["release_date"],
                name=set_data["name"],
                type=set_data["type"],
                card_count=set_data["card_count"],
                block=Block.objects.get(name=set_data["block"])
                if set_data["block"]
                else None,
                keyrune_code=set_data["keyrune_code"],
            )
            set_obj.full_clean()
            set_obj.save()

    def update_sets(self) -> None:
        logger.info("Updating sets")
        with open(_paths.SETS_TO_UPDATE_PATH, "r", encoding="utf8") as set_file:
            set_list = json.load(set_file, encoding="utf8")

        for set_code, set_diff in set_list.items():
            set_obj = Set.objects.get(code=set_code)
            for field, change in set_diff.items():
                if field in {"keyrune_code", "release_date", "name", "card_count"}:
                    setattr(set_obj, field, change["to"])
                elif field == "block":
                    set_obj.block = Block.objects.get(name=change["to"])
                else:
                    raise NotImplementedError(
                        f"Cannot update unrecognised field Set.{field}"
                    )
            set_obj.full_clean()
            set_obj.save()

    def create_cards(self) -> None:
        logger.info("Creating new cards")
        with open(_paths.CARDS_TO_CREATE, "r", encoding="utf8") as card_file:
            card_list = json.load(card_file, encoding="utf8")

        for _, card_data in card_list.items():
            card = Card()
            for field, value in card_data.items():
                setattr(card, field, value)
            card.full_clean()
            card.save()

    def update_cards(self) -> None:
        logger.info("Updating cards")
        with open(_paths.CARDS_TO_UPDATE, "r", encoding="utf8") as card_file:
            card_list = json.load(card_file, encoding="utf8")

        for card_name, card_diff in card_list.items():
            card = Card.objects.get(name=card_name, is_token=False)
            for field, change in card_diff.items():
                if field in {
                    "display_name",
                    "is_reserved",
                    "layout",
                    "loyalty",
                    "num_loyalty",
                    "num_power",
                    "num_toughness",
                    "power",
                    "rules_text",
                    "scryfall_oracle_id",
                    "subtype",
                    "toughness",
                    "type",
                }:
                    setattr(card, field, change["to"])
                else:
                    raise NotImplementedError(
                        f"Cannot update unrecognised field Card.{field}"
                    )
            card.full_clean()
            card.save()

    def create_card_links(self) -> None:
        logger.info("Creating card links")
        with open(_paths.CARD_LINKS_TO_CREATE, "r", encoding="utf8") as lnks_file:
            link_list = json.load(lnks_file, encoding="utf8")

        for card_name, links in link_list.items():
            card_obj = Card.objects.get(name=card_name, is_token=False)
            for link in links:
                card_obj.links.add(Card.objects.get(name=link, is_token=False))
            card_obj.save()

    def create_card_printings(self) -> None:
        logger.info("Creating card printings")
        with open(_paths.PRINTINGS_TO_CREATE, "r", encoding="utf8") as printing_file:
            printing_list = json.load(printing_file, encoding="utf8")

        for scryfall_id, printing_data in printing_list.items():
            card = Card.objects.get(name=printing_data["card_name"])
            set_obj = Set.objects.get(code=printing_data["set_code"])
            printing = CardPrinting(card=card, set=set_obj)
            for field, value in printing_data.items():
                if field in {"card_name", "set_code"}:
                    continue
                elif field in {
                    "artist",
                    "border_colour",
                    "flavour_text",
                    "frame_version",
                    "has_non_foil",
                    "is_starter",
                    "is_timeshifted",
                    "json_id",
                    "multiverse_id",
                    "number",
                    "original_text",
                    "original_ty[e",
                    "scryfall_id",
                    "scryfall_illustration_id",
                }:
                    setattr(printing, field, value)
                elif field == "rarity":
                    printing.rarity = Rarity.objects.get(name__iexact=value)
                else:
                    raise NotImplementedError(
                        f"Cannot update unrecognised field CardPrinting.{field}"
                    )

            try:
                printing.full_clean()
            except ValidationError:
                logger.error(
                    f"Failed to validated {printing_data['card_name']} ({scryfall_id})"
                )
                raise
            printing.save()

    def create_printed_languages(self) -> None:
        logger.info("Creating card printing languages")
        with open(_paths.PRINTLANGS_TO_CREATE, "r", encoding="utf8") as printlang_file:
            printlang_list = json.load(printlang_file, encoding="utf8")

        for printlang_data in printlang_list:
            printed_language = CardPrintingLanguage()
            for field, value in printlang_data.items():
                if field == "printing_uid":
                    printed_language.card_printing = CardPrinting.objects.get(
                        json_id=value
                    )
                elif field == "language":
                    printed_language.language = Language.objects.get(name=value)
                elif field in {"card_name", "multiverse_id", "text", "type"}:
                    setattr(printed_language, field, value)
                elif field in {"base_name"}:
                    continue
                else:
                    raise NotImplementedError(
                        f"Cannot update unrecognised field CardPrintingLanguage.{field}"
                    )

            try:
                printed_language.full_clean()
                printed_language.save()
            except ValidationError:
                logger.error(
                    f"Failed to validate CardPrintingLanguage {printed_language}"
                )
                raise

    def create_physical_cards(self) -> None:
        logger.info("Creating physical cards")
        with open(
            _paths.PHYSICAL_CARDS_TO_CREATE, "r", encoding="utf8"
        ) as physcard_file:
            physical_card_list = json.load(physcard_file, encoding="utf8")

        for phys_data in physical_card_list:
            physical_card = PhysicalCard()
            physical_card.layout = phys_data["layout"]
            physical_card.full_clean()
            physical_card.save()

            language = Language.objects.get(name=phys_data["language"])
            for printing_uid in phys_data["printing_uids"]:
                printed_language = CardPrintingLanguage.objects.get(
                    card_printing__json_id=printing_uid, language=language
                )
                printed_language.physical_cards.add(physical_card)

    def create_rulings(self) -> None:
        logger.info("Creating rulings")
        with open(_paths.RULINGS_TO_CREATE, "r", encoding="utf8") as rulings_file:
            ruling_list = json.load(rulings_file, encoding="utf8")

        for ruling_data in ruling_list:
            ruling = CardRuling()
            ruling.card = Card.objects.get(
                name=ruling_data["card_name"], is_token=False
            )
            ruling.text = ruling_data["text"]
            ruling.date = ruling_data["date"]

            ruling.full_clean()
            ruling.save()

    def delete_rulings(self):
        logger.info("Deleting rulings")
        with open(_paths.RULINGS_TO_DELETE, "r", encoding="utf8") as rulings_file:
            ruling_list = json.load(rulings_file, encoding="utf8")

        for card_name, rulings in ruling_list.items():
            card = Card.objects.get(name=card_name)
            for ruling_text in rulings:
                CardRuling.objects.get(card=card, text=ruling_text).delete()

    def create_legalities(self) -> None:
        logger.info("Creating legalities")
        with open(_paths.LEGALITIES_TO_CREATE, "r", encoding="utf8") as legalities_file:
            legality_list = json.load(legalities_file, encoding="utf8")

        for legality_data in legality_list:
            legality = CardLegality()
            legality.card = Card.objects.get(
                name=legality_data["card_name"], is_token=False
            )
            legality.format = Format.objects.get(name__iexact=legality_data["format"])
            legality.restriction = legality_data["restriction"]

            legality.full_clean()
            legality.save()

    def delete_legalities(self):
        logger.info("Deleting legalities")
        with open(_paths.LEGALITIES_TO_DELETE, "r", encoding="utf8") as legalities_file:
            legality_list = json.load(legalities_file, encoding="utf8")

        for card_name, legalities in legality_list.items():
            card = Card.objects.get(name=card_name)
            for format_name in legalities:
                format_obj = Format.objects.get(name__iexact=format_name)
                CardLegality.objects.get(card=card, format=format_obj).delete()
