from django.test import TestCase

from .models import *


# Create your tests here.

def create_test_card(fields: dict = {}):
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


def create_test_card_printing(card: Card, set_obj: Set, fields: dict = {}):
    printing = CardPrinting()
    printing.card = card
    printing.set = set_obj
    printing.collector_number = 0
    printing.rarity = create_test_rarity('Common', 'C')
    printing.is_starter = False

    for key, value in fields.items():
        printing.__dict__[key] = value

    printing.save()
    return printing


def create_test_set(name: str, setcode: str, fields: dict = {}):
    set_obj = Set(name=name, code=setcode)

    for key, value in fields.items():
        set_obj.__dict__[key] = value

    set_obj.save()

    return set_obj


def create_test_rarity(name: str, symbol: str):
    rarity = Rarity(name=str, symbol=symbol)
    rarity.display_order = 1
    rarity.save()
    return rarity
