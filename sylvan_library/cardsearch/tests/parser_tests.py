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
        self.red_card = create_test_card({"colour_flags": Card.colour_flags.red})
        self.green_card = create_test_card({"colour_flags": Card.colour_flags.green})
        self.red_green_card = create_test_card(
            {"colour_flags": Card.colour_flags.red | Card.colour_flags.green}
        )
        self.red_green_black_card = create_test_card(
            {
                "colour_flags": Card.colour_flags.red
                | Card.colour_flags.green
                | Card.colour_flags.black
            }
        )
        self.blue_red_card = create_test_card(
            {"colour_flags": Card.colour_flags.blue | Card.colour_flags.red}
        )
        self.parse_search = ParseSearch()

    def tearDown(self):
        self.red_card.delete()
        self.green_card.delete()

    def test_name_match(self):
        self.parse_search.query_string = "color:rg"
        self.parse_search.build_parameters()
        results = self.parse_search.get_queryset().all()
        self.assertNotIn(
            self.red_card,
            results,
            "A red card shouldn't be found in a green/red search",
        )
        self.assertNotIn(
            self.green_card,
            results,
            "A green card shouldn't be found in a red/green search",
        )
        self.assertIn(
            self.red_green_card,
            results,
            "A red/green card should be found in a red/green search",
        )
        self.assertIn(
            self.red_green_black_card,
            results,
            "A red/green/black card should be found in a red/green search",
        )
        self.assertNotIn(
            self.blue_red_card,
            results,
            "A blue/red card shouldn't found in a red/green search')",
        )
