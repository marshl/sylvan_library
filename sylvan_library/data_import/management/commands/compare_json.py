"""
Module for the update_database command
"""
import logging
import time
import datetime
from typing import List, Optional, Dict, Tuple, Set as SetType
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

from data_import.staging import (
    StagedCard,
    StagedBlock,
    StagedSet,
    StagedLegality,
    StagedCardPrintingLanguage,
    StagedPhysicalCard,
    StagedCardPrinting,
    StagedRuling,
)


class Command(BaseCommand):
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
    existing_sets = {}  # type: Dict[str, Set]
    existing_blocks = {}  # type: Dict[str, Block]
    existing_rulings = {}  # type: Dict[str, Dict[str, str]]
    existing_legalities = {}  # type: Dict[str, Dict[str, str]]

    cards_to_create = {}  # type: Dict[str, StagedCard]
    cards_to_update = {}  # type: Dict[str, Dict[str, Dict[str]]]
    cards_to_delete = set()

    cards_parsed = set()

    card_printings_to_create = {}  # type: Dict[str, StagedCardPrinting]
    card_printings_to_update = {}  # type: Dict[str, Dict[str,dict]]
    card_printings_parsed = set()
    card_printings_to_delete = set()

    printed_languages_to_create = []  # type: List[StagedCardPrintingLanguage]
    physical_cards_to_create = []

    sets_to_create = {}  # type: Dict[str, StagedSet]
    sets_to_update = {}  # type: Dict[str, Dict[str, Dict[str]]]

    blocks_to_create = {}  # type: Dict[str, StagedBlock]

    rulings_to_create = []  # type: List[StagedRuling]
    rulings_to_delete = {}  # type: Dict[str, List[str]]
    cards_checked_For_rulings = set()  # type: Set

    cards_checked_for_legalities = set()  # type: Set
    legalities_to_create = []  # type: List[StagedLegality]
    legalities_to_delete = {}  # type: Dict[str, List[str]]
    legalities_to_update = {}  # type: Dict[str, Dict[str, Dict[str, str]]]

    card_links_to_create = {}  # type: Dict[str, List[str]]

    force_update = False
    start_time = None

    def add_arguments(self, parser):

        parser.add_argument(
            "--no-transaction",
            action="store_true",
            dest="no_transaction",
            default=False,
            help="Update the database without a transaction (unsafe)",
        )

    def handle(self, *args, **options):

        self.start_time = time.time()

        for card in Card.objects.all():
            if card.name in self.existing_cards:
                raise Exception(f"Multiple cards with the same name found: {card.name}")
            self.existing_cards[card.name] = card

        self.existing_card_printings = {
            cp.json_id: cp
            for cp in CardPrinting.objects.prefetch_related(
                "printed_languages__language"
            ).all()
        }

        self.existing_sets = {s.code: s for s in Set.objects.all()}
        self.existing_blocks = {b.name: b for b in Block.objects.all()}
        for ruling in CardRuling.objects.select_related("card"):
            if ruling.card.name not in self.existing_rulings:
                self.existing_rulings[ruling.card.name] = {}
            self.existing_rulings[ruling.card.name][ruling.text] = ruling

        for legality in (
            CardLegality.objects.prefetch_related("card")
            .prefetch_related("format")
            .all()
        ):
            if legality.card.name not in self.existing_legalities:
                self.existing_legalities[legality.card.name] = {}
            self.existing_legalities[legality.card.name][
                legality.format.code
            ] = legality.restriction

        set_data_list = []

        for set_file_path in [
            os.path.join(_paths.SET_FOLDER, s) for s in os.listdir(_paths.SET_FOLDER)
        ]:
            if not set_file_path.endswith(".json"):
                continue

            with open(set_file_path, "r", encoding="utf8") as set_file:
                set_data = json.load(set_file, encoding="utf8")
                set_data_list.append(set_data)

        set_data_list.sort(key=lambda s: s.get("releaseDate") or str(date.max()))

        for set_data in set_data_list:
            self.parse_set_data(set_data)

        self.cards_to_delete = set(self.existing_cards.keys()).difference(
            self.cards_parsed
        )

        self.card_printings_to_delete = set(
            self.existing_card_printings.keys()
        ).difference(self.card_printings_parsed)

        self.write_to_file()
        self.log_stats()

    def parse_set_data(self, set_data: dict) -> None:
        staged_set = StagedSet(set_data)
        if staged_set.code not in self.existing_sets:
            self.sets_to_create[staged_set.code] = staged_set
        else:
            existing_set = self.existing_sets[staged_set.code]
            differences = self.get_object_differences(
                existing_set,
                staged_set,
                {
                    # "base_set_size",
                    # "is_foil_only",
                    # "is_online_only",
                    "keyrune_code",
                    # "mcm_id",
                    # "mcm_name",
                    # "mtgo_code",
                    "name",
                    # "tcgplayer_group_id",
                    # "total_set_size",
                    "card_count",
                    "type",
                },
            )
            if (not existing_set.block and staged_set.block) or (
                existing_set.block and existing_set.block.name != staged_set.block
            ):
                differences["block"] = {
                    "from": existing_set.block.name if existing_set.block else None,
                    "to": staged_set.block,
                }

            if (
                existing_set.release_date.strftime("%Y-%m-%d")
                != staged_set.release_date
            ):
                differences["release_date"] = {
                    "from": existing_set.release_date.strftime("%Y-%m-%d"),
                    "to": staged_set.release_date,
                }

            if differences:
                self.sets_to_update[staged_set.code] = differences

        if staged_set.block and staged_set.block not in self.existing_blocks:
            block_to_create = self.blocks_to_create.get(staged_set.block)
            if not block_to_create:
                self.blocks_to_create[staged_set.block] = StagedBlock(
                    staged_set.block, staged_set.release_date
                )
            else:
                block_to_create.release_date = min(
                    block_to_create.release_date, staged_set.release_date
                )

        self.process_set_cards(set_data)
        self.process_card_links(set_data)

    def process_set_cards(self, set_data: dict) -> None:
        new_printlangs = []
        for card_data in set_data.get("cards", []):
            staged_card = self.process_card(card_data, False)
            staged_printing, printlangs = self.process_card_printing(
                staged_card, set_data, card_data
            )

            for printlang in printlangs:
                if printlang.is_new:
                    new_printlangs.append(printlang)

        for card_data in set_data.get("tokens", []):
            if (
                card_data["layout"] == "double_faced_token"
                and card_data.get("side", "") == "b"
            ):
                continue
            staged_card = self.process_card(card_data, True)

            staged_printing, printlangs = self.process_card_printing(
                staged_card, set_data, card_data
            )
            for printlang in printlangs:
                if printlang.is_new:
                    new_printlangs.append(printlang)

        for new_printlang in new_printlangs:
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

    def process_card(self, card_data: dict, is_token: bool) -> StagedCard:
        staged_card = StagedCard(card_data, is_token=is_token)
        if staged_card.name in self.cards_parsed:
            return staged_card

        if staged_card.name not in self.existing_cards:
            if staged_card.name not in self.cards_to_create:
                self.cards_to_create[staged_card.name] = staged_card
        elif staged_card.name not in self.cards_to_update:
            existing_card = self.existing_cards[staged_card.name]
            differences = self.get_card_differences(existing_card, staged_card)
            if differences:
                self.cards_to_update[staged_card.name] = differences

        self.process_card_rulings(staged_card)
        self.process_card_legalities(staged_card)
        self.cards_parsed.add(staged_card.name)
        return staged_card

    def process_card_rulings(self, staged_card: StagedCard) -> None:

        # If this card has already had its rulings parsed, than ignore it
        if staged_card.name in self.cards_checked_For_rulings:
            return

        self.cards_checked_For_rulings.add(staged_card.name)

        for ruling in staged_card.rulings:
            if (
                staged_card.name not in self.existing_rulings
                or ruling["text"] not in self.existing_rulings[staged_card.name]
            ):
                staged_ruling = StagedRuling(
                    staged_card.name, ruling["text"], ruling["date"]
                )
                self.rulings_to_create.append(staged_ruling)

        # For every existing ruling, it if isn't contained in the list of rulings,
        # then mark it for deletion
        if staged_card.name in self.existing_rulings:
            for existing_ruling, _ in self.existing_rulings[staged_card.name].items():
                if not any(
                    True
                    for ruling in staged_card.rulings
                    if ruling["text"] == existing_ruling
                ):
                    if staged_card.name not in self.rulings_to_delete:
                        self.rulings_to_delete[staged_card.name] = []

                    self.rulings_to_delete[staged_card.name].append(existing_ruling)

    def process_card_legalities(self, staged_card: StagedCard) -> None:
        if (
            staged_card.name in self.cards_checked_for_legalities
            or not staged_card.legalities
        ):
            return

        self.cards_checked_for_legalities.add(staged_card.name)

        for format, restriction in staged_card.legalities.items():
            if (
                staged_card.name not in self.existing_legalities
                or format not in self.existing_legalities[staged_card.name]
            ):
                staged_legality = StagedLegality(staged_card.name, format, restriction)
                self.legalities_to_create.append(staged_legality)

        if staged_card.name in self.existing_legalities:
            for old_format, old_restriction in self.existing_legalities[
                staged_card.name
            ].items():
                # Legalities to delete
                if old_format not in staged_card.legalities:
                    if staged_card.name not in self.legalities_to_delete:
                        self.legalities_to_delete[staged_card.name] = []
                    self.legalities_to_delete[staged_card.name].append(old_format)

                # Legalities to change
                elif staged_card.legalities[old_format] != old_restriction:
                    if staged_card.name not in self.legalities_to_update:
                        self.legalities_to_update[staged_card.name] = {}

                    self.legalities_to_update[staged_card.name][old_format] = {
                        "from": old_restriction,
                        "to": staged_card.legalities[old_format],
                    }

    def process_card_links(self, set_data: dict):
        for card in set_data.get("cards", []):
            if "names" not in card or not card["names"]:
                continue
            if card["name"] not in self.cards_to_create:
                continue

            staged_card = self.cards_to_create[card["name"]]
            for other_name in staged_card.other_names:
                if other_name not in self.cards_to_create:
                    continue
                other_staged_card = self.cards_to_create[other_name]
                if (
                    staged_card.layout == "meld"
                    and staged_card.side != "c"
                    and other_staged_card.layout != "c"
                ):
                    continue

                if staged_card.name not in self.card_links_to_create:
                    self.card_links_to_create[staged_card.name] = []

                self.card_links_to_create[staged_card.name].append(other_name)

    def get_object_differences(
        self, old_object, new_object, fields: SetType[str]
    ) -> dict:
        result = {}
        for field in fields:
            old_val = getattr(old_object, field)
            new_val = getattr(new_object, field)
            if type(old_val) != type(new_val) and type(None) not in [
                type(old_val),
                type(new_val),
            ]:
                raise Exception(
                    f"Type mismatch for '{field}: {old_val} != {new_val} "
                    f"({type(old_val)} != {type(new_val)})"
                )

            if old_val != new_val:
                result[field] = {"from": old_val, "to": new_val}

        return result

    def get_set_differences(
        self, existing_set: Set, staged_set: StagedSet
    ) -> Dict[str, dict]:
        return self.get_object_differences(
            existing_set, staged_set, {"keyrune_code", "name", "total_set_size", "type"}
        )

    def get_card_differences(
        self, existing_card: Card, staged_card: StagedCard
    ) -> Dict[str, dict]:
        differences = self.get_object_differences(
            existing_card,
            staged_card,
            {
                "rules_text",
                "type",
                "subtype",
                "cmc",
                "colour_count",
                "colour_weight",
                "colour_sort_key",
                "cost",
                "display_name",
                "is_reserved",
                "is_token",
                "layout",
                "loyalty",
                "name",
                "num_loyalty",
                "num_power",
                "num_toughness",
                "power",
                "rules_text",
                "scryfall_oracle_id",
                "side",
                "subtype",
                "toughness",
                "type",
            },
        )

        if staged_card.colour_flags != int(existing_card.colour_flags):
            differences["colour_flags"] = {
                "from": int(existing_card.colour_flags),
                "to": staged_card.colour_flags,
            }

        if staged_card.colour_identity_flags != int(
            existing_card.colour_identity_flags
        ):
            differences["colour_identity_flags"] = {
                "from": int(existing_card.colour_identity_flags),
                "to": staged_card.colour_identity_flags,
            }

        return differences

    def get_card_printing_differences(
        self, existing_printing: CardPrinting, staged_printing: StagedCardPrinting
    ) -> Dict[str, dict]:
        """
        Gets the differences between an existing printing and one from the json

        Most of the time there won't be any differences, but this will be useful for adding in new
        fields that didn't exist before
        :param existing_printing:
        :param staged_printing:
        :return:
        """
        result = {}
        return result

    def process_card_printing(
        self, staged_card: StagedCard, set_data: dict, card_data: dict
    ) -> Tuple[StagedCardPrinting, List[StagedCardPrintingLanguage]]:
        staged_card_printing = StagedCardPrinting(staged_card.name, card_data, set_data)
        uuid = staged_card_printing.json_id
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
            if differences:
                self.card_printings_to_update[uuid] = differences

        printlangs = [
            self.process_printed_language(
                staged_card_printing,
                {
                    "language": "English",
                    "multiverseId": staged_card_printing.multiverse_id,
                    "name": staged_card.display_name,
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
        self.card_printings_parsed.add(staged_card_printing.json_id)

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
            staged_card_printing.json_id, staged_card_printing_language.language
        )

        if not existing_print:
            staged_card_printing_language.is_new = True
            self.printed_languages_to_create.append(staged_card_printing_language)

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

    def write_object_to_json(self, filename: str, data: object) -> None:
        with open(filename, "w") as output_file:
            json.dump(data, output_file, indent=2)

    def write_to_file(self) -> None:
        self.write_object_to_json(
            _paths.BLOCKS_TO_CREATE_PATH,
            {
                block_name: staged_block.to_dict()
                for block_name, staged_block in self.blocks_to_create.items()
            },
        )

        self.write_object_to_json(
            _paths.SETS_TO_CREATE_PATH,
            {
                set_code: set_to_create.to_dict()
                for set_code, set_to_create in self.sets_to_create.items()
            },
        )

        self.write_object_to_json(
            _paths.SETS_TO_UPDATE_PATH,
            {
                set_code: set_to_update
                for set_code, set_to_update in self.sets_to_update.items()
            },
        )

        self.write_object_to_json(
            _paths.CARDS_TO_CREATE_PATH,
            {
                card_name: card_to_create.to_dict()
                for card_name, card_to_create in self.cards_to_create.items()
            },
        )

        self.write_object_to_json(
            _paths.CARDS_TO_UPDATE,
            {
                card_name: card_to_update
                for card_name, card_to_update in self.cards_to_update.items()
            },
        )

        self.write_object_to_json(_paths.CARDS_TO_DELETE, list(self.cards_to_delete))

        self.write_object_to_json(
            _paths.PRINTINGS_TO_CREATE,
            {
                uuid: printing_to_create.to_dict()
                for uuid, printing_to_create in self.card_printings_to_create.items()
            },
        )

        printings_to_delete_dict = {}
        for json_id in self.card_printings_to_delete:
            printing = CardPrinting.objects.get(json_id=json_id)
            printings_to_delete_dict[json_id] = {
                "card_name": printing.card.name,
                "set": printing.set.code,
                "number": printing.number,
            }

        self.write_object_to_json(_paths.PRINTINGS_TO_DELETE, printings_to_delete_dict)

        self.write_object_to_json(
            _paths.PRINTLANGS_TO_CREATE,
            [
                printlang_to_create.to_dict()
                for printlang_to_create in self.printed_languages_to_create
            ],
        )

        self.write_object_to_json(
            _paths.PHYSICAL_CARDS_TO_CREATE,
            [
                physical_card_to_create.to_dict()
                for physical_card_to_create in self.physical_cards_to_create
            ],
        )

        self.write_object_to_json(
            _paths.RULINGS_TO_CREATE,
            [ruling.to_dict() for ruling in self.rulings_to_create],
        )

        self.write_object_to_json(_paths.RULINGS_TO_DELETE, self.rulings_to_delete)

        self.write_object_to_json(
            _paths.LEGALITIES_TO_CREATE,
            [legality.to_dict() for legality in self.legalities_to_create],
        )

        self.write_object_to_json(
            _paths.LEGALITIES_TO_DELETE, self.legalities_to_delete
        )
        self.write_object_to_json(
            _paths.LEGALITIES_TO_UPDATE, self.legalities_to_update
        )

        self.write_object_to_json(
            _paths.CARD_LINKS_TO_CREATE, self.card_links_to_create
        )

    def log_stats(self) -> None:
        logger.info(f"{len(self.blocks_to_create)} blocks to create")
        logger.info(f"{len(self.sets_to_create)} sets to create")
        logger.info(f"{len(self.sets_to_update)} sets to update")
        logger.info(f"{len(self.cards_to_create)} cards to create")
        logger.info(f"{len(self.cards_to_update)} cards to update")
        logger.info(f"{len(self.cards_to_delete)} cards to delete")
        logger.info(f"{len(self.card_links_to_create)} card links to create")
        logger.info(f"{len(self.card_printings_to_create)} card printings to create")
        logger.info(f"{len(self.card_printings_to_delete)} card printings to delete")
        logger.info(f"{len(self.card_printings_to_update)} card printings to update")
        logger.info(
            f"{len(self.printed_languages_to_create)} card printing languages to create"
        )
        logger.info(f"{len(self.physical_cards_to_create)} physical cards to create")
        logger.info(f"{len(self.rulings_to_create)} rulings to create")
        logger.info(f"{len(self.rulings_to_delete)} rulings to delete")
        logger.info(f"{len(self.legalities_to_create)} legalities to create")
        logger.info(f"{len(self.legalities_to_delete)} legalities to delete")
        logger.info(f"{len(self.legalities_to_update)} legalities to update")
        logger.info(f"Completed in {time.time() - self.start_time}")
