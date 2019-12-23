from django.test import TestCase

from cards.models import Card, Set
from cards.tests import create_test_card, create_test_card_printing, create_test_set

from cardsearch.parameters import (
    AndParam,
    CardNameParam,
    CardRulesTextParam,
    CardSetParam,
    CardColourParam,
)

from cardsearch.parse_search import ParseSearch


class ColourContainsTestCase(TestCase):
    """
    Tests for the card name parameter
    """

    def setUp(self):
        self.red_card = create_test_card({"colour": Card.colour_flags.red})
        self.green_card = create_test_card({"colour": Card.colour_flags.green})
        self.parse_search = ParseSearch()

    def tearDown(self):
        self.red_card.delete()
        self.green_card.delete()

    def test_name_match(self):
        self.parse_search.query_string = "color:rg"
        self.parse_search.build_parameters()
        results = self.parse_search.queryset().all()
        pass
