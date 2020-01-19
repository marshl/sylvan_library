from typing import Union, List, Dict, Optional, Tuple, Any

from django.contrib.auth.models import User
from django.db.models import Func, Value, F
from cards.models import Card, Set
from cardsearch.parameters import (
    CardSearchParam,
    OrParam,
    AndParam,
    CardNumPowerParam,
    CardNameParam,
    CardNumToughnessParam,
    CardCmcParam,
    CardColourCountParam,
    CardComplexColourParam,
    CardOwnershipCountParam,
    CardGenericTypeParam,
    CardRulesTextParam,
    CardSetParam,
    CardManaCostComplexParam,
)

from .base_parser import Parser, ParseError

COLOUR_NAMES = {
    "colourless": 0,
    "c": 0,
    "white": Card.colour_flags.white,
    "w": Card.colour_flags.white,
    "blue": Card.colour_flags.blue,
    "u": Card.colour_flags.blue,
    "black": Card.colour_flags.black,
    "b": Card.colour_flags.black,
    "red": Card.colour_flags.red,
    "r": Card.colour_flags.red,
    "green": Card.colour_flags.green,
    "g": Card.colour_flags.green,
    "azorius": Card.colour_flags.white | Card.colour_flags.blue,
    "dimir": Card.colour_flags.blue | Card.colour_flags.black,
    "rakdos": Card.colour_flags.black | Card.colour_flags.red,
    "gruul": Card.colour_flags.red | Card.colour_flags.green,
    "selesnya": Card.colour_flags.green | Card.colour_flags.white,
    "orzhov": Card.colour_flags.white | Card.colour_flags.black,
    "izzet": Card.colour_flags.blue | Card.colour_flags.red,
    "golgari": Card.colour_flags.black | Card.colour_flags.green,
    "boros": Card.colour_flags.red | Card.colour_flags.white,
    "simic": Card.colour_flags.green | Card.colour_flags.blue,
    "esper": Card.colour_flags.white | Card.colour_flags.blue | Card.colour_flags.black,
    "grixis": Card.colour_flags.blue | Card.colour_flags.black | Card.colour_flags.red,
    "jund": Card.colour_flags.black | Card.colour_flags.red | Card.colour_flags.green,
    "naya": Card.colour_flags.red | Card.colour_flags.green | Card.colour_flags.white,
    "bant": Card.colour_flags.green | Card.colour_flags.white | Card.colour_flags.blue,
    "abzan": Card.colour_flags.white
    | Card.colour_flags.black
    | Card.colour_flags.green,
    "jeskai": Card.colour_flags.blue | Card.colour_flags.red | Card.colour_flags.white,
    "sultai": Card.colour_flags.black
    | Card.colour_flags.green
    | Card.colour_flags.blue,
    "mardu": Card.colour_flags.red | Card.colour_flags.white | Card.colour_flags.black,
    "temur": Card.colour_flags.green | Card.colour_flags.blue | Card.colour_flags.red,
    "chaos": Card.colour_flags.blue
    | Card.colour_flags.black
    | Card.colour_flags.red
    | Card.colour_flags.green,
    "aggression": Card.colour_flags.black
    | Card.colour_flags.red
    | Card.colour_flags.green
    | Card.colour_flags.white,
    "altruism": Card.colour_flags.red
    | Card.colour_flags.green
    | Card.colour_flags.white
    | Card.colour_flags.blue,
    "growth": Card.colour_flags.green
    | Card.colour_flags.white
    | Card.colour_flags.blue
    | Card.colour_flags.black,
    "artifice": Card.colour_flags.white
    | Card.colour_flags.blue
    | Card.colour_flags.black
    | Card.colour_flags.red,
}


