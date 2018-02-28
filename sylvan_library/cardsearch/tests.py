from django.test import TestCase

from .cardsearch import *
from cards.tests import create_test_card, create_test_card_printing, create_test_set


class CardNameParamTestCase(TestCase):
    def test_name_match(self):
        card = create_test_card({'name': 'foo'})
        param = CardNameSearchParam('foo')
        self.assertIn(card, param.get_result())

    def test_name_contains(self):
        card = create_test_card({'name': 'foobar'})
        param = CardNameSearchParam('foo')
        self.assertIn(card, param.get_result())

    def test_name_not_contains(self):
        card = create_test_card({'name': 'foo'})
        param = CardNameSearchParam('bar')
        self.assertNotIn(card, param.get_result())

    def test_name_match_invert(self):
        card = create_test_card({'name': 'foo'})
        param = CardNameSearchParam('bar')
        param.boolean_flag = False
        self.assertIn(card, param.get_result())


class CardRulesParamTestCase(TestCase):
    def test_rules_match(self):
        card = create_test_card({'rules_text': 'Flying'})
        param = CardRulesSearchParam('Flying')
        self.assertIn(card, param.get_result())

    def test_rules_contains(self):
        card = create_test_card({'rules_text': 'Double Strike'})
        param = CardRulesSearchParam('strike')
        self.assertIn(card, param.get_result())

    def test_rules_blank(self):
        card = create_test_card({})
        param = CardRulesSearchParam('Vigilance')
        self.assertNotIn(card, param.get_result())


class CardSetParamTestCase(TestCase):
    def test_set_match(self):
        card = create_test_card({})
        set_obj = create_test_set('Foobar', 'FOO')
        printing = create_test_card_printing(card, set_obj)
        param = CardSetParam(Set.objects.get(code='FOO'))
        self.assertIn(card, param.get_result())
