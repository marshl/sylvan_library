"""
The module for searching tests
"""

from django.test import TestCase

from cards.models.card import CardPrinting
from cards.models.sets import Set
from cards.tests import (
    create_test_card,
    create_test_card_printing,
    create_test_set,
    create_test_card_face,
)
from cardsearch.parameters.base_parameters import CardSearchAnd
from cardsearch.parameters.card_name_parameters import CardNameParam
from cardsearch.parameters.card_rules_text_parameter import CardRulesTextParam
from cardsearch.parameters.card_set_parameters import CardSetParam


class CardNameParamTestCase(TestCase):
    """
    Tests for the card name parameter
    """

    def test_name_match(self) -> None:
        """
        Tests that a card name exact match is found
        """
        card = create_test_card({"name": "foo"})
        set_obj = create_test_set("Setty", "SET", {})
        printing = create_test_card_printing(card, set_obj, {})
        param = CardNameParam("foo", match_exact=True)
        self.assertIn(printing, CardPrinting.objects.filter(param.query()))

    def test_name_contains_no_match(self) -> None:
        """
        Tests that a card name exact match is found
        """
        card = create_test_card({"name": "foobar"})
        set_obj = create_test_set("Setty", "SET", {})
        printing = create_test_card_printing(card, set_obj, {})
        param = CardNameParam("foo", match_exact=True)
        self.assertNotIn(printing, CardPrinting.objects.filter(param.query()))

    def test_name_match_inverse(self) -> None:
        """
        Tests that a card name exact match is found
        """
        card = create_test_card({"name": "foo"})
        set_obj = create_test_set("Setty", "SET", {})
        printing = create_test_card_printing(card, set_obj, {})
        param = CardNameParam("foo", match_exact=True)
        param.negated = True
        self.assertNotIn(printing, CardPrinting.objects.filter(param.query()))

    def test_name_contains(self) -> None:
        """
        Tests that a card name containing is found
        """
        card = create_test_card({"name": "foobar"})
        set_obj = create_test_set("Setty", "SET", {})
        printing = create_test_card_printing(card, set_obj, {})
        param = CardNameParam("foo", match_exact=False)
        self.assertIn(printing, CardPrinting.objects.filter(param.query()))

    def test_name_not_contains(self) -> None:
        """
        Test that a card name that doesn't match isn't found
        """
        card = create_test_card({"name": "foo"})
        set_obj = create_test_set("Setty", "SET", {})
        printing = create_test_card_printing(card, set_obj, {})
        param = CardNameParam("bar", match_exact=False)
        self.assertNotIn(printing, CardPrinting.objects.filter(param.query()))

    def test_name_match_invert(self) -> None:
        """
        Tests that
        """
        root_param = CardSearchAnd()
        root_param.negated = True
        card = create_test_card({"name": "foo"})
        set_obj = create_test_set("Setty", "SET", {})
        printing = create_test_card_printing(card, set_obj, {})
        param = CardNameParam("bar")
        root_param.add_parameter(param)
        self.assertIn(printing, CardPrinting.objects.filter(root_param.query()))


class CardRulesParamTestCase(TestCase):
    """
    Tests for the card rules parameter
    """

    def test_rules_match(self) -> None:
        """
        Tests that the rules param will match cards that have the exact text
        :return:
        """
        card = create_test_card()
        create_test_card_face(card, {"rules_text": "Flying"})
        set_obj = create_test_set("Setty", "SET", {})
        printing = create_test_card_printing(card, set_obj, {})
        param = CardRulesTextParam("Flying")
        self.assertIn(printing, CardPrinting.objects.filter(param.query()))

    def test_rules_contains(self) -> None:
        """
        Tests that the rules param will match cards that contain the text
        """
        card = create_test_card()
        create_test_card_face(card, {"rules_text": "Double strike"})
        set_obj = create_test_set("Setty", "SET", {})
        printing = create_test_card_printing(card, set_obj, {})
        param = CardRulesTextParam("strike")
        self.assertIn(printing, CardPrinting.objects.filter(param.query()))

    def test_rules_blank(self) -> None:
        """
        Tests that a card without text won't be found by a param with content
        """
        card = create_test_card({})
        set_obj = create_test_set("Setty", "SET", {})
        printing = create_test_card_printing(card, set_obj, {})
        param = CardRulesTextParam("Vigilance")
        self.assertNotIn(printing, CardPrinting.objects.filter(param.query()))


class CardSetParamTestCase(TestCase):
    """
    Tests for card set parameter
    """

    def test_set_match(self) -> None:
        """
        Tests that a card in a set can be found with this param
        """
        card = create_test_card({})
        set_obj = create_test_set("Foobar", "FOO", {})
        printing = create_test_card_printing(card, set_obj, {})
        param = CardSetParam(Set.objects.get(code="FOO"))
        self.assertIn(printing, CardPrinting.objects.filter(param.query()))
