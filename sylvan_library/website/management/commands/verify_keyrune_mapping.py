"""
Module for the verify_database command
"""

import os
import re

from django.core.management.base import BaseCommand

from cards.models import (
    Set,
)


class Command(BaseCommand):
    """

    """
    help = 'Verifies that database update was successful'

    def __init__(self):
        super().__init__()

    def handle(self, *args, **options):
        sass_path = os.path.join('website', 'static', 'keyrune', 'sass',
                                 '_variables.scss')
        sets = {}
        with open(sass_path) as sass_file:
            for line in sass_file:
                if '$mtg_setlist:' not in line:
                    continue

                for line in sass_file:
                    if '//' in line:
                        continue

                    if line.startswith(')'):
                        break

                    groups = re.search('.+?"(?P<set_name>.+?)", *[\'"](?P<set_code>.+?)[\'"]', line)
                    if groups:
                        sets[groups['set_code']] = groups['set_name']

        for card_set in Set.objects.all().order_by('code'):
            if card_set.keyrune_code not in sets.keys():
                print(f"{card_set.name} ({card_set.code}) doesn't have a set symbol")

        for set_code, set_name in sets.items():
            if not any(s for s in Set.objects.all() if s.keyrune_code == set_code):
                print(f"Keyrune symbol {set_name} ({set_code}) doesn't have a set")
