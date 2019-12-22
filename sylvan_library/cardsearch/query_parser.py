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

from cardsearch.parser import Parser, ParseError


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
