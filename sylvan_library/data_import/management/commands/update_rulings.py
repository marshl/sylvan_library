"""
The module for the update_rulings comand
"""
import logging
from typing import List

from django.db import transaction

from cards.models import (
    Card,
    CardRuling,
)
from data_import.staging import StagedSet
from data_import.importers import JsonImporter
from data_import.management.data_import_command import DataImportCommand

logger = logging.getLogger('django')


class Command(DataImportCommand):
    """
    Command for updating all card rulings
    """
    help = 'Updates all card rulings'

    def handle(self, *args, **options):
        importer = JsonImporter()
        importer.import_data()

        staged_sets = importer.get_staged_sets()
        if not staged_sets:
            logger.error('No sets could be found. Please run the fetch_data command first')
            return

        with transaction.atomic():
            self.update_ruling_list(staged_sets)

        self.log_stats()

    def update_ruling_list(self, staged_sets: List[StagedSet]):
        """
        Updates all card rulings
        :param staged_sets: The list of staged sets
        """
        logger.info('Updating card rulings')
        CardRuling.objects.all().delete()

        for staged_set in staged_sets:
            logger.info('Updating rulings in %s', staged_set.get_name())
            for staged_card in staged_set.get_cards():

                if not staged_card.has_rulings() or staged_card.is_token:
                    continue

                try:
                    card_obj = Card.objects.get(name=staged_card.get_name(), is_token=False)
                except Card.DoesNotExist as ex:
                    raise Exception(f'Could not find card {staged_card.get_name()}: {ex}')

                for ruling in staged_card.get_rulings():
                    ruling, created = CardRuling.objects.get_or_create(
                        card=card_obj, text=ruling['text'], date=ruling['date'])

                    if created:
                        self.increment_created('CardRuling')
                    else:
                        self.increment_updated('CardRuling')

        logger.info('Card rulings updated')
