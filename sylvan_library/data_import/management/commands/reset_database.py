"""
Module for the reset_database command
"""
from django.core.management.base import BaseCommand
from django.db import connection

from cards.models import (
    Block,
    Card,
    CardLegality,
    CardPrinting,
    CardPrintingLanguage,
    CardRuling,
    CardTag,
    Colour,
    Deck,
    DeckCard,
    Format,
    Language,
    PhysicalCard,
    Rarity,
    Set,
    UserCardChange,
    UserOwnedCard,
)
from data_import import _query


class Command(BaseCommand):
    """
    Command for soft resetting the database
    """
    help = 'Delete all records from all tables without dropping the tables'

    def truncate_model(self, model_obj):
        print('Truncating {0}... '.format(model_obj.__name__), end='')
        model_obj.objects.all().delete()
        # pylint: disable=protected-access
        self.reset_sequence(model_obj.objects.model._meta.db_table)
        print('Done')

    def reset_sequence(self, table_name):
        with connection.cursor() as cursor:
            cursor.execute(
                f"SELECT setval(pg_get_serial_sequence('\"{table_name}\"','id'), 1, false);")

    def handle(self, *args, **options):
        confirm = _query.query_yes_no(
            'Are you sure you want to delete all data in the database?', 'no')

        if not confirm:
            return

        self.truncate_model(DeckCard)
        self.truncate_model(Deck)
        self.truncate_model(CardTag)
        self.truncate_model(CardRuling)
        self.truncate_model(CardLegality)
        self.truncate_model(UserCardChange)
        self.truncate_model(UserOwnedCard)
        self.truncate_model(PhysicalCard)
        self.truncate_model(CardPrintingLanguage)
        self.truncate_model(CardPrinting)
        self.truncate_model(Card)
        self.truncate_model(Rarity)
        self.truncate_model(Set)
        self.truncate_model(Block)
        self.truncate_model(Format)
        self.truncate_model(Language)
        self.truncate_model(Colour)

        self.reset_sequence('cards_card_links')
        self.reset_sequence('cards_cardprintinglanguage_physical_cards')
