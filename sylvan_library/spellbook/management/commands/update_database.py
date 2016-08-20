from django.core.management.base import BaseCommand
from ...models import Card, CardPrinting, CardPrintingLanguage, PhysicalCard
from ...models import PhysicalCardLink, UserOwnedCard, UserCardChange, DeckCard
from ...models import Deck, CardTagLink, CardTag, CardRuling, Rarity, Block
from ...models import Set, Language
from . import _query, _parse

class Command(BaseCommand):
    help = 'Downloads the MtG JSON data file'

    def handle(self, *args, **options):

        json_data = _parse.parse_json_data()
        json_data = sorted(json_data.items(),
                       key=lambda card_set: card_set[1]["releaseDate"])


        self.update_rarity_table()
        self.update_language_information()
        self.update_block_information(json_data)
        self.update_set_information(json_data)
        self.update_card_information(json_data)
        self.update_ruling_table(json_data)
        self.update_physical_cards(json_data)


    def update_rarity_table(self):
        pass

    def update_language_information(self):
        pass

    def update_block_information(self):
        pass

    def update_set_information(self):
        pass

    def update_card_information(self):
        pass

    def update_ruling_table(self):
        pass

    def update_physical_cards(self):
        pass
