from django.test import TestCase
from data_import.staging import *


class StagedCardTestCase(TestCase):
    def test_get_type(self):
        staged_card = StagedCard({'types': ['Legendary', 'Creature']})
        self.assertEqual(staged_card.get_types(), 'Legendary Creature')

    def test_is_reserved(self):
        staged_card = StagedCard({'reserved': True})
        self.assertTrue(staged_card.is_reserved())

    def test_colour_weight(self):
        staged_card = StagedCard({'manaCost': '{1}{G}{G}', 'convertedManaCost': 3})
        self.assertEquals(2, staged_card.get_colour_weight())

    def test_colour_weight_colourless(self):
        staged_card = StagedCard({'manaCost': '{11}', 'convertedManaCost': 11})
        self.assertEquals(0, staged_card.get_colour_weight())

    def test_colour_weight_heavy(self):
        staged_card = StagedCard({'manaCost': '{B}{B}{B}{B}', 'convertedManaCost': 4})
        self.assertEquals(4, staged_card.get_colour_weight())

    def test_colour_weight_none(self):
        staged_card = StagedCard({})
        self.assertEquals(0, staged_card.get_colour_weight())
