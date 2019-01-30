"""
Module for website test cases
"""

from django.test import TestCase

from website.templatetags.mana_templates import replace_mana_symbols


class MtgFontTestCase(TestCase):
    """
    Tests for the MTG Font string replacement functions
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
