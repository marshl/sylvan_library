import json
import logging
import re

from django.core.management.base import BaseCommand

from ...models import Card, CardPrinting, CardPrintingLanguage, PhysicalCard
from ...models import PhysicalCardLink
from ...models import CardRuling, Rarity, Block
from ...models import Set, Language
from . import _parse, _paths, _colour


class Command(BaseCommand):
    help = 'Downloads the MtG JSON data file'

    def handle(self, *args, **options):

        json_data = _parse.parse_json_data()
        json_data = sorted(
           json_data.items(),
           key=lambda card_set: card_set[1]["releaseDate"])

        self.update_rarity_list()
        self.update_language_list()
        self.update_block_list(json_data)
        self.update_set_list(json_data)
        self.update_card_list(json_data)
        self.update_ruling_list(json_data)
        self.update_physical_card_list(json_data)

    def update_rarity_list(self):

        logging.info('Updating rarity list')

        f = open(_paths.rarity_json_path, 'r', encoding="utf8")
        rarities = json.load(f, encoding='UTF-8')
        f.close()

        for r in rarities:

            obj = None
            try:

                obj = Rarity.objects.get(symbol=r['symbol'])

                logging.info('Updating rarity %s', obj.name)
                obj.name = r['name']
                obj.display_order = r['display_order']

            except Rarity.DoesNotExist:
                logging.info('Creating new rarity %s', r['name'])

                obj = Rarity(
                     symbol=r['symbol'],
                     name=r['name'],
                     display_order=r['display_order'])

            obj.save()

        logging.info('Rarity update complete')

    def update_language_list(self):

        logging.info('Updating language list')

        f = open(_paths.language_json_path, 'r', encoding="utf8")
        languages = json.load(f, encoding='UTF-8')
        f.close()

        for lang in languages:

            obj = None
            try:
                obj = Language.objects.get(name=lang['name'])
                logging.info('Updating language: %s', lang['name'])
                obj.mci_code = lang['code']

            except Language.DoesNotExist:
                logging.info('Creating new language: %s', lang['name'])
                obj = Language(name=lang['name'], mci_code=lang['code'])

            obj.save()

        logging.info('Language update complete')

    def update_block_list(self, set_list):

        logging.info('Updating block list')

        for s in set_list:

            set_data = s[1]

            # Ignore sets that have no block
            if 'block' not in set_data:
                logging.info('Ignoring %s', set_data['name'])
                continue

            obj = None
            try:
                obj = Block.objects.get(name=set_data['block'])
                logging.info('Block %s already exists', obj.name)

            except Block.DoesNotExist:
                obj = Block(
                    name=set_data['block'],
                    release_date=set_data['releaseDate'])

                logging.info('Created block %s', obj.name)
                obj.save()

        logging.info('BLock list updated')

    def update_set_list(self, set_list):

        logging.info('Updating set list')

        for s in set_list:

            set_code = s[0]
            set_data = s[1]

            # Skip sets that start with 'p' (e.g. pPRE Prerelease Events)
            if set_code[0] == 'p':
                logging.info('Ignoring set %s', set_data['name'])
                continue

            set_obj = None

            if not Set.objects.filter(code=set_code).exists():

                logging.info('Creating set %s', set_data['name'])
                b = Block.objects.filter(name=set_data.get('block')).first()

                set_obj = Set(
                  code=set_code,
                  name=set_data['name'],
                  release_date=set_data['releaseDate'],
                  block=b,
                  mci_code=set_data.get('magicCardsInfoCode'))

                set_obj.save()
            else:
                logging.info('Set %s already exists, no changes made',
                             set_data['name'])

        logging.info('Set list updated')

    def update_card_list(self, set_list):

        logging.info('Updating card list')

        for s in set_list:

            set_code = s[0]
            set_data = s[1]
            default_cnum = 0

            if not Set.objects.filter(code=set_code).exists():
                logging.info('Ignoring set "%s"', set_data['name'])
                continue

            logging.info('Updating cards in set "%s"', set_data['name'])

            set_obj = Set.objects.get(code=set_code)

            for card_data in set_data['cards']:
                default_cnum += 1
                card_obj = self.update_card(card_data)
                printing_obj = self.update_card_printing(
                                card_obj,
                                set_obj,
                                card_data,
                                default_cnum)

                english = {
                    'language': 'English',
                    'name': self.get_card_name(card_data),
                    'multiverseid': card_data.get('multiverseid')
                }

                self.update_card_printing_language(printing_obj, english)

                if 'foreignNames' in card_data:

                    for lang in card_data['foreignNames']:

                        self.update_card_printing_language(printing_obj, lang)

        logging.info('Card list updated')

    def update_card(self, card_data):

        card = None
        card_name = self.get_card_name(card_data)

        try:
            card = Card.objects.get(name=card_name)
            logging.info('Updating existing card "%s"', card)

        except Card.DoesNotExist:
            card = Card(name=card_name)
            logging.info('Creating new card "%s"', card)

        card.cost = card_data.get('manaCost')
        card.cmc = card_data.get('cmc') or 0

        if 'colors' in card_data:
            card.colour = _colour.get_colour_flags_from_names(
                                   card_data['colors'])
        else:
            card.colour = 0

        card.colour_identity = 0
        if 'colourIdentity' in card_data:
            card.colour_identity = _colour.get_colour_flags_from_codes(
                                            card_data['colorIdentity'])
        else:
            card.colour_identity = 0

        card.colour_count = bin(card.colour).count('1')

        card.power = card_data.get('power')
        card.toughness = card_data.get('toughness')

        if 'power' in card_data:
            card.num_power = self.convert_to_number(card_data['power'])
        else:
            card.num_power = 0

        if 'toughness' in card_data:
            card.num_toughness = self.convert_to_number(card_data['toughness'])
        else:
            card.num_toughness = 0

        card.loyalty = card_data.get('loyalty')

        if 'loyalty' in card_data:
            card.num_loyalty = self.convert_to_number(card_data['loyalty'])
        else:
            card.num_loyalty = 0

        if 'types' in card_data:

            types = (card_data.get('supertypes') or []) + \
                    (card_data['types'] or [])
            card.type = ' '.join(types)
        else:
            card.type = None

        if 'subtypes' in card_data:
            card.subtype = ' '.join(card_data.get('subtypes'))
        else:
            card.subtype = None

        card.rules_text = card_data.get('text')

        card.save()

        return card

    def update_card_printing(self, card_obj, set_obj, card_data, default_cnum):

        printing = None

        (cnum, cnum_letter) = self.get_card_cnum(card_data, default_cnum)

        try:
            printing = CardPrinting.objects.get(
                        card_id=card_obj.id,
                        set_id=set_obj.id,
                        collector_number=cnum,
                        collector_letter=cnum_letter)
            logging.info('Updating card printing "%s"', printing)

        except CardPrinting.DoesNotExist:

            printing = CardPrinting(
                            card=card_obj,
                            set=set_obj,
                            collector_number=cnum,
                            collector_letter=cnum_letter)
            logging.info('Created new card priting "%s"', printing)

        printing.artist = card_data['artist']

        rarity_name = card_data['rarity']
        if 'timeshifted' in card_data and card_data['timeshifted']:
            rarity_name = 'Timeshifted'

        printing.rarity = Rarity.objects.get(name=rarity_name)

        printing.flavour_text = card_data.get('flavor')
        printing.original_text = card_data.get('originalText')
        printing.original_type = card_data.get('originalType')

        if 'mciNumber' in card_data:
            mci_match = re.search(
              '^(/(?P<set>[^/]*)/(?P<lang>[^/]*)/)?(?P<num>[0-9]+)(\.html)?$',
              card_data['mciNumber'])

            if mci_match and 'num' not in card_data:
                printing.mci_number = mci_match.group('num')

        printing.save()

        return printing

    def update_card_printing_language(self, printing_obj, lang):

        lang_obj = Language.objects.get(name=lang['language'])

        cardlang = CardPrintingLanguage.objects.filter(
                                           card_printing_id=printing_obj.id,
                                           language_id=lang_obj.id).first()

        if cardlang is not None:
            logging.info('Card printing language "%s" already exists',
                         cardlang)
            return cardlang

        cardlang = CardPrintingLanguage(
                    card_printing=printing_obj,
                    language=lang_obj,
                    card_name=lang['name'],
                    multiverse_id=lang.get('multiverseid'))

        logging.info('Created new printing language "%s"', cardlang)

        cardlang.save()

        return cardlang

    def convert_to_number(self, val):
        match = re.search('([\d.]+)', str(val))
        if match:
            return match.group()

        return 0

    def update_ruling_list(self, set_list):

        logging.info('Updating card rulings')
        CardRuling.objects.all().delete()

        for s in set_list:

            set_code = s[0]
            set_data = s[1]
            if not Set.objects.filter(code=set_code).exists():
                logging.info('Ignoring set "%s"', set_data['name'])
                continue

            logging.info('Updating rulings in "%s"', set_data['name'])

            for card_data in set_data['cards']:

                if 'rulings' not in card_data:
                    continue

                card_name = self.get_card_name(card_data)
                card_obj = Card.objects.get(name=card_name)

                logging.info('Updating rulings for "%s"', card_name)

                for ruling in card_data['rulings']:

                    try:
                        ruling_obj = CardRuling.objects.get(
                                        card=card_obj,
                                        text=ruling['text'],
                                        date=ruling['date'])

                    except CardRuling.DoesNotExist:
                        ruling_obj = CardRuling(
                                        card=card_obj,
                                        text=ruling['text'],
                                        date=ruling['date'])
                        ruling_obj.save()

        logging.info('Card rulings updated')

    def update_physical_card_list(self, set_list):

        logging.info('Updating physical card list')

        for s in set_list:

            set_code = s[0]
            set_data = s[1]

            if not Set.objects.filter(code=set_code).exists():
                logging.info('Skipping set "%s"', set_data['name'])
                continue

            set_obj = Set.objects.get(code=set_code)

            default_cnum = 0

            for card_data in set_data['cards']:

                card_name = self.get_card_name(card_data)

                logging.info('Updating physical cards for %s', card_name)
                card_obj = Card.objects.get(name=card_name)

                default_cnum += 1

                (cnum, cnum_letter) = self.get_card_cnum(
                                         card_data,
                                         default_cnum)

                printing_obj = CardPrinting.objects.get(
                                    card=card_obj,
                                    set=set_obj,
                                    collector_number=cnum,
                                    collector_letter=cnum_letter)

                lang_obj = Language.objects.get(name='English')
                printlang_obj = CardPrintingLanguage.objects.get(
                                     card_printing=printing_obj,
                                     language=lang_obj)

                self.update_physical_card(printlang_obj, card_data)

                if 'foreignNames' in card_data:

                    for card_language in card_data['foreignNames']:

                        lang_obj = Language.objects.get(
                                        name=card_language['language'])

                        printlang_obj = CardPrintingLanguage.objects.get(
                                             card_printing=printing_obj,
                                             language=lang_obj)

                        self.update_physical_card(printlang_obj, card_data)

    def update_physical_card(self, printlang_obj, card_data):

        logging.info('Updating physical cards for "%s"', printlang_obj)

        if (card_data['layout'] == 'meld' and
                len(card_data['names']) == 3 and
                printlang_obj.card_printing.collector_letter == 'b'):

            logging.info('Will not create card link for meld card "%s',
                         printlang_obj)

            return

        if (PhysicalCardLink.objects.filter(printing_language=printlang_obj)
           .exists()):
            logging.info('Physical link already exists for "%s"',
                         printlang_obj)

            return

        linked_language_objs = []

        if 'names' in card_data:

            for link_name in card_data['names']:

                if link_name == card_data['name']:
                    continue

                link_card = Card.objects.get(name=link_name)
                link_print = CardPrinting.objects.get(
                                  card=link_card,
                                  set=printlang_obj.card_printing.set)

                if (card_data['layout'] == 'meld' and
                        printlang_obj.card_printing.collector_letter != 'b' and
                        link_print.collector_letter != 'b'):

                    logging.info('Won''t link %s to %s as they separate cards',
                                 card_data['name'], link_card.name)

                    continue

                link_print_lang = CardPrintingLanguage.objects.get(
                                       card_printing=link_print,
                                       language=printlang_obj.language)

                linked_language_objs.append(link_print_lang)

        physical_card = PhysicalCard(layout=card_data['layout'])
        physical_card.save()

        linked_language_objs.append(printlang_obj)

        for link_lang in linked_language_objs:
            link_obj = PhysicalCardLink(
                            printing_language=link_lang,
                            physical_card=physical_card)

            link_obj.save()

    def get_card_name(self, card_data):
        if card_data['name'] == 'B.F.M. (Big Furry Monster)':
            if 'cmc' in card_data:
                return 'B.F.M. (Big Furry Monster) (right)'
            else:
                return 'B.F.M. (Big Furry Monster) (left)'

        return card_data['name']

    def get_card_cnum(self, card_data, default_cnum):

        if 'number' in card_data:
            cnum_match = re.search(
               '^(?P<special>[\D]+)?(?P<number>[\d]+)(?P<letter>[\D]+)?$',
               card_data['number'])

            cnum = cnum_match.group('number')
            cnum_letter = (
               cnum_match.group('special') or
               cnum_match.group('letter'))

            return (cnum, cnum_letter)

        else:
            return (default_cnum, None)
