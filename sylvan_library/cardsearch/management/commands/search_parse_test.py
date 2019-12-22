import logging
import json
from typing import Union, List, Dict, Optional, Tuple, Any

from django.core.management.base import BaseCommand
from cards.models import (
    Block,
    Card,
    CardLegality,
    CardPrice,
    CardPrinting,
    CardPrintingLanguage,
    CardRuling,
    Colour,
    Format,
    Language,
    PhysicalCard,
    Rarity,
    Set,
)
from cardsearch.parameters import (
    CardSearchParam,
    OrParam,
    AndParam,
    CardNumPowerParam,
    CardNameParam,
    CardNumToughnessParam,
)
from cardsearch.query_parser import CardQueryParser


class Command(BaseCommand):

    help = ()

    def __init__(self, stdout=None, stderr=None, no_color=False):
        self.logger = logging.getLogger("django")
        super().__init__(stdout=stdout, stderr=stderr, no_color=no_color)

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):

        parser = CardQueryParser()
        # print(parser.parse("name"))
        # # print(parser.parse("name:"))
        # r = parser.parse("power>10 and toughness<3")
        # print(r)
        r = parser.parse("power>=10 and toughness<=2 or power<=2 and toughness>=10")
        cards = Card.objects.filter(r.query())
        print(cards.all())
        pass

        r = parser.parse("power:12")
        cards = Card.objects.filter(r.query())
        print(cards.all())
        pass
