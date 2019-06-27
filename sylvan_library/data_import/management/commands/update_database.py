"""
Module for the update_database command
"""
import logging
import time
from typing import List, Optional
from django.db import transaction

from cards.models import (
    Block,
    Card,
    CardPrinting,
    CardPrintingLanguage,
    Colour,
    Language,
    PhysicalCard,
    Rarity,
    Set,
)
from data_import.importers import JsonImporter
from data_import.management.data_import_command import DataImportCommand

from data_import.staging import StagedCard, StagedSet

logger = logging.getLogger("django")


class Command(DataImportCommand):
    """
    The command for updating hte database
    """

    help = (
        "Uses the downloaded JSON files to update the database, "
        "including creating cards, set and rarities\n"
        "Use the update_rulings command to update rulings"
    )

    # Keep track of which sets are new, so that printing information for
    #  existing sets doesn't have to be parsed
    sets_to_update = []

    # Keep track of which cards have been updated, so that reprints don't trigger pointless updates
    updated_cards = []

    force_update = False

    def add_arguments(self, parser):

        parser.add_argument(
            "--no-transaction",
            action="store_true",
            dest="no_transaction",
            default=False,
            help="Update the database without a transaction (unsafe)",
        )

        parser.add_argument(
            "--update-all",
            action="store_true",
            dest="force_update",
            default=False,
            help="Forces an update of sets that already exist, and cards that are already added",
        )

        parser.add_argument(
            "--update-set",
            dest="force_update_sets",
            type=str,
            help="Forces an update of the given sets",
        )

        parser.add_argument(
            "--oracle-only",
            action="store_true",
            dest="oracle_only",
            default=False,
            help="Update only the Card objects",
        )

        parser.add_argument(
            "--sets-only",
            action="store_true",
            dest="sets_only",
            default=False,
            help="Updates only the Set objects",
        )

    def handle(self, *args, **options):

        if not Colour.objects.exists() or not Rarity.objects.exists():
            logger.error(
                "No colours or rarities were found. "
                "Please run the update_metadata command first"
            )
            return

        self.start_time = time.time()

        importer = JsonImporter()
        importer.import_data()

        if not importer.sets:
            logger.error(
                "No sets were imported, please run the fetch_data command first"
            )
            return

        if options["force_update_sets"]:
            self.sets_to_update += options["force_update_sets"].split(",")

        self.force_update = options["force_update"]

        if options["no_transaction"]:
            self.update_database(
                importer,
                oracle_only=options["oracle_only"],
                sets_only=options["sets_only"],
            )
        else:
            with transaction.atomic():
                self.update_database(
                    importer,
                    oracle_only=options["oracle_only"],
                    sets_only=options["sets_only"],
                )

        self.log_stats()

    def update_database(
        self,
        data_importer: JsonImporter,
        oracle_only: bool = False,
        sets_only: bool = False,
    ) -> None:
        """
        Updates the objects with data from the data importer
        :param data_importer: The data importer to load data from
        :param oracle_only: Whether only Oracle (Card) information should be updated,
                            or the whole database
        :param sets_only: Whether only Set information should be updated, or the whole database
        """
        staged_sets = data_importer.get_staged_sets()

        if oracle_only:
            self.force_update = True
            self.update_card_list(staged_sets, oracle_only=True)
            return

        if sets_only:
            self.force_update = True
            self.update_set_list(staged_sets)
            return

        self.update_block_list(staged_sets)
        self.update_set_list(staged_sets)
        self.update_card_list(staged_sets)
        self.update_physical_card_list(staged_sets)
        self.update_card_links(staged_sets)

    def update_block_list(self, staged_sets: List[StagedSet]) -> None:
        """
        Updates the list of blocks using the given list of staged sets
        :param staged_sets: The list of staged sets to create the blocks for
        """
        logger.info("Updating block list")

        for staged_set in staged_sets:

            # Ignore sets that have no block
            if not staged_set.has_block():
                logger.info("Ignoring %s", staged_set.get_name())
                continue

            block = Block.objects.filter(name=staged_set.get_block()).first()

            if block is not None:
                logger.info("Block %s already exists", block.name)
            else:
                block = Block(
                    name=staged_set.get_block(),
                    release_date=staged_set.get_release_date(),
                )

                logger.info("Created block %s", block.name)
                block.full_clean()
                block.save()
                self.increment_created("Block")

        logger.info("Block list updated")

    def update_set_list(self, staged_sets: List[StagedSet]):
        """
        Updates all set objects and finds which ones should have their content updated
        when performing a quick update
        :param staged_sets: The list of staged sets
        :return:
        """
        logger.info("Updating set list")

        for staged_set in staged_sets:
            set_obj = Set.objects.filter(code=staged_set.get_code()).first()

            if set_obj is None:
                logger.info(
                    "Creating set %s (%s)", staged_set.get_name(), staged_set.code
                )
                block = Block.objects.filter(name=staged_set.get_block()).first()

                set_obj = Set(
                    code=staged_set.get_code(),
                    name=staged_set.get_name(),
                    type=staged_set.get_type(),
                    release_date=staged_set.get_release_date(),
                    keyrune_code=staged_set.get_keyrune_code(),
                    block=block,
                    card_count=staged_set.get_card_count(),
                )
                set_obj.full_clean()
                set_obj.save()
                self.increment_created("Set")
                self.sets_to_update.append(staged_set.get_code())

            else:
                logger.info("Set %s already exists, updating", staged_set.get_name())
                set_obj.name = staged_set.get_name()
                set_obj.type = staged_set.get_type()
                set_obj.keyrune_code = staged_set.get_keyrune_code()
                set_obj.card_count = staged_set.get_card_count()
                set_obj.full_clean()
                set_obj.save()
                self.increment_updated("Set")

        logger.info("Set list updated")

    # def update_tokens(self, staged_sets: List[StagedSet]):
    #     uid_token_map = dict()
    #     for staged_set in staged_sets:
    #         for staged_card in staged_set.get_tokens():
    #             uid = staged_card.get_scryfall_oracle_id()
    #             if uid not in uid_token_map:
    #                 uid_token_map[uid] = list()
    #
    #             uid_token_map[uid].append(staged_card)
    #
    #     for uid, staged_cards in uid_token_map.items():
    #         pass

    def update_card_list(
        self, staged_sets: List[StagedSet], oracle_only: bool = False
    ) -> None:
        """
        Updates or creates all Card, CardPrinting and CardPrintingLanguage records
        :param staged_sets:  The list of staged sets to use
        :param oracle_only: Whether only the Oracle (Card) data is all that should be updated,
                            or if everything should be updated
        """
        logger.info("Updating card list")

        for staged_set in staged_sets:
            if (
                staged_set.get_code() not in self.sets_to_update
                and not self.force_update
            ):
                logger.info("Ignoring set %s", staged_set.get_name())
                continue

            logger.info("Updating cards in set %s", staged_set.get_name())
            set_obj = Set.objects.get(code=staged_set.get_code())

            for staged_card in staged_set.get_cards():
                card_obj = self.update_card(staged_card)

                if not oracle_only:
                    printing_obj = self.update_card_printing(
                        card_obj, set_obj, staged_card
                    )

                    # The foreign data of a card doesn't include English, so we have to dummy it up
                    english = {
                        "language": "English",
                        "name": staged_card.get_name(),
                        "multiverseId": staged_card.get_multiverse_id(),
                    }
                    self.update_card_printing_language(printing_obj, english)

                    if staged_card.has_foreign_data():
                        for foreign_info in staged_card.get_foreign_data():
                            self.update_card_printing_language(
                                printing_obj, foreign_info
                            )

        logger.info("Card list updated")

    def update_card(self, staged_card: StagedCard) -> Card:
        """
        Updates or creates the Card object for the given StagedCard
        :param staged_card: The staging information for this card
        :return: The updated or created Card
        """
        try:
            if staged_card.is_token:
                card = Card.objects.get(
                    name=staged_card.get_name(),
                    scryfall_oracle_id=staged_card.get_scryfall_oracle_id(),
                    is_token=True,
                    side=staged_card.get_side(),
                )
            else:
                card = Card.objects.get(name=staged_card.get_name(), is_token=False)
                if (
                    not self.force_update
                    and staged_card.get_name() in self.updated_cards
                ):
                    logger.info("%s has already been updated", card)
                    self.increment_ignores("Card")
                    return card

            logger.info("Updating existing card %s", card)
            self.increment_updated("Card")
        except Card.DoesNotExist:
            card = Card(name=staged_card.get_name())
            logger.info("Creating new card %s", card)
            self.increment_created("Card")

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
        card.side = staged_card.get_side()
        card.scryfall_oracle_id = staged_card.get_scryfall_oracle_id()
        card.is_reserved = staged_card.is_reserved()
        card.is_token = staged_card.is_token

        card.full_clean()
        card.save()
        return card

    def update_card_printing(
        self, card_obj: Card, set_obj: Set, staged_card: StagedCard
    ) -> CardPrinting:

        """
        Updates or creates the CardPrinting object for a given Card/Set
        using the information in the StagedCard
        :param card_obj: The Card tto add the printing to
        :param set_obj: The set the printing is in
        :param staged_card: The staging information for this printing
        :return: The updated or created CardPrinting
        """
        printing = CardPrinting.objects.filter(
            json_id=staged_card.get_json_id()
        ).first()

        if printing is not None:
            logger.info("Updating card printing %s", printing)
            self.increment_updated("CardPrinting")
        else:
            printing = CardPrinting(card=card_obj, set=set_obj)
            logger.info("Created new card printing %s", printing)
            self.increment_created("CardPrinting")

        printing.number = staged_card.get_number()

        printing.artist = staged_card.get_artist()
        printing.rarity = Rarity.objects.get(name__iexact=staged_card.get_rarity_name())

        printing.flavour_text = staged_card.get_flavour_text()
        printing.original_text = staged_card.get_original_text()
        printing.original_type = staged_card.get_original_type()
        printing.json_id = staged_card.get_json_id()
        printing.watermark = staged_card.get_watermark()
        printing.border_colour = staged_card.get_border_colour()
        printing.is_starter = staged_card.is_starter_printing()
        printing.is_timeshifted = staged_card.is_timeshifted()
        printing.scryfall_id = staged_card.get_scryfall_id()

        printing.full_clean()
        printing.save()

        return printing

    def update_card_printing_language(
        self, printing_obj: CardPrinting, foreign_data: dict
    ) -> Optional[CardPrintingLanguage]:
        """
        Updates or creates a CardPrintedLanguage for a card printing with the given foreign data
        :param printing_obj: The CardPrinting the CardPrintedLanguage should be for
        :param foreign_data: The dictionayr of foreign data including the name of the language
        :return: The created or update CardPrintingLanguage object
        """

        # The name of the card is mandatory,so we might as well abort if it doesn't exist
        if "name" not in foreign_data:
            return None

        try:
            lang_obj = Language.objects.get(name=foreign_data["language"])
        except Language.DoesNotExist:
            raise Exception(f"Language {foreign_data['language']} not found")

        cardlang = CardPrintingLanguage.objects.filter(
            card_printing_id=printing_obj.id, language_id=lang_obj.id
        ).first()

        if cardlang is not None:
            logger.info("Card printing language %s already exists", cardlang)
            self.increment_updated("CardPrintingLanguage")
            return cardlang

        cardlang = CardPrintingLanguage(
            card_printing=printing_obj,
            language=lang_obj,
            card_name=foreign_data["name"],
            flavour_text=foreign_data.get("flavorText"),
            type=foreign_data.get("type"),
            multiverse_id=foreign_data.get("multiverseId"),
        )

        logger.info("Created new printing language %s", cardlang)
        cardlang.full_clean()
        cardlang.save()
        self.increment_created("CardPrintingLanguage")
        return cardlang

    def update_physical_card_list(self, staged_sets: List[StagedSet]) -> None:
        """
        Finds all the physical cards for all cards and links them to their printed languages
        :param staged_sets: THe list of staged set
        """
        logger.info("Updating physical card list")

        english_language = Language.objects.get(name="English")
        for staged_set in staged_sets:
            if (
                staged_set.get_code() not in self.sets_to_update
                and not self.force_update
            ):
                logger.info("Skipping set %s", staged_set.get_name())
                continue

            for staged_card in staged_set.get_cards():

                printing_obj = CardPrinting.objects.get(
                    json_id=staged_card.get_json_id()
                )

                printlang_obj = CardPrintingLanguage.objects.get(
                    card_printing=printing_obj, language=english_language
                )

                self.update_physical_card(printlang_obj, staged_card)

                for card_language in staged_card.get_foreign_data():
                    if not card_language.get("name"):
                        continue

                    lang_obj = Language.objects.get(name=card_language["language"])

                    try:
                        printlang_obj = CardPrintingLanguage.objects.get(
                            card_printing=printing_obj, language=lang_obj
                        )
                    except CardPrintingLanguage.DoesNotExist:
                        raise Exception(
                            "Could not find CardPrintingLanguage for {} {}".format(
                                printing_obj, lang_obj
                            )
                        )

                    self.update_physical_card(printlang_obj, staged_card)

    def update_physical_card(
        self, printlang: CardPrintingLanguage, staged_card: StagedCard
    ) -> None:
        """
        Find the physical cards for the given printed language and adds them
        :param printlang:
        :param staged_card:
        :return:
        """
        if printlang.physical_cards.exists():
            logger.info("Physical link already exists for %s", printlang)
            self.increment_ignores("PhysicalCard")
            return

        logger.info("Updating physical cards for %s", printlang)

        linked_language_objs = []

        if staged_card.has_other_names():

            for link_name in staged_card.get_other_names():

                link_card = Card.objects.get(name=link_name, is_token=False)
                link_print = CardPrinting.objects.filter(
                    card=link_card, set=printlang.card_printing.set
                ).first()
                if link_print is None:
                    logger.error(
                        "Printing for link %s in set %s not found",
                        link_card,
                        printlang.card_printing.set,
                    )
                    raise LookupError()

                if (
                    staged_card.get_layout() == "meld"
                    and printlang.card_printing.number[-1] != "b"
                    and link_print.number[-1] != "b"
                ):
                    logger.warning(
                        "Will not link %s to %s as they separate cards",
                        staged_card.get_name(),
                        link_card,
                    )

                    continue
                try:
                    link_print_lang = CardPrintingLanguage.objects.get(
                        card_printing=link_print, language=printlang.language
                    )
                except CardPrintingLanguage.DoesNotExist:
                    continue

                linked_language_objs.append(link_print_lang)

        physical_card = PhysicalCard(layout=staged_card.get_layout())
        physical_card.full_clean()
        physical_card.save()
        self.increment_created("PhysicalCard")

        linked_language_objs.append(printlang)

        for link_lang in linked_language_objs:
            link_lang.physical_cards.add(physical_card)

    def update_card_links(self, staged_sets: List[StagedSet]) -> None:
        """
        Finds the linkages between Card objects and adds them
        :param staged_sets:
        """
        for staged_set in staged_sets:

            if (
                staged_set.get_code() not in self.sets_to_update
                and not self.force_update
            ):
                logger.info("Skipping set %s", staged_set.get_name())
                continue

            cards = staged_set.get_cards()

            for staged_card in [x for x in cards if x.has_other_names()]:
                if staged_card.is_token:
                    pass

                card_obj = Card.objects.get(name=staged_card.get_name(), is_token=False)
                logger.info("Finding card links for %s", card_obj)

                for link_name in staged_card.get_other_names():
                    link_card = Card.objects.get(name=link_name, is_token=False)

                    # Only link front-side meld cards with their other phase
                    if (
                        card_obj.layout == "meld"
                        and link_card.side != "c"
                        and card_obj.side != "c"
                    ):
                        continue

                    card_obj.links.add(link_card)
                    card_obj.full_clean()
                    card_obj.save()
                    self.increment_updated("CardLink")
