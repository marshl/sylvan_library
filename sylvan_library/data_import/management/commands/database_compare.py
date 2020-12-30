"""
Module for the update_database command
"""
import logging
import time
import typing
from typing import List, Optional, Dict, Tuple, Any

from django.core.management.base import BaseCommand
from django.db import transaction, models

from cards.models import Block, Card, CardPrinting, Set, CardFace, CardLocalisation
from data_import.management.commands import get_all_set_data
from data_import.models import (
    UpdateSet,
    UpdateCard,
    UpdateBlock,
    UpdateMode,
    UpdateCardFace,
    UpdateCardRuling,
    UpdateCardLegality,
    UpdateCardPrinting,
    UpdateCardFacePrinting,
    UpdateCardLocalisation,
    UpdateCardFaceLocalisation,
)
from data_import.staging import (
    StagedCard,
    StagedSet,
    StagedCardLocalisation,
    StagedCardPrinting,
    StagedCardFace,
    StagedCardFacePrinting,
    StagedCardFaceLocalisation,
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

    def __init__(self, stdout=None, stderr=None, no_color=False):
        super().__init__(stdout=stdout, stderr=stderr, no_color=no_color)

        self.cards_parsed: typing.Set[str] = set()
        self.card_faces_parsed: typing.Set[Tuple[str, str]] = set()
        self.card_printings_parsed: typing.Set[str] = set()
        self.card_face_printings_parsed: typing.Set[str] = set()
        self.card_localisations_parsed: typing.Set[Tuple[str, str]] = set()

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
            UpdateCardLegality.objects.all().delete()
            UpdateCardPrinting.objects.all().delete()
            UpdateCardFacePrinting.objects.all().delete()
            UpdateCardLocalisation.objects.all().delete()
            UpdateCardFaceLocalisation.objects.all().delete()

            for set_data in get_all_set_data(options.get("set_codes")):
                logger.info("Parsing set %s (%s)", set_data["code"], set_data["name"])
                staged_set, staged_token_set = self.parse_set_data(set_data)
                self.process_set_cards(set_data, staged_set, staged_token_set)
        self.log_stats()

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
                    field_data=staged_set.get_field_data(),
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
            for card in Card.objects.filter(
                scryfall_oracle_id__in=staged_set.scryfall_oracle_ids
            )
            .prefetch_related(
                "faces__subtypes",
                "faces__supertypes",
                "faces__types",
                "rulings",
                "legalities__format",
            )
            .all()
        }
        existing_printings = {
            printing.scryfall_id: printing
            for printing in CardPrinting.objects.filter(
                card__scryfall_oracle_id__in=staged_set.scryfall_oracle_ids
            )
            .prefetch_related(
                "face_printings__frame_effects",
                "face_printings__card_face",
                "rarity",
                "localisations__language",
                "localisations__localised_faces__card_printing_face",
            )
            .all()
        }

        for card_data in set_data.get("cards", []):
            staged_card, staged_card_face = self.process_card(
                card_data, is_token=False, existing_cards=existing_cards
            )

            staged_printing, staged_face_printing = self.process_card_printing(
                staged_card=staged_card,
                staged_card_face=staged_card_face,
                staged_set=staged_set,
                card_data=card_data,
                existing_printings=existing_printings,
            )

            self.process_card_localisations(
                card_data=card_data,
                staged_card_printing=staged_printing,
                staged_face_printing=staged_face_printing,
                existing_printings=existing_printings,
            )

        for card_data in set_data.get("tokens", []):
            staged_card, staged_card_face = self.process_card(
                card_data, is_token=True, existing_cards=existing_cards
            )

            staged_printing, staged_face_printing = self.process_card_printing(
                staged_card=staged_card,
                staged_card_face=staged_card_face,
                # For tokens, prefer the corresponding token set.
                # However some sets are themselves token sets, so in those cases, use the actual set
                staged_set=staged_token_set or staged_set,
                card_data=card_data,
                existing_printings=existing_printings,
            )

            self.process_card_localisations(
                card_data=card_data,
                staged_card_printing=staged_printing,
                staged_face_printing=staged_face_printing,
                existing_printings=existing_printings,
            )

    def process_card(
        self, card_data: dict, is_token: bool, existing_cards: Dict[str, Card]
    ) -> Tuple[StagedCard, StagedCardFace]:
        """
        Parses the given card data dict and returns a new or existing StagedCard
        :param card_data: THe MTG JSON card data dict
        :param is_token: True if this card is a token, otherwise False
        (tokens include emblems, World Championship Bios, checklist cards, etc.)
        :return: A StagedCard that represents the json card
        If the card has already been parsed, then the existing StagedCard will be returned
        """

        staged_card = StagedCard(card_data, is_token=is_token)
        existing_card = existing_cards.get(staged_card.scryfall_oracle_id)

        if staged_card.scryfall_oracle_id not in self.cards_parsed:
            self.cards_parsed.add(staged_card.scryfall_oracle_id)

            self.process_card_rulings(staged_card, existing_card=existing_card)
            self.process_card_legalities(staged_card, existing_card=existing_card)

            if existing_card:
                differences = staged_card.compare_with_card(existing_card)
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
                    field_data=staged_card.get_field_data(),
                )

        staged_card_face = StagedCardFace(card_data)
        face_tuple = (staged_card_face.scryfall_oracle_id, staged_card_face.side)
        card_face = (
            next(
                face
                for face in existing_card.faces.all()
                if face.side == staged_card_face.side
            )
            if existing_card
            else None
        )

        if face_tuple not in self.card_faces_parsed:
            self.card_faces_parsed.add(face_tuple)
            if card_face:
                face_differences = staged_card_face.get_card_face_differences(card_face)
                if face_differences:
                    UpdateCardFace.objects.create(
                        update_mode=UpdateMode.UPDATE,
                        scryfall_oracle_id=staged_card.scryfall_oracle_id,
                        name=staged_card.name,
                        face_name=staged_card_face.name,
                        side=staged_card_face.side,
                        field_data=face_differences,
                    )
            else:
                UpdateCardFace.objects.create(
                    update_mode=UpdateMode.CREATE,
                    scryfall_oracle_id=staged_card.scryfall_oracle_id,
                    name=staged_card.name,
                    face_name=staged_card_face.name,
                    side=staged_card_face.side,
                    field_data=staged_card_face.get_field_data(),
                )

        return staged_card, staged_card_face

    def process_card_rulings(
        self, staged_card: StagedCard, existing_card: Optional[Card] = None
    ) -> None:
        """
        Finds CardRulings of the given StagedCard to create or delete
        :param staged_card: The StagedCard to find rulings for
        """
        # Use prefetch rulings to save performance
        existing_rulings = list(existing_card.rulings.all()) if existing_card else []

        for ruling in staged_card.rulings:
            if not any(
                True
                for existing_ruling in existing_rulings
                if existing_ruling.text == ruling["text"]
            ):
                create_ruling = UpdateCardRuling(
                    update_mode=UpdateMode.CREATE,
                    card_name=staged_card.name,
                    scryfall_oracle_id=staged_card.scryfall_oracle_id,
                    ruling_date=ruling["date"],
                    ruling_text=ruling["text"],
                )
                create_ruling.save()

        # For every existing ruling, it if isn't contained in the list of rulings,
        # then mark it for deletion
        for existing_ruling in existing_rulings:
            if not any(
                True
                for ruling in staged_card.rulings
                if ruling["text"] == existing_ruling.text
            ):
                delete_ruling = UpdateCardRuling(
                    update_mode=UpdateMode.DELETE,
                    card_name=staged_card.name,
                    scryfall_oracle_id=staged_card.scryfall_oracle_id,
                    ruling_date=existing_ruling.date,
                    ruling_text=existing_ruling.text,
                )
                delete_ruling.save()

    def process_card_legalities(
        self, staged_card: StagedCard, existing_card: Optional[Card] = None
    ) -> None:
        """
        Find CardLegalities for a card to update, create or delete
        :param staged_card: The StagedCard to find legalities for
        """
        # Use prefetched legalities to improve performance
        existing_legalities = (
            list(existing_card.legalities.all()) if existing_card else []
        )

        for format_str, restriction in staged_card.legalities.items():
            if not any(
                True
                for existing_legality in existing_legalities
                if existing_legality.format.code == format_str
            ):
                create_legality = UpdateCardLegality(
                    update_mode=UpdateMode.CREATE,
                    card_name=staged_card.name,
                    scryfall_oracle_id=staged_card.scryfall_oracle_id,
                    format_name=format_str,
                    restriction=restriction,
                )
                create_legality.save()

        for old_legality in existing_legalities:
            if old_legality.format.code not in staged_card.legalities:
                delete_legality = UpdateCardLegality(
                    update_mode=UpdateMode.DELETE,
                    card_name=staged_card.name,
                    scryfall_oracle_id=staged_card.scryfall_oracle_id,
                    format_name=old_legality.format.code,
                    restriction=old_legality.restriction,
                )
                delete_legality.save()

            # Legalities to update
            elif (
                staged_card.legalities[old_legality.format.code]
                != old_legality.restriction
            ):
                update_legality = UpdateCardLegality(
                    update_mode=UpdateMode.UPDATE,
                    card_name=staged_card.name,
                    scryfall_oracle_id=staged_card.scryfall_oracle_id,
                    format_name=old_legality.format.code,
                    restriction=staged_card.legalities[old_legality.format.name],
                )
                update_legality.save()

    def process_card_printing(
        self,
        staged_card: StagedCard,
        staged_card_face: StagedCardFace,
        staged_set: StagedSet,
        card_data: dict,
        existing_printings: Dict[str, CardPrinting],
    ) -> Tuple[StagedCardPrinting, StagedCardFacePrinting]:
        """
        Process a Card printed in a given set,
         returning the printings and printed languages that were found
        :param staged_card: The already known StagedCard
        :param staged_set: The staged set data
        :param card_data: The data of the card
        :return: A tuple containing the StagedCardPrinting and a list of StagedCardLocalisations
        """
        staged_card_printing = StagedCardPrinting(card_data, staged_set)
        existing_printing = existing_printings.get(staged_card_printing.scryfall_id)
        if staged_card_printing.scryfall_id not in self.card_printings_parsed:
            self.card_printings_parsed.add(staged_card_printing.scryfall_id)
            if not existing_printing:
                create_printing = UpdateCardPrinting(
                    update_mode=UpdateMode.CREATE,
                    card_scryfall_oracle_id=staged_card.scryfall_oracle_id,
                    card_name=staged_card.name,
                    scryfall_id=staged_card_printing.scryfall_id,
                    set_code=staged_set.code,
                    field_data=staged_card_printing.get_field_data(),
                )
                create_printing.save()
            else:
                differences = staged_card_printing.compare_with_existing_card_printing(
                    existing_printing
                )
                if differences:
                    UpdateCardPrinting.objects.create(
                        update_mode=UpdateMode.UPDATE,
                        card_scryfall_oracle_id=staged_card.scryfall_oracle_id,
                        card_name=staged_card.name,
                        scryfall_id=staged_card_printing.scryfall_id,
                        set_code=staged_set.code,
                        field_data=differences,
                    )
        staged_face_printing = StagedCardFacePrinting(card_data)
        if staged_face_printing.uuid not in self.card_face_printings_parsed:
            self.card_face_printings_parsed.add(staged_face_printing.uuid)
            existing_face_printing = (
                next(
                    (
                        face_printing
                        for face_printing in existing_printing.face_printings.all()
                        if face_printing.card_face.side == staged_card_face.side
                    ),
                    None,
                )
                if existing_printing
                else None
            )
            if existing_face_printing:
                differences = staged_face_printing.compare_with_existing_face_printing(
                    existing_face_printing
                )
                if differences:
                    UpdateCardFacePrinting.objects.create(
                        update_mode=UpdateMode.UPDATE,
                        scryfall_id=staged_card_printing.scryfall_id,
                        scryfall_oracle_id=staged_card.scryfall_oracle_id,
                        card_name=staged_card.name,
                        card_face_name=staged_card_face.name,
                        printing_uuid=staged_face_printing.uuid,
                        side=staged_card_face.side,
                        field_data=differences,
                    )
            else:
                UpdateCardFacePrinting.objects.create(
                    update_mode=UpdateMode.CREATE,
                    scryfall_id=staged_card_printing.scryfall_id,
                    scryfall_oracle_id=staged_card.scryfall_oracle_id,
                    card_name=staged_card.name,
                    card_face_name=staged_card_face.name,
                    printing_uuid=staged_face_printing.uuid,
                    side=staged_card_face.side,
                    field_data=staged_face_printing.get_field_data(),
                )

        return staged_card_printing, staged_face_printing

    def process_card_localisations(
        self,
        card_data: dict,
        staged_card_printing: StagedCardPrinting,
        staged_face_printing: StagedCardFacePrinting,
        existing_printings: Dict[str, CardPrinting],
    ):
        existing_printing: Optional[CardPrinting] = existing_printings.get(
            staged_card_printing.scryfall_id
        )

        foreign_data_list = card_data.get("foreignData", [])
        english_data = {
            "language": "English",
            "name": card_data.get("name"),
            "text": card_data.get("text"),
            "type": card_data.get("type"),
        }
        if "faceName" in card_data:
            english_data["faceName"] = card_data["faceName"]
        if "multiverseId" in card_data["identifiers"]:
            english_data["multiverseId"] = card_data["identifiers"]["multiverseId"]
        foreign_data_list.append(english_data)

        for foreign_data in foreign_data_list:
            staged_localisation = StagedCardLocalisation(
                staged_card_printing, foreign_data
            )
            tuple_key = (
                staged_card_printing.scryfall_id,
                staged_localisation.language_name,
            )
            if tuple_key in self.card_localisations_parsed:
                continue
            self.card_localisations_parsed.add(tuple_key)

            existing_localisation: Optional[CardLocalisation] = next(
                (
                    localisation
                    for localisation in existing_printing.localisations.all()
                    if localisation.language.name == staged_localisation.language_name
                ),
                None,
            )

            if not existing_localisation:
                UpdateCardLocalisation.objects.create(
                    update_mode=UpdateMode.CREATE,
                    language_code=staged_localisation.language_name,
                    printing_scryfall_id=staged_card_printing.scryfall_id,
                    card_name=staged_localisation.card_name,
                    field_data=staged_localisation.get_field_data(),
                )
            else:
                differences = staged_localisation.compare_with_existing_localisation(
                    existing_localisation
                )
                if differences:
                    UpdateCardLocalisation.objects.create(
                        update_mode=UpdateMode.UPDATE,
                        language_code=staged_localisation.language_name,
                        printing_scryfall_id=staged_card_printing.scryfall_id,
                        card_name=staged_localisation.card_name,
                        field_data=differences,
                    )

            existing_localised_face = (
                None
                if not existing_localisation
                else next(
                    (
                        face
                        for face in existing_localisation.localised_faces.all()
                        if face.card_printing_face.uuid == staged_face_printing.uuid
                    ),
                    None,
                )
            )
            staged_localised_face = StagedCardFaceLocalisation(
                staged_card_printing, staged_face_printing, foreign_data
            )

            if not existing_localised_face:
                UpdateCardFaceLocalisation.objects.create(
                    update_mode=UpdateMode.CREATE,
                    language_code=staged_localised_face.language_name,
                    printing_scryfall_id=staged_card_printing.scryfall_id,
                    face_name=staged_localised_face.face_name,
                    face_printing_uuid=staged_localised_face.face_printing_uuid,
                    field_data=staged_localised_face.get_field_data(),
                )
            else:
                differences = staged_localised_face.compare_with_existing_face_localisation(
                    existing_localised_face
                )
                if differences:
                    UpdateCardFaceLocalisation.objects.create(
                        update_mode=UpdateMode.UPDATE,
                        language_code=staged_localised_face.language_name,
                        printing_scryfall_id=staged_card_printing.scryfall_id,
                        face_name=staged_localised_face.face_name,
                        face_printing_uuid=staged_localised_face.face_printing_uuid,
                        field_data=differences,
                    )

    def log_single_stat(self, model_name: str, update_type: typing.Type[models.Model]):
        create_count = update_type.objects.filter(update_mode=UpdateMode.CREATE).count()
        if create_count > 0:
            logger.info("%s %s objects to create", create_count, model_name)
        update_count = update_type.objects.filter(update_mode=UpdateMode.UPDATE).count()
        if update_count > 0:
            logger.info("%s %s objects to update", update_count, model_name)

    def log_stats(self) -> None:
        """
        Logs out the number sof objects to delete/create/update
        """
        self.log_single_stat("block", UpdateBlock)
        self.log_single_stat("set", UpdateSet)
        self.log_single_stat("card", UpdateCard)
        self.log_single_stat("card face", UpdateCardFace)
        self.log_single_stat("card printing", UpdateCardPrinting)
        self.log_single_stat("card printing face", UpdateCardFacePrinting)
        self.log_single_stat("card localisation", UpdateCardLocalisation)
        self.log_single_stat("legality", UpdateCardLegality)
        self.log_single_stat("ruling", UpdateCardRuling)
        logger.info("Completed in %ss", time.time() - self.start_time)
