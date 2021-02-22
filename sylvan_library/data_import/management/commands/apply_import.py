"""
Module for the apply_import command
"""
import logging
import math
from typing import Any, Dict, Optional

import typing
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandParser
from django.db import transaction, models

from cards.models import (
    Block,
    Colour,
    Rarity,
    Set,
    Card,
    CardFace,
    CardRuling,
    CardLegality,
    Format,
    CardType,
    CardSubtype,
    CardSupertype,
    CardPrinting,
    CardFacePrinting,
    FrameEffect,
    CardLocalisation,
    Language,
    CardFaceLocalisation,
)
from data_import.models import (
    UpdateBlock,
    UpdateSet,
    UpdateMode,
    UpdateCard,
    UpdateCardFace,
    UpdateCardRuling,
    UpdateCardLegality,
    UpdateCardPrinting,
    UpdateCardFacePrinting,
    UpdateCardLocalisation,
    UpdateCardFaceLocalisation,
)


class Command(BaseCommand):
    """
    The command for updating hte database
    """

    help = (
        "Uses the downloaded JSON files to update the database, "
        "including creating cards, set and rarities\n"
    )

    cached_languages: Optional[Dict[str, Language]] = None
    scryfall_oracle_id_to_card_id: Dict[str, int] = None
    scryfall_id_to_card_printing_id: Dict[str, int] = None

    def __init__(self, stdout=None, stderr=None, no_color=False):
        self.logger = logging.getLogger("django")
        super().__init__(stdout=stdout, stderr=stderr, no_color=no_color)

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument(
            "--no-transaction",
            action="store_true",
            dest="no_transaction",
            default=False,
            help="Update the database without a transaction (unsafe)",
        )

    def handle(self, *args: Any, **options: Any):

        with transaction.atomic():
            # pylint: disable=too-many-boolean-expressions
            if (
                not self.update_blocks()
                or not self.update_sets()
                or not self.update_cards()
                or not self.update_card_faces()
                or not self.update_card_rulings()
                or not self.update_card_legalities()
                or not self.update_card_printings()
                or not self.update_card_face_printings()
                or not self.update_card_localisations()
                or not self.update_card_face_localisations()
            ):
                raise Exception("Change application aborted")

    def get_language(self, language_name: str) -> Language:
        if not self.cached_languages:
            self.cached_languages = {
                language.name: language for language in Language.objects.all()
            }
        return self.cached_languages[language_name]

    def get_card_id(self, scryfall_oracle_id: str) -> int:
        if not self.scryfall_oracle_id_to_card_id:
            self.scryfall_oracle_id_to_card_id = {
                c[1]: c[0] for c in Card.objects.values_list("id", "scryfall_oracle_id")
            }

        card_id = self.scryfall_oracle_id_to_card_id.get(scryfall_oracle_id)
        if card_id:
            return card_id
        card = Card.objects.get(scryfall_oracle_id=scryfall_oracle_id)
        self.scryfall_oracle_id_to_card_id[scryfall_oracle_id] = card.id
        return card.id

    def get_card_printing_id(self, scryfall_id: str) -> int:
        if not self.scryfall_id_to_card_printing_id:
            self.scryfall_id_to_card_printing_id = {
                c[1]: c[0]
                for c in CardPrinting.objects.values_list("id", "scryfall_id")
            }
        card_printing_id = self.scryfall_id_to_card_printing_id.get(scryfall_id)
        if card_printing_id:
            return card_printing_id

        card_printing = CardPrinting.objects.get(scryfall_id=scryfall_id)
        self.scryfall_id_to_card_printing_id[scryfall_id] = card_printing.id
        return card_printing.id

    def update_blocks(self) -> bool:
        """
        Creates new Block objects
        returns: True if there were no errors, otherwise False
        """
        self.logger.info("Creating new blocks")
        for block_to_create in UpdateBlock.objects.filter(
            update_mode=UpdateMode.CREATE
        ):
            Block.objects.create(
                name=block_to_create.name, release_date=block_to_create.release_date
            )
        return True

    def update_sets(self) -> bool:
        """
        Creates new Set objects
        returns: True if there were no errors, otherwise False
        """
        self.logger.info("Creating new sets")
        for set_to_create in UpdateSet.objects.all():
            if set_to_create.update_mode == UpdateMode.CREATE:
                set_obj = Set()
                set_obj.code = set_to_create.set_code
            else:
                set_obj = Set.objects.get(code=set_to_create.set_code)

            for field, value in set_to_create.field_data.items():
                if set_to_create.update_mode == UpdateMode.UPDATE:
                    value = value.get("to")
                if field in ("parent_set_code",):
                    continue

                if field == "block":
                    if not value:
                        set_obj.block = None
                    else:
                        try:
                            set_obj.block = Block.objects.get(name=value)
                        except Block.DoesNotExist as ex:
                            raise Exception(
                                f"Cannot find block {value} for set {set_obj.code}"
                            ) from ex

                elif hasattr(set_obj, field):
                    setattr(set_obj, field, value)
                else:
                    raise NotImplementedError(
                        f"Cannot update unrecognised field Set.{field} with value {value} for {set_to_create}"
                    )

            set_obj.save()

        for set_to_create in UpdateSet.objects.filter(update_mode=UpdateMode.CREATE):
            parent_set_code = set_to_create.field_data.get("parent_set_code")
            if parent_set_code:
                set_obj = Set.objects.get(code=set_to_create.set_code)
                try:
                    set_obj.parent_set = Set.objects.get(code=parent_set_code)
                except Set.DoesNotExist:
                    self.logger.error(
                        "Cannot find parent set %s of %s",
                        parent_set_code,
                        set_to_create,
                    )
                    raise
                set_obj.save()

        return True

    def update_cards(self) -> bool:
        """
                Updates existing Cards with any changes
                returns: True if there were no errors, otherwise False
                """
        self.logger.info("Updating %s cards", UpdateCard.objects.count())
        card_to_update: UpdateCard
        for card_to_update in UpdateCard.objects.all():
            if card_to_update.update_mode == UpdateMode.CREATE:
                card = Card(
                    scryfall_oracle_id=card_to_update.scryfall_oracle_id,
                    name=card_to_update.name,
                )
            else:
                card = Card.objects.get(
                    scryfall_oracle_id=card_to_update.scryfall_oracle_id
                )

            for field, value in card_to_update.field_data.items():
                if card_to_update.update_mode == UpdateMode.UPDATE:
                    value = value["to"]

                if hasattr(card, field):
                    setattr(card, field, value)
                else:
                    raise NotImplementedError(
                        f"Cannot update unrecognised field Card.{field}"
                    )
            card.save()
        return True

    def update_card_faces(self) -> bool:
        self.logger.info("Creating %s card faces", UpdateCardFace.objects.count())

        for card_face_update in UpdateCardFace.objects.filter():
            if card_face_update.update_mode == UpdateMode.CREATE:
                card_face = CardFace(
                    card_id=self.get_card_id(card_face_update.scryfall_oracle_id),
                    side=card_face_update.side,
                )
            elif card_face_update.update_mode == UpdateMode.UPDATE:
                card_face = CardFace.objects.get(
                    card__scryfall_oracle_id=card_face_update.scryfall_oracle_id,
                    side=card_face_update.side,
                )
            else:
                raise ValueError()

            for field, value in card_face_update.field_data.items():
                if card_face_update.update_mode == UpdateMode.UPDATE:
                    value = value.get("to")

                if field in ("types", "subtypes", "supertypes", "scryfall_oracle_id"):
                    continue

                if not hasattr(card_face, field):
                    raise NotImplementedError(
                        f"Cannot set unrecognised field CardFace.{field}"
                    )

                if field == "num_power" and value == "∞":
                    value = math.inf
                setattr(card_face, field, value)
            try:
                card_face.save()
            except ValidationError:
                self.logger.exception("Could not {}", card_face_update)
                raise

            self.apply_card_face_types(
                card_face,
                card_face_update,
                "types",
                CardType,
                card_face_update.update_mode,
            )
            self.apply_card_face_types(
                card_face,
                card_face_update,
                "subtypes",
                CardSubtype,
                card_face_update.update_mode,
            )
            self.apply_card_face_types(
                card_face,
                card_face_update,
                "supertypes",
                CardSupertype,
                card_face_update.update_mode,
            )

        return True

    def apply_card_face_types(
        self,
        card_face: CardFace,
        card_face_to_create: UpdateCardFace,
        type_key: str,
        type_model: typing.Type[models.Model],
        update_mode: UpdateMode,
    ):
        if type_key not in card_face_to_create.field_data:
            return

        if update_mode == UpdateMode.UPDATE:
            new_types = card_face_to_create.field_data.get(type_key, {}).get("to", [])
        else:
            new_types = card_face_to_create.field_data.get(type_key, [])

        for old_type in getattr(card_face, type_key).all():
            if old_type.name not in new_types:
                getattr(card_face, type_key).remove(old_type)

        for type_str in new_types:
            try:
                type_obj = type_model.objects.get(name=type_str)
            except type_model.DoesNotExist:
                type_obj = type_model.objects.create(name=type_str)
                self.logger.warning("Created %s %s", type_key, type_str)
            getattr(card_face, type_key).add(type_obj)

    def update_card_rulings(self) -> bool:
        self.logger.info("Updating %s card rulings", UpdateCardRuling.objects.count())
        for update_card_ruling in UpdateCardRuling.objects.all():
            if update_card_ruling.update_mode == UpdateMode.DELETE:
                CardRuling.objects.filter(
                    card__scryfall_oracle_id=update_card_ruling.scryfall_oracle_id,
                    text=update_card_ruling.ruling_text,
                ).delete()
            elif update_card_ruling.update_mode == UpdateMode.CREATE:
                CardRuling.objects.create(
                    card_id=self.get_card_id(update_card_ruling.scryfall_oracle_id),
                    text=update_card_ruling.ruling_text,
                    date=update_card_ruling.ruling_date,
                )
            else:
                raise Exception(
                    f"Invalid operation {update_card_ruling.update_mode} for card ruling update: {update_card_ruling}"
                )
        return True

    def update_card_legalities(self) -> bool:
        self.logger.info(
            "Updating %s card legalities", UpdateCardLegality.objects.count()
        )
        format_map = {
            format_obj.code: format_obj for format_obj in Format.objects.all()
        }
        for update_card_legality in UpdateCardLegality.objects.all():
            if update_card_legality.format_name not in format_map:
                raise ValueError(
                    f'Could not find format "{update_card_legality.format_name}" for {update_card_legality}'
                )

            if update_card_legality.update_mode == UpdateMode.DELETE:
                deletions, _ = CardLegality.objects.filter(
                    card__scryfall_oracle_id=update_card_legality.scryfall_oracle_id,
                    format__code=update_card_legality.format_name,
                ).delete()

                if deletions == 0:
                    raise Exception(f"No legality found for {update_card_legality}")

            elif update_card_legality.update_mode == UpdateMode.CREATE:
                CardLegality.objects.create(
                    card_id=self.get_card_id(update_card_legality.scryfall_oracle_id),
                    format=format_map[update_card_legality.format_name],
                    restriction=update_card_legality.restriction,
                )
            elif update_card_legality.update_mode == UpdateMode.UPDATE:
                existing_legality = CardLegality.objects.get(
                    card__scryfall_oracle_id=update_card_legality.scryfall_oracle_id,
                    format__code=update_card_legality.format_name,
                )
                existing_legality.restriction = update_card_legality.restriction
                existing_legality.save()
        return True

    def update_card_printings(self) -> bool:
        self.logger.info(
            "Updating %s card printings", UpdateCardPrinting.objects.count()
        )
        set_map = {set_obj.code: set_obj for set_obj in Set.objects.all()}
        rarity_map = {rarity.name.lower(): rarity for rarity in Rarity.objects.all()}
        update_card_printing: UpdateCardPrinting
        for update_card_printing in UpdateCardPrinting.objects.all():
            if update_card_printing.update_mode == UpdateMode.CREATE:
                printing = CardPrinting(
                    card_id=self.get_card_id(
                        update_card_printing.card_scryfall_oracle_id
                    ),
                    scryfall_id=update_card_printing.scryfall_id,
                    set=set_map[update_card_printing.set_code],
                )
            elif update_card_printing.update_mode == UpdateMode.UPDATE:
                printing = CardPrinting.objects.get(
                    card__scryfall_oracle_id=update_card_printing.card_scryfall_oracle_id,
                    set__code=update_card_printing.set_code,
                    scryfall_id=update_card_printing.scryfall_id,
                )
            else:
                raise Exception

            for field, value in update_card_printing.field_data.items():
                if update_card_printing.update_mode == UpdateMode.UPDATE:
                    value = value["to"]

                if field in ("card_name", "set_code"):
                    continue

                if field == "rarity":
                    printing.rarity = rarity_map.get(value.lower())
                elif hasattr(printing, field):
                    setattr(printing, field, value)
                else:
                    raise NotImplementedError(
                        f"Cannot set unrecognised field CardPrinting.{field}"
                    )
            printing.save()
        return True

    def update_card_face_printings(self) -> bool:
        self.logger.info(
            "Updating %s card face printings", UpdateCardFacePrinting.objects.count()
        )
        for update_card_face_printing in UpdateCardFacePrinting.objects.all():
            if update_card_face_printing.update_mode == UpdateMode.CREATE:
                printing = CardPrinting.objects.get(
                    scryfall_id=update_card_face_printing.scryfall_id
                )
                face_printing = CardFacePrinting(
                    uuid=update_card_face_printing.printing_uuid,
                    card_printing=printing,
                    card_face=CardFace.objects.get(
                        card=printing.card, side=update_card_face_printing.side
                    ),
                )
            elif update_card_face_printing.update_mode == UpdateMode.UPDATE:
                try:
                    face_printing = CardFacePrinting.objects.get(
                        uuid=update_card_face_printing.printing_uuid
                    )
                except CardFacePrinting.DoesNotExist:
                    logging.error(
                        f"Could not find card printing %s fpr %s",
                        update_card_face_printing.printing_uuid,
                        update_card_face_printing,
                    )
                    raise ValueError(
                        f"Could not find card printing {update_card_face_printing.printing_uuid} fpr {update_card_face_printing}"
                    )
            else:
                continue

            for field, value in update_card_face_printing.field_data.items():
                if update_card_face_printing.update_mode == UpdateMode.UPDATE:
                    value = value["to"]

                if field in ("frame_effects",):
                    continue
                elif hasattr(face_printing, field):
                    setattr(face_printing, field, value)
                else:
                    raise NotImplementedError(
                        f"Cannot set unrecognised field CardFacePrinting.{field}"
                    )

            try:
                face_printing.save()
            except ValidationError:
                self.logger.error("Failed to validate %s", update_card_face_printing)
                raise

            if "frame_effects" in update_card_face_printing.field_data:
                frame_effects = update_card_face_printing.field_data["frame_effects"]
                if update_card_face_printing.update_mode == UpdateMode.UPDATE:
                    frame_effects = frame_effects["to"]
                face_printing.frame_effects.set(
                    FrameEffect.objects.filter(code__in=frame_effects)
                )

        return True

    def update_card_localisations(self) -> bool:
        self.logger.info(
            "Updating %s card localisations", UpdateCardLocalisation.objects.count()
        )

        for update_localisation in UpdateCardLocalisation.objects.all():
            if update_localisation.update_mode == UpdateMode.CREATE:
                localisation = CardLocalisation(
                    language=self.get_language(update_localisation.language_code),
                    card_printing_id=self.get_card_printing_id(
                        update_localisation.printing_scryfall_id
                    ),
                )
            elif update_localisation.update_mode == UpdateMode.UPDATE:
                localisation = CardLocalisation.objects.get(
                    language=self.get_language(update_localisation.language_code),
                    card_printing__scryfall_id=update_localisation.printing_scryfall_id,
                )
            else:
                raise Exception()

            localisation.card_name = update_localisation.card_name
            for field, value in update_localisation.field_data.items():
                if update_localisation.update_mode == UpdateMode.UPDATE:
                    value = value["to"]

                if hasattr(localisation, field):
                    setattr(localisation, field, value)
                else:
                    raise NotImplementedError(
                        f"Cannot set unrecognised field CardLocalisation.{field}"
                    )
            try:
                localisation.save()
            except ValidationError:
                self.logger.error("Failed to validate %s", update_localisation)
                raise

        return True

    def update_card_face_localisations(self):
        self.logger.info(
            "Updating %s card face localisations",
            UpdateCardFaceLocalisation.objects.count(),
        )

        for update_face_localisation in UpdateCardFaceLocalisation.objects.all():
            localisation = CardLocalisation.objects.get(
                card_printing__scryfall_id=update_face_localisation.printing_scryfall_id,
                language=self.get_language(update_face_localisation.language_code),
            )
            try:
                card_printing_face = CardFacePrinting.objects.get(
                    uuid=update_face_localisation.face_printing_uuid
                )
            except CardFacePrinting.DoesNotExist:
                logging.error(
                    "Could not find CardFacePrinting with uuid %s for %s",
                    update_face_localisation.face_printing_uuid,
                    update_face_localisation,
                )
                raise ValueError(
                    f"Could not find CardFacePrinting with uuid {update_face_localisation.face_printing_uuid} for {update_face_localisation}"
                )

            if update_face_localisation.update_mode == UpdateMode.CREATE:
                face_localisation = CardFaceLocalisation(
                    localisation=localisation, card_printing_face=card_printing_face
                )
            elif update_face_localisation.update_mode == UpdateMode.UPDATE:
                face_localisation = CardFaceLocalisation.objects.get(
                    localisation=localisation, card_printing_face=card_printing_face
                )
            else:
                raise Exception()

            face_localisation.face_name = update_face_localisation.face_name
            for field, value in update_face_localisation.field_data.items():
                if field in ("face_printing_uuid",):
                    continue

                if update_face_localisation.update_mode == UpdateMode.UPDATE:
                    value = value["to"]

                if hasattr(face_localisation, field):
                    setattr(face_localisation, field, value)
                else:
                    raise NotImplementedError(
                        f"Cannot set unrecognised field CardFaceLocalisation.{field}"
                    )
            try:
                face_localisation.save()
            except ValidationError:
                self.logger.error("Failed to validate %s", update_face_localisation)
                raise

        return True
