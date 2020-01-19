from django.test import TestCase

from cards.models import Card
from cards.tests import create_test_card

from cardsearch.parameters import (
    AndParam,
    OrParam,
    CardNameParam,
    CardComplexColourParam,
    CardGenericTypeParam,
    CardRulesTextParam,
)

from cardsearch.parse_search import ParseSearch
from cardsearch.parser import CardQueryParser


class ParserTests(TestCase):
    def setUp(self):
        self.parser = CardQueryParser()

    def test_single_unquoted_param(self):
        root_param = self.parser.parse("foo")
        self.assertIsInstance(root_param, CardNameParam)
        self.assertEquals(root_param.card_name, "foo")

    def test_and_param(self):
        root_param = self.parser.parse("foo and bar")
        self.assertIsInstance(root_param, AndParam)
        self.assertEquals(len(root_param.child_parameters), 2)
        foo_param, bar_param = root_param.child_parameters
        self.assertIsInstance(foo_param, CardNameParam)
        self.assertIsInstance(bar_param, CardNameParam)
        self.assertEquals(foo_param.card_name, "foo")
        self.assertEquals(bar_param.card_name, "bar")

    def test_or_param(self):
        root_param = self.parser.parse("foo or bar")
        self.assertIsInstance(root_param, OrParam)
        self.assertEquals(len(root_param.child_parameters), 2)
        foo_param, bar_param = root_param.child_parameters
        self.assertIsInstance(foo_param, CardNameParam)
        self.assertIsInstance(bar_param, CardNameParam)
        self.assertEquals(foo_param.card_name, "foo")
        self.assertEquals(bar_param.card_name, "bar")

    def test_double_unquoted_param(self):
        root_param = self.parser.parse("foo bar")
        self.assertIsInstance(root_param, AndParam)
        self.assertEquals(len(root_param.child_parameters), 2)
        first_param = root_param.child_parameters[0]
        second_param = root_param.child_parameters[1]
        self.assertIsInstance(first_param, CardNameParam)
        self.assertIsInstance(second_param, CardNameParam)
        self.assertEquals(first_param.card_name, "foo")
        self.assertEquals(second_param.card_name, "bar")

    def test_negated_param(self):
        root_param = self.parser.parse("-foo")
        self.assertIsInstance(root_param, CardNameParam)
        self.assertEquals(root_param.card_name, "foo")
        self.assertTrue(root_param.negated)

    def test_negated_bracketed_param(self):
        root_param = self.parser.parse("-(name:foo)")
        self.assertIsInstance(root_param, CardNameParam)
        self.assertEquals(root_param.card_name, "foo")
        self.assertTrue(root_param.negated)

    def test_color_rg_param(self):
        root_param = self.parser.parse("color:rg")
        self.assertIsInstance(root_param, CardComplexColourParam)
        self.assertEquals(
            root_param.colours, Card.colour_flags.red | Card.colour_flags.green
        )
        self.assertEquals(root_param.operator, ">=")

    def test_multiple_colour_params(self):
        root_param = self.parser.parse("color>=uw -c:red")
        self.assertIsInstance(root_param, AndParam)
        self.assertEquals(len(root_param.child_parameters), 2)
        white_blue_param, not_red_param = root_param.child_parameters
        self.assertIsInstance(white_blue_param, CardComplexColourParam)
        self.assertIsInstance(not_red_param, CardComplexColourParam)

        self.assertEquals(
            white_blue_param.colours, Card.colour_flags.white | Card.colour_flags.blue
        )
        self.assertEquals(white_blue_param.operator, ">=")
        self.assertEquals(white_blue_param.negated, False)

        self.assertEquals(not_red_param.colours, Card.colour_flags.red)
        self.assertEquals(not_red_param.operator, ">=")
        self.assertEquals(not_red_param.negated, True)

    def test_less_than_colour_identity(self):
        root_param = self.parser.parse("id<=esper t:instant")
        self.assertIsInstance(root_param, AndParam)
        self.assertEquals(len(root_param.child_parameters), 2)
        esper_param, instant_param = root_param.child_parameters

        self.assertIsInstance(esper_param, CardComplexColourParam)
        self.assertEquals(
            esper_param.colours,
            Card.colour_flags.white | Card.colour_flags.blue | Card.colour_flags.black,
        )
        self.assertEquals(esper_param.operator, "<=")
        self.assertFalse(esper_param.negated)

        self.assertIsInstance(instant_param, CardGenericTypeParam)
        self.assertEquals(instant_param.card_type, "instant")
        self.assertFalse(instant_param.negated)

    def test_no_colour_id_and_type_param(self):
        root_param = self.parser.parse("id:c t:land")
        self.assertIsInstance(root_param, AndParam)
        self.assertEquals(len(root_param.child_parameters), 2)
        id_param, type_param = root_param.child_parameters
        self.assertIsInstance(id_param, CardComplexColourParam)
        self.assertIsInstance(type_param, CardGenericTypeParam)
        self.assertEquals(id_param.colours, 0)
        self.assertEquals(id_param.operator, "<=")

        self.assertEquals(type_param.operator, ":")
        self.assertEquals(type_param.card_type, "land")

    def test_legendary_merfolk_param(self):
        root_param = self.parser.parse("t:legend t:merfolk")
        self.assertIsInstance(root_param, AndParam)
        self.assertEquals(len(root_param.child_parameters), 2)
        legend_param, merfolk_param = root_param.child_parameters
        self.assertIsInstance(legend_param, CardGenericTypeParam)
        self.assertIsInstance(merfolk_param, CardGenericTypeParam)

        self.assertEquals(legend_param.operator, ":")
        self.assertEquals(legend_param.card_type, "legend")

        self.assertEquals(merfolk_param.operator, ":")
        self.assertEquals(merfolk_param.card_type, "merfolk")

    def test_noncreature_goblins_param(self):
        root_param = self.parser.parse("t:goblin -t:creature")
        self.assertIsInstance(root_param, AndParam)
        self.assertEquals(len(root_param.child_parameters), 2)
        goblin_param, noncreature_param = root_param.child_parameters
        self.assertIsInstance(goblin_param, CardGenericTypeParam)
        self.assertIsInstance(noncreature_param, CardGenericTypeParam)

        self.assertEquals(goblin_param.operator, ":")
        self.assertEquals(goblin_param.card_type, "goblin")

        self.assertEquals(noncreature_param.operator, ":")
        self.assertEquals(noncreature_param.card_type, "creature")
        self.assertTrue(noncreature_param.negated)

    def test_creature_draw_param(self):
        root_param = self.parser.parse("t:creature o:draw")
        self.assertIsInstance(root_param, AndParam)
        self.assertEquals(len(root_param.child_parameters), 2)
        creature_param, draw_param = root_param.child_parameters
        self.assertIsInstance(creature_param, CardGenericTypeParam)
        self.assertIsInstance(draw_param, CardRulesTextParam)

        self.assertEquals(creature_param.operator, ":")
        self.assertEquals(creature_param.card_type, "creature")

        self.assertFalse(draw_param.exact_match)
        self.assertEquals(draw_param.card_rules, "draw")

    def test_card_name_enters_param(self):
        root_param = self.parser.parse('o:"~ enters the battlefield tapped"')
        self.assertIsInstance(root_param, CardRulesTextParam)
        self.assertFalse(root_param.exact_match)
        self.assertEquals(root_param.card_rules, "~ enters the battlefield tapped")


