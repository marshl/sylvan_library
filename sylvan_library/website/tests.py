"""
Module for website test cases
"""

from django.test import TestCase

from website.templatetags.mana_templates import replace_mana_symbols, replace_loyalty_symbols


class ManaReplaceTestCase(TestCase):
    """
    Tests for the mana string replacement functions
    """

    def test_simple_replace(self) -> None:
        """
        Test that a card with a {0} cost is converted correctly
        """
        mana_cost = '{R}'
        self.assertEqual('<i class="ms ms-r ms-cost"></i>', replace_mana_symbols(mana_cost))

    def test_simple_replace_lowercsae(self) -> None:
        """
        Test that a card with a lowercase cost is replaced correctly
        """
        mana_cost = '{u}'
        self.assertEqual('<i class="ms ms-u ms-cost"></i>', replace_mana_symbols(mana_cost))

    def test_phyrexian_replace(self) -> None:
        """
        Test that a phyrexian mana card is replaced correctly
        """
        mana_cost = '{W/P}'
        self.assertEqual('<i class="ms ms-p ms-w ms-cost"></i>', replace_mana_symbols(mana_cost))

    def test_hybrid_replace(self):
        """
        Test that a hybrid mana cost if replaced correctly
        """
        mana_cost = '{W/U}'
        self.assertEqual('<i class="ms ms-wu ms-cost"></i>', replace_mana_symbols(mana_cost))

    def test_large_number_replace(self) -> None:
        """
        Test that a multiple numeral card is replaced correctly
        """
        mana_cost = '{11}'
        self.assertEqual('<i class="ms ms-11 ms-cost"></i>', replace_mana_symbols(mana_cost))


class LoyaltyReplaceTestCase(TestCase):
    """
    Tests for the loyalty string replacement functions
    """

    def test_zero_replace(self) -> None:
        """
        Test that a card with a 0 loyalty cost ability is converted correctly
        """
        rules = '0: Some rules.'
        self.assertEqual('<i class="ms ms-loyalty-0 ms-loyalty-zero"></i>: Some rules.',
                         replace_loyalty_symbols(rules))

    def test_positive_replace(self) -> None:
        """
        Test that a card with a positive loyalty cost ability is converted correctly
        """
        rules = '+5: Some rules.'
        self.assertEqual('<i class="ms ms-loyalty-5 ms-loyalty-up"></i>: Some rules.',
                         replace_loyalty_symbols(rules))

    def test_negative_replace(self) -> None:
        """
        Test that a card with a negative loyalty cost ability is converted correctly
        """
        rules = '−3: Some rules.'
        self.assertEqual('<i class="ms ms-loyalty-3 ms-loyalty-down"></i>: Some rules.',
                         replace_loyalty_symbols(rules))
