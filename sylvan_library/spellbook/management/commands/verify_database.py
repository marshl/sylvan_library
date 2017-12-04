import json
import logging
import re

from django.core.management.base import BaseCommand
from django.db import transaction

from spellbook.models import Card, CardPrinting, CardPrintingLanguage
from spellbook.models import PhysicalCard
from spellbook.models import CardRuling, Rarity, Block
from spellbook.models import Set, Language
from spellbook.management.commands import _parse, _paths, _colour


class Command(BaseCommand):
    help = 'Downloads the MtG JSON data file'

    # Keep track of which sets are new, so that printing information for existing sets doesn't have to be parsed
    new_sets = []

    # Keep track of which cards have been updated, so that reprints don't trigger pointless updates
    updated_cards = []

    def add_arguments(self, parser):

        parser.add_argument(
            '--no-transaction',
            action='store_true',
            dest='no_transaction',
            default=False,
            help='Update the database without a transaction (unsafe)',
        )

        parser.add_argument(
            '--force-update',
            action='store_true',
            dest='force_update',
            default=False,
            help='Forces an update of sets that alredy exist, and cards that have already been added',
        )


    @transaction.atomic
    def handle(self, *args, **options):

        json_data = _parse.parse_json_data()
        json_data = sorted(
            json_data.items(),
            key=lambda card_set: card_set[1]["releaseDate"])

        if options['no_transaction']:
            self.update_database(json_data)
        else:
            with(transaction.atomic()):
                self.update_database(json_data)

    def update_database(self, json_data):
        self.update_rarity_list()
        self.update_language_list()
        self.update_block_list(json_data)
        self.update_set_list(json_data)
        self.update_card_list(json_data)
        self.update_ruling_list(json_data)
        self.update_physical_card_list(json_data)
        self.update_card_links(json_data)

    def update_rarity_list(self):

        logging.info('Updating rarity list')

        f = open(_paths.rarity_json_path, 'r', encoding="utf8")
        rarities = json.load(f, encoding='UTF-8')
        f.close()

        for rarity in rarities:
            rarity_obj = Rarity.objects.filter(symbol=rarity['symbol']).first()
            if rarity_obj is not None:
                rarity_obj = Rarity.objects.get(symbol=rarity['symbol'])

                logging.info('Updating existing rarity %s', rarity_obj.name)
                rarity_obj.name = rarity['name']
                rarity_obj.display_order = rarity['display_order']
                rarity_obj.save()

            else:
                logging.info('Creating new rarity %s', rarity['name'])

                rarity_obj = Rarity(
                    symbol=rarity['symbol'],
                    name=rarity['name'],
                    display_order=rarity['display_order'])

                rarity_obj.save()

        logging.info('Rarity update complete')

    def update_language_list(self):

        logging.info('Updating language list')

        f = open(_paths.language_json_path, 'r', encoding="utf8")
        languages = json.load(f, encoding='UTF-8')
        f.close()

        for lang in languages:
            language_obj = Language.objects.filter(name=lang['name']).first()
            if language_obj is not None:
                logging.info('Updating language: %s', lang['name'])
                language_obj.mci_code = lang['code']
                language_obj.save()
            else:
                logging.info('Creating new language: %s', lang['name'])
                language_obj = Language(name=lang['name'], mci_code=lang['code'])
                language_obj.save()

        logging.info('Language update complete')

    def update_block_list(self, set_list):
        logging.info('Updating block list')

        for s in set_list:

            set_data = s[1]

            # Ignore sets that have no block
            if 'block' not in set_data:
                logging.info('Ignoring %s', set_data['name'])
                continue

            block = Block.objects.filter(name=set_data['block']).first()

            if block is not None:
                logging.info('Block %s already exists', block.name)
            else:
                block = Block(
                    name=set_data['block'],
                    release_date=set_data['releaseDate'])

                logging.info('Created block %s', block.name)
                block.save()

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

            if not Set.objects.filter(code=set_code).exists():

                logging.info('Creating set %s', set_data['name'])
                block = Block.objects.filter(name=set_data.get('block')).first()

                set_obj = Set(
                    code=set_code,
                    name=set_data['name'],
                    release_date=set_data['releaseDate'],
                    block=block,
                    mci_code=set_data.get('magicCardsInfoCode'))

                set_obj.save()
                self.new_sets.append(set_code)
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

            if set_code not in self.new_sets:
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
        card_name = self.get_card_name(card_data)
        card = Card.objects.filter(name=card_name).first()
        if card is not None:
            logging.info('Updating existing card "%s"', card)
        else:
            card = Card(name=card_name)
            logging.info('Creating new card "%s"', card)

        if card_name in self.updated_cards:
            logging.info(f'{card} has already been updated')
            return card

        self.updated_cards.append(card_name)

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
        (cnum, cnum_letter) = self.get_card_cnum(card_data, default_cnum)

        printing = CardPrinting.objects.filter(
            card_id=card_obj.id,
            set_id=set_obj.id,
            collector_number=cnum,
            collector_letter=cnum_letter).first()

        if printing is not None:
            logging.info('Updating card printing "%s"', printing)
        else:
            printing = CardPrinting(
                card=card_obj,
                set=set_obj,
                collector_number=cnum,
                collector_letter=cnum_letter)
            logging.info('Created new card printing "%s"', printing)

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
            if set_code not in self.new_sets:
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

                    ruling_obj = CardRuling.objects.filter(
                        card=card_obj,
                        text=ruling['text'],
                        date=ruling['date']).first()

                    if ruling_obj is None:
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

            if set_code not in self.new_sets:
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

    def update_physical_card(self, printlang, card_data):
        logging.info('Updating physical cards for "%s"', printlang)

        if (card_data['layout'] == 'meld' and
                    len(card_data['names']) == 3 and
                    printlang.card_printing.collector_letter == 'b'):
            logging.info('Will not create card link for meld card "%s',
                         printlang)

            return

        if (printlang.physical_cards.exists()):
            logging.info('Physical link already exists for "%s"',
                         printlang)
            return

        linked_language_objs = []

        cp = printlang.card_printing

        if 'names' in card_data:

            for link_name in card_data['names']:

                if link_name == card_data['name']:
                    continue

                link_card = Card.objects.get(name=link_name)
                link_print = CardPrinting.objects.filter(
                    card=link_card,
                    set=cp.set).first()
                if link_print is None:
                    logging.error(f'Printing for link {link_card} in set {cp.set} not found')
                    raise LookupError()

                if (card_data['layout'] == 'meld' and
                            printlang.card_printing.collector_letter != 'b' and
                            link_print.collector_letter != 'b'):
                    logging.info('Won''t link %s to %s as they separate cards',
                                 card_data['name'], link_card.name)

                    continue

                link_print_lang = CardPrintingLanguage.objects.get(
                    card_printing=link_print,
                    language=printlang.language)

                linked_language_objs.append(link_print_lang)

        physical_card = PhysicalCard(layout=card_data['layout'])
        physical_card.save()

        linked_language_objs.append(printlang)

        for link_lang in linked_language_objs:
            link_lang.physical_cards.add(physical_card)

    def update_card_links(self, set_list):
        for s in set_list:

            set_code = s[0]
            set_data = s[1]

            if set_code not in self.new_sets:
                logging.info('Skipping set "%s"', set_data['name'])
                continue

            cards = set_data['cards']

            for card_data in [x for x in cards if 'names' in x]:

                card_name = self.get_card_name(card_data)
                card_obj = Card.objects.get(name=card_name)

                logging.info('Finding card links for {0}'.format(card_name))

                links = card_data['names']

                for link_name in [x for x in links if x != card_name]:

                    # B.F.M. has the same name for both cards, so the link_name has to be manually set
                    if card_name == 'B.F.M. (Big Furry Monster) (left)':
                        link_name = 'B.F.M. (Big Furry Monster) (right)'
                    elif card_name == 'B.F.M. (Big Furry Monster) (right)':
                        link_name = 'B.F.M. (Big Furry Monster) (left)'

                    link_card = Card.objects.get(name=link_name)

                    card_obj.links.add(link_card)
                    card_obj.save()

    def get_card_name(self, card_data):
        # B.F.M. has the same name for both "cards", so we rely on the image name to separate the two
        if card_data['name'] == 'B.F.M. (Big Furry Monster)':
            if card_data['imageName'] == "b.f.m. 1":
                return 'B.F.M. (Big Furry Monster) (left)'
            elif card_data['imageName'] == "b.f.m. 2":
                return 'B.F.M. (Big Furry Monster) (right)'

        return card_data['name']

    def get_card_cnum(self, card_data, default_cnum):
        if 'number' not in card_data:
            return (default_cnum, None)
        cnum_match = re.search(
            '^(?P<special>[\D]+)?(?P<number>[\d]+)(?P<letter>[\D]+)?$',
            card_data['number'])

        cnum = cnum_match.group('number')
        cnum_letter = (
            cnum_match.group('special') or
            cnum_match.group('letter'))

        return (cnum, cnum_letter)
