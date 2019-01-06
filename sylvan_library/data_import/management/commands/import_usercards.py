import logging

from django.core.management.base import BaseCommand
from django.db import transaction

from cards.models import *

logger = logging.getLogger('django')


class Command(BaseCommand):
    help = 'Imports a list of user owned cards from a csv file'

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
            logger.error(f'Cannot find user with name {username}')
            return

        with(transaction.atomic()):
            user.owned_cards.all().delete()

            with open(filename, 'r') as f:
                for line in f:
                    (name, number, setcode) = line.rstrip().split('\t')

                    card = Card.objects.get(name=name)
                    logger.info(f'Card ID: {card.id}')
                    try:
                        cardset = Set.objects.get(code=setcode)
                    except Set.DoesNotExist:
                        raise Exception(f"Could not find the set {setcode} for {name}")

                    logger.info(f'Set ID: {cardset.id}')

                    printing = CardPrinting.objects.filter(
                        card=card,
                        set=cardset).first()
                    logger.info(f'CardPrinting ID: {printing.id}')

                    printlang = CardPrintingLanguage.objects.get(
                        card_printing=printing,
                        language=english)
                    logger.info(f'CardPrintingLanguage ID: {printlang.id}')

                    physcards = PhysicalCard.objects.filter(
                        printed_languages=printlang)

                    if UserOwnedCard.objects.filter(
                            physical_card__in=physcards,
                            owner=user).exists():
                        logger.info('Other half of this card already has been added')
                        continue

                    for phys in physcards:
                        usercard = UserOwnedCard(
                            physical_card=phys,
                            count=number,
                            owner=user)
                        usercard.save()
