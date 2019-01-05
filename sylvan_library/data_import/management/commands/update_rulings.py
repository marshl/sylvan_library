import logging, time

from django.core.management.base import BaseCommand
from django.db import transaction

from cards.models import *
from data_import.importers import *

logger = logging.getLogger('django')


class Command(BaseCommand):
    help = 'Downloads the MtG JSON data file'

    def handle(self, *args, **options):
        importer = JsonImporter()
        importer.import_data()

        staged_sets = importer.get_staged_sets()
        self.update_ruling_list(staged_sets)

    def update_ruling_list(self, staged_sets):
        logger.info('Updating card rulings')
        CardRuling.objects.all().delete()

        for staged_set in staged_sets:

            if staged_set.get_code().startswith('p'):
                logger.info(f'Ignoring set {s.get_name()}')
                continue

            logger.info(f'Updating rulings in {staged_set.get_name()}')

            for staged_card in staged_set.get_cards():

                if not staged_card.has_rulings():
                    continue

                card_obj = Card.objects.get(name=staged_card.get_name())

                for ruling in staged_card.get_rulings():
                    ruling, created = CardRuling.objects.get_or_create(
                        card=card_obj, text=ruling['text'], date=ruling['date'])

        logger.info('Card rulings updated')
