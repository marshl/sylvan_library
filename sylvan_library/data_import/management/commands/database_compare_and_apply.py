"""
Module for the update_database command
"""

import logging

from django.core.management import call_command
from django.core.management.base import BaseCommand

logger = logging.getLogger("django")


class Command(BaseCommand):
    """
    The command for updating hte database
    """

    help = (
        "Uses the downloaded JSON files to update the database, "
        "including creating cards, set and rarities\n"
    )

    def handle(self, *args, **options):
        call_command("database_compare")
        call_command("apply_import")