class ColourContainsTestCase(TestCase):
    """
    Tests for the card name parameter
    """

    def setUp(self):
        self.red_card = create_test_card({"colour_flags": Card.colour_flags.red})
        self.green_card = create_test_card({"colour_flags": Card.colour_flags.green})
        self.red_green_card = create_test_card(
            {"colour_flags": Card.colour_flags.red | Card.colour_flags.green}
        )
        self.red_green_black_card = create_test_card(
            {
                "colour_flags": Card.colour_flags.red
                | Card.colour_flags.green
                | Card.colour_flags.black
            }
        )
        self.blue_red_card = create_test_card(
            {"colour_flags": Card.colour_flags.blue | Card.colour_flags.red}
        )
        self.parse_search = ParseSearch()

    def tearDown(self):
        self.red_card.delete()
        self.green_card.delete()

    def test_name_match(self):
        self.parse_search.query_string = "color:rg"
        self.parse_search.build_parameters()
        results = self.parse_search.get_queryset().all()
        self.assertNotIn(
            self.red_card,
            results,
            "A red card shouldn't be found in a green/red search",
        )
        self.assertNotIn(
            self.green_card,
            results,
            "A green card shouldn't be found in a red/green search",
        )
        self.assertIn(
            self.red_green_card,
            results,
            "A red/green card should be found in a red/green search",
        )
        self.assertIn(
            self.red_green_black_card,
            results,
            "A red/green/black card should be found in a red/green search",
        )
        self.assertNotIn(
            self.blue_red_card,
            results,
            "A blue/red card shouldn't found in a red/green search')",
        )
