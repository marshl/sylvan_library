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
)

# https://www.booleanworld.com/building-recursive-descent-parsers-definitive-guide/
class ParseError(Exception):
    def __init__(self, pos: int, msg: str, *args):
        self.pos = pos
        self.msg = msg
        self.args = args

    def __str__(self):
        return "%s at position %s" % (self.msg % self.args, self.pos)


class Parser:
    def __init__(self):
        self.cache = {}
        self.text = ""
        self.pos = -1
        self.len = 0

    def parse(self, text: str) -> Any:
        self.text = text
        self.pos = -1
        self.len = len(text) - 1
        rv = self.start()
        self.assert_end()
        return rv

    def start(self):
        pass

    def assert_end(self) -> None:
        if self.pos < self.len:
            raise ParseError(
                self.pos + 1,
                "Expected end of string but got %s",
                self.text[self.pos + 1],
            )

    def eat_whitespace(self) -> None:
        while self.pos < self.len and self.text[self.pos + 1] in " \f\v\r\t\n":
            self.pos += 1

    def split_char_ranges(self, chars: str) -> List[str]:
        try:
            return self.cache[chars]
        except KeyError:
            pass

        rv = []
        index = 0
        length = len(chars)

        while index < length:
            if index + 2 < length and chars[index + 1] == "-":
                if chars[index] >= chars[index + 2]:
                    raise ValueError("Bad character range")
                rv.append(chars[index : index + 3])
                index += 3
            else:
                rv.append(chars[index])
                index += 1
        self.cache[chars] = rv
        return rv

    def char(self, chars: Optional[str] = None) -> str:
        if self.pos >= self.len:
            raise ParseError(
                self.pos + 1,
                "Expected %s but got end of string",
                "character" if chars is None else "[%s]" % chars,
            )

        next_char = self.text[self.pos + 1]
        if chars is None:
            self.pos += 1
            return next_char

        for char_range in self.split_char_ranges(chars):
            if len(char_range) == 1:
                if next_char == char_range:
                    self.pos += 1
                    return next_char
            elif char_range[0] <= next_char <= char_range[2]:
                self.pos += 1
                return next_char

        raise ParseError(
            self.pos + 1,
            "Expected %s but got %s",
            "character" if chars is None else "[%s]" % chars,
            next_char,
        )

    def keyword(self, *keywords: str) -> str:
        self.eat_whitespace()
        if self.pos >= self.len:
            raise ParseError(
                self.pos + 1, "Expected %s but got end of string", ",".join(keywords)
            )

        for keyword in keywords:
            low = self.pos + 1
            high = low + len(keyword)

            if self.text[low:high] == keyword:
                self.pos += len(keyword)
                self.eat_whitespace()
                return keyword

        raise ParseError(
            self.pos + 1,
            "Expected %s but got %s",
            ",".join(keywords),
            self.text[self.pos + 1],
        )

    # def item(self) -> Union[str, int]:
    #     return self.match("number", "word")

    def match(self, *rules):
        self.eat_whitespace()
        last_error_pos = -1
        last_exception = None
        last_error_rules = []

        for rule in rules:
            initial_pos = self.pos
            try:
                rv = getattr(self, rule)()
                self.eat_whitespace()
                return rv
            except ParseError as e:
                self.pos = initial_pos
                if e.pos > last_error_pos:
                    last_exception = e
                    last_error_pos = e.pos
                    last_error_rules.clear()
                    last_error_rules.append(rule)
                elif e.pos == last_error_pos:
                    last_error_rules.append(rule)

        if len(last_error_rules) == 1:
            raise last_exception
        else:
            raise ParseError(
                last_error_pos,
                "Expected %s but got %s",
                ",".join(last_error_rules),
                self.text[last_error_pos],
            )

    def maybe_char(self, chars: Optional[str] = None) -> Optional[str]:
        try:
            return self.char(chars)
        except ParseError:
            return None

    def maybe_match(self, *rules: str) -> Optional[str]:
        try:
            return self.match(*rules)
        except ParseError:
            return None

    def maybe_keyword(self, *keywords: str) -> Optional[str]:
        try:
            return self.keyword(*keywords)
        except ParseError:
            return None


