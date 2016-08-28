from django.core.management.base import BaseCommand

import json
import re

from ...models import Card, CardPrinting, CardPrintingLanguage, PhysicalCard
from ...models import PhysicalCardLink
from ...models import CardRuling, Rarity, Block
from ...models import Set, Language
from . import _parse, _paths, _colour

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

            # Skip sets that start with 'p' (e.g. pPRE Prerelease Events)
            if set_code[0] == 'p':
                continue

            set_data = s[1]
            set_obj = None

            if not Set.objects.filter(code=set_code).exists():

                b = Block.objects.filter(name=set_data.get('block')).first()
                set_obj = Set(code=set_code, name=set_data['name'], release_date=set_data['releaseDate'], block=b, mci_code=set_data.get('magicCardsInfoCode'))
                set_obj.save()


    def update_card_table(self, set_list):

        for s in set_list:

            set_code = s[0]
            set_data = s[1]

            default_cnum = 0

            if not Set.objects.filter(code=set_code).exists():
                continue

            set_obj = Set.objects.get(code=set_code)

            for card_data in set_data['cards']:
                default_cnum += 1
                card_obj = self.update_card(card_data)
                printing_obj = self.update_card_printing(card_obj, set_obj, card_data, default_cnum)

                english = {'language': 'English', 'name': card_data['name'], 'multiverseid': card_data.get('multiverseid')}
                self.update_card_printing_language(printing_obj, english)

                if 'foreignNames' in card_data:

                    for lang in card_data['foreignNames']:

                        self.update_card_printing_language(printing_obj, lang)

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

        (cnum, cnum_letter) = self.get_card_cnum(card_data, default_cnum)

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

        CardRuling.objects.all().delete()

        for s in set_list:

            set_code = s[0]
            if not Set.objects.filter(code=set_code).exists():
                continue

            set_data = s[1]

            for card_data in set_data['cards']:

                if 'rulings' not in card_data:
                    continue

                card_obj = Card.objects.get(name=card_data['name'])

                for ruling in card_data['rulings']:

                    try:
                        ruling_obj = CardRuling.objects.get(card=card_obj, text=ruling['text'], date=ruling['date'])

                    except CardRuling.DoesNotExist:
                        ruling_obj = CardRuling(card=card_obj, text=ruling['text'], date=ruling['date'])
                        ruling_obj.save()

    def update_physical_cards(self, set_list):

        for s in set_list:

            set_code = s[0]
            set_data = s[1]

            if not Set.objects.filter(code=set_code).exists():
                continue

            set_obj = Set.objects.get(code=set_code)

            default_cnum = 0

            for card_data in set_data['cards']:
                default_cnum += 1

                (cnum, cnum_letter) = self.get_card_cnum(card_data, default_cnum)

                card_obj = Card.objects.get(name=card_data['name'])
                assert(card_obj is not None)
                printing_obj = CardPrinting.objects.get(card=card_obj, set=set_obj, collector_number=cnum, collector_letter=cnum_letter)

                lang_obj = Language.objects.get(name='English')
                printlang_obj = CardPrintingLanguage.objects.get(card_printing=printing_obj, language=lang_obj)
                self.update_physical_card(printlang_obj, card_data)

                if 'foreignNames' in card_data and False:

                    for card_language in card_data['foreignNames']:

                        lang_obj = Language.objects.get(name=card_language['language'])
                        printlang_obj = CardPrintingLanguage.objects.get(card_printing=printing_obj, language=lang_obj)
                        self.update_physical_card(printlang_obj, card_data)

    def update_physical_card(self, printlang_obj, card_data):

        if card_data['layout'] == 'meld' and len(card_data['names']) == 3 and printlang_obj.card_printing.collector_letter == 'b':
            print(('Will not create card link for ' + printlang_obj.card_name).encode('utf-8'))
            return

        if PhysicalCardLink.objects.filter(printing_language=printlang_obj).exists():
            print('Physical link already exists for ' + printlang_obj.card_name)
            return

        linked_language_objs = []

        if 'names' in card_data:

            for link_name in card_data['names']:

                if link_name == card_data['name']:
                    continue

                link_card = Card.objects.get(name=link_name)

                print('Link: ' + link_name + ' cnum ' + card_data['number'])

                link_print = CardPrinting.objects.get(card=link_card,
                                                      set=printlang_obj.card_printing.set)

                if card_data['layout'] == 'meld' and printlang_obj.card_printing.collector_letter != 'b' and link_print.collector_letter != 'b':
                    print('Will not link ' + card_data['name'] + ' to ' + link_card.name + ' as they separate cards')
                    continue

                link_print_lang = CardPrintingLanguage.objects.get(card_printing=link_print, language=printlang_obj.language)

                linked_language_objs.append(link_print_lang)

        physical_card = PhysicalCard(layout=card_data['layout'])
        physical_card.save()

        linked_language_objs.append(printlang_obj)

        for link_lang in linked_language_objs:
            print('Linking ' + link_lang.card_name + ' to ' + printlang_obj.card_name)
            link_obj = PhysicalCardLink(printing_language=link_lang, physical_card=physical_card)
            link_obj.save()
            print('Link ID ' + str(link_obj.id))

    def get_card_cnum(self, card_data, default_cnum):

        if 'number' in card_data:
            cnum_match = re.search('^(?P<special>[\D]+)?(?P<number>[\d]+)(?P<letter>[\D]+)?$',
                                   card_data['number'])

            cnum = cnum_match.group('number')
            cnum_letter = cnum_match.group('special') or cnum_match.group('letter')

            return (cnum, cnum_letter)

        else:
            return (default_cnum, None)

