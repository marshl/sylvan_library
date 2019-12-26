"""
Unit tests for the cards module
"""
from django.test import TestCase

from django.contrib.auth.models import User

import uuid

from cards.models import (
    Card,
    CardPrinting,
    CardPrintingLanguage,
    Language,
    PhysicalCard,
    Rarity,
    Set,
)


def create_test_card(fields: dict) -> Card:
    """
    Creates a test card with fields from the given dict
    :param fields: The fields to populate
    :return: A card object
    """
    card = Card()
    card.name = uuid.uuid1()
    card.cmc = 0
    card.num_power = 0
    card.num_toughness = 0
    card.num_loyalty = 0
    card.colour_flags = 0
    card.colour_identity_flags = 0
    card.colour_count = 0
    card.colour_identity_count = 0
    card.colour_sort_key = 0
    card.colour_weight = 0
    card.layout = "normal"
    card.is_reserved = False
    card.is_token = False

    for key, value in fields.items():
        setattr(card, key, value)

    if not card.display_name:
        card.display_name = card.name

    card.full_clean()
    card.save()
    return card


def create_test_card_printing(card: Card, set_obj: Set, fields: dict) -> CardPrinting:
    """
    Creates a test CardPrinting object with values set to passed fields
    :param card: The card for the printing
    :param set_obj: The set the card is in
    :param fields: Other fields
    :return: A test CardPrinting
    """
    printing = CardPrinting()
    printing.card = card
    printing.set = set_obj
    printing.rarity = create_test_rarity("Common", "C")
    printing.is_starter = False
    printing.is_timeshifted = fields.get("is_timeshifted", False)

    for key, value in fields.items():
        printing.__dict__[key] = value

    printing.save()
    return printing


def create_test_language(name: str, code: str) -> Language:
    """
    Creates a test Language object
    :param name: The name of the language
    :param code: The language code
    :return:
    """
    lang = Language(name=name, code=code)
    lang.full_clean()
    lang.save()
    return lang


def create_test_card_printing_language(
    printing: CardPrinting, language: Language
) -> CardPrintingLanguage:
    """
    Creates a dummy CardPrintingLanguage object
    :param printing: The printing to use
    :param language: The language to use
    :return:
    """
    print_lang = CardPrintingLanguage()
    print_lang.card_printing = printing
    print_lang.language = language
    print_lang.card_name = printing.card.name
    print_lang.full_clean()
    print_lang.save()
    return print_lang


def create_test_physical_card(printlang: CardPrintingLanguage) -> PhysicalCard:
    """
    Creates a dummy PhysicalCard object for the given printed language
    :param printlang:
    :return:
    """
    physcard = PhysicalCard()
    physcard.layout = "normal"
    physcard.full_clean()
    physcard.save()
    physcard.printed_languages.add(printlang)
    physcard.full_clean()
    physcard.save()
    return physcard


def create_test_set(name: str, setcode: str, fields: dict) -> Set:
    """
    Creates a test Set with the input values
    :param name: The name of the set
    :param setcode: The code of the set
    :param fields: Other fields
    :return: A set object
    """
    set_obj = Set(name=name, code=setcode, total_set_size=0)

    for key, value in fields.items():
        set_obj.__dict__[key] = value

    set_obj.save()

    return set_obj


def create_test_rarity(name: str, symbol: str) -> Rarity:
    """
    Creates a test rarity with the given values
    :param name: The name of the rarity
    :param symbol: The rarity symbl
    :return: The dummy rarity object
    """
    rarity = Rarity(name=str, symbol=symbol)
    rarity.name = name
    rarity.display_order = 1
    rarity.save()
    return rarity


def create_test_user():
    """
    Creates a test user
    """
    user = User(username="testuser", password="password")
    user.full_clean()
    user.save()
    return user


class CardOwnershipTestCase(TestCase):
    """
    Test cases for card ownership
    """

    def setUp(self):
        """
        Sets up the for the unit tests
        """
        self.user = create_test_user()
        card = create_test_card({"name": "Bionic Beaver"})
        set_obj = create_test_set("Setty", "SET", {})
        printing = create_test_card_printing(card, set_obj, {})
        lang = create_test_language("English", "en")
        printlang = create_test_card_printing_language(printing, lang)
        self.physical_card = create_test_physical_card(printlang)

    def test_add_card(self):
        """
        Tests that adding a card works
        """
        self.physical_card.apply_user_change(5, self.user)
        ownership = self.physical_card.ownerships.get(owner=self.user)
        self.assertEqual(ownership.count, 5)

    def test_subtract_card(self):
        """
        Tests that adding a card and then subtracting from it works
        """
        self.physical_card.apply_user_change(3, self.user)
        ownership = self.physical_card.ownerships.get(owner=self.user)
        self.assertEqual(ownership.count, 3)
        self.physical_card.apply_user_change(-2, self.user)
        ownership = self.physical_card.ownerships.get(owner=self.user)
        self.assertEqual(ownership.count, 1)

    def test_remove_card(self):
        """
        Tests that a card is removed if it is added and then subtracted from entirely
        """
        self.physical_card.apply_user_change(3, self.user)
        ownership = self.physical_card.ownerships.get(owner=self.user)
        self.assertEqual(ownership.count, 3)
        self.physical_card.apply_user_change(-3, self.user)
        self.assertFalse(self.physical_card.ownerships.filter(owner=self.user).exists())

    def test_overremove_card(self):
        """
        Tests that a card is removed correctly if is added and then has a subtraction greater
        than the number that was added
        """
        self.physical_card.apply_user_change(3, self.user)
        ownership = self.physical_card.ownerships.get(owner=self.user)
        self.assertEqual(ownership.count, 3)
        self.physical_card.apply_user_change(-10, self.user)
        self.assertFalse(self.physical_card.ownerships.filter(owner=self.user).exists())
