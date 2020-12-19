"""
Module for the update_database command
"""
import logging
import math
import time
import typing
from datetime import date
from typing import List, Optional, Dict, Tuple, Any

from django.core.management.base import BaseCommand
from django.db import models, transaction

from cards.models import (
    Block,
    Card,
    CardPrinting,
    CardPrintingLanguage,
    Set,
    CardFace,
    CardRuling,
)
from data_import import _paths
from data_import.management.commands import get_all_set_data
from data_import.models import (
    UpdateSet,
    UpdateCard,
    UpdateBlock,
    UpdateMode,
    UpdateCardFace,
    UpdateCardRuling,
)
from data_import.staging import (
    StagedCard,
    StagedSet,
    StagedCardPrintingLanguage,
    StagedCardPrinting,
    StagedCardFace,
)

logger = logging.getLogger("django")


def staging_object_to_dict(obj: object, fields_to_ignore: Optional[set] = None) -> dict:
    """
    Converts any kind of staging object to a dictionary to save out to json
    :param obj: The staging object
    :param fields_to_ignore:  Fields that shouldn't be serialized out
    :return: The staged object as a dictionary
    """
    result = {}
    for key in dir(obj):
        if fields_to_ignore and key in fields_to_ignore:
            continue

        if key.startswith("_"):
            continue

        attr = getattr(obj, key)
        if callable(attr):
            continue

        if isinstance(attr, date):
            result[key] = attr.strftime("%Y-%m-%d")
            continue

        if attr == math.inf:
            result[key] = "\u221e"
            continue

        result[key] = attr
    return result


