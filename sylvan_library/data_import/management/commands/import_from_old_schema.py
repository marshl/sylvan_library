import logging

import psycopg2
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandParser
from django.db import transaction

from _query import query_yes_no
from cards.models import (
    UserOwnedCard,
    CardLocalisation,
    CardPrinting,
    UserCardChange,
    Deck,
    DeckCard,
    Colour,
    Card,
)

logger = logging.getLogger("django")


"DATABASE_URL=psql://melira:Wg1DHKXV5OMoQXTF0TMl@localhost:5432/sylvan_db"


class Command(BaseCommand):
    help = "Imports a list of user owned cards from a tsv file"

    def add_arguments(self, parser: CommandParser):
        parser.add_argument("--dbname", help="The database name")
        parser.add_argument("--user", help="The database user")
        parser.add_argument("--password", help="The database password")
        parser.add_argument(
            "--overwrite",
            action="store_true",
            dest="remove_existing",
            default=False,
            help="Remove existing data before importing",
        )

    def handle(self, *args, **options) -> None:
        connection = self.get_database_connection(
            dbname=options["dbname"], user=options["user"], password=options["password"]
        )
        with transaction.atomic():
            self.import_users(connection)

            self.import_user_owned_cards(
                connection, remove_existing=options["remove_existing"]
            )
            self.import_user_card_changes(
                connection, remove_existing=options["remove_existing"]
            )
            self.import_decks(connection, remove_existing=options["remove_existing"])
        connection.close()

    def get_database_connection(
        self, dbname: str, user: str, password: str
    ) -> psycopg2._psycopg.connection:
        conn = psycopg2.connect(dbname=dbname, user=user, password=password)
        return conn

    def import_users(self, connection: psycopg2._psycopg.connection):
        """
        Imports User objects from the given postgres connection
        :param connection:
        :return:
        """
        cur = connection.cursor()
        cur.execute("SELECT username, date_joined FROM auth_user")
        for username, date_joined in cur.fetchall():
            if not User.objects.filter(username=username).exists():
                logger.info("Creating user %s", username)
                User.objects.create_user(
                    username=username, date_joined=date_joined, password="password"
                )

    def import_user_owned_cards(
        self, connection: psycopg2._psycopg.connection, remove_existing: bool
    ):
        cur = connection.cursor()

        cur.execute(
            """
SELECT
DISTINCT(auth_user.username)
FROM cards_userownedcard user_owned_card
JOIN auth_user
ON auth_user.id = user_owned_card.owner_id
"""
        )
        users_with_cards = cur.fetchall()

        if remove_existing and users_with_cards:
            for (username,) in users_with_cards:
                user = User.objects.get(username=username)
                user_cards = UserOwnedCard.objects.filter(owner=user)
                if user_cards.exists():
                    logger.info(
                        "Clearing %s user cards from %s", user_cards.count(), username
                    )
                    user_cards.delete()

        cur.execute(
            """
SELECT
card.name,
user_owned_card.count,
cards_set.code,
auth_user.username,
cards_language.name,
cardprinting.scryfall_id,
cardprinting.json_id AS face_uuid
FROM cards_userownedcard user_owned_card
JOIN auth_user
ON auth_user.id = user_owned_card.owner_id
JOIN cards_physicalcard physical_card
ON physical_card.id = user_owned_card.physical_card_id
JOIN cards_cardprintinglanguage_physical_cards printlang_to_physicalcard
ON printlang_to_physicalcard.physicalcard_Id = physical_card.id
JOIN cards_cardprintinglanguage printlang
ON printlang.id = printlang_to_physicalcard.cardprintinglanguage_id
JOIN cards_language
ON cards_language.id = printlang.language_id
JOIN cards_cardprinting cardprinting
ON cardprinting.id = printlang.card_printing_id
JOIN cards_card card ON card.id = cardprinting.card_id
JOIN cards_set ON cards_set.id = cardprinting.set_id
ORDER BY user_owned_card.id ASC
"""
        )
        for (
            card_name,
            count,
            set_code,
            username,
            language_name,
            scryfall_id,
            face_uuid,
        ) in cur.fetchall():
            print(card_name, count, set_code)
            user = User.objects.get(username=username)
            localisation = self.get_card_localisation(
                scryfall_id=scryfall_id, language_name=language_name
            )
            existing_user_card = UserOwnedCard.objects.filter(
                owner=user, card_localisation=localisation
            )
            if existing_user_card.exists():
                if localisation.localised_faces.count() >= 1:
                    continue
                result = query_yes_no(
                    "{} already exists, skip it?".format(existing_user_card.first())
                )
                if not result:
                    raise Exception
            UserOwnedCard.objects.create(
                owner=user, card_localisation=localisation, count=count
            )

    def import_user_card_changes(
        self, connection: psycopg2._psycopg.connection, remove_existing: bool
    ):
        cur = connection.cursor()

        cur.execute(
            """
SELECT
DISTINCT auth_user.username
FROM cards_usercardchange user_card_change
JOIN auth_user
ON auth_user.id = user_card_change.owner_id
"""
        )
        users_with_changes = cur.fetchall()

        if remove_existing and users_with_changes:
            for (username,) in users_with_changes:
                user = User.objects.get(username=username)
                card_changes = UserCardChange.objects.filter(owner=user)
                if card_changes.exists():
                    logger.info(
                        "Clearing %s user card changes from %s",
                        card_changes.count(),
                        username,
                    )
                    card_changes.delete()

        cur.execute(
            """
SELECT
card.name,
user_card_change.difference,
user_card_change.date,
cards_set.code,
auth_user.username,
cards_language.name,
cardprinting.scryfall_id,
cardprinting.json_id AS face_uuid
FROM cards_usercardchange user_card_change
JOIN auth_user
ON auth_user.id = user_card_change.owner_id
JOIN cards_physicalcard physical_card
ON physical_card.id = user_card_change.physical_card_id
JOIN cards_cardprintinglanguage_physical_cards printlang_to_physicalcard
ON printlang_to_physicalcard.physicalcard_Id = physical_card.id
JOIN cards_cardprintinglanguage printlang
ON printlang.id = printlang_to_physicalcard.cardprintinglanguage_id
JOIN cards_language
ON cards_language.id = printlang.language_id
JOIN cards_cardprinting cardprinting
ON cardprinting.id = printlang.card_printing_id
JOIN cards_card card ON card.id = cardprinting.card_id
JOIN cards_set ON cards_set.id = cardprinting.set_id
ORDER BY user_card_change.id ASC
"""
        )
        for (
            card_name,
            difference,
            change_date,
            set_code,
            username,
            language_name,
            scryfall_id,
            face_uuid,
        ) in cur.fetchall():
            print(card_name, difference, set_code, change_date)
            user = User.objects.get(username=username)
            card_localisation = self.get_card_localisation(
                scryfall_id=scryfall_id, language_name=language_name
            )
            existing_change = UserCardChange.objects.filter(
                owner=user, card_localisation=card_localisation, date=change_date
            )
            if (
                existing_change.exists()
                and card_localisation.localised_faces.count() > 1
            ):
                continue
            UserCardChange.objects.create(
                owner=user,
                card_localisation=card_localisation,
                difference=difference,
                date=change_date,
            )

    def get_card_localisation(
        self, scryfall_id: str, language_name: str
    ) -> CardLocalisation:
        """
        Gets the card localisation (a card in a set of a language) given a scryfall id and language
        :param scryfall_id: The scryfall ID to get
        :param language_name: The name of the language of the localisation
        :return: The localisation that matches
        """
        printing = CardPrinting.objects.get(scryfall_id=scryfall_id)
        localisation = CardLocalisation.objects.get(
            language__name=language_name, card_printing=printing
        )
        return localisation

    def import_decks(self, connection, remove_existing):
        cur = connection.cursor()
        cur.execute(
            """
SELECT
DISTINCT auth_user.username
FROM cards_deck
JOIN auth_user
ON auth_user.id = cards_deck.owner_id
"""
        )
        users_with_decks = cur.fetchall()

        if remove_existing and users_with_decks:
            for (username,) in users_with_decks:
                user = User.objects.get(username=username)
                user_decks = Deck.objects.filter(owner=user)
                if user_decks.exists():
                    logger.info(
                        "Clearing %s decks from %s", user_decks.count(), username
                    )
                    user_decks.delete()

        cur.execute(
            """
SELECT
cards_deck.id,
date_created,
last_modified,
name,
auth_user.username,
description,
format,
subtitle,
is_private,
is_prototype
FROM cards_deck
JOIN auth_user ON auth_user.id = cards_deck.owner_id
"""
        )

        for (
            deck_id,
            date_created,
            last_modified,
            deck_name,
            username,
            description,
            deck_format,
            subtitle,
            is_private,
            is_prototype,
        ) in cur.fetchall():
            print(username, deck_name)
            user = User.objects.get(username=username)
            deck: Deck = Deck.objects.create(
                owner=user,
                date_created=date_created,
                last_modified=last_modified,
                name=deck_name,
                description=description,
                format=deck_format,
                subtitle=subtitle,
                is_private=is_private,
                is_prototype=is_prototype,
            )
            colour_cursor = connection.cursor()
            colour_cursor.execute(
                """
SELECT colour.symbol
FROM cards_deck_exclude_colours exclude_colours
JOIN cards_colour colour ON exclude_colours.colour_id = colour.id
WHERE exclude_colours.deck_id = %s
""",
                (deck_id,),
            )
            symbols = [symbol for symbol, in colour_cursor.fetchall()]
            exclude_colours = Colour.objects.filter(symbol__in=symbols)
            deck.exclude_colours.set(exclude_colours)
            deck.save()

            card_cursor = connection.cursor()
            card_cursor.execute(
                """
SELECT
card.scryfall_oracle_id,
deckcard.count,
deckcard.board,
deckcard.is_commander
FROM cards_deckcard deckcard
JOIN cards_card card
ON card.id = deckcard.card_id
WHERE deckcard.deck_id = %s
""",
                (deck_id,),
            )
            for (
                scryfall_oracle_id,
                deck_count,
                deck_board,
                is_commander,
            ) in card_cursor.fetchall():
                card = Card.objects.get(scryfall_oracle_id=scryfall_oracle_id)
                DeckCard.objects.create(
                    deck=deck,
                    card=card,
                    count=deck_count,
                    board=deck_board,
                    is_commander=is_commander,
                )
