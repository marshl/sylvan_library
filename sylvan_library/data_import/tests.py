"""
The module for staging tests
"""
from django.test import TestCase
from data_import.staging import (
    StagedCard
)


class StagedCardTestCase(TestCase):
    """
    The tests cases for StagedCard
    """

    def test_get_type(self):
        """
        Tests that a card with multiple types has the correct type string
        """
        staged_card = StagedCard({'types': ['Legendary', 'Creature']})
        self.assertEqual(staged_card.get_types(), 'Legendary Creature')

    def test_is_reserved(self):
        """
        Tests the reserved status of a card
        """
        staged_card = StagedCard({'reserved': True})
        self.assertTrue(staged_card.is_reserved())

    def test_colour_weight(self):
        """
        Tests the colour weight of a card
        """
        staged_card = StagedCard({'manaCost': '{1}{G}{G}', 'convertedManaCost': 3})
        self.assertEqual(2, staged_card.get_colour_weight())

    def test_colour_weight_colourless(self):
        """
        Tests that a colourless card has the correct colour weight
        """
        staged_card = StagedCard({'manaCost': '{11}', 'convertedManaCost': 11})
        self.assertEqual(0, staged_card.get_colour_weight())

    def test_colour_weight_heavy(self):
        """
        Tests that a card with only coloured mana symbols has the correct colour weight
        """
        staged_card = StagedCard({'manaCost': '{B}{B}{B}{B}', 'convertedManaCost': 4})
        self.assertEqual(4, staged_card.get_colour_weight())

    def test_colour_weight_none(self):
        """
        Tests that a card without any mana cost has zero colour weight
        """
        staged_card = StagedCard({})
        self.assertEqual(0, staged_card.get_colour_weight())

    def test_token_type(self):
        """
        Tests that a token card has its types parsed correctly
        """
        staged_card = StagedCard({'type': 'Token Legendary Creature — Monkey'}, is_token=True)
        self.assertEqual('Token Legendary Creature', staged_card.get_types())

    def test_token_subtype(self):
        """
        Tests that a token card has its subtypes parsed correctly
        """
        staged_card = StagedCard({'type': 'Token Legendary Creature — Monkey'}, is_token=True)
        self.assertEqual('Monkey', staged_card.get_subtypes())