class Command(BaseCommand):
    """
    The command for updating hte database
    """

    help = (
        "Uses the downloaded JSON files to update the database, "
        "including creating cards, set and rarities\n"
        "Use the update_rulings command to update rulings"
    )

    def __init__(self, stdout=None, stderr=None, no_color=False):
        super().__init__(stdout=stdout, stderr=stderr, no_color=no_color)
        self.existing_scryfall_oracle_ids: typing.Set[str] = set()
        self.existing_card_faces: typing.Set[Tuple[str, str]] = set()

        self.cards_parsed: typing.Set[str] = set()
        self.card_faces_parsed: typing.Set[Tuple[str, str]] = set()

        self.force_update = False
        self.start_time = None

    def add_arguments(self, parser):
        parser.add_argument(
            "--set",
            dest="set_codes",
            nargs="*",
            help="Update only the given list of sets",
        )

    def handle(self, *args, **options):
        self.start_time = time.time()
        with transaction.atomic():
            UpdateBlock.objects.all().delete()
            UpdateSet.objects.all().delete()
            UpdateCard.objects.all().delete()
            UpdateCardFace.objects.all().delete()
            UpdateCardRuling.objects.all().delete()

            logger.info("Getting existing data")
            for card in Card.objects.prefetch_related("faces").all():
                self.existing_scryfall_oracle_ids.add(card.scryfall_oracle_id)
                for face in card.faces.all():
                    self.existing_card_faces.add((card.scryfall_oracle_id, face.side))

            for set_data in get_all_set_data(options.get("set_codes")):
                logger.info("Parsing set %s (%s)", set_data["code"], set_data["name"])
                staged_set, staged_token_set = self.parse_set_data(set_data)
                self.process_set_cards(set_data, staged_set, staged_token_set)

    def parse_set_data(self, set_data: dict) -> Tuple[StagedSet, Optional[StagedSet]]:
        """
        Parses a set dict and checks for updates/creates/deletes to be done
        :param set_data: The MTGJSON set dict
        """
        sets = [StagedSet(set_data, for_token=False)]
        # If the set has tokens, and isn't a dedicated token set, then create a separate set just
        # for the tokens of that set
        if set_data.get("tokens") and set_data.get("type") != "token":
            sets.append(StagedSet(set_data, for_token=True))

        for staged_set in sets:
            if Set.objects.filter(code=staged_set.code).exists():
                existing_set = Set.objects.get(code=staged_set.code)
                set_differences = staged_set.compare_with_set(existing_set)
                if set_differences:
                    UpdateSet.objects.create(
                        update_mode=UpdateMode.UPDATE,
                        set_code=staged_set.code,
                        field_data=set_differences,
                    )

            elif not UpdateSet.objects.filter(set_code=staged_set.code).exists():
                UpdateSet.objects.create(
                    update_mode=UpdateMode.CREATE,
                    set_code=staged_set.code,
                    field_data=staging_object_to_dict(
                        staged_set, fields_to_ignore={"scryfall_oracle_ids"}
                    ),
                )

            if (
                staged_set.block
                and not Block.objects.filter(name=staged_set.block).exists()
            ):
                try:
                    existing_block_update = UpdateBlock.objects.get(
                        name=staged_set.block
                    )
                    if existing_block_update.release_date > staged_set.release_date:
                        existing_block_update.release_date = staged_set.release_date
                        existing_block_update.save()
                except UpdateBlock.DoesNotExist:
                    UpdateBlock.objects.create(
                        update_mode=UpdateMode.CREATE,
                        name=staged_set.block,
                        release_date=staged_set.release_date,
                    )

        return sets[0], sets[1] if len(sets) > 1 else None

    def process_set_cards(
        self,
        set_data: dict,
        staged_set: StagedSet,
        staged_token_set: Optional[StagedSet] = None,
    ) -> None:
        """
        Processes the cards within a set dictionary
        :param set_data:  The MTGJSON set dictionary
        """

        existing_cards = {
            card.scryfall_oracle_id: card
            # for card in Card.objects.filter(printings__set__code=staged_set.code)
            for card in Card.objects.filter(
                scryfall_oracle_id__in=staged_set.scryfall_oracle_ids
            )
        }

        for card_data in set_data.get("cards", []):
            # staged_card = StagedCard(card_data, is_token=False)
            staged_card = self.process_card(
                card_data, is_token=False, existing_cards=existing_cards
            )

        for card_data in set_data.get("tokens", []):
            staged_card = self.process_card(
                card_data, is_token=True, existing_cards=existing_cards
            )

            # staged_card = self.process_card(card_data, False)
            # _, printlangs = self.process_card_printing(
            #     staged_card, staged_set, card_data, is_token=False
            # )

            # for printlang in printlangs:
            #     if printlang.is_new:
            #         new_printlangs.append(printlang)

        # for card_data in set_data.get("tokens", []):
        #     # Double-faced tokens can't be handled with the current way the database is set up
        #     # example, there could exist a Knight/Saproling as well as a Saproling/Elemental
        #     # They could be connected at the printing level, but they can't be connected at the Card
        #     # level or the Knight and the Elemental would also be linked together
        #     if card_data["layout"] == "token" and card_data.get("side", "") == "b":
        #         continue
        #     staged_card = self.process_card(card_data, is_token=True)
        #     _, printlangs = self.process_card_printing(
        #         staged_card, staged_token_set or staged_set, card_data, is_token=True
        #     )
        #     for printlang in printlangs:
        #         if printlang.is_new:
        #             new_printlangs.append(printlang)
        # self.process_physical_cards(new_printlangs)

    def process_card(
        self, card_data: dict, is_token: bool, existing_cards: Dict[str, Card]
    ) -> StagedCard:
        """
        Parses the given card data dict and returns a new or existing StagedCard
        :param card_data: THe MTG JSON card data dict
        :param is_token: True if this card is a token, otherwise False
        (tokens include emblems, World Championship Bios, checklist cards, etc.)
        :return: A StagedCard that represents the json card
        If the card has already been parsed, then the existing StagedCard will be returned
        """

        staged_card = StagedCard(card_data, is_token=is_token)
        if staged_card.scryfall_oracle_id not in self.cards_parsed:
            self.cards_parsed.add(staged_card.scryfall_oracle_id)

            if staged_card.scryfall_oracle_id in existing_cards:
                differences = staged_card.compare_with_card(
                    existing_cards[staged_card.scryfall_oracle_id]
                )
                if differences:
                    UpdateCard.objects.create(
                        update_mode=UpdateMode.UPDATE,
                        scryfall_oracle_id=staged_card.scryfall_oracle_id,
                        name=staged_card.name,
                        field_data=differences,
                    )
            else:
                UpdateCard.objects.create(
                    update_mode=UpdateMode.CREATE,
                    scryfall_oracle_id=staged_card.scryfall_oracle_id,
                    name=staged_card.name,
                    field_data=staging_object_to_dict(
                        staged_card,
                        {"has_other_names", "legalities", "other_names", "rulings"},
                    ),
                )

        staged_card_face = StagedCardFace(card_data)
        face_tuple = (staged_card_face.scryfall_oracle_id, staged_card_face.side)
        if face_tuple not in self.card_faces_parsed:
            self.card_faces_parsed.add(face_tuple)
            try:
                existing_face = CardFace.objects.get(
                    card__scryfall_oracle_id=staged_card_face.scryfall_oracle_id,
                    side=staged_card_face.side,
                )
                face_differences = staged_card_face.get_card_face_differences(
                    existing_face
                )
                if face_differences:
                    UpdateCardFace.objects.create(
                        update_mode=UpdateMode.UPDATE,
                        scryfall_oracle_id=staged_card.scryfall_oracle_id,
                        name=staged_card.name,
                        face_name=staged_card_face.name,
                        side=staged_card_face.side,
                        field_data=face_differences,
                    )
            except CardFace.DoesNotExist:
                UpdateCardFace.objects.create(
                    update_mode=UpdateMode.CREATE,
                    scryfall_oracle_id=staged_card.scryfall_oracle_id,
                    name=staged_card.name,
                    face_name=staged_card_face.name,
                    side=staged_card_face.side,
                    field_data=staging_object_to_dict(
                        staged_card_face, fields_to_ignore={"generic_mana_count"}
                    ),
                )

        self.process_card_rulings(staged_card)
        # self.process_card_legalities(staged_card)
        # self.cards_parsed.add(staged_card.name)
        return staged_card

    def process_card_rulings(self, staged_card: StagedCard) -> None:
        """
        Finds CardRulings of the given StagedCard to create or delete
        :param staged_card: The StagedCard to find rulings for
        """
        if UpdateCardRuling.objects.filter(
            scryfall_oracle_id=staged_card.scryfall_oracle_id
        ).exists():
            return

        existing_rulings: List[CardRuling] = list(
            CardRuling.objects.filter(
                card__scryfall_oracle_id=staged_card.scryfall_oracle_id
            )
        )
        for ruling in staged_card.rulings:
            if not any(
                True
                for existing_ruling in existing_rulings
                if existing_ruling.text == ruling["text"]
            ):
                UpdateCardRuling.objects.create(
                    update_mode=UpdateMode.CREATE,
                    card_name=staged_card.name,
                    scryfall_oracle_id=staged_card.scryfall_oracle_id,
                    ruling_date=ruling["date"],
                    ruling_text=ruling["text"],
                )

        # For every existing ruling, it if isn't contained in the list of rulings,
        # then mark it for deletion
        for existing_ruling in existing_rulings:
            if not any(
                True
                for ruling in staged_card.rulings
                if ruling["text"] == existing_ruling.text
            ):
                UpdateCardRuling.objects.create(
                    update_mode=UpdateMode.DELETE,
                    card_name=staged_card.name,
                    scryfall_oracle_id=staged_card.scryfall_oracle_id,
                    ruling_date=existing_ruling.date,
                    ruling_text=existing_ruling.text,
                )

    def process_card_printing(
        self,
        staged_card: StagedCard,
        staged_set: StagedSet,
        card_data: dict,
        is_token: bool,
    ) -> Tuple[StagedCardPrinting, List[StagedCardPrintingLanguage]]:
        """
        Process a Card printed in a given set,
         returning the printings and printined languages that were found
        :param staged_card: The already known StagedCard
        :param staged_set: The staged set data
        :param card_data: The data of the card
        :param is_token: Whether the card is a token or not
        :return: A tuple containing the StagedCardPrinting and a list of StagedCardPrintingLanguages
        """
        staged_card_printing = StagedCardPrinting(
            staged_card.name, card_data, staged_set, for_token=is_token
        )
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
        foreign_data: Dict[str, Any],
        card_data: Dict[str, Any],
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
    ) -> Dict[str, Dict[str, Any]]:
        """
       Gets the differences between an existing printed language and one from the json

       Most of the time there won't be any differences, but this will be useful for adding in new
       fields that didn't exist before
       :param existing_printlang: The existing CardPrintingLanguage object
       :param staged_printlang: The json StagedCardPrintingLanguage object
       :return: The dict of differences between the two objects
       """
        result = self.get_object_differences(
            existing_printlang,
            staged_printlang,
            {"id", "language_id", "card_printing_id"},
        )
        return result

    def write_to_file(self) -> None:
        """
        WRites all lists of changes out to their respective files
        """
        self.write_object_to_json(
            _paths.BLOCKS_TO_CREATE_PATH,
            {
                block_name: staging_object_to_dict(staged_block, set())
                for block_name, staged_block in self.blocks_to_create.items()
            },
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
