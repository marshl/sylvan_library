"""
Module for the update_database command
"""
import logging
import json
from typing import Union

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
from data_import import _query
import _paths


class Command(BaseCommand):
    """
    The command for updating hte database
    """

    help = (
        "Uses the downloaded JSON files to update the database, "
        "including creating cards, set and rarities\n"
    )

    def __init__(self, stdout=None, stderr=None, no_color=False):
        self.logger = logging.getLogger("django")
        super().__init__(stdout=stdout, stderr=stderr, no_color=no_color)

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
            self.logger.error(
                "No colours or rarities were found. "
                "Please run the update_metadata command first"
            )
            return

        transaction.atomic()
        with transaction.atomic():
            # pylint: disable=too-many-boolean-expressions
            if (
                not self.create_new_blocks()
                or not self.create_new_sets()
                or not self.update_sets()
                or not self.delete_card_printings()
                or not self.delete_rulings()
                or not self.delete_legalities()
                or not self.delete_cards()
                or not self.create_cards()
                or not self.update_cards()
                or not self.create_card_links()
                or not self.create_card_printings()
                or not self.create_printed_languages()
                or not self.create_physical_cards()
                or not self.create_rulings()
                or not self.create_legalities()
                or not self.update_legalities()
            ):
                raise Exception("Change application aborted")

    def read_json(self, filepath: str) -> Union[dict, list]:
        """
        Reads the given file, parses it as JSON and returns the result
        :param filepath: The file to parse
        :return: The dict or list content of the file
        """
        self.logger.debug("Reading json file %s", filepath)
        with open(filepath, "r", encoding="utf8") as json_file:
            return json.load(json_file, encoding="utf8")

    def create_new_blocks(self) -> bool:
        """
        Creates new Block objects
        returns: True if there were no errors, otherwise False
        """
        self.logger.info("Creating new blocks")
        block_list = self.read_json(_paths.BLOCKS_TO_CREATE_PATH)
        for _, block_data in block_list.items():
            block = Block(
                name=block_data["name"], release_date=block_data["release_date"]
            )
            block.full_clean()
            block.save()
        return True

    def create_new_sets(self) -> bool:
        """
        Creates new Set objects
        returns: True if there were no errors, otherwise False
        """
        self.logger.info("Creating new sets")
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
        return True

    def update_sets(self) -> bool:
        """
        Updates Sets that have changed
        returns: True if there were no errors, otherwise False
        """
        self.logger.info("Updating sets")
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
        return True

    def delete_cards(self) -> bool:
        """
        Detels Cards that have been removed
        returns: True if there were no errors, otherwise False
        """
        self.logger.info("Deleting cards")
        with open(_paths.CARDS_TO_DELETE, "r", encoding="utf8") as card_file:
            card_list = json.load(card_file, encoding="utf8")

        for card_name in card_list:
            card = Card.objects.get(name=card_name)
            if card.printings.filter(
                printed_languages__physical_cards__ownerships__isnull=False
            ):
                if not _query.query_yes_no(
                    f"Trying to delete card {card} but it has ownerships. Continue?",
                    "no",
                ):
                    return False
            card.delete()
        PhysicalCard.objects.filter(printed_languages__isnull=True).delete()
        return True

    def create_cards(self) -> bool:
        """
        Creates new Cards
        returns: True if there were no errors, otherwise False
        """
        self.logger.info("Creating new cards")
        with open(_paths.CARDS_TO_CREATE_PATH, "r", encoding="utf8") as card_file:
            card_list = json.load(card_file, encoding="utf8")

        for _, card_data in card_list.items():
            card = Card()
            for field, value in card_data.items():
                setattr(card, field, value)
            card.full_clean()
            card.save()

        return True

    def update_cards(self) -> bool:
        """
        Updates existing Cards with any changes
        returns: True if there were no errors, otherwise False
        """
        self.logger.info("Updating cards")
        with open(_paths.CARDS_TO_UPDATE, "r", encoding="utf8") as card_file:
            card_list = json.load(card_file, encoding="utf8")

        for card_name, card_diff in card_list.items():
            try:
                card = Card.objects.get(name=card_name)
            except Card.DoesNotExist:
                self.logger.error("Could not find card %s", card_name)
                raise

            for field, change in card_diff.items():
                if field in {
                    "colour_count",
                    "colour_flags",
                    "colour_sort_key",
                    "colour_identity_flags",
                    "colour_indicator_flags",
                    "colour_weight",
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
                    "side",
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
        return True

    def create_card_links(self) -> bool:
        """
        Creates new links between Card objects
        returns: True if there were no errors, otherwise False
        """
        self.logger.info("Creating card links")
        with open(_paths.CARD_LINKS_TO_CREATE, "r", encoding="utf8") as lnks_file:
            link_list = json.load(lnks_file, encoding="utf8")

        for card_name, links in link_list.items():
            card_obj = Card.objects.get(name=card_name, is_token=False)
            for link in links:
                card_obj.links.add(Card.objects.get(name=link, is_token=False))
            card_obj.save()
        return True

    def create_card_printings(self) -> bool:
        """
        Creates new CardPrintings
        returns: True if there were no errors, otherwise False
        """
        self.logger.info("Creating card printings")
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
                self.logger.error(
                    "Failed to validated %s (%s)",
                    printing_data["card_name"],
                    scryfall_id,
                )
                raise
            printing.save()
        return True

    def delete_card_printings(self) -> bool:
        """
        Deletes CardPrintings that should no longer exist
        returns: True if there were no errors, otherwise False
        """
        self.logger.info("Deleting card printings")
        with open(_paths.PRINTINGS_TO_DELETE, "r", encoding="utf8") as printings_file:
            printing_list = json.load(printings_file, encoding="utf8")

        for json_id, _ in printing_list.items():
            printing = CardPrinting.objects.get(json_id=json_id)
            if printing.printed_languages.filter(
                physical_cards__ownerships__isnull=False
            ):
                if not _query.query_yes_no(
                    f"Trying to delete {printing} but it has ownerships. Continue?",
                    "no",
                ):
                    return False

            printing.delete()

        PhysicalCard.objects.filter(printed_languages__isnull=True).delete()
        return True

    def create_printed_languages(self) -> bool:
        """
        Creates new CardPrintingLanguages
        returns: True if there were no errors, otherwise False
        """
        self.logger.info("Creating card printing languages")
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
                self.logger.error(
                    "Failed to validate CardPrintingLanguage %s", printed_language
                )
                raise
        return True

    def create_physical_cards(self) -> bool:
        """
        Creates new PhysicalCards
        returns: True if there were no errors, otherwise False
        """
        self.logger.info("Creating physical cards")
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
        return True

    def create_rulings(self) -> bool:
        """
        Creates new rulings
        returns: True if there were no errors, otherwise False
        """
        self.logger.info("Creating rulings")
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
        return True

    def delete_rulings(self) -> bool:
        """
        Deletes removed rulings
        returns: True if there were no errors, otherwise False
        """
        self.logger.info("Deleting rulings")
        with open(_paths.RULINGS_TO_DELETE, "r", encoding="utf8") as rulings_file:
            ruling_list = json.load(rulings_file, encoding="utf8")

        for card_name, rulings in ruling_list.items():
            card = Card.objects.get(name=card_name)
            for ruling_text in rulings:
                CardRuling.objects.get(card=card, text=ruling_text).delete()

        return True

    def create_legalities(self) -> bool:
        """
        Creates new CardLegalities
        returns: True if there were no errors, otherwise False
        """
        self.logger.info("Creating legalities")
        with open(_paths.LEGALITIES_TO_CREATE, "r", encoding="utf8") as legalities_file:
            legality_list = json.load(legalities_file, encoding="utf8")

        for legality_data in legality_list:
            legality = CardLegality()
            legality.card = Card.objects.get(
                name=legality_data["card_name"], is_token=False
            )
            try:
                legality.format = Format.objects.get(code=legality_data["format"])
            except Format.DoesNotExist:
                self.logger.error("Could not find format '%s'", legality_data["format"])
                raise

            legality.restriction = legality_data["restriction"]

            legality.full_clean()
            legality.save()
        return True

    def delete_legalities(self) -> bool:
        """
        Deletes the CardLegalities marked for deleting
        returns: True if there were no errors, otherwise False
        """
        self.logger.info("Deleting legalities")
        with open(_paths.LEGALITIES_TO_DELETE, "r", encoding="utf8") as legalities_file:
            legality_list = json.load(legalities_file, encoding="utf8")

        for card_name, legalities in legality_list.items():
            card = Card.objects.get(name=card_name)
            for format_code in legalities:
                format_obj = Format.objects.get(code=format_code)
                CardLegality.objects.get(card=card, format=format_obj).delete()

        return True

    def update_legalities(self) -> bool:
        """
        Applies the CardLegality changes
        returns: True if there were no errors, otherwise False
        """
        self.logger.info("Updating legalities")
        with open(_paths.LEGALITIES_TO_UPDATE, "r", encoding="utf8") as legalities_file:
            legality_list = json.load(legalities_file, encoding="utf8")

        for card_name, changes in legality_list.items():
            card = Card.objects.get(name=card_name)
            for format_name, change in changes.items():
                legality = CardLegality.objects.get(
                    card=card, format__code=format_name, restriction=change["from"]
                )
                legality.restriction = change["to"]
                legality.full_clean()
                legality.save()

        return True
