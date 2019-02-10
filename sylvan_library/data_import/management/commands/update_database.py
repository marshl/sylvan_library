"""
Module for the update_database command
"""
import logging
import time

from django.core.management.base import BaseCommand
from django.db import transaction

from cards.models import (
    Block,
    Card,
    CardLegality,
    CardPrinting,
    CardPrintingLanguage,
    Colour,
    Format,
    Language,
    PhysicalCard,
    Rarity,
    Set,
)
from data_import.importers import (
    JsonImporter,
)
from data_import.staging import StagedCard

logger = logging.getLogger('django')


class Command(BaseCommand):
    """
    The command for updating hte database
    """
    help = 'Uses the downloaded JSON files to update the database, ' \
           'including creating cards, set and rarities\n' \
           'Use the update_rulings command to update rulings'

    # Keep track of which sets are new, so that printing information for
    #  existing sets doesn't have to be parsed
    sets_to_update = []

    # Keep track of which cards have been updated, so that reprints don't trigger pointless updates
    updated_cards = []

    force_update = False
    start_time = None

    update_counts = {'rarities_created': 0, 'rarities_updated': 0,
                     'colours_created': 0, 'colours_updated': 0,
                     'languages_created': 0, 'languages_updated': 0,
                     'cards_created': 0, 'cards_updated': 0, 'cards_ignored': 0,
                     'card_printings_created': 0, 'card_printings_updated': 0,
                     'printing_languages_created': 0, 'printing_languages_skipped': 0,
                     'physical_cards_created': 0, 'physical_cards_skipped': 0,
                     'card_links_created': 0,
                     'blocks_created': 0,
                     'sets_created': 0, 'sets_updated': 0,
                     'legalities_created': 0, 'legalities_updated': 0}

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
            help='Forces an update of sets that already exist, and cards that are already added',
        )

        parser.add_argument(
            '--update-set',
            dest='force_update_sets',
            nargs='*',
            help='Forces an update of the given sets'
        )

    def handle(self, *args, **options):

        self.start_time = time.time()

        importer = JsonImporter()
        importer.import_data()

        if options['force_update_sets']:
            self.sets_to_update += options['force_update_sets']

        self.force_update = options['force_update']

        if options['no_transaction']:
            self.update_database(importer)
        else:
            with transaction.atomic():
                self.update_database(importer)

        self.log_stats()

    def update_database(self, data_importer):
        self.update_rarity_list(data_importer)
        self.update_colour_list(data_importer)
        self.update_language_list(data_importer)

        staged_sets = data_importer.get_staged_sets()

        self.update_block_list(staged_sets)
        self.update_set_list(staged_sets)
        self.update_card_list(staged_sets)
        self.update_physical_card_list(staged_sets)
        self.update_card_links(staged_sets)
        self.update_legalities(staged_sets)

    def update_colour_list(self, data_importer):
        logger.info('Updating colour list')

        for colour in data_importer.import_colours():
            colour_obj = Colour.objects.filter(symbol=colour['symbol']).first()
            if colour_obj is not None:
                logger.info('Updating existing colour %s', colour_obj)
                self.update_counts['colours_updated'] += 1
            else:
                logger.info('Creating new colour %s', colour['name'])
                colour_obj = Colour(symbol=colour['symbol'],
                                    name=colour['name'],
                                    display_order=colour['display_order'],
                                    bit_value=colour['bit_value'])
                colour_obj.full_clean()
                colour_obj.save()
                self.update_counts['colours_created'] += 1

    def update_rarity_list(self, data_importer):

        logger.info('Updating rarity list')

        for rarity in data_importer.import_rarities():
            rarity_obj = Rarity.objects.filter(symbol=rarity['symbol']).first()
            if rarity_obj is not None:
                logger.info('Updating existing rarity %s', rarity_obj.name)
                rarity_obj.name = rarity['name']
                rarity_obj.display_order = rarity['display_order']
                rarity_obj.full_clean()
                rarity_obj.save()
                self.update_counts['rarities_updated'] += 1
            else:
                logger.info('Creating new rarity %s', rarity['name'])

                rarity_obj = Rarity(
                    symbol=rarity['symbol'],
                    name=rarity['name'],
                    display_order=rarity['display_order'])
                rarity_obj.full_clean()
                rarity_obj.save()
                self.update_counts['rarities_created'] += 1

        logger.info('Rarity update complete')

    def update_language_list(self, data_importer):

        logger.info('Updating language list')

        for lang in data_importer.import_languages():
            language_obj = Language.objects.filter(name=lang['name']).first()
            if language_obj is not None:
                logger.info("Updating language: %s", lang['name'])
                self.update_counts['languages_updated'] += 1
            else:
                logger.info("Creating new language: %s", lang['name'])
                language_obj = Language(name=lang['name'])
                self.update_counts['languages_created'] += 1

            language_obj.code = lang['code']
            language_obj.full_clean()
            language_obj.save()

        logger.info('Language update complete')

    def update_block_list(self, staged_sets):
        logger.info('Updating block list')

        for staged_set in staged_sets:

            # Ignore sets that have no block
            if not staged_set.has_block():
                logger.info('Ignoring %s', staged_set.get_name())
                continue

            block = Block.objects.filter(name=staged_set.get_block()).first()

            if block is not None:
                logger.info('Block %s already exists', block.name)
            else:
                block = Block(
                    name=staged_set.get_block(),
                    release_date=staged_set.get_release_date())

                logger.info('Created block %s', block.name)
                block.full_clean()
                block.save()
                self.update_counts['blocks_created'] += 1

        logger.info('Block list updated')

    def update_set_list(self, staged_sets):
        logger.info('Updating set list')

        for staged_set in staged_sets:
            set_obj = Set.objects.filter(code=staged_set.get_code()).first()

            if set_obj is None:

                logger.info('Creating set %s (%s)', staged_set.get_name(), staged_set.code)
                block = Block.objects.filter(name=staged_set.get_block()).first()

                set_obj = Set(
                    code=staged_set.get_code(),
                    name=staged_set.get_name(),
                    release_date=staged_set.get_release_date(),
                    block=block)
                set_obj.full_clean()
                set_obj.save()
                self.update_counts['sets_created'] += 1
                self.sets_to_update.append(staged_set.get_code())

            else:
                logger.info('Set %s already exists, updating', staged_set.get_name())
                set_obj.full_clean()
                set_obj.save()
                self.update_counts['sets_updated'] += 1

                if self.force_update:  # use the set anyway during a force update
                    self.sets_to_update.append(staged_set.get_code())
        logger.info('Set list updated')

    def update_card_list(self, staged_sets):
        logger.info('Updating card list')

        for staged_set in staged_sets:

            if staged_set.get_code() not in self.sets_to_update:
                logger.info('Ignoring set %s', staged_set.get_name())
                continue

            logger.info('Updating cards in set %s', staged_set.get_name())

            set_obj = Set.objects.get(code=staged_set.get_code())

            default_number = 1

            for staged_card in staged_set.get_cards():
                if staged_card.get_number() is None:
                    staged_card.set_number(default_number)

                card_obj = self.update_card(staged_card)

                printing_obj = self.update_card_printing(
                    card_obj,
                    set_obj,
                    staged_card)

                english = {
                    'language': 'English',
                    'name': staged_card.get_name(),
                    'multiverseId': staged_card.get_multiverse_id()
                }

                self.update_card_printing_language(printing_obj, english)

                if staged_card.has_foreign_data():
                    for foreign_info in staged_card.get_foreign_data():
                        self.update_card_printing_language(printing_obj, foreign_info)

        logger.info('Card list updated')

    def update_card(self, staged_card: StagedCard):
        card = Card.objects.filter(name=staged_card.get_name()).first()

        if card is not None:
            if not self.force_update and staged_card.get_name() in self.updated_cards:
                logger.info('%s has already been updated', card)
                self.update_counts['cards_ignored'] += 1
                return card

            logger.info('Updating existing card %s', card)
            self.update_counts['cards_updated'] += 1
        else:
            card = Card(name=staged_card.get_name())
            logger.info('Creating new card %s', card)
            self.update_counts['cards_created'] += 1

        self.updated_cards.append(staged_card.get_name())

        card.cost = staged_card.get_mana_cost()
        card.cmc = staged_card.get_cmc()
        card.colour_flags = staged_card.get_colour()
        card.colour_identity_flags = staged_card.get_colour_identity()
        card.colour_count = staged_card.get_colour_count()
        card.colour_sort_key = staged_card.get_colour_sort_key()
        card.colour_weight = staged_card.get_colour_weight()

        card.power = staged_card.get_power()
        card.toughness = staged_card.get_toughness()
        card.num_power = staged_card.get_num_power()
        card.num_toughness = staged_card.get_num_toughness()
        card.loyalty = staged_card.get_loyalty()
        card.num_loyalty = staged_card.get_num_loyalty()

        card.type = staged_card.get_types()
        card.subtype = staged_card.get_subtypes()
        card.original_type = staged_card.get_original_type()

        card.rules_text = staged_card.get_rules_text()
        card.original_text = staged_card.get_original_text()
        card.layout = staged_card.get_layout()

        card.is_reserved = staged_card.is_reserved()
        card.full_clean()
        card.save()
        return card

    def update_card_printing(self, card_obj: Card, set_obj: Set, staged_card: StagedCard):

        printing = CardPrinting.objects.filter(json_id=staged_card.get_json_id()).first()

        if printing is not None:
            logger.info('Updating card printing %s', printing)
            self.update_counts['card_printings_updated'] += 1
        else:
            printing = CardPrinting(
                card=card_obj,
                set=set_obj,
            )
            logger.info('Created new card printing %s', printing)
            self.update_counts['card_printings_created'] += 1

        printing.number = staged_card.get_number()

        printing.artist = staged_card.get_artist()
        printing.rarity = Rarity.objects.get(name__iexact=staged_card.get_rarity_name())

        printing.flavour_text = staged_card.get_flavour_text()
        printing.original_text = staged_card.get_original_text()
        printing.original_type = staged_card.get_original_type()
        printing.json_id = staged_card.get_json_id()
        printing.watermark = staged_card.get_watermark()
        printing.border_colour = staged_card.get_border_colour()
        printing.release_date = staged_card.get_release_date()
        printing.is_starter = staged_card.is_starter_printing()
        printing.scryfall_id = staged_card.get_scryfall_id()

        printing.full_clean()
        printing.save()

        return printing

    def update_card_printing_language(self, printing_obj, foreign_data):

        if 'name' not in foreign_data:
            return None

        try:
            lang_obj = Language.objects.get(name=foreign_data['language'])
        except Language.DoesNotExist:
            raise Exception(f"Language {foreign_data['language']} not found")

        cardlang = CardPrintingLanguage.objects.filter(
            card_printing_id=printing_obj.id,
            language_id=lang_obj.id).first()

        if cardlang is not None:
            logger.info('Card printing language %s already exists', cardlang)
            self.update_counts['printing_languages_skipped'] += 1
            return cardlang

        cardlang = CardPrintingLanguage(
            card_printing=printing_obj,
            language=lang_obj,
            card_name=foreign_data['name'],
            flavour_text=foreign_data.get('flavorText'),
            type=foreign_data.get('type'),
            multiverse_id=foreign_data.get('multiverseId'))

        logger.info('Created new printing language %s', cardlang)
        cardlang.full_clean()
        cardlang.save()
        self.update_counts['printing_languages_created'] += 1
        return cardlang

    def update_physical_card_list(self, staged_sets):
        logger.info('Updating physical card list')

        english_language = Language.objects.get(name='English')
        for staged_set in staged_sets:

            if staged_set.get_code() not in self.sets_to_update:
                logger.info('Skipping set %s', staged_set.get_name())
                continue

            for staged_card in staged_set.get_cards():

                printing_obj = CardPrinting.objects.get(json_id=staged_card.get_json_id())

                printlang_obj = CardPrintingLanguage.objects.get(
                    card_printing=printing_obj,
                    language=english_language)

                self.update_physical_card(printlang_obj, staged_card)

                if staged_card.has_foreign_data():
                    for card_language in staged_card.get_foreign_data():
                        if not card_language.get('name'):
                            continue

                        lang_obj = Language.objects.get(
                            name=card_language['language'])

                        try:
                            printlang_obj = CardPrintingLanguage.objects.get(
                                card_printing=printing_obj,
                                language=lang_obj)
                        except CardPrintingLanguage.DoesNotExist:
                            raise Exception(
                                'Could not find CardPrintingLanguage for {} {}'.format(
                                    printing_obj, lang_obj))

                        self.update_physical_card(printlang_obj, staged_card)

    def update_physical_card(self, printlang: CardPrintingLanguage, staged_card: StagedCard):

        if printlang.physical_cards.exists():
            logger.info('Physical link already exists for %s', printlang)
            self.update_counts['physical_cards_skipped'] += 1
            return

        if (staged_card.get_layout() == 'meld' and
                staged_card.get_name_count() == 3 and
                printlang.card_printing.number and
                printlang.card_printing.number[-1] == 'b'):
            logger.info('Will not create card link for meld card%s', printlang)
            return

        logger.info('Updating physical cards for %s', printlang)

        linked_language_objs = []

        if staged_card.has_other_names():

            for link_name in staged_card.get_other_names():

                link_card = Card.objects.get(name=link_name)
                link_print = CardPrinting.objects.filter(
                    card=link_card,
                    set=printlang.card_printing.set).first()
                if link_print is None:
                    logger.error(
                        'Printing for link %s in set %s not found',
                        link_card, printlang.card_printing.set)
                    raise LookupError()

                if (staged_card.get_layout() == 'meld' and
                        printlang.card_printing.number[-1] != 'b' and
                        link_print.number[-1] != 'b'):
                    logger.warning(
                        'Will not link %s to %s as they separate cards',
                        staged_card.get_name(), link_card)

                    continue
                try:
                    link_print_lang = CardPrintingLanguage.objects.get(
                        card_printing=link_print,
                        language=printlang.language)
                except CardPrintingLanguage.DoesNotExist:
                    continue

                linked_language_objs.append(link_print_lang)

        physical_card = PhysicalCard(layout=staged_card.get_layout())
        physical_card.full_clean()
        physical_card.save()
        self.update_counts['physical_cards_created'] += 1

        linked_language_objs.append(printlang)

        for link_lang in linked_language_objs:
            link_lang.physical_cards.add(physical_card)

    def update_card_links(self, staged_sets):
        for staged_set in staged_sets:

            if staged_set.get_code() not in self.sets_to_update:
                logger.info('Skipping set %s', staged_set.get_name())
                continue

            cards = staged_set.get_cards()

            for staged_card in [x for x in cards if x.has_other_names()]:
                card_obj = Card.objects.get(name=staged_card.get_name())

                logger.info('Finding card links for %s', staged_card.get_name())

                for link_name in staged_card.get_other_names():
                    link_card = Card.objects.get(name=link_name)

                    card_obj.links.add(link_card)
                    card_obj.full_clean()
                    card_obj.save()
                    self.update_counts['card_links_created'] += 1

    def update_legalities(self, staged_sets):

        cards_updated = []

        for staged_set in staged_sets:
            if staged_set.get_code() not in self.sets_to_update:
                logger.info('Skipping set %s', staged_set.get_name())
                continue

            logger.info('Finding legalities for %s', staged_set.get_name())

            for staged_card in staged_set.get_cards():

                if staged_card.get_name() in cards_updated:
                    continue

                card_obj = Card.objects.get(name=staged_card.get_name())

                # Legalities can disappear form the json data if the card rolls out of standard,
                # so all legalities should be cleared out and redone
                card_obj.legalities.all().delete()

                for format_name, legality in staged_card.get_legalities().items():
                    format_obj, created = Format.objects.get_or_create(name=format_name)
                    legality, created = CardLegality.objects.get_or_create(
                        card=card_obj, format=format_obj, restriction=legality
                    )
                    self.update_counts[
                        'legalities_created' if created else 'legalities_updated'] += 1

                cards_updated.append(staged_card.get_name())

    def log_stats(self):
        logger.info('%s', '\n' + ('=' * 80) + '\n\nUpdate complete:\n')
        elapsed_time = time.time() - self.start_time
        logger.info('Time elapsed: %s', time.strftime("%H:%M:%S", time.gmtime(elapsed_time)))
        for key, value in self.update_counts.items():
            logger.info('%s %s', key, value)