class CalcParser(Parser):
    def start(self):
        return self.expression()

    def expression(self):
        rv = self.match("term")
        while True:
            op = self.maybe_keyword("+", "-")
            if op is None:
                break

            term = self.match("term")
            if op == "+":
                rv += term
            else:
                rv -= term

        return rv

    def term(self):
        rv = self.match("factor")
        while True:
            op = self.maybe_keyword("*", "/")
            if op is None:
                break

            term = self.match("factor")
            if op == "*":
                rv *= term
            else:
                rv /= term

        return rv

    def factor(self):
        if self.maybe_keyword("("):
            rv = self.match("expression")
            self.keyword(")")

            return rv

        return self.match("number")

    def number(self):
        chars = []

        sign = self.maybe_keyword("+", "-")
        if sign is not None:
            chars.append(sign)

        chars.append(self.char("0-9"))

        while True:
            char = self.maybe_char("0-9")
            if char is None:
                break
            chars.append(char)

        if self.maybe_char("."):
            chars.append(".")
            chars.append(self.char("0-9"))

            while True:
                char = self.maybe_char("0-9")
                if char is None:
                    break
                chars.append(char)

        rv = float("".join(chars))
        return rv


class JSONParser(Parser):
    def eat_whitespace(self) -> None:
        is_processing_comment = False

        while self.pos < self.len:
            char = self.text[self.pos + 1]
            if is_processing_comment:
                if char == "\n":
                    is_processing_comment = False
            else:
                if char == "#":
                    is_processing_comment = True
                elif char not in " \f\v\r\t\n":
                    break

            self.pos += 1

    def start(self) -> Union[str, dict, list]:
        return self.match("any_type")

    def any_type(self) -> Union[str, dict, list]:
        return self.match("complex_type", "primitive_type")

    def primitive_type(self) -> Union[None, bool, str]:
        return self.match("null", "boolean", "quoted_string", "unquoted")

    def complex_type(self) -> Union[list, dict]:
        return self.match("list", "map")

    def list(self) -> list:
        rv = []

        self.keyword("[")
        while True:
            item = self.maybe_match("any_type")
            if item is None:
                break

            rv.append(item)

            if not self.maybe_keyword(","):
                break

        self.keyword("]")
        return rv

    def map(self) -> dict:
        rv = {}

        self.keyword("{")
        while True:
            item = self.maybe_match("pair")
            if item is None:
                break

            rv[item[0]] = item[1]

            if not self.maybe_keyword(","):
                break

        self.keyword("}")
        return rv

    def pair(self) -> Tuple[str, Union[str, dict, list]]:
        key = self.match("quoted_string", "unquoted")

        if type(key) is not str:
            raise ParseError(
                self.pos + 1, "Expected string but got number", self.text[self.pos + 1]
            )

        self.keyword(":")
        value = self.match("any_type")

        return key, value

    def null(self) -> None:
        self.keyword("null")
        return None

    def boolean(self) -> bool:
        boolean = self.keyword("true", "false")
        return boolean[0] == "t"

    def unquoted(self) -> Union[str, float]:
        acceptable_chars = "0-9A-Za-z \t!$%&()*+./;<=>?^_`|~-"
        number_type = int

        chars = [self.char(acceptable_chars)]

        while True:
            char = self.maybe_char(acceptable_chars)
            if char is None:
                break

            if char in "Ee.":
                number_type = float

            chars.append(char)

        rv = "".join(chars).rstrip(" \t")
        try:
            return number_type(rv)
        except ValueError:
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
                escape = self.char()
                if escape == "u":
                    code_point = []
                    for i in range(4):
                        code_point.append(self.char("0-9a-fA-F"))

                    chars.append(chr(int("".join(code_point), 16)))
                else:
                    chars.append(escape_sequences.get(char, char))
            else:
                chars.append(char)

        return "".join(chars)


