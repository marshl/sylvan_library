"""
The module for the import_usercards command
"""

import logging

from django.core.management.base import BaseCommand, CommandParser
from django.db import transaction
from django.contrib.auth.models import User

from cards.models.card import (
    Card,
    CardPrinting,
    CardLocalisation,
    UserOwnedCard,
)
from cards.models.language import Language
from cards.models.sets import Set
from data_import._query import query_yes_no

logger = logging.getLogger("django")


class Command(BaseCommand):
    """
    The command for importing user cards from a tab separated file
    """

    help = "Imports a list of user owned cards from a tsv file"

    def __init__(self, stdout=None, stderr=None, no_color=False):
        self.user = None
        super().__init__(stdout=stdout, stderr=stderr, no_color=no_color)

    def add_arguments(self, parser: CommandParser):

        # Positional arguments
        parser.add_argument(
            "username", nargs=1, type=str, help="The user to who owns the cards"
        )
        parser.add_argument(
            "filename", nargs=1, type=str, help="The file to import the cards from"
        )

    def handle(self, *args, **options) -> None:

        filename = options.get("filename")[0]
        username = options.get("username")[0]

        try:
            self.user = User.objects.get(username=username)
        except User.DoesNotExist:
            logger.error("Cannot find user with name %s", username)
            return

        with transaction.atomic():
            self.user.owned_cards.all().delete()

            with open(filename, "r") as file:
                for line in file:
                    logger.info(line)
                    (name, number, setcode) = line.rstrip().split("\t")

                    card = Card.objects.get(name=name, is_token=False)
                    logger.info("Card ID: %s", card.id)
                    try:
                        cardset = Set.objects.get(code=setcode)
                    except Set.DoesNotExist:
                        raise Exception(f"Could not find the set {setcode} for {name}")

                    logger.info("Set ID: %s", cardset.id)
                    self.import_usercard(card, cardset, int(number))

    def import_usercard(self, card: Card, cardset: Set, count: int):
        """
        Imports a single user owned card
        :param card: The card the user owns
        :param cardset: The set the card is in
        :param count: The number of that card the user owns
        """
        printing = CardPrinting.objects.filter(card=card, set=cardset).first()
        logger.info("CardPrinting ID: %s", printing.id)

        localisation = CardLocalisation.objects.get(
            card_printing=printing, language=Language.english()
        )
        logger.info("CardLocalisation ID: %s", localisation.id)

        existing_rec = UserOwnedCard.objects.filter(
            card_locaisation=localisation, owner=self.user
        )
        if existing_rec.exists():
            existing_rec = existing_rec.first()
            result = query_yes_no(
                f"{existing_rec} already exists, do you want to add to it?"
            )
            if result:
                existing_rec.count += count
                existing_rec.save()

            return

        usercard = UserOwnedCard(
            card_localisation=localisation, count=count, owner=self.user
        )
        usercard.full_clean()
        usercard.save()
