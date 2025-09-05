"""
The module for searching tests
"""

from django.test import TestCase

from cards.models.card import CardPrinting, Card
from cards.tests import (
    create_test_card,
    create_test_card_printing,
    create_test_set,
    create_test_card_face,
)
from cardsearch.parameters.base_parameters import (
    CardSearchAnd,
    ParameterArgs,
    QueryContext,
    CardSearchContext,
)
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
        param = CardNameParam(ParameterArgs(value="foo", operator="=", keyword="name"))
        self.assertIn(
            printing,
            CardPrinting.objects.filter(
                param.query(QueryContext(search_mode=CardSearchContext.PRINTING))
            ),
        )

    def test_name_contains_no_match(self) -> None:
        """
        Tests that a card name exact match is found
        """
        card = create_test_card({"name": "foobar"})
        set_obj = create_test_set("Setty", "SET", {})
        printing = create_test_card_printing(card, set_obj, {})
        param = CardNameParam(ParameterArgs(value="foo", operator="=", keyword="name"))
        self.assertNotIn(
            printing,
            CardPrinting.objects.filter(
                param.query(QueryContext(search_mode=CardSearchContext.PRINTING))
            ),
        )

    def test_name_match_inverse(self) -> None:
        """
        Tests that a card name exact match is found
        """
        card = create_test_card({"name": "foo"})
        set_obj = create_test_set("Setty", "SET", {})
        printing = create_test_card_printing(card, set_obj, {})
        param = CardNameParam(ParameterArgs(value="foo", operator="=", keyword="name"))
        param.negated = True
        self.assertNotIn(
            printing,
            CardPrinting.objects.filter(
                param.query(
                    query_context=QueryContext(search_mode=CardSearchContext.PRINTING)
                )
            ),
        )

    def test_name_contains(self) -> None:
        """
        Tests that a card name containing is found
        """
        card = create_test_card({"name": "foobar"})
        param = CardNameParam(ParameterArgs(value="foo", operator=":", keyword="name"))
        self.assertIn(
            card,
            Card.objects.filter(param.query(QueryContext())),
        )

    def test_name_contains_case_insensitive(self) -> None:
        """
        Tests that a card name containing is found
        """
        card = create_test_card({"name": "Foobar"})
        param = CardNameParam(ParameterArgs(value="foo", operator=":", keyword="name"))
        self.assertIn(
            card,
            Card.objects.filter(param.query(QueryContext())),
        )

    def test_name_not_contains(self) -> None:
        """
        Test that a card name that doesn't match isn't found
        """
        card = create_test_card({"name": "foo"})
        param = CardNameParam(ParameterArgs("name", "=", "bar"))
        self.assertNotIn(card, Card.objects.filter(param.query(QueryContext())))

    def test_name_match_invert(self) -> None:
        """
        Tests that
        """
        root_param = CardSearchAnd()
        root_param.negated = True
        card = create_test_card({"name": "foo"})
        param = CardNameParam(ParameterArgs(value="bar", operator=":", keyword="name"))
        root_param.add_parameter(param)
        self.assertIn(card, Card.objects.filter(root_param.query(QueryContext())))


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
        param = CardRulesTextParam(ParameterArgs("rules", ":", "Flying"))
        self.assertIn(card, Card.objects.filter(param.query(QueryContext())))

    def test_rules_contains(self) -> None:
        """
        Tests that the rules param will match cards that contain the text
        """
        card = create_test_card()
        create_test_card_face(card, {"rules_text": "Double strike"})
        param = CardRulesTextParam(ParameterArgs("rules", ":", "strike"))
        self.assertIn(card, Card.objects.filter(param.query(QueryContext())))

    def test_rules_blank(self) -> None:
        """
        Tests that a card without text won't be found by a param with content
        """
        card = create_test_card({})
        param = CardRulesTextParam(ParameterArgs("rules", ":", "Vigilance"))
        self.assertNotIn(card, Card.objects.filter(param.query(QueryContext())))


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
        param = CardSetParam(ParameterArgs("set", ":", "FOO"))
        param.validate(QueryContext())
        self.assertIn(card, Card.objects.filter(param.query(QueryContext())))
        self.assertIn(
            printing,
            CardPrinting.objects.filter(
                param.query(QueryContext(search_mode=CardSearchContext.PRINTING))
            ),
        )
