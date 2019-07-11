"""
Module for the update_database command
"""
import logging
import time
from typing import List, Optional, Dict, Tuple
from django.db import transaction

from cards.models import (
    Block,
    Card,
    CardPrinting,
    CardPrintingLanguage,
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


class StagedCard:
    def __init__(self, json_data: dict, is_token: bool):
        self.is_token = is_token

        self.colour_identity = json_data.get("colourIdentity", [])
        self.colours = json_data.get("colors", [])
        self.cmc = json_data.get("convertedManaCost", 0)
        self.layout = json_data.get("layout")
        self.mana_cost = json_data.get("maaaCost")
        self.name = json_data.get("name")
        self.power = json_data.get("number")
        self.scryfall_oracle_id = json_data.get("scryfallOracleId")
        # self.subtypes = json_data.get("subtypes")
        # self.supertypes = json_data.get("supertypes")
        self.rules_text = json_data.get("text")
        self.toughness = json_data.get("toughness")
        # self.type = json_data.get("type")
        # self.type = json_data.get("types")

        self.type = None
        if self.is_token:
            if "type" in json_data:
                self.type = json_data["type"].split("—")[0].strip()
        elif "types" in json_data:
            self.type = " ".join(
                (json_data.get("supertypes") or []) + (json_data["types"])
            )

        self.subtype = None
        if self.is_token:
            if "type" in json_data:
                self.subtype = json_data["type"].split("—")[-1].strip()
        elif "subtypes" in json_data:
            self.subtype = " ".join(json_data.get("subtypes"))


class StagedSet:
    def __init__(self, set_data: dict):
        self.base_set_size = set_data["baseSetSize"]
        self.block = set_data.get("block")
        self.code = set_data["code"]
        self.is_foil_only = set_data["isFoilOnly"]
        self.is_online_only = set_data["isOnlineOnly"]
        self.keyruneCode = set_data["keyruneCode"]
        self.mcm_id = set_data.get("mcmId")
        self.mcm_name = set_data.get("mcmName")
        self.mtg_code = set_data.get("mtgoCode")
        self.name = set_data["name"]
        self.release_date = set_data["releaseDate"]
        self.tcg_player_group_id = set_data.get("tcg_player_group_id")
        self.total_set_sie = set_data["totalSetSize"]
        self.type = set_data["type"]


class StagedCardPrinting:
    # Staged Card
    # Staged Set
    def __init__(self, card_name: str, json_data: dict, set_data: dict):
        self.card_name = card_name

        self.artist = json_data.get("artist")
        self.border_colour = json_data.get("borderColor")
        self.frame_version = json_data.get("frameVersion")
        self.hasFoil = json_data.get("hasFoil")
        self.hasNonFoil = json_data.get("hasNonFoil")
        self.number = json_data.get("number")
        self.rarity = json_data.get("rarity")
        self.scryfall_id = json_data.get("scryfallId")
        self.scryfall_illustration_id = json_data.get("scryfallIllustrationId")
        self.uuid = json_data.get("uuid")
        self.multiverse_id = json_data.get("multiverseId")
        self.other_languages = json_data.get("foreignData")
        self.names = json_data.get("names", [])

        self.set_code = set_data["code"]

        self.is_new = False


class StagedLegality:
    pass


class StagedRuling:
    pass


class StagedCardPrintingLanguage:
    def __init__(
        self,
        staged_card_printing: StagedCardPrinting,
        foreign_data: dict,
        card_data: dict,
    ):
        self.printing_uuid = staged_card_printing.uuid

        self.language = foreign_data["language"]
        self.foreign_name = foreign_data["name"]

        self.multiverse_id = foreign_data.get("multiverseId")
        self.text = foreign_data.get("text")
        self.type = foreign_data.get("type")

        self.other_names = card_data.get("names", [])
        self.base_name = card_data["name"]
        if self.base_name in self.other_names:
            self.other_names.remove(self.base_name)
        self.layout = card_data["layout"]
        self.side = card_data.get("side")

        self.is_new = False
        self.has_physical_card = False


class StagedPhysicalCard:
    def __init__(self, printing_uuids: List[str], language_code: str, layout: str):
        self.printing_uids = printing_uuids
        self.language_code = language_code
        self.layout = layout

    def __str__(self) -> str:
        return f"{'/'.join(self.printing_uids)} in {self.language_code} ({self.layout})"


"""
Two split cards have the same scryfall IDs and scryfall oracle ids
 but different names and different uuids

Two tokens of the same type have different scryfall ids and different uuids, 
but the same scryfall oracle ids

json_id (uuid) is unique on the DB


Non-token cards have unique names

Card Printings have unique UUIDs



"""


class Command(DataImportCommand):
    """
    The command for updating hte database
    """

    help = (
        "Uses the downloaded JSON files to update the database, "
        "including creating cards, set and rarities\n"
        "Use the update_rulings command to update rulings"
    )

    existing_cards = {}  # type: Dict[str, Card]
    existing_card_printings = {}  # type: Dict[str, CardPrinting]

    cards_to_create = {}  # type: Dict[str, StagedCard]
    cards_to_update = {}  # type: Dict[str, Dict[str, Dict[str]]]
    cards_to_delete = {}  # type: Dict[str, Card]

    card_printings_to_create = {}  # type: Dict[str, StagedCardPrinting]
    card_printings_to_update = {}  # type: Dict[str, StagedCardPrinting]

    printed_languages_to_create = []
    physical_cards_to_create = []

    force_update = False

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

        self.start_time = time.time()

        for card in Card.objects.filter(is_token=False):
            if card.name in self.existing_cards:
                raise Exception(f"Multiple cards with the same name found: {card.name}")
            self.existing_cards[card.name] = card

        self.existing_card_printings = {
            cp.scryfall_id: cp
            for cp in CardPrinting.objects.prefetch_related(
                "printed_languages__language"
            ).all()
        }

        for set_file_path in [
            os.path.join(_paths.SET_FOLDER, s) for s in os.listdir(_paths.SET_FOLDER)
        ]:
            if not set_file_path.endswith(".json"):
                continue

            # setcode = os.path.splitext(os.path.basename(set_file_path))[0].strip("_")

            # if not Set.objects.filter(code__iexact=setcode).exists():
            #     print(f"changed {setcode}")
            # else:
            #     continue

            with open(set_file_path, "r", encoding="utf8") as set_file:
                set_data = json.load(set_file, encoding="UTF-8")
                self.parse_set_data(set_data)

        print("\nCards to create:")
        for card_name, staged_card in self.cards_to_create.items():
            print(card_name)

        print("\nCards to update:")
        for card_name, differences in self.cards_to_update.items():
            print(f"{card_name}: {differences}")

        # for scryfall_id, staged_printing in self.card_printings_to_create.items():
        #     print(f"{staged_printing.scryfall_oracle_id} in {staged_printing.set_code}")

        print(time.time() - self.start_time)

    def parse_set_data(self, set_data: dict) -> None:
        # new_printings = []
        staged_set = StagedSet(set_data)
        if not Set.objects.filter(code=staged_set.code).exists():
            print(staged_set.name)

        new_printlangs = []

        for card_data in set_data.get("cards", []):
            staged_card = self.process_card(card_data, False)
            staged_printing, printlangs = self.process_card_printing(
                staged_card, set_data, card_data
            )
            # if staged_printing.is_new:
            #     new_printings.append(staged_printing)

            for printlang in printlangs:
                if printlang.is_new:
                    new_printlangs.append(printlang)

        for new_printlang in new_printlangs:  # new_printings:
            if new_printlang.has_physical_card or (
                new_printlang.layout == "meld" and new_printlang.side == "c"
            ):
                continue

            uids = []
            if new_printlang.other_names:

                for pl in new_printlangs:
                    if (
                        pl.base_name in new_printlang.other_names
                        and pl.language == new_printlang.language
                        and (
                            new_printlang.layout != "meld"
                            or new_printlang.side == "c"
                            or pl.side == "c"
                        )
                    ):
                        pl.has_physical_card = True
                        uids.append(pl.printing_uuid)
            uids.append(new_printlang.printing_uuid)

            staged_physical_card = StagedPhysicalCard(
                printing_uuids=uids,
                language_code=new_printlang.language,
                layout=new_printlang.layout,
            )
            self.physical_cards_to_create.append(staged_physical_card)
            new_printlang.has_physical_card = True
            # print(staged_physical_card)

    def process_card(self, card_data: dict, is_token: bool) -> StagedCard:
        # scryfall_oracle_id = card_data["scryfallOracleId"]
        staged_card = StagedCard(card_data, is_token=is_token)
        if staged_card.name not in self.existing_cards:
            if staged_card.name not in self.cards_to_create:
                self.cards_to_create[staged_card.name] = staged_card
        elif staged_card.name not in self.cards_to_update:
            existing_card = self.existing_cards[staged_card.name]
            differences = self.get_card_differences(existing_card, staged_card)
            if differences:
                self.cards_to_update[staged_card.name] = differences

        return staged_card

    def get_card_differences(
        self, existing_card: Card, staged_card: StagedCard
    ) -> Dict[str, dict]:
        result = {}
        if staged_card.name != existing_card.name:
            result["name"] = {"from": existing_card.name, "to": staged_card.name}

        if staged_card.rules_text != existing_card.rules_text:
            result["rules_text"] = {
                "from": existing_card.rules_text,
                "to": staged_card.rules_text,
            }

        if staged_card.type != existing_card.type:
            result["type"] = {"from": existing_card.type, "to": staged_card.type}

        if staged_card.subtype != existing_card.subtype:
            result["subtype"] = {
                "from": existing_card.subtype,
                "to": staged_card.subtype,
            }
        return result

    def get_card_printing_differences(
        self, existing_printing: CardPrinting, staged_printing: StagedCardPrinting
    ) -> Dict[str, dict]:
        result = {}
        return result

    # def get_existing_card(self, scryfall_oracle_id: str, side: str):
    #     if scryfall_oracle_id not in self.existing_cards:
    #         return None
    #
    #     cards = self.existing_cards[scryfall_oracle_id]
    #
    #     return next((card for card in cards if card.side == side), None)

    def process_card_printing(
        self, staged_card: StagedCard, set_data: dict, card_data: dict
    ) -> Tuple[StagedCardPrinting, List[StagedCardPrintingLanguage]]:
        staged_card_printing = StagedCardPrinting(staged_card.name, card_data, set_data)
        # scryfall_id = staged_card_printing.scryfall_id
        uuid = staged_card_printing.uuid
        if uuid not in self.existing_card_printings:
            if uuid not in self.card_printings_to_update:
                staged_card_printing.is_new = True
                self.card_printings_to_create[uuid] = staged_card_printing
            else:
                raise Exception(f"Printing already to be update {uuid}")
        elif uuid not in self.card_printings_to_update:
            existing_printing = self.existing_card_printings[uuid]
            differences = self.get_card_printing_differences(
                existing_printing, staged_card_printing
            )
            self.card_printings_to_create[uuid] = differences

        printlangs = [
            self.process_printed_language(
                staged_card_printing,
                {
                    "language": "English",
                    "multiverseId": staged_card_printing.multiverse_id,
                    "name": card_data["name"],
                    "text": card_data.get("text"),
                    "type": card_data.get("type"),
                },
                card_data,
            )
        ]

        for foreign_data in staged_card_printing.other_languages:
            staged_printlang = self.process_printed_language(
                staged_card_printing, foreign_data, card_data
            )
            printlangs.append(staged_printlang)

        return staged_card_printing, printlangs

    def process_printed_language(
        self,
        staged_card_printing: StagedCardPrinting,
        foreign_data: dict,
        card_data: dict,
    ) -> StagedCardPrintingLanguage:
        staged_card_printing_language = StagedCardPrintingLanguage(
            staged_card_printing, foreign_data, card_data
        )

        existing_print = self.get_existing_printed_language(
            staged_card_printing.scryfall_id, staged_card_printing_language.language
        )

        if not existing_print:
            staged_card_printing_language.is_new = True
            self.printed_languages_to_create.append(staged_card_printing_language)
            # self.process_physical_cards(staged_card_printing_language, card_data)
            # print(
            #     f"Need to make new print {staged_card_printing_language.language} {staged_card_printing_language.name} in {staged_card_printing.set_code}"
            # )
        return staged_card_printing_language

    def get_existing_printed_language(
        self, uuid: str, language: str
    ) -> Optional[CardPrintingLanguage]:
        existing_print = self.existing_card_printings.get(uuid)
        if not existing_print:
            return None

        for printlang in existing_print.printed_languages.all():
            if printlang.language.name == language:
                return printlang

        return None

    def process_physical_cards(
        self, printing_language: StagedCardPrintingLanguage, card_data: dict
    ) -> None:
        pass
