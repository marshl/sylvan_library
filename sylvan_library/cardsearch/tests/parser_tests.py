"""
Tests for the parser (search parameter tests are elsewhere)
"""
from django.test import TestCase

from cards.models.colour import Colour
from cards.tests import (
    create_test_card,
    create_test_set,
    create_test_card_printing,
    create_test_card_face,
)
from cardsearch.parameters.base_parameters import CardSearchAnd, CardSearchOr
from cardsearch.parameters.card_colour_parameters import (
    CardComplexColourParam,
)
from cardsearch.parameters.card_mana_cost_parameters import (
    CardManaCostComplexParam,
)
from cardsearch.parameters.card_name_parameters import CardNameParam
from cardsearch.parameters.card_rules_text_parameter import (
    CardRulesTextParam,
)
from cardsearch.parameters.card_type_parameters import (
    CardGenericTypeParam,
)
from cardsearch.parse_search import ParseSearch
from cardsearch.parser.query_parser import CardQueryParser


class ParserTests(TestCase):
    """
    Tests for the CardQueryParser
    """

    fixtures = ["colours.json"]

    def setUp(self) -> None:
        self.parser = CardQueryParser()

    def test_single_unquoted_param(self) -> None:
        """
        Tests that a single unquoted word is converted to a parameter
        """
        root_param = self.parser.parse("foo")
        self.assertIsInstance(root_param, CardNameParam)
        self.assertEqual(root_param.card_name, "foo")

    def test_and_param(self) -> None:
        """
        Tests that the and keyword in a query string is converted to a parameter group
        """
        root_param = self.parser.parse("foo and bar")
        self.assertIsInstance(root_param, CardSearchAnd)
        self.assertEqual(len(root_param.child_parameters), 2)
        foo_param, bar_param = root_param.child_parameters
        self.assertIsInstance(foo_param, CardNameParam)
        self.assertIsInstance(bar_param, CardNameParam)
        self.assertEqual(foo_param.card_name, "foo")
        self.assertEqual(bar_param.card_name, "bar")

    def test_or_param(self) -> None:
        """
        Tests that the or keyword is converted to a parameter group
        """
        root_param = self.parser.parse("foo or bar")
        self.assertIsInstance(root_param, CardSearchOr)
        self.assertEqual(len(root_param.child_parameters), 2)
        foo_param, bar_param = root_param.child_parameters
        self.assertIsInstance(foo_param, CardNameParam)
        self.assertIsInstance(bar_param, CardNameParam)
        self.assertEqual(foo_param.card_name, "foo")
        self.assertEqual(bar_param.card_name, "bar")

    def test_and_or_param(self) -> None:
        """
        Ensures that combining an "and" and an "or" parameter together works as expected
        """
        root_param = self.parser.parse("foo and (bar or baz)")
        self.assertIsInstance(root_param, CardSearchAnd)
        self.assertEqual(len(root_param.child_parameters), 2)
        foo_param, or_param = root_param.child_parameters
        self.assertIsInstance(foo_param, CardNameParam)
        self.assertIsInstance(or_param, CardSearchOr)
        self.assertEqual(foo_param.card_name, "foo")
        self.assertEqual(len(or_param.child_parameters), 2)
        bar_param, baz_param = or_param.child_parameters
        self.assertIsInstance(bar_param, CardNameParam)
        self.assertIsInstance(baz_param, CardNameParam)
        self.assertEqual(bar_param.card_name, "bar")
        self.assertEqual(baz_param.card_name, "baz")

    def test_double_unquoted_param(self) -> None:
        """
        Tests that multiple unquoted words in a query string are converted to two
        "and" grouped name parameters
        :return:
        """
        root_param = self.parser.parse("foo bar")
        self.assertIsInstance(root_param, CardSearchAnd)
        self.assertEqual(len(root_param.child_parameters), 2)
        first_param = root_param.child_parameters[0]
        second_param = root_param.child_parameters[1]
        self.assertIsInstance(first_param, CardNameParam)
        self.assertIsInstance(second_param, CardNameParam)
        self.assertEqual(first_param.card_name, "foo")
        self.assertEqual(second_param.card_name, "bar")

    def test_negated_param(self) -> None:
        """
        Tests that a negated query string is converted to the correct parameters
        """
        root_param = self.parser.parse("-foo")
        self.assertIsInstance(root_param, CardNameParam)
        self.assertEqual(root_param.card_name, "foo")
        self.assertTrue(root_param.negated)

    def test_negated_bracketed_param(self) -> None:
        """
        Tests that a negated grouped query string is converted to the correct parameters
        """
        root_param = self.parser.parse("-(name:foo)")
        self.assertIsInstance(root_param, CardNameParam)
        self.assertEqual(root_param.card_name, "foo")
        self.assertTrue(root_param.negated)

    def test_color_rg_param(self) -> None:
        """
        Tests that a multiple colour query is converted to the correct parametes
        """
        root_param = self.parser.parse("color:rg")
        self.assertIsInstance(root_param, CardComplexColourParam)
        self.assertEqual(root_param.colours, [Colour.red(), Colour.green()])
        self.assertEqual(root_param.operator, ">=")

    def test_multiple_colour_params(self) -> None:
        """
        Tests that a colour query string is converted to parameters
        """
        root_param = self.parser.parse("color>=uw -c:red")
        self.assertIsInstance(root_param, CardSearchAnd)
        self.assertEqual(len(root_param.child_parameters), 2)
        white_blue_param, not_red_param = root_param.child_parameters
        self.assertIsInstance(white_blue_param, CardComplexColourParam)
        self.assertIsInstance(not_red_param, CardComplexColourParam)

        self.assertListEqual(white_blue_param.colours, [Colour.blue(), Colour.white()])
        self.assertEqual(white_blue_param.operator, ">=")
        self.assertEqual(white_blue_param.negated, False)

        self.assertEqual(not_red_param.colours, [Colour.red()])
        self.assertEqual(not_red_param.operator, ">=")
        self.assertEqual(not_red_param.negated, True)

    def test_less_than_colour_identity(self) -> None:
        """
        Tests that a colour identity string is converted to parameters
        """
        root_param = self.parser.parse("id<=esper t:instant")
        self.assertIsInstance(root_param, CardSearchAnd)
        self.assertEqual(len(root_param.child_parameters), 2)
        esper_param, instant_param = root_param.child_parameters

        self.assertIsInstance(esper_param, CardComplexColourParam)
        self.assertEqual(
            esper_param.colours, [Colour.white(), Colour.blue(), Colour.black()]
        )
        self.assertEqual(esper_param.operator, "<=")
        self.assertFalse(esper_param.negated)

        self.assertIsInstance(instant_param, CardGenericTypeParam)
        self.assertEqual(instant_param.card_type, "instant")
        self.assertFalse(instant_param.negated)

    def test_no_colour_id_and_type_param(self) -> None:
        """
        Tests that a colour identity plus a type parameter parse ok
        """
        root_param = self.parser.parse("id:c t:land")
        self.assertIsInstance(root_param, CardSearchAnd)
        self.assertEqual(len(root_param.child_parameters), 2)
        id_param, type_param = root_param.child_parameters
        self.assertIsInstance(id_param, CardComplexColourParam)
        self.assertIsInstance(type_param, CardGenericTypeParam)
        self.assertEqual(id_param.colours, [Colour.colourless()])
        self.assertEqual(id_param.operator, "<=")

        self.assertEqual(type_param.operator, ":")
        self.assertEqual(type_param.card_type, "land")

    def test_legendary_merfolk_param(self) -> None:
        """
        Tests that a multi-part type parameter parses correctly
        """
        root_param = self.parser.parse("t:legend t:merfolk")
        self.assertIsInstance(root_param, CardSearchAnd)
        self.assertEqual(len(root_param.child_parameters), 2)
        legend_param, merfolk_param = root_param.child_parameters
        self.assertIsInstance(legend_param, CardGenericTypeParam)
        self.assertIsInstance(merfolk_param, CardGenericTypeParam)

        self.assertEqual(legend_param.operator, ":")
        self.assertEqual(legend_param.card_type, "legend")

        self.assertEqual(merfolk_param.operator, ":")
        self.assertEqual(merfolk_param.card_type, "merfolk")

    def test_noncreature_goblins_param(self) -> None:
        """
        Tests that a type param plus an inverted type param parse correctly
        """
        root_param = self.parser.parse("t:goblin -t:creature")
        self.assertIsInstance(root_param, CardSearchAnd)
        self.assertEqual(len(root_param.child_parameters), 2)
        goblin_param, noncreature_param = root_param.child_parameters
        self.assertIsInstance(goblin_param, CardGenericTypeParam)
        self.assertIsInstance(noncreature_param, CardGenericTypeParam)

        self.assertEqual(goblin_param.operator, ":")
        self.assertEqual(goblin_param.card_type, "goblin")

        self.assertEqual(noncreature_param.operator, ":")
        self.assertEqual(noncreature_param.card_type, "creature")
        self.assertTrue(noncreature_param.negated)

    def test_creature_draw_param(self) -> None:
        """
        Tests that a type and text parameter work in conjunction
        """
        root_param = self.parser.parse("t:creature o:draw")
        self.assertIsInstance(root_param, CardSearchAnd)
        self.assertEqual(len(root_param.child_parameters), 2)
        creature_param, draw_param = root_param.child_parameters
        self.assertIsInstance(creature_param, CardGenericTypeParam)
        self.assertIsInstance(draw_param, CardRulesTextParam)

        self.assertEqual(creature_param.operator, ":")
        self.assertEqual(creature_param.card_type, "creature")

        self.assertFalse(draw_param.exact_match)
        self.assertEqual(draw_param.card_rules, "draw")

    def test_card_name_enters_param(self) -> None:
        """
        Tests that a quoted string contain tilde (name substitution) is converted to a parameter
        :return:
        """
        root_param = self.parser.parse('o:"~ enters the battlefield tapped"')
        self.assertIsInstance(root_param, CardRulesTextParam)
        self.assertFalse(root_param.exact_match)
        self.assertEqual(root_param.card_rules, "~ enters the battlefield tapped")

    def test_mana_gu_param(self) -> None:
        """
        Tests a mana cost query is converted to a parameter ok
        """
        root_param = self.parser.parse("mana:{G}{U}")
        self.assertIsInstance(root_param, CardManaCostComplexParam)
        self.assertFalse(root_param.negated)
        self.assertEqual(root_param.generic_mana, 0)
        self.assertEqual(root_param.symbol_counts["g"], 1)
        self.assertEqual(root_param.symbol_counts["u"], 1)
        self.assertEqual(root_param.symbol_counts["b"], 0)

    def test_mana_2ww_param(self) -> None:
        """
        Tests a mana cost query is converted to the right parameters
        """
        root_param = self.parser.parse("m:2WW")
        self.assertIsInstance(root_param, CardManaCostComplexParam)
        self.assertFalse(root_param.negated)
        self.assertEqual(root_param.generic_mana, 2)
        self.assertEqual(root_param.symbol_counts["w"], 2)
        self.assertEqual(root_param.symbol_counts["u"], 0)
        self.assertEqual(root_param.symbol_counts["b"], 0)
        self.assertEqual(root_param.symbol_counts["r"], 0)
        self.assertEqual(root_param.symbol_counts["g"], 0)

    def test_mana_3wu_param(self) -> None:
        """
        Tests a mana cost query is converted to the right parameters
        """
        root_param = self.parser.parse("mana>3wu")
        self.assertIsInstance(root_param, CardManaCostComplexParam)
        self.assertFalse(root_param.negated)
        self.assertEqual(root_param.operator, ">")
        self.assertEqual(root_param.generic_mana, 3)
        self.assertEqual(root_param.symbol_counts["w"], 1)
        self.assertEqual(root_param.symbol_counts["u"], 1)
        self.assertEqual(root_param.symbol_counts["b"], 0)
        self.assertEqual(root_param.symbol_counts["r"], 0)
        self.assertEqual(root_param.symbol_counts["g"], 0)


