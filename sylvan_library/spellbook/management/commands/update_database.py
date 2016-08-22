from django.core.management.base import BaseCommand
import json
from os import path
import zipfile
import json
import requests
import re
import queue
import threading
import pprint

from ...models import Card, CardPrinting, CardPrintingLanguage, PhysicalCard
from ...models import PhysicalCardLink, UserOwnedCard, UserCardChange, DeckCard
from ...models import Deck, CardTagLink, CardTag, CardRuling, Rarity, Block
from ...models import Set, Language
from . import _query, _parse, _paths, _colour

class Command(BaseCommand):
    help = 'Downloads the MtG JSON data file'

    def handle(self, *args, **options):

        json_data = _parse.parse_json_data()
        json_data = sorted(json_data.items(),
                       key=lambda card_set: card_set[1]["releaseDate"])

        self.update_rarity_table()
        self.update_language_table()
        self.update_block_table(json_data)
        self.update_set_table(json_data)
        self.update_card_table(json_data)
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


    def update_language_table(self):

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

    def update_block_table(self, set_list):

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

    def update_set_table(self, set_list):

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


    def update_card_table(self, set_list):

        for s in set_list:

            set_code = s[0]
            set_data = s[1]

            default_cnum = 0

            set_obj = Set.objects.get(code=set_code)

            for card_data in set_data['cards']:
                default_cnum += 1
                card_obj = self.update_card(card_data)
                printing_obj = self.update_card_printing(card_obj, set_obj, card_data, default_cnum)

                english = {'language': 'English', 'name': card_data['name'], 'multiverseid': card_data.get('multiverseid')}
                cardlang_obj = self.update_card_printing_language(printing_obj, english)

                if 'foreignNames' in set_data:
                    for lang in set_data.get('foreignNames'):
                        cardlang_obj = self.update_card_printing_language(printing_obj, lang)

    def update_card(self, card_data):

        card = None

        try:
            card = Card.objects.get(name=card_data['name'])

        except Card.DoesNotExist:

            card = Card(name=card_data['name'])

        card.cost = card_data.get('manaCost')
        card.cmc = card_data.get('cmc') or 0
        card.colour = 0
        if 'colors' in card_data:
            card.card_colour = _colour.get_colour_flags_from_names(card_data['colors'])

        card.colour_identity = 0
        if 'colourIdentity' in card_data:
            card.colour_identity = _colour.get_colour_flags_from_codes(card_data['colorIdentity'])

        card.colour_count = bin(card.colour).count('1')

        card.power = card_data.get('power')
        card.toughness = card_data.get('toughness')
        card.num_power = 0
        if 'power' in card_data:
            card.num_power = self.convert_to_number(card_data['power'])

        card.num_toughness = 0
        if 'toughness' in card_data:
            card.num_toughness = self.convert_to_number(card_data['toughness'])

        card.loyalty = card_data.get('loyalty')
        card.num_loyalty = 0
        if 'loyalty' in card_data:
            card.num_loyalty = self.convert_to_number(card_data['loyalty'])

        if 'types' in card_data:
            card.type = ' '.join(card_data['types'])

        if 'subtypes' in card_data:
            card.subtype = ' '.join(card_data['subtypes'])

        card.rules_text = card_data.get('text')

        card.save()

        return card

    def update_card_printing(self, card_obj, set_obj, card_data, default_cnum):

        printing = None

        cnum = None
        cnum_letter = None

        if 'number' in card_data:
            cnum_match = re.search('^(?P<special>[\D]+)?(?P<number>[\d]+)(?P<letter>[\D]+)?$',
                                   card_data['number'])

            cnum = cnum_match.group('number')
            cnum_letter = cnum_match.group('special') or cnum_match.group('letter')

        else:
            cnum = default_cnum

        try:
            printing = CardPrinting.objects.get(card=card_obj, set=set_obj, collector_number=cnum, collector_letter=cnum_letter)

        except CardPrinting.DoesNotExist:
            printing = CardPrinting(card=card_obj, set=set_obj, collector_number=cnum, collector_letter=cnum_letter)

        printing.artist = card_data['artist']

        rarity_name = 'Timeshifted' if card_data['rarity'] == 'timeshifted' else card_data['rarity']
        printing.rarity = Rarity.objects.get(name=rarity_name)

        printing.flavour_text = card_data.get('flavor')
        printing.original_text = card_data.get('originalText')
        printing.original_type = card_data.get('originalType')

        if 'mciNumber' in card_data:
            mci_match = re.search('^(/(?P<setcode>[^/]*)/(?P<language>[^/]*)/)?(?P<number>[0-9]+)(\.html)?$', card_data['mciNumber'])

            if mci_match and 'number' not in card_data:
                printing.mci_number = mci_match.group('number')

        printing.save()

        return printing

    def update_card_printing_language(self, printing_obj, lang):

        lang_obj = Language.objects.get(name=lang['language'])
        # print(printing_obj)

        try:
            cardlang = CardPrintingLanguage.objects.get(card_printing=printing_obj, language=lang_obj)

        except CardPrintingLanguage.DoesNotExist:
            cardlang = CardPrintingLanguage(card_printing=printing_obj, language=lang_obj)

        cardlang.multiverse_id = lang.get('multiverseid')
        cardlang.card_name = lang['name']

        cardlang.save()

        return cardlang

    def convert_to_number(self, val):
        match = re.search('([\d.]+)', str(val))
        if match:
            return match.group()

        return 0

    def update_ruling_table(self, set_list):
        pass

    def update_physical_cards(self, set_list):
        pass
