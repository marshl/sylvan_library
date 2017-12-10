from django.core.management.base import BaseCommand

from cards.models import *
from data_import.management.commands import _query
from django.db import connection


class Command(BaseCommand):
    help = 'Downloads the MtG JSON data file'

    def truncate_model(self, model_obj):
        print('Truncating {0}... '.format(model_obj.__name__), end='')
        model_obj.objects.all().delete()

        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT setval(pg_get_serial_sequence('\"{0}\"','id'), 1, false);".format(
                    model_obj.objects.model._meta.db_table
                )
            )

        print('Done')

    def handle(self, *args, **options):
        confirm = _query.query_yes_no(
            'Are you sure you want to delete all data in the database?', 'no')

        if not confirm:
            return

        self.truncate_model(DeckCard)
        self.truncate_model(Deck)
        self.truncate_model(CardTagLink)
        self.truncate_model(CardTag)
        self.truncate_model(CardRuling)
        self.truncate_model(UserCardChange)
        self.truncate_model(UserOwnedCard)
        self.truncate_model(PhysicalCard)
        self.truncate_model(CardPrintingLanguage)
        self.truncate_model(CardPrinting)
        self.truncate_model(Card)
        self.truncate_model(Rarity)
        self.truncate_model(Set)
        self.truncate_model(Block)
        self.truncate_model(Language)