class CardQueryParser(Parser):
    def __init__(self, user: User = None):
        super().__init__()
        self.user: User = user

    def start(self) -> CardSearchParam:
        return self.or_group()

    def or_group(self) -> CardSearchParam:
        subgroup = self.match("and_group")
        or_group = None
        while True:
            op = self.maybe_keyword("or")
            if op is None:
                break

            param_group = self.match("and_group")
            if or_group is None:
                or_group = OrParam()
                or_group.add_parameter(subgroup)
            or_group.add_parameter(param_group)

        return or_group or subgroup

    def and_group(self) -> CardSearchParam:
        rv = self.match("parameter_group")
        and_group = None
        while True:
            self.maybe_keyword("and")
            param_group = self.maybe_match("parameter_group")
            if not param_group:
                break

            if and_group is None:
                and_group = AndParam()
                and_group.add_parameter(rv)
            and_group.add_parameter(param_group)

        return and_group or rv

    def parameter_group(self) -> CardSearchParam:
        is_negated = self.maybe_char("-") is not None
        if self.maybe_keyword("("):
            or_group = self.match("or_group")
            self.keyword(")")
            or_group.negated = is_negated
            return or_group

        parameter = self.match(
            "quoted_name_parameter", "normal_parameter", "unquoted_name_parameter"
        )
        parameter.negated = is_negated
        return parameter

    def param_type(self) -> str:
        acceptable_param_types = "a-zA-Z0-9"
        chars = [self.char(acceptable_param_types)]

        while True:
            char = self.maybe_char(acceptable_param_types)
            if char is None:
                break
            chars.append(char)

        return "".join(chars).rstrip(" \t").lower()

    def normal_parameter(self) -> CardSearchParam:
        parameter_type = self.match("param_type")
        operator = self.match("operator")
        parameter_value = self.match("quoted_string", "unquoted")
        return self.parse_param(parameter_type, operator, parameter_value)

    def quoted_name_parameter(self) -> CardSearchParam:
        parameter_value = self.match("quoted_string")
        return self.parse_param("name", ":", parameter_value)

    def unquoted_name_parameter(self) -> CardSearchParam:
        parameter_value = self.match("unquoted")
        if parameter_value in ("or", "and"):
            raise ParseError(
                self.pos + 1,
                'Expected a parameter but got "%s" instead',
                parameter_value,
            )
        return self.parse_param("name", ":", parameter_value)

    def parse_param(self, parameter_type: str, operator: str, parameter_value: str):
        if parameter_type == "name" or parameter_type == "n":
            return self.parse_name_param(operator, parameter_value)
        elif parameter_type in ("p", "power", "pow"):
            return self.parse_power_param(operator, parameter_value)
        elif parameter_type in ("toughness", "tough", "tou"):
            return self.parse_toughness_param(operator, parameter_value)
        elif parameter_type in ("cmc",):
            return self.parse_cmc_param(operator, parameter_value)
        elif parameter_type == "color" or parameter_type == "c":
            return self.parse_colour_param(operator, parameter_value)
        elif parameter_type in ("identity", "ci", "id"):
            return self.parse_colour_param(operator, parameter_value, identity=True)
        elif parameter_type in ("own", "have"):
            return self.parse_ownership_param(operator, parameter_value)
        elif parameter_type in ("t", "type"):
            return self.parse_type_param(operator, parameter_value)
        elif parameter_type in ("o", "oracle", "text"):
            return self.parse_text_param(operator, parameter_value)
        elif parameter_type in ("m", "mana", "cost"):
            return self.parse_mana_cost_param(operator, parameter_value)
        elif parameter_type in ("s", "set"):
            return self.parse_set_param(operator, parameter_value)

        raise ParseError(self.pos + 1, "Unknown parameter type %s", parameter_type)

    def operator(self):
        acceptable_operators = ":<>="
        chars = [self.char(acceptable_operators)]
        while True:
            char = self.maybe_char(acceptable_operators)
            if char is None:
                break
            chars.append(char)

        rv = "".join(chars).rstrip(" \t")
        return rv

    def unquoted(self) -> Union[str, float]:
        acceptable_chars = "0-9A-Za-z!$%&*+./;<=>?^_`|~{}/-:"
        chars = [self.char(acceptable_chars)]

        while True:
            char = self.maybe_char(acceptable_chars)
            if char is None:
                break
            chars.append(char)

        rv = "".join(chars).rstrip(" \t")
        return rv

    def quoted_string(self) -> str:
        quote = self.char("\"'")
        chars = []

        escape_sequences = {"b": "\b", "f": "\f", "n": "\n", "r": "\r", "t": "\t"}

        while True:
            char = self.char()
            if char == quote:
                break
            elif char == "\\":
                chars.append(escape_sequences.get(char, char))
            else:
                chars.append(char)

        return "".join(chars)

    def text_to_colours(self, text: str) -> int:
        text = text.lower()
        if text in COLOUR_NAMES:
            return int(COLOUR_NAMES[text])

        result = 0
        for char in text:
            if char not in COLOUR_NAMES:
                raise ParseError(0, "Unknown colour %s at %s", text, self.pos)

            result |= COLOUR_NAMES[char]
        return int(result)

    def parse_name_param(
        self, operator: str, text: str, inverse: bool = False
    ) -> CardNameParam:
        if operator not in ("=", ":"):
            raise ParseError(
                self.pos, "Unsupported operator for name parameter %s", operator
            )

        match_exact = operator == "="
        if text.startswith("!"):
            match_exact = True
            text = text[1:]
        return CardNameParam(card_name=text, match_exact=match_exact)

    def parse_colour_param(
        self, operator: str, text: str, identity: bool = False
    ) -> Union[CardComplexColourParam, CardColourCountParam]:
        if operator not in [">", ">=", "=", ":", "<", "<="]:
            raise ParseError(self.pos + 1, "Unknown operator %s", operator)

        try:
            num = int(text)
            return CardColourCountParam(num, operator, identity=identity)
        except ValueError:
            pass

        return CardComplexColourParam(
            self.text_to_colours(text), operator, identity=identity
        )

    def parse_ownership_param(
        self, operator: str, text: str, inverse: bool = False
    ) -> CardOwnershipCountParam:

        if self.user.is_anonymous:
            raise ParseError(
                self.pos + 1, "Cannot search by ownership if you aren't logged in"
            )

        if operator == ":" and text == "any":
            return CardOwnershipCountParam(self.user, ">=", 1)

        if operator == ":" and text == "none":
            return CardOwnershipCountParam(self.user, "=", 0)

        try:
            count = int(text)
        except ValueError:
            raise ParseError(self.pos + 1, "Cannot parse number %s", text)

        return CardOwnershipCountParam(self.user, operator, count)

    def parse_type_param(self, operator: str, text: str) -> CardGenericTypeParam:
        return CardGenericTypeParam(text, operator)

    def parse_text_param(self, operator: str, text: str) -> CardRulesTextParam:
        if operator not in (":", "="):
            raise ParseError(
                self.pos + 1, "Unsupported operator for oracle search: '%s'", operator
            )
        return CardRulesTextParam(text, exact=operator == "=")

    def parse_mana_cost_param(
        self, operator: str, text: str
    ) -> CardManaCostComplexParam:
        if operator not in ("<", "<=", ":", "=", ">", ">="):
            raise ParseError(
                self.pos + 1, "Unsupported operator for mana cost search %s", operator
            )
        return CardManaCostComplexParam(text, operator)

    def parse_set_param(self, operator: str, text: str):
        if operator not in ("<", "<=", ":", "=", ">", ">="):
            raise ParseError(
                self.pos + 1, "Unsupported operator for set parameter %s", operator
            )

        try:
            card_set = Set.objects.get(code__iexact=text)
        except Set.DoesNotExist:
            raise ParseError(self.pos + 1, "Unknown set %s", text)

        return CardSetParam(card_set)

    def parse_power_param(self, operator: str, text: str) -> CardNumPowerParam:
        power = self.parse_numeric_parameter("power", operator, text)
        return CardNumPowerParam(power, operator)

    def parse_toughness_param(self, operator: str, text: str) -> CardNumToughnessParam:
        toughness = self.parse_numeric_parameter("toughness", operator, text)
        return CardNumToughnessParam(toughness, operator)

    def parse_cmc_param(self, operator: str, text: str) -> CardCmcParam:
        cmc = self.parse_numeric_parameter("converted mana cost", operator, text)
        return CardCmcParam(cmc, operator)

    def parse_numeric_parameter(
        self, param_name: str, operator: str, text: str
    ) -> Union[int, F]:
        if operator not in (":", "=", "<=", "<", ">=", ">"):
            raise ParseError(
                self.pos + 1,
                "Unsupported operator for %s search %s",
                param_name,
                operator,
            )

        if text in ("toughness", "tough", "tou"):
            return F("num_toughness")
        elif text in ("power", "pow"):
            return F("num_power")
        elif text in ("loyalty", "loy"):
            return F("num_loyalty")
        elif text in ("cmc",):
            return F("cmc")

        try:
            return int(text)
        except ValueError:
            raise ParseError(self.pos + 1, "Could not convert %s to number", text)