class CardQueryParser(Parser):
    def start(self) -> CardSearchParam:
        return self.expression()

    def expression(self) -> CardSearchParam:
        rv = self.match("term")
        or_group = None
        while True:
            op = self.maybe_keyword("or")
            if op is None:
                break

            term = self.match("term")
            if or_group is None:
                or_group = OrParam()
                or_group.add_parameter(rv)
            or_group.add_parameter(term)
            pass
            # if op == "+":
            #     rv += term
            # else:
            #     rv -= term

        return or_group or rv

    def term(self) -> CardSearchParam:
        rv = self.match("factor")
        and_group = None
        while True:
            op = self.maybe_keyword("and")
            if op is None:
                break

            term = self.match("factor")
            if and_group is None:
                and_group = AndParam()
                and_group.add_parameter(rv)
            and_group.add_parameter(term)
            pass
            # if op == "*":
            #     rv *= term
            # else:
            #     rv /= term

        return and_group or rv

    #
    # def expression(self):
    #     rv = self.match("factor")
    #     while True:
    #         op = self.maybe_keyword("and", "or")
    #         if op is None:
    #             break
    #
    #         term = self.match("parameter")
    #         print("term", term, "op", op)
    #
    #         # if op == "+":
    #         #     rv += term
    #         # else:
    #         #     rv -= term
    #
    #     return rv

    # def term(self):
    #     rv = self.match("factor")
    #     while True:
    #         op = self.maybe_keyword("and", "or")
    #         if op is None:
    #             break
    #
    #         term = self.match("factor")
    #         # if op == "*":
    #         #     rv *= term
    #         # else:
    #         #     rv /= term
    #
    #     return rv

    def factor(self) -> CardSearchParam:
        if self.maybe_keyword("("):
            rv = self.match("expression")
            self.keyword(")")

            return rv

        return self.match("parameter")

    # def number(self):
    #     chars = []
    #
    #     chars.append(self.char("0-9"))
    #
    #     while True:
    #         char = self.maybe_char("0-9")
    #         if char is None:
    #             break
    #         chars.append(char)
    #
    #     if self.maybe_char("."):
    #         chars.append(".")
    #         chars.append(self.char("0-9"))
    #
    #         while True:
    #             char = self.maybe_char("0-9")
    #             if char is None:
    #                 break
    #             chars.append(char)
    #
    #     rv = float("".join(chars))
    #     return rv

    def parameter(self) -> CardSearchParam:
        # acceptable_chars = "0-9A-Za-z \t!$%&()*+./;<=>?^_`|~-"

        acceptable_param_types = "a-zA-Z0-9"
        chars = [self.char(acceptable_param_types)]

        while True:
            char = self.maybe_char(acceptable_param_types)
            if char is None:
                break
            chars.append(char)

        param = "".join(chars).rstrip(" \t")
        # print("param", param)
        modifier = self.match("modifier")
        if modifier:
            # rv += modifier
            # print("param+modifier", modifier)
            if self.maybe_char("\"'"):
                value = self.quoted_string()
            else:
                value = self.unquoted()
            # rv += self.match("quoted_string", "unquoted")
            # print("param+modifier+rest", value)

        else:
            value = param
            param = "name"

        if param == "name":
            return CardNameParam(card_name=value)
        elif param == "toughness":
            return CardNumToughnessParam(number=int(value), operator=modifier)
        elif param == "power":
            return CardNumPowerParam(number=int(value), operator=modifier)

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
        acceptable_chars = "0-9A-Za-z\t!$%&*+./;<=>?^_`|~-"
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


class Command(BaseCommand):

    help = ()

    def __init__(self, stdout=None, stderr=None, no_color=False):
        self.logger = logging.getLogger("django")
        super().__init__(stdout=stdout, stderr=stderr, no_color=no_color)

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        parser = CalcParser()
        # print(parser.parse("1 + 2"))
        # print(parser.parse("3 * 4"))
        # print(parser.parse("4/5"))
        # print(parser.parse("(1 + 2) * 3"))
        # print(parser.parse("(1 + (2 + ( 4 * (5 / (6 * 7)))))"))
        # print(parser.parse("1 * (2 + 3) * 4"))
        parser = JSONParser()
        r = parser.parse(
            "{'hello': 'there', 'general': 'kenobi', 'foo': '20394702983y02934)(*&)#$&(#*@Q$'}"
        )
        # print(r)

        parser = CardQueryParser()
        # print(parser.parse("name"))
        # # print(parser.parse("name:"))
        # r = parser.parse("power>10 and toughness<3")
        # print(r)
        r = parser.parse("power>=10 and toughness<=2 or power<=2 and toughness>=10")
        cards = Card.objects.filter(r.query())
        print(cards.all())
        pass

        r = parser.parse("power:12")
        cards = Card.objects.filter(r.query())
        print(cards.all())
        pass
