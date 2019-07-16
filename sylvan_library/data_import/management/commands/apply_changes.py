"""
Module for the update_database command
"""
import logging
import time
from typing import List, Optional, Dict, Tuple
from django.db import transaction

from django.core.management.base import BaseCommand
from cards.models import (
    Block,
    Card,
    CardLegality,
    CardPrinting,
    CardPrintingLanguage,
    CardRuling,
    Colour,
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
            raise Exception()

    def create_new_blocks(self) -> None:
        with open(_paths.BLOCKS_TO_CREATE_PATH, "r", encoding="utf8") as block_file:
            block_list = json.load(block_file, encoding="utf8")

        for _, block_data in block_list.items():
            block = Block(
                name=block_data["name"], release_date=block_data["release_date"]
            )
            block.full_clean()
            block.save()

    def create_new_sets(self) -> None:
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
        with open(_paths.SETS_TO_UPDATE_PATH, "r", encoding="utf8") as set_file:
            set_list = json.load(set_file, encoding="utf8")

        for set_code, set_diff in set_list.items():
            set_obj = Set.objects.get(code=set_code)
            for field, change in set_diff.items():
                if field == "keyrune_code":
                    set_obj.keyrune_code = change["to"]
                elif field == "block":
                    set_obj.block = Block.objects.get(name=change["to"])
                elif field == "release_date":
                    set_obj.release_date = change["to"]
                elif field == "name":
                    set_obj.name = change["to"]
                else:
                    raise NotImplementedError(
                        f"Cannot update unrecognised field Set.{field}"
                    )
            set_obj.full_clean()
            set_obj.save()

    def create_cards(self) -> None:
        with open(_paths.CARDS_TO_CREATE, "r", encoding="utf8") as card_file:
            card_list = json.load(card_file, encoding="utf8")

        for _, card_data in card_list.items():
            card = Card(
                name=card_data["name"],
                cost=card_data["cost"],
                cmc=card_data["cmc"],
                colour_flags=card_data["colour"],
                colour_identity_flags=card_data["colour_identity"],
                colour_count=card_data["colour_count"],
                colour_sort_key=card_data["colour_sort_key"],
                colour_weight=card_data["colour_weight"],
                type=card_data["type"],
                subtype=card_data["subtype"],
                power=card_data["power"],
                num_power=card_data["num_power"],
                toughness=card_data["toughness"],
                num_toughness=card_data["num_toughness"],
                loyalty=card_data["loyalty"],
                num_loyalty=card_data["num_loyalty"],
                rules_text=card_data["rules_text"],
                layout=card_data["rules_text"],
                side=card_data["side"],
                is_reserved=card_data["is_reserved"],
                scryfall_oracle_id=card_data["scryfall_oracle_id"],
                is_token=card_data["is_token"],
            )
            card.full_clean()
            card.save()
