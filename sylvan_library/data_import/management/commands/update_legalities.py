"""
The module for the update_rulings comand
"""
import logging
from typing import List

from django.db import transaction

from cards.models import (
    Card,
    CardLegality,
    Format
)
from data_import.staging import StagedSet
from data_import.management.data_import_command import DataImportCommand

logger = logging.getLogger('django')


class Command(DataImportCommand):
    """
    Command for updating all card legalities
    """
    help = 'Updates all card legalities'

    def handle(self, *args, **options):
        with transaction.atomic():
            self.update_legalities(self.get_staged_sets())

        self.log_stats()

    def update_legalities(self, staged_sets: List[StagedSet]) -> None:
        """
        Updates the list of Legalities for every card
        :param staged_sets:
        """

        cards_updated = set()
        format_map = {f.code: f for f in Format.objects.all()}

        for staged_set in staged_sets:
            logger.info('Finding legalities for %s', staged_set.get_name())

            for staged_card in staged_set.get_cards():

                if staged_card.get_name() in cards_updated or staged_card.is_token:
                    continue

                card_obj = Card.objects.get(name=staged_card.get_name(), is_token=False)

                # Legalities can disappear form the json data if the card rolls out of standard,
                # so all legalities should be cleared out and redone
                card_obj.legalities.all().delete()

                for format_code, legality in staged_card.get_legalities().items():
                    format_obj = format_map[format_code]
                    legality_obj = CardLegality(
                        card=card_obj, format=format_obj, restriction=legality
                    )
                    legality_obj.full_clean()
                    legality_obj.save()
                    self.increment_created('Legality')

                cards_updated.add(staged_card.get_name())
