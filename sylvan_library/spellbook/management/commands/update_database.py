from django.core.management.base import BaseCommand
import json
from os import path

from ...models import Card, CardPrinting, CardPrintingLanguage, PhysicalCard
from ...models import PhysicalCardLink, UserOwnedCard, UserCardChange, DeckCard
from ...models import Deck, CardTagLink, CardTag, CardRuling, Rarity, Block
from ...models import Set, Language
from . import _query, _parse, _paths

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

        f = open(_paths.rarity_json_path, 'r', encoding="utf8")
        rarities = json.load(f, encoding='UTF-8')
        f.close()

        for r in rarities:

            obj = None
            try:
                obj = Rarity.objects.get(symbol=r['symbol'])
                obj.name = r['name']
                obj.display_order = r['display_order']

            except Rarity.DoesNotExist:
                obj = Rarity(symbol=r['symbol'], name=r['name'], display_order=r['display_order'])

            obj.save()


    def update_language_information(self):

        # print(path.abspath('languages.json'))
        f = open(_paths.language_json_path, 'r', encoding="utf8")
        languages = json.load(f, encoding='UTF-8')
        f.close()

        for lang in languages:

            obj = None
            try:
                obj = Language.objects.get(name=lang['name'])
                obj.mci_code = lang['code']

            except Language.DoesNotExist:
                obj = Language(name=lang['name'], mci_code=lang['code'])

            obj.save()

    def update_block_information(self, set_list):

        for s in set_list:

            set_data = s[1]

            # Ignore sets that have no block
            if 'block' not in set_data:
                continue

            obj = None
            try:
                obj = Block.objects.get(name=set_data['block'])

            except Block.DoesNotExist:
                obj = Block(name=set_data['block'], release_date=set_data['releaseDate'])
                obj.save()

    def update_set_information(self, set_list):

        for s in set_list:

            set_code = s[0]
            set_data = s[1]
            obj = None

            try:
                obj = Set.objects.get(code=set_code)

            except Set.DoesNotExist:

                b = Block.objects.filter(name=set_data.get('block')).first()
                obj = Set(code=set_code, name=set_data['name'], release_date=set_data['releaseDate'], block=b, mci_code=set_data.get('magicCardsInfoCode'))
                obj.save()


    def update_card_information(self, set_list):
        pass

    def update_ruling_table(self, set_list):
        pass

    def update_physical_cards(self, set_list):
        pass