class ColourContainsTestCase(TestCase):
    # pylint: disable=too-many-instance-attributes
    """
    Tests for the card name parameter
    """
    fixtures = ["colours.json"]

    def setUp(self) -> None:
        self.set_obj = create_test_set("Setty", "SET", {})
        self.red_card = create_test_card({"name": "Red Card"})
        create_test_card_face(self.red_card, {"colour": Colour.RED})
        self.red_card_printing = create_test_card_printing(
            self.red_card, self.set_obj, {}
        )

        self.green_card = create_test_card({"name": "Green Card"})
        create_test_card_face(self.green_card, {"colour": Colour.GREEN})
        self.green_card_printing = create_test_card_printing(
            self.green_card, self.set_obj, {}
        )

        self.blue_card = create_test_card({"name": "Blue Card"})
        create_test_card_face(self.blue_card, {"colour": Colour.BLUE})
        self.blue_card_printing = create_test_card_printing(
            self.blue_card, self.set_obj, {}
        )

        self.red_green_card = create_test_card({"name": "Red/Green Card"})
        create_test_card_face(
            self.red_green_card, {"colour": Colour.RED | Colour.GREEN}
        )
        self.red_green_card_printing = create_test_card_printing(
            self.red_green_card, self.set_obj, {}
        )

        self.red_green_black_card = create_test_card({"name": "Red/Black/Green Card"})
        create_test_card_face(
            self.red_green_black_card,
            {"colour": Colour.RED | Colour.GREEN | Colour.BLACK},
        )

        self.red_green_black_card_printing = create_test_card_printing(
            self.red_green_black_card, self.set_obj, {}
        )

        self.blue_red_card = create_test_card({"name": "Blue/Red Card"})
        create_test_card_face(self.blue_red_card, {"colour": Colour.BLUE | Colour.RED})
        self.blue_red_card_printing = create_test_card_printing(
            self.blue_red_card, self.set_obj, {}
        )

        self.parse_search = ParseSearch()

    def tearDown(self) -> None:
        self.red_card.delete()
        self.green_card.delete()

    def test_eq_colour_search(self) -> None:
        """
        Test colour match
        """
        self.parse_search.query_string = "color=rg"
        self.parse_search.build_parameters()
        results = self.parse_search.get_queryset().all()
        self.assertNotIn(self.red_card, results)
        self.assertNotIn(self.green_card, results)
        self.assertIn(self.red_green_card, results)
        self.assertNotIn(self.red_green_black_card, results)
        self.assertNotIn(self.blue_red_card, results)

    def test_gte_colour_search(self) -> None:
        """
        Test colour match
        """
        self.parse_search.query_string = "color:rg"
        self.parse_search.build_parameters()
        results = self.parse_search.get_queryset().all()
        self.assertNotIn(self.red_card, results)
        self.assertNotIn(self.green_card, results)
        self.assertIn(self.red_green_card, results)
        self.assertIn(self.red_green_black_card, results)
        self.assertNotIn(self.blue_red_card, results)

    def test_gt_colour_search(self) -> None:
        """
        Test colour match
        """
        self.parse_search.query_string = "color>rg"
        self.parse_search.build_parameters()
        results = self.parse_search.get_queryset().all()
        self.assertNotIn(self.red_card, results)
        self.assertNotIn(self.green_card, results)
        self.assertNotIn(self.red_green_card, results)
        self.assertIn(self.red_green_black_card, results)
        self.assertNotIn(self.blue_red_card, results)
        self.assertNotIn(self.blue_card, results)

    def test_lte_colour_search(self) -> None:
        """
        Test colour match
        """
        self.parse_search.query_string = "color<=rg"
        self.parse_search.build_parameters()
        results = self.parse_search.get_queryset().all()
        self.assertIn(self.red_card, results)
        self.assertIn(self.green_card, results)
        self.assertIn(self.red_green_card, results)
        self.assertNotIn(self.red_green_black_card, results)
        self.assertNotIn(self.blue_red_card, results)
        self.assertNotIn(self.blue_card, results)

    def test_lt_colour_search(self) -> None:
        """
        Test colour match
        """
        self.parse_search.query_string = "color<rg"
        self.parse_search.build_parameters()
        results = self.parse_search.get_queryset().all()
        self.assertIn(self.red_card, results)
        self.assertIn(self.green_card, results)
        self.assertNotIn(self.red_green_card, results)
        self.assertNotIn(self.red_green_black_card, results)
        self.assertNotIn(self.blue_red_card, results)
        self.assertNotIn(self.blue_card, results)
