"""
Module for the update_metadata command
"""
import json
import logging

from django.db import transaction

from cards.models import (
    Colour,
    Format,
    Language,
    Rarity,
)
from data_import._paths import LANGUAGE_JSON_PATH, RARITY_JSON_PATH, COLOUR_JSON_PATH, \
    FORMAT_JSON_PATH

from data_import.management.data_import_command import DataImportCommand

logger = logging.getLogger('django')


def import_json(file_path: str) -> dict:
    """
    Imports data from a json file and returns the dict
    :param file_path: The file to read
    :return: The dict representation of the file
    """
    with open(file_path, 'r', encoding="utf8") as json_file:
        return json.load(json_file, encoding='UTF-8')


class Command(DataImportCommand):
    """
    The command for updating all metadata in the database
    (data that is stored in external files, and not in mtgjson)
    """
    help = "The command for updating all metadata in the database " \
           "(data that is stored in external files, and not in mtgjson)"

    def handle(self, *args, **options):
        with transaction.atomic():
            self.update_rarities()
            self.update_colours()
            self.update_languages()
            self.update_formats()

        self.log_stats()

    def update_colours(self):
        """
        Updates all colours from file
        """
        logger.info('Updating colour list')

        for colour in import_json(COLOUR_JSON_PATH):
            colour_obj = Colour.objects.filter(symbol=colour['symbol']).first()
            if colour_obj is not None:
                logger.info('Updating existing colour %s', colour_obj)
                self.increment_updated('Colour')
            else:
                logger.info('Creating new colour %s', colour['name'])
                colour_obj = Colour(symbol=colour['symbol'],
                                    name=colour['name'],
                                    display_order=colour['display_order'],
                                    bit_value=colour['bit_value'])
                colour_obj.full_clean()
                colour_obj.save()
                self.increment_updated('Colour')

    def update_rarities(self):
        """
        Updates all rarities from file
        """
        logger.info('Updating rarity list')

        for rarity in import_json(RARITY_JSON_PATH):
            rarity_obj = Rarity.objects.filter(symbol=rarity['symbol']).first()
            if rarity_obj is not None:
                logger.info('Updating existing rarity %s', rarity_obj.name)
                rarity_obj.name = rarity['name']
                rarity_obj.display_order = rarity['display_order']
                rarity_obj.full_clean()
                rarity_obj.save()
                self.increment_updated('Rarity')
            else:
                logger.info('Creating new rarity %s', rarity['name'])

                rarity_obj = Rarity(
                    symbol=rarity['symbol'],
                    name=rarity['name'],
                    display_order=rarity['display_order'])
                rarity_obj.full_clean()
                rarity_obj.save()
                self.increment_created('Rarity')

        logger.info('Rarity update complete')

    def update_languages(self):
        """
        Updates all languages from file
        """
        logger.info('Updating language list')

        for lang in import_json(LANGUAGE_JSON_PATH):
            language_obj = Language.objects.filter(name=lang['name']).first()
            if language_obj is not None:
                logger.info("Updating language: %s", lang['name'])
                self.increment_updated('Language')
            else:
                logger.info("Creating new language: %s", lang['name'])
                language_obj = Language(name=lang['name'])
                self.increment_created('Language')

            language_obj.code = lang['code']
            language_obj.full_clean()
            language_obj.save()

        logger.info('Language update complete')

    def update_formats(self):
        """
        Updates all formats from file
        """
        logger.info('Updating format list')

        for fmt in import_json(FORMAT_JSON_PATH):
            try:
                format_obj = Format.objects.get(code=fmt['code'])
                self.increment_updated('Format')
            except Format.DoesNotExist:
                format_obj = Format(code=fmt['code'])
                self.increment_created('Format')

            format_obj.name = fmt['name']
            format_obj.full_clean()
            format_obj.save()
