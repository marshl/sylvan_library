"""
The module for searching tests
"""

from django.test import TestCase

from cards.models import Card, Set
from cards.tests import create_test_card, create_test_card_printing, create_test_set

from cardsearch.parameters import (
    AndParam,
    CardNameParam,
    CardRulesTextParam,
    CardSetParam,
)


class CardNameParamTestCase(TestCase):
    """
    Tests for the card name parameter
    """

    def test_name_match(self):
        """
        Tests that a card name exact match is found
        """
        card = create_test_card({"name": "foo"})
        param = CardNameParam("foo", match_exact=True)
        self.assertIn(card, Card.objects.filter(param.query()))

    def test_name_contains_no_match(self):
        """
        Tests that a card name exact match is found
        """
        card = create_test_card({"name": "foobar"})
        param = CardNameParam("foo", match_exact=True)
        self.assertNotIn(card, Card.objects.filter(param.query()))

    def test_name_match_inverse(self):
        """
        Tests that a card name exact match is found
        """
        card = create_test_card({"name": "foo"})
        param = CardNameParam("foo", match_exact=True, inverse=True)
        self.assertNotIn(card, Card.objects.filter(param.query()))

    def test_name_contains(self):
        """
        Tests that a card name containing is found
        """
        card = create_test_card({"name": "foobar"})
        param = CardNameParam("foo", match_exact=False)
        self.assertIn(card, Card.objects.filter(param.query()))

    def test_name_not_contains(self):
        """
        Test that a card name that doesn't match isn't found
        """
        card = create_test_card({"name": "foo"})
        param = CardNameParam("bar", match_exact=False)
        self.assertNotIn(card, Card.objects.filter(param.query()))

    def test_name_match_invert(self):
        """
        Tests that
        """
        root_param = AndParam(True)
        card = create_test_card({"name": "foo"})
        param = CardNameParam("bar")
        root_param.add_parameter(param)
        self.assertIn(card, Card.objects.filter(root_param.query()))


class CardRulesParamTestCase(TestCase):
    """
    Tests for the card rules parameter
    """

    def test_rules_match(self):
        """
        Tests that the rules param will match cards that have the exact text
        :return:
        """
        card = create_test_card({"rules_text": "Flying"})
        param = CardRulesTextParam("Flying")
        self.assertIn(card, Card.objects.filter(param.query()))

    def test_rules_contains(self):
        """
        Tests that the rules param will match cards that contain the text
        """
        card = create_test_card({"rules_text": "Double Strike"})
        param = CardRulesTextParam("strike")
        self.assertIn(card, Card.objects.filter(param.query()))

    def test_rules_blank(self):
        """
        Tests that a card without text won't be found by a param with content
        """
        card = create_test_card({})
        param = CardRulesTextParam("Vigilance")
        self.assertNotIn(card, Card.objects.filter(param.query()))


class CardSetParamTestCase(TestCase):
    """
    Tests for card set parameter
    """

    def test_set_match(self):
        """
        Tests that a card in a set can be found with this param
        """
        card = create_test_card({})
        set_obj = create_test_set("Foobar", "FOO", {})
        create_test_card_printing(card, set_obj, {})
        param = CardSetParam(Set.objects.get(code="FOO"))
        self.assertIn(card, Card.objects.filter(param.query()))
