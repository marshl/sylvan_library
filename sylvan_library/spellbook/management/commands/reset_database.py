from django.core.management.base import BaseCommand
from ...models import Card, CardPrinting, CardPrintingLanguage, PhysicalCard
from ...models import PhysicalCardLink, UserOwnedCard, UserCardChange, DeckCard
from ...models import Deck, CardTagLink, CardTag, CardRuling, Rarity, Block
from ...models import Set, Language
from . import _query

class Command(BaseCommand):
    help = 'Downloads the MtG JSON data file'

    def handle(self, *args, **options):

        confirm = _query.query_yes_no('Are you sure you want to delete all data in the database?', 'no')

        if not confirm:
            return

        print('Truncating DeckCards...')
        DeckCard.objects.all().delete()

        print('Truncating Decks...')
        Deck.objects.all().delete()

        print('Truncating CardTagLinks...')
        CardTagLink.objects.all().delete()

        print('Truncating CardTags...')
        CardTag.objects.all().delete()

        print('Truncating CardRulings...')
        CardRuling.objects.all().delete()

        print('Truncating UserCardChanges...')
        UserCardChange.objects.all().delete()

        print('Truncating UserOwnedCards...')
        UserOwnedCard.objects.all().delete()

        print('Truncating PhysicalCardLinks...')
        PhysicalCardLink.objects.all().delete()

        print('Truncating PhysicalCards...')
        PhysicalCard.objects.all().delete()

        print('Truncating CardPrintingLanguages...')
        CardPrintingLanguage.objects.all().delete()

        print('Truncating CardPrintings...')
        CardPrinting.objects.all().delete()

        print('Truncating Cards...')
        Card.objects.all().delete()

        print('Truncating Rarities...')
        Rarity.objects.all().delete()

        print('Truncating Sets...')
        Set.objects.all().delete()

        print('Truncating Blocks...')
        Block.objects.all().delete()

        print('Truncating Languages...')
        Language.objects.all().delete()
