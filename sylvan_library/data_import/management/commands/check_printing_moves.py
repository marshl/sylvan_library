"""
Module for the check_printing_moves command
"""

import logging
from collections import defaultdict

from django.core.management.base import BaseCommand
from django.db.models import Count

from sylvan_library.cards.models.card import (
    CardPrinting,
    UserOwnedCard,
    Card,
)
from sylvan_library.cards.models.sets import Set
from sylvan_library.data_import._query import query_yes_no
from sylvan_library.data_import.management.commands import get_all_set_data
from sylvan_library.data_import.parsers.set_file_parser import SetFileParser

logger = logging.getLogger("django")


class Command(BaseCommand):
    """
    The command for checking any card move or missing cards
    """

    help = (
        "Checks the downloaded set files against the existing cards ion the database to see if "
        "any cards may have been moved from one set to another, or perhaps deleted entirely."
    )

    def __init__(self, stdout=None, stderr=None, no_color=False):
        super().__init__(stdout=stdout, stderr=stderr, no_color=no_color)

    def handle(self, *args, **options):
        existing_scryfall_mapping = {
            c[0]: c[1]
            for c in CardPrinting.objects.values_list("scryfall_id", "set__code")
        }
        new_scryfall_mapping = {}
        parsed_sets = []
        for set_data in get_all_set_data(options.get("set_codes")):
            for staged_set in SetFileParser(set_data).get_staged_sets():
                set_code = staged_set.code
                parsed_sets.append(set_code)
                for card in staged_set.get_cards():
                    scryfall_id = card["identifiers"]["scryfallId"]
                    new_scryfall_mapping[scryfall_id] = set_code
        moves = defaultdict(list)
        missing_cards = defaultdict(list)

        for scryfall_id, set_code in existing_scryfall_mapping.items():
            if scryfall_id not in new_scryfall_mapping:
                missing_cards[set_code].append(scryfall_id)
                continue
            new_set_code = new_scryfall_mapping[scryfall_id]
            if new_set_code != set_code:
                moves[(set_code, new_set_code)].append(scryfall_id)

        for (old_set_code, new_set_code), scryfall_ids in moves.items():
            print(
                f"The following cards have been moved from {old_set_code} to {new_set_code}:"
            )
            for scryfall_id in scryfall_ids:
                printing = CardPrinting.objects.get(scryfall_id=scryfall_ids)
                print(f"\t{printing} ({scryfall_id}")

            if query_yes_no("Would you like to move them all?"):
                for scryfall_id in scryfall_ids:
                    existing_printing = CardPrinting.objects.get(
                        scryfall_id=scryfall_id
                    )
                    existing_printing.set = Set.objects.get(code=new_set_code)
                    existing_printing.full_clean()
                    existing_printing.save()

        for set_code, missing_scryfall_ids in missing_cards.items():
            print(f"The following cards from {set_code} can't be found.")
            if set_code not in parsed_sets:
                print("The set appears to have been ignored")

            for scryfall_id in missing_scryfall_ids:
                print(
                    f"\t{CardPrinting.objects.get(scryfall_id=scryfall_id).card.name} ({scryfall_id})"
                )

            for missing_scryfall_id in missing_scryfall_ids:
                user_owned_cards = UserOwnedCard.objects.filter(
                    card_localisation__card_printing__scryfall_id=missing_scryfall_id
                )

                if user_owned_cards.exists():
                    raise ValueError(
                        f"Cannot delete missing cards as a user owns a version of it: {user_owned_cards.first()}"
                    )
            if query_yes_no("Would you like to delete them all?"):
                CardPrinting.objects.filter(
                    scryfall_id__in=missing_scryfall_ids
                ).delete()

        cards_without_printings = Card.objects.annotate(
            printing_count=Count("printings")
        ).filter(printing_count=0)
        if cards_without_printings.exists():
            print("The following cards have no printings:")
            for card in cards_without_printings:
                print(f"\t{card}")

            if query_yes_no("Would you like to delete them all?"):
                cards_without_printings.delete()
