"""
Unit tests for the cards module
"""

from cards.models import (
    Card,
    CardPrinting,
    Rarity,
    Set,
)


# Create your tests here.
def create_test_card(fields: dict) -> Card:
    """
    Creates a test card with fields from the given dict
    :param fields: The fields to populate
    :return: A card object
    """
    card = Card()
    card.name = 'undefined'
    card.cmc = 0
    card.num_power = 0
    card.num_toughness = 0
    card.num_loyalty = 0
    card.colour_count = 0
    card.colour_sort_key = 0
    card.colour_weight = 0
    card.is_reserved = False

    for key, value in fields.items():
        card.__dict__[key] = value

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
    printing.rarity = create_test_rarity('Common', 'C')
    printing.is_starter = False

    for key, value in fields.items():
        printing.__dict__[key] = value

    printing.save()
    return printing


def create_test_set(name: str, setcode: str, fields: dict) -> Set:
    """
    Creates a test Set with the input values
    :param name: The name of the set
    :param setcode: The code of the set
    :param fields: Other fields
    :return: A set object
    """
    set_obj = Set(name=name, code=setcode)

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
