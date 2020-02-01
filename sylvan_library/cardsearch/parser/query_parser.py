"""
Module for the card query recursive descent parser
"""
from typing import Union, Optional

from django.contrib.auth.models import User
from django.db.models import F

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

COLOUR_NAMES_TO_FLAGS = {
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


def parse_numeric_parameter(param_name: str, operator: str, text: str) -> Union[int, F]:
    """
    Parses a numeric parameter and returns the value that should be used for an operator
    :param param_name: The name of the parameter
    :param operator: The parameter operator
    :param text: The parameter text
    :return: The value to use for the operator
    """
    if operator not in (":", "=", "<=", "<", ">=", ">"):
        raise ValueError(f"Cannot use {operator} operator for {param_name} search")

    if text in ("toughness", "tough", "tou"):
        return F("num_toughness")

    if text in ("power", "pow"):
        return F("num_power")

    if text in ("loyalty", "loy"):
        return F("num_loyalty")

    if text in ("cmc", "cost"):
        return F("cmc")

    try:
        return int(text)
    except ValueError:
        raise ValueError(f"Could not convert {text} to number")


def parse_cmc_param(operator: str, text: str) -> CardCmcParam:
    """
    Parses a converted mana cost parameter
    :param operator: The parameter operator
    :param text: The mana cost text
    :return: The converted mana cost parameter
    """
    cmc = parse_numeric_parameter("converted mana cost", operator, text)
    return CardCmcParam(cmc, operator)


def parse_toughness_param(operator: str, text: str) -> CardNumToughnessParam:
    """
    Parses a card numerical toughness parameter
    :param operator: The parameter operator
    :param text: The parameter text
    :return: Te toughness parameter
    """
    toughness = parse_numeric_parameter("toughness", operator, text)
    return CardNumToughnessParam(toughness, operator)


def parse_power_param(operator: str, text: str) -> CardNumPowerParam:
    """
    Parses a card power parameter
    :param operator: The parameter operator
    :param text: The power text
    :return: The card power parameter
    """
    power = parse_numeric_parameter("power", operator, text)
    return CardNumPowerParam(power, operator)


def parse_text_param(operator: str, text: str) -> CardRulesTextParam:
    """
    Parses and returns a text parameter
    :param operator: The parameter operator
    :param text: The parameter text
    :return: The rules parameter
    """
    if operator not in (":", "="):
        raise ValueError(f'Unsupported operator for oracle search: "{operator}"')
    return CardRulesTextParam(text, exact=operator == "=")


def parse_type_param(operator: str, text: str) -> CardGenericTypeParam:
    """
    Parses a card type parameter
    :param operator: The parameter operator
    :param text: The type text
    :return: The card type parameter
    """
    return CardGenericTypeParam(text, operator)


def parse_set_param(operator: str, text: str):
    """
    Creates a card set parameter from the given operator and text
    :param operator: The operator
    :param text: The parameter text
    :return: The set parameter
    """
    if operator not in ("<", "<=", ":", "=", ">", ">="):
        raise ValueError(f"Unsupported operator for set parameter {operator}")

    card_set: Optional[Set] = None
    try:
        card_set = Set.objects.get(code__iexact=text)
    except Set.DoesNotExist:
        pass
    if card_set:
        return CardSetParam(card_set)

    try:
        card_set = Set.objects.get(name__icontains=text)
    except Set.DoesNotExist:
        raise ValueError(f'Unknown set "{text}"')
    except Set.MultipleObjectsReturned:
        raise ValueError(f'Multiple sets match "{text}"')

    return CardSetParam(card_set)


def parse_mana_cost_param(operator: str, text: str) -> CardManaCostComplexParam:
    """
    Creates a mana cost parameter from the given operator and text
    :param operator: The parameter operator
    :param text: The mana cost text
    :return: The created mana cost parameter
    """
    if operator not in ("<", "<=", ":", "=", ">", ">="):
        raise ValueError(f"Unsupported operator for mana cost search {operator}")
    return CardManaCostComplexParam(text, operator)


def text_to_colours(text: str) -> int:
    """
    Converts text to a list of colour flag
    Raises a value error if the text doesn't match any known colours
    :param text: The colour text to parse
    :return: The colours or'd together
    """
    text = text.lower()
    if text in COLOUR_NAMES_TO_FLAGS:
        return int(COLOUR_NAMES_TO_FLAGS[text])

    result = 0
    for char in text:
        if char not in COLOUR_NAMES_TO_FLAGS:
            raise ValueError(f"Unknown colour {text}")

        result |= COLOUR_NAMES_TO_FLAGS[char]
    return int(result)


def parse_name_param(operator: str, text: str) -> CardNameParam:
    """
    Parses a card name parameter
    :param operator: The parameter operator
    :param text: The name text
    :return: The name parameter
    """
    if operator not in ("=", ":"):
        raise ValueError(f"Unsupported operator for name parameter {operator}")

    match_exact = operator == "="
    if text.startswith("!"):
        match_exact = True
        text = text[1:]
    return CardNameParam(card_name=text, match_exact=match_exact)


def parse_colour_param(
    operator: str, text: str, identity: bool = False
) -> Union[CardComplexColourParam, CardColourCountParam]:
    """
    Parses a card colour parameter
    :param operator: The parameter operator
    :param text: The colour text
    :param identity: Whether this is for a colour identity search or not
    :return:
    """
    if operator not in [">", ">=", "=", ":", "<", "<="]:
        raise ValueError(f"Unknown operator {operator}")

    try:
        num = int(text)
        return CardColourCountParam(num, operator, identity=identity)
    except ValueError:
        pass

    return CardComplexColourParam(text_to_colours(text), operator, identity=identity)


class CardQueryParser(Parser):
    """
    Parser for parsing a scryfall-style card qquery
    """

    def __init__(self, user: User = None):
        super().__init__()
        self.user: User = user

    def start(self) -> CardSearchParam:
        """
        Starts matching with the text
        :return: The root parameter node
        """
        return self.or_group()

    def or_group(self) -> CardSearchParam:
        """
        Matches a group of parameters separated by "or"s or the single "and" group if
        that's all this group contains
        :return: The OR group
        """
        subgroup = self.match("and_group")
        or_group = None
        while True:
            or_keyword = self.maybe_keyword("or")
            if or_keyword is None:
                break

            param_group = self.match("and_group")
            if or_group is None:
                or_group = OrParam()
                or_group.add_parameter(subgroup)
            or_group.add_parameter(param_group)

        return or_group or subgroup

    def and_group(self) -> CardSearchParam:
        """
        Attempts to parse a list of parameters separated by "and"s
        :return: The AndParam group, or the single parameter if there is only one
        """
        result = self.match("parameter_group")
        and_group = None
        while True:
            self.maybe_keyword("and")
            param_group = self.maybe_match("parameter_group")
            if not param_group:
                break

            if and_group is None:
                and_group = AndParam()
                and_group.add_parameter(result)
            and_group.add_parameter(param_group)

        return and_group or result

    def parameter_group(self) -> CardSearchParam:
        """
        Attempts to parse a parameter group (type + operator + value)
        :return: The parsed parameter
        """
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
        """
        Parses the type of a parameter
        :return: The parameter type
        """
        acceptable_param_types = "a-zA-Z0-9"
        chars = [self.char(acceptable_param_types)]

        while True:
            char = self.maybe_char(acceptable_param_types)
            if char is None:
                break
            chars.append(char)

        return "".join(chars).rstrip(" \t").lower()

    def normal_parameter(self) -> CardSearchParam:
        """
        Attempts to parse a parameter with a type, operator and value
        :return: THe parsed parameter
        """
        parameter_type = self.match("param_type")
        operator = self.match("operator")
        parameter_value = self.match("quoted_string", "unquoted")
        return self.parse_param(parameter_type, operator, parameter_value)

    def quoted_name_parameter(self) -> CardSearchParam:
        """
        Attempts to parse a parameter that is just a quoted string
        :return: The name parameter
        """
        parameter_value = self.match("quoted_string")
        return self.parse_param("name", ":", parameter_value)

    def unquoted_name_parameter(self) -> CardSearchParam:
        """
        Attempts to parse a parameter that is just an unquoted string
        :return: The name parameter
        """
        parameter_value = self.match("unquoted")
        if parameter_value in ("or", "and"):
            raise ParseError(
                self.pos + 1,
                'Expected a parameter but got "%s" instead',
                parameter_value,
            )
        return self.parse_param("name", ":", parameter_value)

    def parse_param(self, parameter_type: str, operator: str, parameter_value: str):
        # pylint: disable=too-many-return-statements
        """
        REturns a parameter based on the given parameter type
        :param parameter_type: The type of the parameter
        :param operator: The parameter operator
        :param parameter_value: The parameter alue
        :return: The parsed parameter
        """
        if parameter_type in ("name", "n"):
            return parse_name_param(operator, parameter_value)
        if parameter_type in ("p", "power", "pow"):
            return parse_power_param(operator, parameter_value)
        if parameter_type in ("toughness", "tough", "tou"):
            return parse_toughness_param(operator, parameter_value)
        if parameter_type in ("cmc",):
            return parse_cmc_param(operator, parameter_value)
        if parameter_type in ("color", "colour", "c"):
            return parse_colour_param(operator, parameter_value)
        if parameter_type in ("identity", "ci", "id"):
            return parse_colour_param(operator, parameter_value, identity=True)
        if parameter_type in ("own", "have"):
            return self.parse_ownership_param(operator, parameter_value)
        if parameter_type in ("t", "type"):
            return parse_type_param(operator, parameter_value)
        if parameter_type in ("o", "oracle", "text"):
            return parse_text_param(operator, parameter_value)
        if parameter_type in ("m", "mana", "cost"):
            return parse_mana_cost_param(operator, parameter_value)
        if parameter_type in ("s", "set"):
            return parse_set_param(operator, parameter_value)

        raise ParseError(self.pos + 1, "Unknown parameter type %s", parameter_type)

    def operator(self):
        """
        Attempts to parse a parameter operator
        :return: The parameter operator
        """
        acceptable_operators = ":<>="
        chars = [self.char(acceptable_operators)]
        while True:
            char = self.maybe_char(acceptable_operators)
            if char is None:
                break
            chars.append(char)

        return "".join(chars).rstrip(" \t")

    def unquoted(self) -> Union[str, float]:
        """
        Attempts to parse an unquoted string (basically any characters without spaces)
        :return: The contents of the unquoted string
        """
        acceptable_chars = "0-9A-Za-z!$%&*+./;<=>?^_`|~{}/-:"
        chars = [self.char(acceptable_chars)]

        while True:
            char = self.maybe_char(acceptable_chars)
            if char is None:
                break
            chars.append(char)

        return "".join(chars).rstrip(" \t")

    def quoted_string(self) -> str:
        """
        Attempts to parse a double quoted string
        Spaces are allowed inside the string
        :return: The contents of the double quoted string (including the quotes)
        """
        quote = self.char("\"'")
        chars = []

        escape_sequences = {"b": "\b", "f": "\f", "n": "\n", "r": "\r", "t": "\t"}

        while True:
            char = self.char()
            if char == quote:
                break

            if char == "\\":
                chars.append(escape_sequences.get(char, char))
            else:
                chars.append(char)

        return "".join(chars)

    def parse_ownership_param(
        self, operator: str, text: str
    ) -> CardOwnershipCountParam:
        """
        Creates an ownership parameter from the given operator and text
        :param operator: The parameter operator to use
        :param text: The colour text
        :return: The colour parameter
        """
        if self.user.is_anonymous:
            raise ValueError("Cannot search by ownership if you aren't logged in")

        if operator == ":" and text == "any":
            return CardOwnershipCountParam(self.user, ">=", 1)

        if operator == ":" and text == "none":
            return CardOwnershipCountParam(self.user, "=", 0)

        try:
            count = int(text)
        except (ValueError, TypeError):
            raise ValueError(f'Cannot parse number "{text}"')

        return CardOwnershipCountParam(self.user, operator, count)
