import logging

from django.core.management.base import BaseCommand
from django.db import transaction

from cards.models import *
from data_import.importers import *


class Command(BaseCommand):
    help = 'Downloads the MtG JSON data file'

    # Keep track of which sets are new, so that printing information for existing sets doesn't have to be parsed
    sets_to_update = []

    # Keep track of which cards have been updated, so that reprints don't trigger pointless updates
    updated_cards = []

    force_update = False

    def add_arguments(self, parser):

        parser.add_argument(
            '--no-transaction',
            action='store_true',
            dest='no_transaction',
            default=False,
            help='Update the database without a transaction (unsafe)',
        )

        parser.add_argument(
            '--update-all',
            action='store_true',
            dest='force_update',
            default=False,
            help='Forces an update of sets that already exist, and cards that have already been added',
        )

        parser.add_argument(
            '--update-set',
            dest='force_update_sets',
            nargs='*',
            help='Forces an update of the given sets'
        )

    def handle(self, *args, **options):

        importer = JsonImporter()
        importer.import_data()

        if options['force_update_sets']:
            self.sets_to_update += options['force_update_sets']

        self.force_update = options['force_update']

        if options['no_transaction']:
            self.update_database(importer)
        else:
            with(transaction.atomic()):
                self.update_database(importer)

    def update_database(self, data_importer):
        self.update_rarity_list(data_importer)
        self.update_language_list(data_importer)

        staged_sets = data_importer.get_staged_sets()

        self.update_block_list(staged_sets)
        self.update_set_list(staged_sets)
        self.update_card_list(staged_sets)
        self.update_ruling_list(staged_sets)
        self.update_physical_card_list(staged_sets)
        self.update_card_links(staged_sets)
        self.update_legalities(staged_sets)

    def update_rarity_list(self, data_importer):

        logging.info('Updating rarity list')

        for rarity in data_importer.import_rarities():
            rarity_obj = Rarity.objects.filter(symbol=rarity['symbol']).first()
            if rarity_obj is not None:
                logging.info(f'Updating existing rarity {rarity_obj.name}', )
                rarity_obj.name = rarity['name']
                rarity_obj.display_order = rarity['display_order']
                rarity_obj.save()

            else:
                logging.info(f"Creating new rarity {rarity['name']}")

                rarity_obj = Rarity(
                    symbol=rarity['symbol'],
                    name=rarity['name'],
                    display_order=rarity['display_order'])

                rarity_obj.save()

        logging.info('Rarity update complete')

    def update_language_list(self, data_importer):

        logging.info('Updating language list')

        for lang in data_importer.import_languages():
            language_obj = Language.objects.filter(name=lang['name']).first()
            if language_obj is not None:
                logging.info(f"Updating language: {lang['name']}", )
                language_obj.mci_code = lang['code']
                language_obj.save()
            else:
                logging.info(f"Creating new language: {lang['name']}")
                language_obj = Language(name=lang['name'], mci_code=lang['code'])
                language_obj.save()

        logging.info('Language update complete')

    def update_block_list(self, staged_sets):
        logging.info('Updating block list')

        for staged_set in staged_sets:

            # Ignore sets that have no block
            if not staged_set.has_block():
                logging.info(f'Ignoring {staged_set.get_name()}')
                continue

            block = Block.objects.filter(name=staged_set.get_block()).first()

            if block is not None:
                logging.info(f'Block {block.name} already exists')
            else:
                block = Block(
                    name=staged_set.get_block(),
                    release_date=staged_set.get_release_date())

                logging.info(f'Created block {block.name}')
                block.save()

        logging.info('Block list updated')

    def update_set_list(self, staged_sets):
        logging.info('Updating set list')

        for s in staged_sets:

            # Skip sets that start with 'p' (e.g. pPRE Prerelease Events)
            if s.get_code()[0] == 'p':
                logging.info(f'Ignoring set {s.get_name()}')
                continue

            set_obj = Set.objects.filter(code=s.get_code()).first()

            if set_obj is None:

                logging.info(f'Creating set {s.get_name()}')
                block = Block.objects.filter(name=s.get_block()).first()

                set_obj = Set(
                    code=s.get_code(),
                    name=s.get_name(),
                    release_date=s.get_release_date(),
                    block=block,
                    mci_code=s.get_mci_code(),
                    border_colour=s.get_border_colour())

                set_obj.save()
                self.sets_to_update.append(s.get_code())
            else:
                logging.info(f'Set {s.get_name()} already exists, updating')

                set_obj.border_colour = s.get_border_colour()
                set_obj.save()

                if self.force_update:  # use the set anyway during a force update
                    self.sets_to_update.append(s.get_code())
        logging.info('Set list updated')

    def update_card_list(self, staged_sets):
        logging.info('Updating card list')

        for staged_set in staged_sets:

            if staged_set.get_code() not in self.sets_to_update:
                logging.info(f'Ignoring set {staged_set.get_name()}')
                continue

            print(f'Updating cards in set {staged_set.get_name()}')
            logging.info(f'Updating cards in set {staged_set.get_name()}')

            set_obj = Set.objects.get(code=staged_set.get_code())

            default_collector_number = 1

            for staged_card in staged_set.get_cards():
                if staged_card.get_collector_number() is None:
                    staged_card.set_collector_number(default_collector_number)

                default_collector_number = staged_card.get_collector_number() + 1

                card_obj = self.update_card(staged_card)

                printing_obj = self.update_card_printing(
                    card_obj,
                    set_obj,
                    staged_card)

                english = {
                    'language': 'English',
                    'name': staged_card.get_name(),
                    'multiverseid': staged_card.get_multiverse_id()
                }

                self.update_card_printing_language(printing_obj, english)

                if staged_card.has_foreign_names():
                    for lang in staged_card.get_foreign_names():
                        self.update_card_printing_language(printing_obj, lang)

        logging.info('Card list updated')

    def update_card(self, staged_card: StagedCard):
        card = Card.objects.filter(name=staged_card.get_name()).first()
        if card is not None:
            logging.info(f'Updating existing card {card}')
        else:
            card = Card(name=staged_card.get_name())
            logging.info(f'Creating new card {card}')

        if not self.force_update and staged_card.get_name() in self.updated_cards:
            logging.info(f'{card} has already been updated')
            return card

        self.updated_cards.append(staged_card.get_name())

        card.cost = staged_card.get_mana_cost()
        card.cmc = staged_card.get_cmc()
        card.colour = staged_card.get_colour()
        card.colour_identity = staged_card.get_colour_identity()
        card.colour_count = staged_card.get_colour_count()
        card.power = staged_card.get_power()
        card.toughness = staged_card.get_toughness()
        card.num_power = staged_card.get_num_power()
        card.num_toughness = staged_card.get_num_toughness()
        card.loyalty = staged_card.get_loyalty()
        card.num_loyalty = staged_card.get_num_loyalty()
        card.type = staged_card.get_types()
        card.subtype = staged_card.get_subtypes()
        card.rules_text = staged_card.get_rules_text()
        card.layout = staged_card.get_layout()
        card.original_text = staged_card.get_original_text()

        card.save()
        return card

    def update_card_printing(self, card_obj: Card, set_obj: Set, staged_card: StagedCard):

        printing = CardPrinting.objects.filter(
            card=card_obj,
            set=set_obj,
            collector_number=staged_card.get_collector_number(),
            collector_letter=staged_card.get_collector_letter()).first()

        if printing is not None:
            logging.info(f'Updating card printing {printing}')
        else:
            printing = CardPrinting(
                card=card_obj,
                set=set_obj,
                collector_number=staged_card.get_collector_number(),
                collector_letter=staged_card.get_collector_letter())
            logging.info(f'Created new card printing {printing}')

        printing.artist = staged_card.get_artist()
        printing.rarity = Rarity.objects.get(name=staged_card.get_rarity_name())

        printing.flavour_text = staged_card.get_flavour_text()
        printing.original_text = staged_card.get_original_text()
        printing.original_type = staged_card.get_original_type()
        printing.mci_number = staged_card.get_mci_number()
        printing.json_id = staged_card.get_json_id()

        printing.save()

        return printing

    def update_card_printing_language(self, printing_obj, lang):
        lang_obj = Language.objects.get(name=lang['language'])

        cardlang = CardPrintingLanguage.objects.filter(
            card_printing_id=printing_obj.id,
            language_id=lang_obj.id).first()

        if cardlang is not None:
            logging.info(f'Card printing language {cardlang} already exists')
            return cardlang

        cardlang = CardPrintingLanguage(
            card_printing=printing_obj,
            language=lang_obj,
            card_name=lang['name'],
            multiverse_id=lang.get('multiverseid'))

        logging.info(f'Created new printing language {cardlang}', )
        cardlang.save()
        return cardlang

    def update_ruling_list(self, staged_sets):
        logging.info('Updating card rulings')
        CardRuling.objects.all().delete()

        for staged_set in staged_sets:

            if staged_set.get_code() not in self.sets_to_update:
                logging.info(f'Ignoring set {staged_set.get_name()}', )
                continue

            print(f'Updating rulings in {staged_set.get_name()}', )
            logging.info(f'Updating rulings in {staged_set.get_name()}', )

            for staged_card in staged_set.get_cards():

                if not staged_card.has_rulings():
                    continue

                card_obj = Card.objects.get(name=staged_card.get_name())
                logging.info(f'Updating rulings for {staged_card.get_name()}', )

                for ruling in staged_card.get_rulings():

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

    def update_physical_card_list(self, staged_sets):
        logging.info('Updating physical card list')

        for staged_set in staged_sets:

            if staged_set.get_code() not in self.sets_to_update:
                logging.info(f'Skipping set {staged_set.get_name()}')
                continue

            set_obj = Set.objects.get(code=staged_set.get_code())

            print(f'Updating physical cards for {set_obj}')

            for staged_card in staged_set.get_cards():
                card_obj = Card.objects.get(name=staged_card.get_name())

                printing_obj = CardPrinting.objects.get(
                    card=card_obj,
                    set=set_obj,
                    collector_number=staged_card.get_collector_number(),
                    collector_letter=staged_card.get_collector_letter())

                lang_obj = Language.objects.get(name='English')
                printlang_obj = CardPrintingLanguage.objects.get(
                    card_printing=printing_obj,
                    language=lang_obj)

                self.update_physical_card(printlang_obj, staged_card)

                if staged_card.has_foreign_names():
                    for card_language in staged_card.get_foreign_names():
                        lang_obj = Language.objects.get(
                            name=card_language['language'])

                        printlang_obj = CardPrintingLanguage.objects.get(
                            card_printing=printing_obj,
                            language=lang_obj)

                        self.update_physical_card(printlang_obj, staged_card)

    def update_physical_card(self, printlang: CardPrintingLanguage, staged_card: StagedCard):

        logging.info(f'Updating physical cards for {printlang}')

        if (staged_card.get_layout() == 'meld' and
                    staged_card.get_name_count() == 3 and
                    printlang.card_printing.collector_letter == 'b'):
            logging.info(f'Will not create card link for meld card {printlang}')

            return

        if printlang.physical_cards.exists():
            logging.info(f'Physical link already exists for {printlang}')
            return

        linked_language_objs = []

        cp = printlang.card_printing

        if staged_card.has_other_names():

            for link_name in staged_card.get_other_names():

                link_card = Card.objects.get(name=link_name)
                link_print = CardPrinting.objects.filter(
                    card=link_card,
                    set=cp.set).first()
                if link_print is None:
                    logging.error(f'Printing for link {link_card} in set {cp.set} not found')
                    raise LookupError()

                if (staged_card.get_layout() == 'meld' and
                            printlang.card_printing.collector_letter != 'b' and
                            link_print.collector_letter != 'b'):
                    logging.warning(
                        f'Will not link {staged_card.get_name()} to {link_card.get_name()} as they separate cards')

                    continue

                link_print_lang = CardPrintingLanguage.objects.get(
                    card_printing=link_print,
                    language=printlang.language)

                linked_language_objs.append(link_print_lang)

        physical_card = PhysicalCard(layout=staged_card.get_layout())
        physical_card.save()

        linked_language_objs.append(printlang)

        for link_lang in linked_language_objs:
            link_lang.physical_cards.add(physical_card)

    def update_card_links(self, staged_sets):
        for staged_set in staged_sets:

            if staged_set.get_code() not in self.sets_to_update:
                logging.info(f'Skipping set {staged_set.get_name()}')
                continue

            cards = staged_set.get_cards()

            for staged_card in [x for x in cards if x.has_other_names()]:
                card_obj = Card.objects.get(name=staged_card.get_name())

                logging.info(f'Finding card links for {staged_card.get_name()}')

                for link_name in staged_card.get_other_names():
                    link_card = Card.objects.get(name=link_name)

                    card_obj.links.add(link_card)
                    card_obj.save()

    def update_legalities(self, staged_sets):

        cards_updated = []

        for staged_set in staged_sets:
            if staged_set.get_code() not in self.sets_to_update:
                logging.info(f'Skipping set {staged_set.get_name()}')
                continue

            for staged_card in staged_set.get_cards():

                if staged_card.get_name() in cards_updated:
                    continue

                card_obj = Card.objects.get(name=staged_card.get_name())

                # Legalities can disappear form the json data if the card rolls out of standard,
                # so all legalities should be cleared out and redone
                card_obj.legalities.all().delete()

                for legality in staged_card.get_legalities():
                    format_obj, created = Format.objects.get_or_create(name=legality['format'])
                    legality, created = CardLegality.objects.get_or_create(card=card_obj, format=format_obj,
                                                                           restriction=legality['legality'])

                cards_updated.append(staged_card.get_name())
