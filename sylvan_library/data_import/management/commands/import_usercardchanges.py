"""
The module for the import_usercardchanges command
"""

import logging

from datetime import datetime
from pytz import utc

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

from cards.models import Card, CardPrinting, CardPrintingLanguage
from cards.models import UserCardChange, Set, Language, PhysicalCard

logger = logging.getLogger('django')


class Command(BaseCommand):
    """
    The command for importing user card changes from a tab separated file
    Tis will delete all cards that the user has
    """
    help = 'Imports user card changes from a tab separated file'

    def add_arguments(self, parser):

        # Positional arguments
        parser.add_argument('username', nargs=1, type=str)
        parser.add_argument('filename', nargs=1, type=str)

    def handle(self, *args, **options):

        filename = options.get('filename')[0]

        english = Language.objects.get(name='English')

        try:
            user = User.objects.get(username=options.get('username')[0])
        except User.DoesNotExist:
            logger.error('Cannot find user with name "{0}"'.format(
                options.get('username')[0]))
            return

        user.card_changes.all().delete()

        with open(filename, 'r') as file:

            for line in file:

                logger.info(line)
                (name, setcode, datestr, number) = line.rstrip().split('\t')
                date = datetime.strptime(datestr, '%Y-%m-%d %H:%M:%S')
                date = utc.localize(date)

                card = Card.objects.get(name=name)
                logger.info('Card: %s', card)

                cardset = Set.objects.get(code=setcode)
                logger.info('Set: %s', cardset)

                printing = CardPrinting.objects.filter(
                    card=card,
                    set=cardset).first()
                logger.info('CardPrinting: %s', printing)

                printlang = CardPrintingLanguage.objects.get(
                    card_printing=printing,
                    language=english)
                logger.info('CardPrintingLanguage: %s', printlang)

                physcards = PhysicalCard.objects.filter(
                    printed_languages=printlang)

                if UserCardChange.objects.filter(
                        physical_card__in=physcards,
                        owner=user, date=date, difference=number).exists():
                    logger.info('Other half of this card already has been added')
                    continue

                for phys in physcards:
                    usercard = UserCardChange(
                        physical_card=phys,
                        difference=number,
                        owner=user,
                        date=date)
                    usercard.save()
