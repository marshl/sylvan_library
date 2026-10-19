"""
Module for the verify_keyrune_mapping command
"""

import os
import re

from django.conf import settings
from django.core.management.base import BaseCommand

from sylvan_library.cards.models.sets import Set


class Command(BaseCommand):
    """
    Finds any keyrune set symbols that are unused
    and any sets that have codes that can't be found in keyrune
    """

    help = "Verifies that database update was successful"

    def __init__(self) -> None:
        super().__init__()

    def handle(self, *args, **options) -> None:
        icons_path = os.path.join(
            settings.SITE_ROOT,
            "sylvan-react",
            "node_modules",
            "keyrune",
            "less",
            "icons.less",
        )
        # Lines look like '.@{ss-prefix}-lea:before { content: "\e600"; } // Alpha',
        # but several codes can share one icon, with the comment on only one line
        sets = {}
        with open(icons_path, encoding="utf8") as icons_file:
            for line in icons_file:
                comment = re.search(r"//\s*(?P<set_name>.+)$", line)
                for set_code in re.findall(
                    r"\.@\{ss-prefix\}-([a-z0-9]+):before", line
                ):
                    sets[set_code] = (
                        comment["set_name"].strip() if comment else set_code
                    )

        for card_set in Set.objects.all().order_by("code"):
            if card_set.keyrune_code.lower() not in sets:
                print(f"{card_set.name} ({card_set.code}) doesn't have a set symbol")

        for set_code, set_name in sets.items():
            if not any(
                s for s in Set.objects.all() if s.keyrune_code.lower() == set_code
            ):
                print(f"Keyrune symbol {set_name} ({set_code}) doesn't have a set")
