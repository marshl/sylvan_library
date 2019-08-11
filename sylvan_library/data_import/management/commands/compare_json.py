"""
Module for the update_database command
"""
import logging
import time
import os
from datetime import date
import json
from typing import List, Optional, Dict, Tuple, Set as SetType, Union

from django.core.management.base import BaseCommand
from cards.models import (
    Block,
    Card,
    CardLegality,
    CardPrinting,
    CardPrintingLanguage,
    CardRuling,
    Set,
)
import _paths
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
    printed_languages_to_update = []  # type: List[dict]
    physical_cards_to_create = []

    sets_to_create = {}  # type: Dict[str, StagedSet]
    sets_to_update = {}  # type: Dict[str, Dict[str, Dict[str]]]

    blocks_to_create = {}  # type: Dict[str, StagedBlock]

    rulings_to_create = []  # type: List[StagedRuling]
    rulings_to_delete = {}  # type: Dict[str, List[str]]
    cards_checked_For_rulings = set()  # type: set

    cards_checked_for_legalities = set()  # type: set
    legalities_to_create = []  # type: List[StagedLegality]
    legalities_to_delete = {}  # type: Dict[str, List[str]]
    legalities_to_update = {}  # type: Dict[str, Dict[str, Dict[str, str]]]

    card_links_to_create = {}  # type: Dict[str, set]

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
            self.process_set_cards(set_data)
            self.process_card_links(set_data)

        self.cards_to_delete = set(self.existing_cards.keys()).difference(
            self.cards_parsed
        )

        self.card_printings_to_delete = set(
            self.existing_card_printings.keys()
        ).difference(self.card_printings_parsed)

        self.write_to_file()
        self.log_stats()

    def parse_set_data(self, set_data: dict) -> None:
        """
        Parses a set dict and checks for updates/creates/deletes to be done
        :param set_data: The MTGJSON set dict
        """
        staged_set = StagedSet(set_data)
        if staged_set.code not in self.existing_sets:
            self.sets_to_create[staged_set.code] = staged_set
        else:
            existing_set = self.existing_sets[staged_set.code]
            self.compare_sets(existing_set, staged_set)

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

    def compare_sets(self, existing_set: Set, staged_set: StagedSet) -> None:
        """
        Compares and existing  Set with a staged one,
        and stores a list of updates if any are required
        :param existing_set: THe existing Set object
        :param staged_set: The StagedSet object
        """
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

        old_release_date_str = existing_set.release_date.strftime("%Y-%m-%d")
        if old_release_date_str != staged_set.release_date:
            differences["release_date"] = {
                "from": old_release_date_str,
                "to": staged_set.release_date,
            }

        if differences:
            self.sets_to_update[staged_set.code] = differences

    def process_set_cards(self, set_data: dict) -> None:
        """
        Processes the cards within a set dictionary
        :param set_data:  The MTGJSON set dictionary
        """
        # Store which CardPrintingLanguages are new so PhysicalCards can be created for them
        new_printlangs = []
        for card_data in set_data.get("cards", []):
            staged_card = self.process_card(card_data, False)
            _, printlangs = self.process_card_printing(staged_card, set_data, card_data)

            for printlang in printlangs:
                if printlang.is_new:
                    new_printlangs.append(printlang)

        for card_data in set_data.get("tokens", []):
            # Double-faced tokens can't be handled with the current way the database is set up
            # example, there could exist a Knight/Saproling as well as a Saproling/Elemental
            # They could be connected at the printing level, but they can't be connected at the Card
            # level or the Knight and the Elemental would also be linked together
            if (
                card_data["layout"] == "double_faced_token"
                and card_data.get("side", "") == "b"
            ):
                continue
            staged_card = self.process_card(card_data, True)
            _, printlangs = self.process_card_printing(staged_card, set_data, card_data)
            for printlang in printlangs:
                if printlang.is_new:
                    new_printlangs.append(printlang)
        self.process_physical_cards(new_printlangs)

    def process_physical_cards(
        self, new_printlangs: List[StagedCardPrintingLanguage]
    ) -> None:
        """
        Finds ne PhysicalCards to be created using a list of new printlangs
        :param new_printlangs: The StagedCardPrintingLanguages that are going to be made for a set
        """
        for new_printlang in new_printlangs:
            # Ignore "C" side meld cards, we don't want a single PhysicalCard for A/B/C
            # For example, we don't want a Brisela/Gisela/Bruna card,
            # instead we want a Bruna/Brisela card and a Gisela/Brisela card
            if new_printlang.has_physical_card or (
                new_printlang.layout == "meld" and new_printlang.side == "c"
            ):
                continue

            uids = []
            if new_printlang.other_names:
                for other_printlang in new_printlangs:
                    if (
                        other_printlang.base_name in new_printlang.other_names
                        and other_printlang.language == new_printlang.language
                        and (
                            new_printlang.layout != "meld"
                            or new_printlang.side == "c"
                            or other_printlang.side == "c"
                        )
                    ):
                        other_printlang.has_physical_card = True
                        uids.append(other_printlang.printing_uuid)
            uids.append(new_printlang.printing_uuid)

            staged_physical_card = StagedPhysicalCard(
                printing_uuids=uids,
                language_code=new_printlang.language,
                layout=new_printlang.layout,
            )
            self.physical_cards_to_create.append(staged_physical_card)
            new_printlang.has_physical_card = True

    def process_card(self, card_data: dict, is_token: bool) -> StagedCard:
        """
        Parses the given card data dict and returns a new or existing StagedCard
        :param card_data: THe MTG JSON card data dict
        :param is_token: True if this card is a token, otherwise False
        (tokens include emblems, World Championship Bios, checklist cards, etc.)
        :return: A StagedCard that represents the json card
        If the card has already been parsed, then the existing StagedCard will be returned
        """
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
        """
        Finds CardRulings of the given StagedCard to create or delete
        :param staged_card: The StagedCard to find rulings for
        """
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
        """
        Find CardLegalities for a card to update, create or delete
        :param staged_card: The StagedCard to find legalities for
        """
        if (
            staged_card.name in self.cards_checked_for_legalities
            or not staged_card.legalities
        ):
            return

        self.cards_checked_for_legalities.add(staged_card.name)

        # Legalities to create
        for format_obj, restriction in staged_card.legalities.items():
            if (
                staged_card.name not in self.existing_legalities
                or format_obj not in self.existing_legalities[staged_card.name]
            ):
                staged_legality = StagedLegality(
                    staged_card.name, format_obj, restriction
                )
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

                # Legalities to update
                elif staged_card.legalities[old_format] != old_restriction:
                    if staged_card.name not in self.legalities_to_update:
                        self.legalities_to_update[staged_card.name] = {}

                    self.legalities_to_update[staged_card.name][old_format] = {
                        "from": old_restriction,
                        "to": staged_card.legalities[old_format],
                    }

    def process_card_links(self, set_data: dict) -> None:
        """
        Finds potential links between cards in the set
        Note that tokens are deliberately NOT linked, as they can be linked in different ways
        depending on the set (this isn't possible iwht normal cards)
        :param set_data: The JSON set to parse
        """
        for card in set_data.get("cards", []):
            if "names" not in card or not card["names"]:
                continue
            # Don't bother creating links for existing cards
            # NOTE: This could cause a broken link on cards that are added piecemeal
            # (such as during a card spoiler season)
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
                    self.card_links_to_create[staged_card.name] = set()

                self.card_links_to_create[staged_card.name].add(other_name)

    @staticmethod
    def get_object_differences(old_object, new_object, fields: SetType[str]) -> dict:
        """
        Gets the differences between the given fields of two objects
        :param old_object: The old version of the object (stored in the database)
        :param new_object: The new version of hte object (the Staged* object)
        :param fields: The fields to compare
        :return: A dict of "field* => {"old" => "x", "new" => "y"} differences
        """
        result = {}
        for field in fields:
            old_val = getattr(old_object, field)
            new_val = getattr(new_object, field)
            if (
                not isinstance(old_val, type(new_val))
                and not isinstance(old_val, type(None))
                and not isinstance(new_val, type(None))
            ):
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
        """
        Gets the differences between an existing and staged Set object
        :param existing_set: The existing Set object
        :param staged_set: The StagedSet object
        :return: A dict of the differences between the sets
        """
        return self.get_object_differences(
            existing_set, staged_set, {"keyrune_code", "name", "total_set_size", "type"}
        )

    def get_card_differences(
        self, existing_card: Card, staged_card: StagedCard
    ) -> Dict[str, dict]:
        """
        Returns the differences between an existing Card object and the StagedCard version
        :param existing_card: The existing database Card object
        :param staged_card: The json StagedCard object
        :return: A dict of differences between the two object
        """
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
                "face_cmc",
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

        # Colour flags need to be handled slightly explicitly because the database values aren't int
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

        if staged_card.colour_indicator_flags != int(
            existing_card.colour_indicator_flags
        ):
            differences["colour_indicator_flags"] = {
                "from": int(existing_card.colour_indicator_flags),
                "to": staged_card.colour_indicator_flags,
            }

        return differences

    def get_card_printing_differences(
        self, existing_printing: CardPrinting, staged_printing: StagedCardPrinting
    ) -> Dict[str, dict]:
        """
        Gets the differences between an existing printing and one from the json

        Most of the time there won't be any differences, but this will be useful for adding in new
        fields that didn't exist before
        :param existing_printing: The existing CardPrinting object
        :param staged_printing: The json StagedCardPrinting object
        :return: The dict of differences between the two objects
        """
        result = self.get_object_differences(
            existing_printing,
            staged_printing,
            {"duel_deck_side", "frame_effect", "frame_version"},
        )
        return result

    def process_card_printing(
        self, staged_card: StagedCard, set_data: dict, card_data: dict
    ) -> Tuple[StagedCardPrinting, List[StagedCardPrintingLanguage]]:
        """
        Process a Card printed in a given set,
         returning the printings and printined languages that were found
        :param staged_card: The already known StagedCard
        :param set_data: The set data
        :param card_data: The data of the card
        :return: A tuple containing the StagedCardPrinting and a list of StagedCardPrintingLanguages
        """
        staged_card_printing = StagedCardPrinting(staged_card.name, card_data, set_data)
        uuid = staged_card_printing.json_id
        if uuid not in self.existing_card_printings:
            if uuid not in self.card_printings_to_update:
                staged_card_printing.is_new = True
                self.card_printings_to_create[uuid] = staged_card_printing
            else:
                raise Exception(f"Printing already to be update {uuid}")
        else:
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
                    "flavorText": card_data.get("flavorText"),
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
        """
        Processes card data nad returns the StagedCardPritningLanguage that would represent it
        :param staged_card_printing: The CardPrinting the printlang belongs to
        :param foreign_data: The dict of firegn data, that may include original text etc.
        :param card_data: The JSON data dict
        :return:
        """
        staged_card_printing_language = StagedCardPrintingLanguage(
            staged_card_printing, foreign_data, card_data
        )

        existing_printlang = self.get_existing_printed_language(
            staged_card_printing.json_id, staged_card_printing_language.language
        )

        if not existing_printlang:
            staged_card_printing_language.is_new = True
            self.printed_languages_to_create.append(staged_card_printing_language)
        else:
            differences = self.get_card_printing_language_differences(
                existing_printlang, staged_card_printing_language
            )
            if differences:
                self.printed_languages_to_update.append(
                    {
                        "uuid": staged_card_printing.json_id,
                        "language": staged_card_printing_language.language,
                        "changes": differences,
                    }
                )

        return staged_card_printing_language

    def get_existing_printed_language(
        self, uuid: str, language: str
    ) -> Optional[CardPrintingLanguage]:
        """
        Tried to find the existing CardPrintingLanguage for the given CardPrinting uuid/language
        combineation, if it exists (otherwise None)
        :param uuid: The uuid (json_id) of the CardPrinting
        :param language: The _name_ of the language ('English', not 'english')
        :return: The existing CardPrintingLanguage if it exists, otherwise None
        """
        existing_print = self.existing_card_printings.get(uuid)
        if not existing_print:
            return None

        for printlang in existing_print.printed_languages.all():
            if printlang.language.name == language:
                return printlang

        return None

    def get_card_printing_language_differences(
        self,
        existing_printlang: CardPrintingLanguage,
        staged_printlang: StagedCardPrintingLanguage,
    ) -> Dict[str, dict]:
        """
       Gets the differences between an existing printed language and one from the json

       Most of the time there won't be any differences, but this will be useful for adding in new
       fields that didn't exist before
       :param existing_printlang: The existing CardPrintingLanguage object
       :param staged_printlang: The json StagedCardPrintingLanguage object
       :return: The dict of differences between the two objects
       """
        result = self.get_object_differences(
            existing_printlang, staged_printlang, {"text", "flavour_text", "type"}
        )
        return result

    @staticmethod
    def write_object_to_json(filename: str, data: Union[list, dict]) -> None:
        """
        Writes out the given object to file as JSON
        :param filename: The file to write out to
        :param data: THe data to write to file
        """
        with open(filename, "w") as output_file:
            json.dump(data, output_file, indent=2)

    def write_to_file(self) -> None:
        """
        WRites all lists of changes out to their respective files
        """
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

        self.write_object_to_json(
            _paths.PRINTINGS_TO_UPDATE, self.card_printings_to_update
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
            _paths.PRINTLANGS_TO_UPDATE, self.printed_languages_to_update
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
        """
        Logs out the number sof objects to delete/create/update
        """
        logger.info("%s blocks to create", len(self.blocks_to_create))
        logger.info("%s sets to create", len(self.sets_to_create))
        logger.info("%s sets to update", len(self.sets_to_update))
        logger.info("%s cards to create", len(self.cards_to_create))
        logger.info("%s cards to update", len(self.cards_to_update))
        logger.info("%s cards to delete", len(self.cards_to_delete))
        logger.info("%s card links to create", len(self.card_links_to_create))
        logger.info("%s card printings to create", len(self.card_printings_to_create))
        logger.info("%s card printings to delete", len(self.card_printings_to_delete))
        logger.info("%s card printings to update", len(self.card_printings_to_update))
        logger.info(
            "%s card printing languages to create",
            len(self.printed_languages_to_create),
        )
        logger.info(
            "%s card printing languages to update",
            len(self.printed_languages_to_update),
        )
        logger.info("%s physical cards to create", len(self.physical_cards_to_create))
        logger.info("%s rulings to create", len(self.rulings_to_create))
        logger.info("%s rulings to delete", len(self.rulings_to_delete))
        logger.info("%s legalities to create", len(self.legalities_to_create))
        logger.info("%s legalities to delete", len(self.legalities_to_delete))
        logger.info("%s legalities to update", len(self.legalities_to_update))
        logger.info("Completed in %ss", time.time() - self.start_time)
