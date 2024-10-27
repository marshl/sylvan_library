"""
Module for the update_metadata command
"""

import json
import logging
import time

from django.core.management.base import BaseCommand
from django.db import transaction

from cards.models.card import (
    CardType,
    CardSubtype,
    CardSupertype,
    FrameEffect,
)
from cards.models.colour import Colour
from cards.models.language import Language
from cards.models.rarity import Rarity
from cards.models.sets import Format
from data_import import _paths
from data_import._paths import (
    COLOUR_JSON_PATH,
    RARITY_JSON_PATH,
    LANGUAGE_JSON_PATH,
    FORMAT_JSON_PATH,
)

logger = logging.getLogger("django")


def import_json(file_path: str) -> dict:
    """
    Imports data from a json file and returns the dict
    :param file_path: The file to read
    :return: The dict representation of the file
    """
    with open(file_path, "r", encoding="utf8") as json_file:
        return json.load(json_file)


class Command(BaseCommand):
    """
    The command for updating all metadata in the database
    (data that is stored in external files, and not in mtgjson)
    """

    help = (
        "The command for updating all metadata in the database "
        "(data that is stored in external files, and not in mtgjson)"
    )

    def __init__(self, stdout=None, stderr=None, no_color=False):
        self.update_counts = {}
        self.created_counts = {}
        self.ignored_counts = {}
        self.start_time = time.time()

        super().__init__(stdout=stdout, stderr=stderr, no_color=no_color)

    def handle(self, *args, **options):
        with transaction.atomic():
            self.update_rarities()
            self.update_colours()
            self.update_languages()
            self.update_formats()
            self.update_types()
            self.update_frame_effects()

        self.log_stats()

    def update_colours(self) -> None:
        """
        Updates all colours from file
        """
        logger.info("Updating colour list")

        for colour in import_json(COLOUR_JSON_PATH):
            colour_obj = Colour.objects.filter(symbol=colour["symbol"]).first()
            if colour_obj is not None:
                logger.info("Updating existing colour %s", colour_obj)
                self.increment_updated("Colour")
            else:
                logger.info("Creating new colour %s", colour["name"])
                colour_obj = Colour(symbol=colour["symbol"])
                self.increment_created("Colour")
            colour_obj.name = colour["name"]
            colour_obj.display_order = colour["display_order"]
            colour_obj.bit_value = colour["bit_value"]
            colour_obj.chart_colour = colour["chart_colour"]
            colour_obj.full_clean()
            colour_obj.save()

    def update_rarities(self) -> None:
        """
        Updates all rarities from file
        """
        logger.info("Updating rarity list")

        for rarity in import_json(RARITY_JSON_PATH):
            rarity_obj = Rarity.objects.filter(symbol=rarity["symbol"]).first()
            if rarity_obj is not None:
                logger.info("Updating existing rarity %s", rarity_obj.name)
                rarity_obj.name = rarity["name"]
                rarity_obj.display_order = rarity["display_order"]
                rarity_obj.full_clean()
                rarity_obj.save()
                self.increment_updated("Rarity")
            else:
                logger.info("Creating new rarity %s", rarity["name"])

                rarity_obj = Rarity(
                    symbol=rarity["symbol"],
                    name=rarity["name"],
                    display_order=rarity["display_order"],
                )
                rarity_obj.full_clean()
                rarity_obj.save()
                self.increment_created("Rarity")

        logger.info("Rarity update complete")

    def update_languages(self) -> None:
        """
        Updates all languages from file
        """
        logger.info("Updating language list")

        for lang in import_json(LANGUAGE_JSON_PATH):
            language_obj = Language.objects.filter(name=lang["name"]).first()
            if language_obj is not None:
                logger.info("Updating language: %s", lang["name"])
                self.increment_updated("Language")
            else:
                logger.info("Creating new language: %s", lang["name"])
                language_obj = Language(name=lang["name"])
                self.increment_created("Language")

            language_obj.code = lang["code"]
            language_obj.full_clean()
            language_obj.save()

        logger.info("Language update complete")

    def update_formats(self):
        """
        Updates all formats from file
        """
        logger.info("Updating format list")

        for fmt in import_json(FORMAT_JSON_PATH):
            try:
                format_obj = Format.objects.get(code=fmt["code"])
                self.increment_updated("Format")
            except Format.DoesNotExist:
                format_obj = Format(code=fmt["code"])
                self.increment_created("Format")

            format_obj.name = fmt["name"]
            format_obj.full_clean()
            format_obj.save()

    def update_types(self) -> None:
        logger.info("Updating types")

        type_dict = import_json(_paths.TYPES_JSON_PATH)["data"]
        for type_str, children in type_dict.items():
            type_str = type_str.title()
            if not CardType.objects.filter(name=type_str).exists():
                CardType.objects.create(name=type_str)
                self.increment_created("CardType")

            for subtype in children.get("subTypes"):
                if not CardSubtype.objects.filter(name=subtype).exists():
                    CardSubtype.objects.create(name=subtype)
                    self.increment_created("CardSubtype")

            for supertype in children.get("superTypes"):
                if not CardSupertype.objects.filter(name=supertype).exists():
                    CardSupertype.objects.create(name=supertype)
                    self.increment_created("CardSupertype")

        for extra_type in ["Token", "Card", "Emblem"]:
            if not CardType.objects.filter(name=extra_type).exists():
                CardType.objects.create(name=extra_type)
                self.increment_created("CardType")

    def update_frame_effects(self) -> None:
        """
        Updates all changes to frame effects
        """
        logger.info("Updating frame effects")
        frame_effects = import_json(_paths.FRAME_EFFECT_JSON_PATH)
        for frame_effect in frame_effects:
            try:
                existing_frame_effect = FrameEffect.objects.get(
                    code=frame_effect["code"]
                )
                if frame_effect["name"] != existing_frame_effect.name:
                    existing_frame_effect.name = frame_effect["name"]
                    existing_frame_effect.save()
                    self.increment_updated("FrameEffect")
            except FrameEffect.DoesNotExist:
                FrameEffect.objects.create(
                    name=frame_effect["name"], code=frame_effect["code"]
                )
                self.increment_created("FrameEffect")

    def increment_updated(self, object_type: str):
        """
        Increments the number of objects that were updated
        :param object_type: The type of object that was updated
        :param object_type:
        """
        if object_type not in self.update_counts:
            self.update_counts[object_type] = 0

        self.update_counts[object_type] += 1

    def increment_created(self, object_type: str):
        """
        Increments the number of objects that were created
        :param object_type: The type of object that was created
        """
        if object_type not in self.created_counts:
            self.created_counts[object_type] = 0

        self.created_counts[object_type] += 1

    def increment_ignores(self, object_type: str) -> None:
        """
        Increments the number of objects that were ignored
        :param object_type: The type of object that was ignored
        """
        if object_type not in self.ignored_counts:
            self.ignored_counts[object_type] = 0

        self.ignored_counts[object_type] += 1

    def log_stats(self) -> None:
        """
        Logs all updated/created/ignored objects
        """
        logger.info("%s", "\n" + ("=" * 80) + "\n\nUpdate complete:\n")
        elapsed_time = time.time() - self.start_time
        logger.info(
            "Time elapsed: %s", time.strftime("%H:%M:%S", time.gmtime(elapsed_time))
        )
        for key, value in self.created_counts.items():
            logger.info("Created %s %s", key, value)

        for key, value in self.update_counts.items():
            logger.info("Updated %s %s", key, value)

        for key, value in self.ignored_counts.items():
            logger.info("Ignored %s %s", key, value)
