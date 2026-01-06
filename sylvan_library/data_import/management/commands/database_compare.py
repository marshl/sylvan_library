"""
Module for the update_database command
"""

import logging
import time
import typing

from django.core.management.base import BaseCommand
from django.db import transaction, models

from sylvan_library.data_import.management.commands import get_all_set_data
from sylvan_library.data_import.models import (
    UpdateSet,
    UpdateCard,
    UpdateBlock,
    UpdateMode,
    UpdateCardFace,
    UpdateCardPrinting,
    UpdateCardFacePrinting,
    UpdateCardLocalisation,
    UpdateCardFaceLocalisation,
    UpdateCardRuling,
    UpdateCardLegality,
)
from sylvan_library.data_import.parsers.set_file_parser import SetFileParser
from sylvan_library.data_import.parsers.parse_counter import ParseCounter

logger = logging.getLogger("django")


class Command(BaseCommand):
    """
    The command for updating hte database
    """

    help = (
        "Uses the downloaded JSON files to update the database, "
        "including creating cards, set and rarities\n"
    )

    def __init__(self, stdout=None, stderr=None, no_color=False):
        super().__init__(stdout=stdout, stderr=stderr, no_color=no_color)
        self.parse_counter = ParseCounter()

        self.force_update = False
        self.start_time = None

    def add_arguments(self, parser):
        parser.add_argument(
            "--set",
            dest="set_codes",
            nargs="*",
            help="Update only the given list of sets",
        )

    def handle(self, *args, **options):
        self.start_time = time.time()
        with transaction.atomic():
            UpdateBlock.objects.all().delete()
            UpdateSet.objects.all().delete()
            UpdateCard.objects.all().delete()
            UpdateCardFace.objects.all().delete()
            UpdateCardRuling.objects.all().delete()
            UpdateCardLegality.objects.all().delete()
            UpdateCardPrinting.objects.all().delete()
            UpdateCardFacePrinting.objects.all().delete()
            UpdateCardLocalisation.objects.all().delete()
            UpdateCardFaceLocalisation.objects.all().delete()

            for set_data in get_all_set_data(options.get("set_codes")):
                logger.info("Parsing set %s (%s)", set_data["code"], set_data["name"])
                set_file_parser = SetFileParser(
                    set_data,
                    parse_counter=self.parse_counter,
                )
                set_file_parser.parse_set_file()
        self.log_stats()

    def log_single_stat(
        self, model_name: str, update_type: typing.Type[models.Model]
    ) -> None:
        """
        Logs a single update statistic
        :param model_name: The name of the model that was changed
        :param update_type: The model that was changed
        """
        create_count = update_type.objects.filter(update_mode=UpdateMode.CREATE).count()
        if create_count > 0:
            logger.info("%s %s objects to create", create_count, model_name)

        update_count = update_type.objects.filter(update_mode=UpdateMode.UPDATE).count()
        if update_count > 0:
            logger.info("%s %s objects to update", update_count, model_name)

    def log_stats(self) -> None:
        """
        Logs out the number sof objects to delete/create/update
        """
        self.log_single_stat("block", UpdateBlock)
        self.log_single_stat("set", UpdateSet)
        self.log_single_stat("card", UpdateCard)
        self.log_single_stat("card face", UpdateCardFace)
        self.log_single_stat("card printing", UpdateCardPrinting)
        self.log_single_stat("card printing face", UpdateCardFacePrinting)
        self.log_single_stat("card localisation", UpdateCardLocalisation)
        self.log_single_stat("card face localisation", UpdateCardFaceLocalisation)
        self.log_single_stat("legality", UpdateCardLegality)
        self.log_single_stat("ruling", UpdateCardRuling)
        logger.info("Completed in %ss", time.time() - self.start_time)
