"""
Module for the reset_database command
"""

from typing import Type, Any

from django.core.management.base import BaseCommand
from django.db import connection
from django.db import models

from cards.models.card import (
    CardFace,
    Card,
    CardPrinting,
    CardFacePrinting,
    CardLocalisation,
    UserOwnedCard,
    UserCardChange,
)
from cards.models.colour import Colour
from cards.models.decks import DeckCard, Deck
from cards.models.language import Language
from cards.models.legality import CardLegality
from cards.models.rarity import Rarity
from cards.models.ruling import CardRuling
from cards.models.sets import Set, Block, Format
from cards.models.tag import CardTag
from data_import import _query


def reset_sequence(table_name: str) -> None:
    """
    Resets the sequence of a table
    :param table_name: The name of the table to have its sequence reset
    """
    with connection.cursor() as cursor:
        cursor.execute(
            f"SELECT setval(pg_get_serial_sequence('\"{table_name}\"','id'), 1, false);"
        )


def truncate_model(model_obj: Type[models.Model]) -> None:
    """
    Truncates the table of the given model
    :param model_obj: The model to truncate
    """
    print("Truncating {0}... ".format(model_obj.__name__), end="")
    model_obj.objects.all().delete()
    # pylint: disable=protected-access
    reset_sequence(model_obj.objects.model._meta.db_table)
    print("Done")


class Command(BaseCommand):
    """
    Command for soft resetting the database
    """

    help = "Delete all records from all tables without dropping the tables"

    def handle(self, *args: Any, **options: Any) -> None:
        db_name = connection.cursor().db.settings_dict.get("NAME")
        confirm = _query.query_yes_no(
            f"Are you sure you want to delete all data in the database {db_name}?", "no"
        )

        if not confirm:
            return

        truncate_model(DeckCard)
        truncate_model(Deck)
        truncate_model(CardTag)
        truncate_model(CardRuling)
        truncate_model(CardLegality)
        truncate_model(UserCardChange)
        truncate_model(UserOwnedCard)
        truncate_model(CardLocalisation)
        truncate_model(CardFacePrinting)
        truncate_model(CardPrinting)
        truncate_model(CardFace)
        truncate_model(Card)
        truncate_model(Rarity)
        truncate_model(Set)
        truncate_model(Block)
        truncate_model(Format)
        truncate_model(Language)
        truncate_model(Colour)
