"""
Module for the apply_import command
"""
import logging
import math
from typing import Any

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
)


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
                not self.create_new_blocks()
                or not self.create_new_sets()
                or not self.update_sets()
                or not self.create_new_cards()
                or not self.update_cards()
                or not self.update_card_faces()
                or not self.update_card_rulings()
                or not self.update_card_legalities()
                or not self.update_card_printings()
            ):
                raise Exception("Change application aborted")

    def create_new_blocks(self) -> bool:
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

    def create_new_sets(self) -> bool:
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

            set_obj.full_clean()
            set_obj.save()

        for set_to_create in UpdateSet.objects.filter(update_mode=UpdateMode.CREATE):
            parent_set_code = set_to_create.field_data.get("parent_set_code")
            if parent_set_code:
                set_obj = Set.objects.get(code=set_to_create.set_code)
                set_obj.parent_set = Set.objects.get(code=parent_set_code)
                set_obj.full_clean()
                set_obj.save()

        return True

    def update_sets(self) -> bool:
        """
        Updates Sets that have changed
        returns: True if there were no errors, otherwise False
        """
        self.logger.info("Updating sets")
        for set_to_update in UpdateSet.objects.filter(update_mode=UpdateMode.UPDATE):
            pass
        # TODO
        return True

    def create_new_cards(self) -> bool:
        self.logger.info("Creating cards")

        for card_to_create in UpdateCard.objects.filter(update_mode=UpdateMode.CREATE):

            card = Card(
                scryfall_oracle_id=card_to_create.scryfall_oracle_id,
                name=card_to_create.name,
            )
            for field, value in card_to_create.field_data.items():
                if hasattr(card, field):
                    setattr(card, field, value)
                elif field in ("generic_mana_count",):
                    continue
                else:
                    raise NotImplementedError(
                        f"Cannot set unrecognised field Card.{field}"
                    )
            card.full_clean()
            card.save()

        return True

    def update_cards(self) -> bool:
        """
                Updates existing Cards with any changes
                returns: True if there were no errors, otherwise False
                """
        self.logger.info("Updating cards")
        for card_to_update in UpdateCard.objects.filter(
            update_mode=UpdateMode.UPDATE
        ).all():
            try:
                card = Card.objects.get(
                    scryfall_oracle_id=card_to_update.scryfall_oracle_id
                )
            except Card.DoesNotExist:
                self.logger.error("Could not find card %s", card_to_update)
                raise

            for field, change in card_to_update.field_data.items():
                if hasattr(card, field):
                    setattr(card, field, change["to"])
                else:
                    raise NotImplementedError(
                        f"Cannot update unrecognised field Card.{field}"
                    )
            card.full_clean()
            card.save()
        return True

    def update_card_faces(self) -> bool:
        self.logger.info("Creating card faces")

        for card_face_update in UpdateCardFace.objects.filter():
            try:
                card = Card.objects.get(
                    scryfall_oracle_id=card_face_update.scryfall_oracle_id
                )
            except Card.DoesNotExist:
                self.logger.error(
                    f"Cannot find Card {card_face_update.scryfall_oracle_id} for face {card_face_update}"
                )
                raise

            if card_face_update.update_mode == UpdateMode.CREATE:
                card_face = CardFace(card=card, side=card_face_update.side)
            elif card_face_update.update_mode == UpdateMode.UPDATE:
                card_face = CardFace.objects.get(card=card, side=card_face_update.side)
            else:
                raise Exception()  # TODO: Proper exception class

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
                card_face.full_clean()
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

        # old_types = list(getattr(card_face, type_key).values_list('name', flat=True))
        for old_type in getattr(card_face, type_key).all():
            if old_type.name not in new_types:
                getattr(card_face, type_key).remove(old_type)
        # for card_face_type in getattr(card_face, type_key).all():
        # if card_face_type.name not in new_types:
        # card_face_type.delete()

        for type_str in new_types:
            try:
                type_obj = type_model.objects.get(name=type_str)
            except type_model.DoesNotExist:
                type_obj = type_model.objects.create(name=type_str)
                self.logger.warning("Created %s %s", type_key, type_str)
            getattr(card_face, type_key).add(type_obj)

    def update_card_rulings(self) -> bool:
        for update_card_ruling in UpdateCardRuling.objects.all():
            if update_card_ruling.update_mode == UpdateMode.DELETE:
                CardRuling.objects.filter(
                    scryfall_oracle_id=update_card_ruling.scryfall_oracle_id,
                    text=update_card_ruling.ruling_text,
                ).delete()
            elif update_card_ruling.update_mode == UpdateMode.CREATE:
                CardRuling.objects.create(
                    card=Card.objects.get(
                        scryfall_oracle_id=update_card_ruling.scryfall_oracle_id
                    ),
                    text=update_card_ruling.ruling_text,
                    date=update_card_ruling.ruling_date,
                )
            else:
                raise Exception(
                    f"Invalid operation {update_card_ruling.update_mode} for card ruling update: {update_card_ruling}"
                )
        return True

    def update_card_legalities(self) -> bool:
        self.logger.info("Updating card legalities")
        for update_card_legality in UpdateCardLegality.objects.all():
            try:
                if update_card_legality.update_mode == UpdateMode.DELETE:
                    deletions, _ = CardLegality.objects.filter(
                        card__scryfall_oracle_id=update_card_legality.scryfall_oracle_id,
                        format__code=update_card_legality.format_name,
                    ).delete()

                    if deletions == 0:
                        raise Exception(f"No legality found for {update_card_legality}")
                elif update_card_legality.update_mode == UpdateMode.CREATE:
                    CardLegality.objects.create(
                        card=Card.objects.get(
                            scryfall_oracle_id=update_card_legality.scryfall_oracle_id
                        ),
                        format=Format.objects.get(
                            code=update_card_legality.format_name
                        ),
                        restriction=update_card_legality.restriction,
                    )
                elif update_card_legality.update_mode == UpdateMode.UPDATE:
                    existing_legality = CardLegality.objects.get(
                        card__scryfall_oracle_id=update_card_legality.scryfall_oracle_id,
                        format__code=update_card_legality.format_name,
                    )
                    existing_legality.restriction = update_card_legality.restriction
                    existing_legality.full_clean()
                    existing_legality.save()
            except Format.DoesNotExist:
                self.logger.error(
                    "Could not find format %s for %s",
                    update_card_legality.format_name,
                    update_card_legality,
                )
                raise

        return True

    def update_card_printings(self) -> bool:
        for update_card_printing in UpdateCardPrinting.objects.all():
            if update_card_printing.update_mode == UpdateMode.CREATE:
                printing = CardPrinting(
                    card=Card.objects.get(
                        scryfall_oracle_id=update_card_printing.card_scryfall_oracle_id
                    ),
                    scryfall_id=update_card_printing.scryfall_id,
                    set=Set.objects.get(code=update_card_printing.set_code),
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
                    printing.rarity = Rarity.objects.get(name__iexact=value)
                elif hasattr(printing, field):
                    setattr(printing, field, value)
                else:
                    raise NotImplementedError(
                        f"Cannot set unrecognised field CardPrinting.{field}"
                    )
            printing.full_clean()
            printing.save()
        return True
