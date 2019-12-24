import logging
import json
from typing import Union, List, Dict, Optional, Tuple, Any

from django.core.management.base import BaseCommand
from cards.models import (
    Block,
    Card,
    CardLegality,
    CardPrice,
    CardPrinting,
    CardPrintingLanguage,
    CardRuling,
    Colour,
    Format,
    Language,
    PhysicalCard,
    Rarity,
    Set,
)
from cardsearch.parameters import (
    CardSearchParam,
    OrParam,
    AndParam,
    CardNumPowerParam,
    CardNameParam,
    CardNumToughnessParam,
    CardColourParam,
    CardColourCountParam,
    CardComplexColourParam,
)

from cardsearch.parser import Parser, ParseError

COLOUR_NAMES = {
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
    def start(self) -> CardSearchParam:
        return self.expression()

    def expression(self) -> CardSearchParam:
        print("expression")
        rv = self.match("term")
        or_group = None
        while True:
            op = self.maybe_keyword("or")
            if op is None:
                print("no or, breaking")
                break

            term = self.match("term")
            if or_group is None:
                or_group = OrParam()
                or_group.add_parameter(rv)
            or_group.add_parameter(term)

        return or_group or rv

    def term(self) -> CardSearchParam:
        print("term")
        rv = self.match("factor")
        and_group = None
        while True:
            self.maybe_keyword("and")

            term = self.maybe_match("factor")
            if term is None:
                print("no term, breaking")
                break

            if and_group is None:
                and_group = AndParam()
                and_group.add_parameter(rv)
            and_group.add_parameter(term)

            # if self.pos == self.len:
            #     print('end of string, breaking')
            #     break

        return and_group or rv

    def factor(self) -> CardSearchParam:
        print("factor")
        if self.maybe_keyword("("):
            rv = self.match("expression")
            self.keyword(")")

            return rv

        return self.match("parameter")

    def parameter(self) -> CardSearchParam:
        print("parameter")
        acceptable_param_types = "a-zA-Z0-9-"
        chars = [self.char(acceptable_param_types)]

        while True:
            char = self.maybe_char(acceptable_param_types)
            if char is None:
                break
            chars.append(char)

        param = "".join(chars).rstrip(" \t")
        if param in ("or", "and"):
            raise ParseError(self.pos + 1, "Bad logical operator %s", param)

        modifier = self.match("modifier")
        if modifier:
            if self.maybe_char("\"'"):
                value = self.quoted_string()
            else:
                value = self.unquoted()
        else:
            value = param
            param = "name"

        inverse = False
        if param.startswith("-"):
            param = param[1:]
            inverse = True

        if param == "name" or param == "n":
            return CardNameParam(card_name=value)
        elif param == "toughness":
            return CardNumToughnessParam(number=int(value), operator=modifier)
        elif param == "power":
            return CardNumPowerParam(number=int(value), operator=modifier)
        elif param == "color" or param == "c":
            return self.parse_colour_param(modifier, value, inverse)
        elif param in ("identity", "ci", "id"):
            return self.parse_colour_param(modifier, value, inverse, identity=True)

        raise ParseError(self.pos + 1, "Unknown parameter type %s", param)

    def modifier(self):
        chars = []
        acceptable_modifiers = ":<>="
        while True:
            char = self.maybe_char(acceptable_modifiers)
            if char is None:
                break
            chars.append(char)

        rv = "".join(chars).rstrip(" \t")
        return rv

    def unquoted(self) -> Union[str, float]:
        acceptable_chars = "0-9A-Za-z!$%&*+./;<=>?^_`|~-"
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

    def parse_colour_param(
        self, operator: str, text: str, inverse: bool = False, identity: bool = False
    ) -> Union[CardComplexColourParam, CardColourCountParam]:
        if operator not in [">", ">=", "=", ":", "<", "<="]:
            raise ParseError(self.pos + 1, "Unknown operator %s", operator)

        try:
            num = int(text)
            return CardColourCountParam(num, operator, identity=identity)
        except ValueError:
            pass

        return CardComplexColourParam(
            self.text_to_colours(text), operator, inverse, identity=identity
        )
