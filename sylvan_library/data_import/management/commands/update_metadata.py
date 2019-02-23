"""
Module for the update_metadata command
"""
import logging

from django.db import transaction

from cards.models import (
    Colour,
    Language,
    Rarity,
)
from data_import._paths import LANGUAGE_JSON_PATH, RARITY_JSON_PATH, COLOUR_JSON_PATH

from data_import.management.data_import_command import DataImportCommand

logger = logging.getLogger('django')


class Command(DataImportCommand):
    """
    The command for updating all metadata in the database
    (data that is stored in external files, and not in mtgjson)
    """
    help = """The command for updating all metadata in the database 
              (data that is stored in external files, and not in mtgjson)"""

    def handle(self, *args, **options):
        with transaction.atomic():
            self.update_rarities()
            self.update_colours()
            self.update_languages()

        self.log_stats()

    def update_colours(self):
        logger.info('Updating colour list')

        for colour in self.import_json(COLOUR_JSON_PATH):
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

        logger.info('Updating rarity list')

        for rarity in self.import_json(RARITY_JSON_PATH):
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

        logger.info('Updating language list')

        for lang in self.import_json(LANGUAGE_JSON_PATH):
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
