"""
Module for the verify_keyrune_mapping command
"""

import os
import re

from django.core.management.base import BaseCommand

from sylvan_library.cards.models import Set


class Command(BaseCommand):
    """
    Finds any keyrune set symbols that are unused
    and any sets that have codes that can't be found in keyrune
    """

    help = "Verifies that database update was successful"

    def __init__(self) -> None:
        super().__init__()

    def handle(self, *args, **options) -> None:
        sass_path = os.path.join(
            "website", "static", "node_modules", "keyrune", "sass", "_variables.scss"
        )
        sets = {}
        with open(sass_path) as sass_file:
            for line in sass_file:
                if "$mtg_setlist:" not in line:
                    continue

                for set_line in sass_file:
                    if "//" in set_line:
                        continue

                    if set_line.startswith(")"):
                        break

                    groups = re.search(
                        '.+?"(?P<set_name>.+?)", *[\'"](?P<set_code>.+?)[\'"]', set_line
                    )

                    if groups:
                        sets[groups["set_code"]] = groups["set_name"]

        for card_set in Set.objects.all().order_by("code"):
            if card_set.keyrune_code.lower() not in sets.keys():
                print(f"{card_set.name} ({card_set.code}) doesn't have a set symbol")

        for set_code, set_name in sets.items():
            if not any(
                s for s in Set.objects.all() if s.keyrune_code.lower() == set_code
            ):
                print(f"Keyrune symbol {set_name} ({set_code}) doesn't have a set")
