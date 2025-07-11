"""
The module for the import_usercardchanges command
"""

import logging
from datetime import datetime

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from pytz import utc

from cards.models.card import (
    UserCardChange,
    CardLocalisation,
    CardPrinting,
    Card,
)
from cards.models.language import Language
from cards.models.sets import Set

logger = logging.getLogger("django")


class Command(BaseCommand):
    """
    The command for importing user card changes from a tab separated file
    Tis will delete all cards that the user has
    """

    help = "Imports user card changes from a tab separated file"

    def __init__(self, stdout=None, stderr=None, no_color=False):
        self.user = None
        super().__init__(stdout=stdout, stderr=stderr, no_color=no_color)

    def add_arguments(self, parser):

        # Positional arguments
        parser.add_argument("username", nargs=1, type=str)
        parser.add_argument("filename", nargs=1, type=str)

    def handle(self, *args, **options):
        filename = options.get("filename")[0]

        try:
            self.user = get_user_model().objects.get(
                username=options.get("username")[0]
            )
        except get_user_model().DoesNotExist:
            logger.error('Cannot find user with name "%s"', options.get("username")[0])
            return

        self.user.card_changes.all().delete()

        with open(filename, "r") as file:
            for line in file:
                logger.info(line)
                (name, setcode, datestr, number) = line.rstrip().split("\t")
                date = datetime.strptime(datestr, "%Y-%m-%d %H:%M:%S")
                date = utc.localize(date)
                self.import_usercardchange(
                    name=name, setcode=setcode, date=date, number=number
                )

    def import_usercardchange(
        self, name: str, setcode: str, date: datetime, number: int
    ):
        """
        Imports a single user card change into the database
        :param name: The name of the card
        :param setcode: The set of the card that the change was in
        :param date:  The date that the change was made
        :param number: The number of cards the change was
        :return:
        """
        card = Card.objects.get(name=name)
        logger.info("Card: %s", card)

        cardset = Set.objects.get(code=setcode)
        logger.info("Set: %s", cardset)

        printing = CardPrinting.objects.filter(card=card, set=cardset).first()
        logger.info("CardPrinting: %s", printing)

        printlang = CardLocalisation.objects.get(
            card_printing=printing, language=Language.english()
        )
        logger.info("CardLocalisation: %s", printlang)

        if UserCardChange.objects.filter(
            card_localisation__in=printlang.localisations,
            owner=self.user,
            date=date,
            difference=number,
        ).exists():
            logger.info("Other half of this card already has been added")
            return

        for localisation in printlang.localisations:
            user_card = UserCardChange(
                localisation=localisation, difference=number, owner=self.user, date=date
            )
            user_card.save()
