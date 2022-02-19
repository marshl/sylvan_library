"""
The module for staging tests
"""
from django.test import TestCase
from data_import.staging import StagedCard, StagedCardFace, convert_number_field_to_numerical


class StagedCardTestCase(TestCase):
    """
    The tests cases for StagedCard
    """

    def test_get_type(self) -> None:
        """
        Tests that a card with multiple types has the correct type string
        """
        staged_card_face = StagedCardFace(
            {"name": "test", "types": ["Legendary", "Creature"]}
        )
        self.assertEqual(staged_card_face.types, ["Legendary", "Creature"])

    def test_is_reserved(self) -> None:
        """
        Tests the reserved status of a card
        """
        staged_card = StagedCard({"name": "test", "isReserved": True})
        self.assertTrue(staged_card.is_reserved)

    def test_colour_weight(self) -> None:
        """
        Tests the colour weight of a card
        """
        staged_card_face = StagedCardFace(
            {"name": "test", "manaCost": "{1}{G}{G}", "manaValue": 3}
        )
        self.assertEqual(2, staged_card_face.colour_weight)

    def test_colour_weight_colourless(self) -> None:
        """
        Tests that a colourless card has the correct colour weight
        """
        staged_card_face = StagedCardFace(
            {"name": "test", "manaCost": "{11}", "manaValue": 11}
        )
        self.assertEqual(0, staged_card_face.colour_weight)

    def test_colour_weight_heavy(self) -> None:
        """
        Tests that a card with only coloured mana symbols has the correct colour weight
        """
        staged_card_face = StagedCardFace(
            {"name": "test", "manaCost": "{B}{B}{B}{B}", "manaValue": 4}
        )
        self.assertEqual(4, staged_card_face.colour_weight)

    def test_colour_weight_none(self) -> None:
        """
        Tests that a card without any mana cost has zero colour weight
        """
        staged_card_face = StagedCardFace({"name": "test"})
        self.assertEqual(0, staged_card_face.colour_weight)

    def test_token_type(self) -> None:
        """
        Tests that a token card has its types parsed correctly
        """
        staged_card_face = StagedCardFace(
            {"name": "test", "type": "Token Legendary Creature — Monkey"}
        )
        self.assertEqual(
            "Token Legendary Creature — Monkey", staged_card_face.type_line
        )

    def test_token_subtype(self) -> None:
        """
        Tests that a token card has its subtypes parsed correctly
        """
        staged_card_face = StagedCardFace(
            {"name": "test", "type": "Token Legendary Creature — Monkey"}
        )
        self.assertEqual(
            "Token Legendary Creature — Monkey", staged_card_face.type_line
        )


class NumberConversionTestCase(TestCase):
    """
    Test cases for conversion functions
    """
    def test_convert_number_field_to_numerical(self):
        param_list = [("", 0), (None, 0), ("1", 1), ("2", 2), ("*", 0), ("2+*", 2)]
        for param1, param2 in param_list:
            with self.subTest():
                self.assertEqual(convert_number_field_to_numerical(param1), param2)
