from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

from spellbook.models import Card, CardPrinting, CardPrintingLanguage
from spellbook.models import UserOwnedCard, Set, Language
from spellbook.models import PhysicalCardLink


class Command(BaseCommand):
    help = 'Downloads the MtG JSON data file'

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
            print('Cannot find user with name "{0}"'.format(options.get('username')[0]))
            return

        user.userownedcard_set.all().delete()

        with open(filename, 'r') as f:

            for line in f:

                (name, number, setcode) = line.rstrip().split('\t')

                card = Card.objects.get(name=name)
                print('Card ID: {0}'.format(card.id))

                cardset = Set.objects.get(code=setcode)
                print('Set ID: {0}'.format(cardset.id))

                printing = CardPrinting.objects.filter(
                               card=card,
                               set=cardset).first()
                print('CardPrinting ID: {0}'.format(printing.id))

                printlang = CardPrintingLanguage.objects.get(
                             card_printing=printing,
                             language=english)
                print('CardPrintingLanguage ID: {0}'.format(printlang.id))

                link = PhysicalCardLink.objects.get(
                        printing_language=printlang)
                print('PhysicalCardLink ID: {0}'.format(link.id))

                phys = link.physical_card
                print('PhysicaCard ID: {0}'.format(phys.id))

                if phys.layout != 'normal' and UserOwnedCard.objects.filter(
                        physical_card=phys,
                        owner=user).exists():
                    print('Other half of this card already has been added')
                    continue

                usercard = UserOwnedCard(
                             physical_card=phys,
                             count=number,
                             owner=user)
                usercard.save()
