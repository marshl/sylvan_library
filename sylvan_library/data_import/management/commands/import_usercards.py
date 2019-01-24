"""
The module for the import_usercards command
"""

import logging

from django.core.management.base import BaseCommand
from django.db import transaction
from django.contrib.auth.models import User

from cards.models import (
    Card,
    CardPrinting,
    CardPrintingLanguage,
    Language,
    PhysicalCard,
    Set,
    UserOwnedCard,
)
from _query import query_yes_no

logger = logging.getLogger('django')


class Command(BaseCommand):
    """
    The command for importing user cards from a tab separated file
    """
    help = 'Imports a list of user owned cards from a tsv file'

    def add_arguments(self, parser):

        # Positional arguments
        parser.add_argument('username', nargs=1, type=str, help='The user to who owns teh cards')
        parser.add_argument('filename', nargs=1, type=str, help='The file to import the cards from')

    def handle(self, *args, **options):

        filename = options.get('filename')[0]
        username = options.get('username')[0]
        english = Language.objects.get(name='English')

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            logger.error('Cannot find user with name %s', username)
            return

        with transaction.atomic():
            user.owned_cards.all().delete()

            with open(filename, 'r') as file:
                for line in file:
                    logger.info(line)
                    (name, number, setcode) = line.rstrip().split('\t')

                    card = Card.objects.get(name=name)
                    logger.info('Card ID: %s', card.id)
                    try:
                        cardset = Set.objects.get(code=setcode)
                    except Set.DoesNotExist:
                        raise Exception(f"Could not find the set {setcode} for {name}")

                    logger.info('Set ID: %s', cardset.id)

                    printing = CardPrinting.objects.filter(
                        card=card,
                        set=cardset).first()
                    logger.info('CardPrinting ID: %s', printing.id)

                    printlang = CardPrintingLanguage.objects.get(
                        card_printing=printing,
                        language=english)
                    logger.info('CardPrintingLanguage ID: %s', printlang.id)

                    physcards = PhysicalCard.objects.filter(
                        printed_languages=printlang)

                    existing_rec = UserOwnedCard.objects.filter(
                        physical_card__in=physcards,
                        owner=user)
                    if existing_rec.exists():
                        if card.links.exists():
                            logger.info('Other half of this card already has been added')
                            continue
                        else:
                            existing_rec = existing_rec.first()
                            result = query_yes_no(
                                f'{existing_rec} already exists, do you want to add to it?')
                            if result:
                                existing_rec.count += int(number)
                                existing_rec.save()
                            continue

                    for phys in physcards:
                        usercard = UserOwnedCard(
                            physical_card=phys,
                            count=number,
                            owner=user)
                        usercard.save()
