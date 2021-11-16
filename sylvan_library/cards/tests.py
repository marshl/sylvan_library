"""
Unit tests for the cards module
"""
import uuid
from typing import Dict, Any, Optional

from django.test import TestCase
from django.contrib.auth.models import User

from cards.models import (
    Card,
    CardPrinting,
    CardLocalisation,
    Language,
    Rarity,
    Set,
    CardFace,
)


def create_test_card(fields: Optional[Dict[str, Any]] = None) -> Card:
    """
    Creates a test card with fields from the given dict
    :param fields: The fields to populate
    :return: A card object
    """
    card = Card()
    card.scryfall_oracle_id = uuid.uuid4()
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
    card.converted_mana_cost = 0

    for key, value in (fields or {}).items():
        assert hasattr(card, key)
        setattr(card, key, value)

    card.full_clean()
    card.save()
    return card


def create_test_card_face(
    card: Card, fields: Optional[Dict[str, Any]] = None
) -> CardFace:
    card_face = CardFace(card=card)
    card_face.name = uuid.uuid4()
    card_face.converted_mana_cost = 0
    card_face.colour_count = 0
    card_face.colour_weight = 0
    card_face.colour_sort_key = 0

    for key, value in (fields or {}).items():
        assert hasattr(card_face, key)
        setattr(card_face, key, value)

    card_face.full_clean()
    card_face.save()
    return card_face


def create_test_card_printing(
    card: Card, set_obj: Set, fields: Optional[Dict[str, Any]] = None
) -> CardPrinting:
    """
    Creates a test CardPrinting object with values set to passed fields
    :param card: The card for the printing
    :param set_obj: The set the card is in
    :param fields: Other fields
    :return: A test CardPrinting
    """
    printing = CardPrinting()
    printing.scryfall_id = uuid.uuid4()
    printing.card = card
    printing.set = set_obj
    printing.rarity = create_test_rarity("Common", "C")
    printing.is_starter = False
    printing.is_timeshifted = fields.get("is_timeshifted", False) if fields else False
    printing.json_id = uuid.uuid4()

    if fields:
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


def create_test_card_localisation(
    printing: CardPrinting, language: Language
) -> CardLocalisation:
    """
    Creates a dummy CardLocalisation object
    :param printing: The printing to use
    :param language: The language to use
    :return:
    """
    print_lang = CardLocalisation()
    print_lang.card_printing = printing
    print_lang.language = language
    print_lang.card_name = printing.card.name
    print_lang.full_clean()
    print_lang.save()
    return print_lang


def create_test_set(name: str, setcode: str, fields: Dict[str, Any]) -> Set:
    """
    Creates a test Set with the input values
    :param name: The name of the set
    :param setcode: The code of the set
    :param fields: Other fields
    :return: A set object
    """
    set_obj, _ = Set.objects.get_or_create(name=name, code=setcode, total_set_size=0)

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
    rarity, _ = Rarity.objects.get_or_create(name=name, symbol=symbol, display_order=1)
    return rarity


def create_test_user() -> User:
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

    def setUp(self) -> None:
        """
        Sets up the for the unit tests
        """
        self.user = create_test_user()
        card = create_test_card({"name": "Bionic Beaver"})
        set_obj = create_test_set("Setty", "SET", {})
        printing = create_test_card_printing(card, set_obj, {})
        lang = create_test_language("English", "en")
        self.localisation = create_test_card_localisation(printing, lang)

    def test_add_card(self) -> None:
        """
        Tests that adding a card works
        """
        self.localisation.apply_user_change(5, self.user)
        ownership = self.localisation.ownerships.get(owner=self.user)
        self.assertEqual(ownership.count, 5)

    def test_subtract_card(self) -> None:
        """
        Tests that adding a card and then subtracting from it works
        """
        self.localisation.apply_user_change(3, self.user)
        ownership = self.localisation.ownerships.get(owner=self.user)
        self.assertEqual(ownership.count, 3)
        self.localisation.apply_user_change(-2, self.user)
        ownership = self.localisation.ownerships.get(owner=self.user)
        self.assertEqual(ownership.count, 1)

    def test_remove_card(self) -> None:
        """
        Tests that a card is removed if it is added and then subtracted from entirely
        """
        self.localisation.apply_user_change(3, self.user)
        ownership = self.localisation.ownerships.get(owner=self.user)
        self.assertEqual(ownership.count, 3)
        self.localisation.apply_user_change(-3, self.user)
        self.assertFalse(self.localisation.ownerships.filter(owner=self.user).exists())

    def test_overremove_card(self) -> None:
        """
        Tests that a card is removed correctly if is added and then has a subtraction greater
        than the number that was added
        """
        self.localisation.apply_user_change(3, self.user)
        ownership = self.localisation.ownerships.get(owner=self.user)
        self.assertEqual(ownership.count, 3)
        self.localisation.apply_user_change(-10, self.user)
        self.assertFalse(self.localisation.ownerships.filter(owner=self.user).exists())
