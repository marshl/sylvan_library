"""
Module for the card query recursive descent parser
"""
import inspect
import math
import sys
from typing import Union, Optional, Dict, Callable, List

from django.contrib.auth.models import User
from django.db.models import F, Q

from cards.models import Set, Rarity, colour
from cards.models.colour import get_colours_for_nickname
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
    CardNumLoyaltyParam,
    CardRarityParam,
    CardHasColourIndicatorParam,
    CardHasWatermarkParam,
    CardIsReprintParam,
    CardIsPhyrexianParam,
    CardProducesManaParam,
    CardFlavourTextParam,
    CardIsHybridParam,
)
from .base_parser import Parser, ParseError


class ParameterArgs:
    # pylint: disable=too-few-public-methods
    """
    Argument container for all parameter parser functions
    """

    def __init__(self, keyword: str, operator: str, text: str, context_user: User):
        self.keyword = keyword
        self.operator = operator
        self.text = text
        self.context_user = context_user


def parse_numeric_parameter(
    param_name: str, operator: str, text: str
) -> Union[float, F]:
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
        return F("card__num_toughness")

    if text in ("power", "pow"):
        return F("card__num_power")

    if text in ("loyalty", "loy"):
        return F("card__num_loyalty")

    if text in ("cmc", "cost"):
        return F("card__cmc")

    if text in ("inf", "infinity", "∞"):
        return math.inf

    try:
        return float(text)
    except ValueError:
        raise ValueError(f"Could not convert {text} to number")


def param_parser(
    name: str, keywords: List[str], operators: List[str]
) -> Callable[
    [Callable[[ParameterArgs], CardSearchParam]],
    Callable[[ParameterArgs], CardSearchParam],
]:
    """
    Decorator for parameter parsing functions
    Only functions with this decorator can be used to parse parameters
    :param name: The friendly name of the operator for warning messages
    :param keywords: The keywords that can be used for the parameter (e.g. oracle, o)
    :param operators: The operators that are allowed for the parameter
    :return:
    """

    def decorator(function: Callable[[ParameterArgs], CardSearchParam]):
        function.is_param_parser = True
        function.param_name = name
        function.param_keywords = keywords
        function.param_operators = operators
        return function

    return decorator


@param_parser(
    name="converted mana cost",
    keywords=["cmc"],
    operators=["<", "<=", ":", "=", ">", ">="],
)
def parse_cmc_param(param_args: ParameterArgs) -> CardCmcParam:
    """
    Parses a converted mana cost parameter
    :param param_args: The parameter arguments
    :return: The converted mana cost parameter
    """
    cmc = parse_numeric_parameter(
        "converted mana cost", param_args.operator, param_args.text
    )
    return CardCmcParam(cmc, param_args.operator)


@param_parser(
    name="toughness",
    keywords=["tou", "toughness", "tough", "tuff"],
    operators=["<", "<=", ":", "=", ">", ">="],
)
def parse_toughness_param(param_args: ParameterArgs) -> CardNumToughnessParam:
    """
    Parses a card numerical toughness parameter
    :param param_args: The parameter arguments
    :return: Te toughness parameter
    """
    toughness = parse_numeric_parameter(
        "toughness", param_args.operator, param_args.text
    )
    return CardNumToughnessParam(toughness, param_args.operator)


@param_parser(
    name="power", keywords=["pow", "power"], operators=["<", "<=", ":", "=", ">", ">="]
)
def parse_power_param(param_args: ParameterArgs) -> CardNumPowerParam:
    """
    Parses a card power parameter
    :param param_args: The parameter arguments
    :return: The card power parameter
    """
    power = parse_numeric_parameter("power", param_args.operator, param_args.text)
    return CardNumPowerParam(power, param_args.operator)


@param_parser(
    name="loyalty",
    keywords=["l", "loy", "loyalty"],
    operators=["<", "<=", ":", "=", ">", ">="],
)
def parse_loyalty(param_args: ParameterArgs) -> CardNumLoyaltyParam:
    """
    Parses a card numerical loyalty parameter
    :param param_args: The parameter arguments
    :return: Te toughness parameter
    """
    toughness = parse_numeric_parameter("loyalty", param_args.operator, param_args.text)
    return CardNumLoyaltyParam(toughness, param_args.operator)


@param_parser(
    name="rules text", keywords=["o", "oracle", "rules", "text"], operators=[":", "="]
)
def parse_text_param(param_args: ParameterArgs) -> CardRulesTextParam:
    """
    Parses and returns a text parameter
    :param param_args: The parameter arguments
    :return: The rules parameter
    """
    return CardRulesTextParam(param_args.text, exact=param_args.operator == "=")


@param_parser(
    name="flavour text", keywords=["f", "flavour", "flavor"], operators=[":", "="]
)
def parse_flavour_text_param(param_args: ParameterArgs) -> CardFlavourTextParam:
    """
    Parses and returns a flavour text parameter
    :param param_args: The parameter arguments
    :return: The rules parameter
    """
    return CardFlavourTextParam(param_args.text)


@param_parser(name="type", keywords=["t", "type"], operators=[":", "="])
def parse_type_param(param_args: ParameterArgs) -> CardGenericTypeParam:
    """
    Parses a card type parameter
    :param param_args: The parameter arguments
    :return: The card type parameter
    """
    return CardGenericTypeParam(param_args.text, param_args.operator)


@param_parser(name="set", keywords=["s", "set"], operators=[":", "="])
def parse_set_param(param_args: ParameterArgs) -> CardSetParam:
    """
    Creates a card set parameter from the given operator and text
    :param param_args: The parameter arguments
    :return: The set parameter
    """
    card_set: Optional[Set] = None
    try:
        card_set = Set.objects.get(code__iexact=param_args.text)
    except Set.DoesNotExist:
        pass
    if card_set:
        return CardSetParam(card_set)

    try:
        card_set = Set.objects.get(name__icontains=param_args.text)
    except Set.DoesNotExist:
        raise ValueError(f'Unknown set "{param_args.text}"')
    except Set.MultipleObjectsReturned:
        raise ValueError(f'Multiple sets match "{param_args.text}"')

    return CardSetParam(card_set)


@param_parser(
    name="mana cost", keywords=["m", "mana"], operators=[":", "=", "<", "<=", ">", ">="]
)
def parse_mana_cost_param(param_args: ParameterArgs) -> CardManaCostComplexParam:
    """
    Creates a mana cost parameter from the given operator and text
    :param param_args: The parameter arguments
    :return: The created mana cost parameter
    """
    return CardManaCostComplexParam(param_args.text, param_args.operator)


@param_parser(name="is", keywords=["is", "has", "not"], operators=[":"])
def parse_is_param(param_args: ParameterArgs) -> CardSearchParam:
    """
    Creates various simple boolean parameters based on the text
    :param param_args: The parameter arguments
    :return: The created parameter (various types)
    """
    if param_args.text == "reprint":
        param = CardIsReprintParam()
    elif param_args.text == "indicator":
        param = CardHasColourIndicatorParam()
    elif param_args.text == "phyrexian":
        param = CardIsPhyrexianParam()
    elif param_args.text == "watermark":
        param = CardHasWatermarkParam()
    elif param_args.text == "hybrid":
        param = CardIsHybridParam()
    else:
        raise ValueError(f'Unknown parameter "{param_args.keyword}:{param_args.text}"')

    if param_args.keyword == "not":
        param.negated = True
    return param


@param_parser(name="name", keywords=["n", "name"], operators=[":", "="])
def parse_name_param(param_args: ParameterArgs) -> CardNameParam:
    """
    Parses a card name parameter
    :param param_args: The parameter arguments
    :return: The name parameter
    """
    match_exact = param_args.operator == "="
    if param_args.text.startswith("!"):
        match_exact = True
        text = param_args.text[1:]
    else:
        text = param_args.text
    return CardNameParam(card_name=text, match_exact=match_exact)


@param_parser(
    name="colour",
    keywords=["c", "color", "colour"],
    operators=[":", "=", "<", "<=", ">", ">="],
)
def parse_colour_param(
    param_args: ParameterArgs
) -> Union[CardComplexColourParam, CardColourCountParam]:
    """
    Parses a card colour parameter
    :param param_args: The parameter arguments
    :return:
    """
    try:
        num = int(param_args.text)
        return CardColourCountParam(num, param_args.operator, identity=False)
    except ValueError:
        pass
    colours = colour.get_colours_for_nickname(param_args.text)
    return CardComplexColourParam(colours, param_args.operator, identity=False)


@param_parser(
    name="produces",
    keywords=["p", "produce", "produces"],
    operators=[":", "=", "<", "<=", ">", ">="],
)
def parse_produces_param(param_args: ParameterArgs) -> CardProducesManaParam:
    """
    Parses a card produces colour param
    :param param_args: The parameter arguments
    :return:
    """
    if param_args.text == "any":
        return CardProducesManaParam([], param_args.operator, any_colour=True)

    colours = colour.get_colours_for_nickname(param_args.text)
    return CardProducesManaParam(colours, param_args.operator)


@param_parser(
    name="colour identity",
    keywords=["id", "identity"],
    operators=[":", "=", "<", "<=", ">", ">="],
)
def parse_colour_identity_param(
    param_args: ParameterArgs
) -> Union[CardComplexColourParam, CardColourCountParam]:
    """
    Parses a card colour identity parameter
    :param param_args: The parameter arguments
    :return:
    """
    if param_args.text == "all":
        param_args.operator = ">="

    try:
        num = int(param_args.text)
        return CardColourCountParam(num, param_args.operator, identity=True)
    except ValueError:
        pass

    return CardComplexColourParam(
        get_colours_for_nickname(param_args.text), param_args.operator, identity=True
    )


@param_parser(
    name="ownership",
    keywords=["have", "own"],
    operators=[":", "=", "<", "<=", ">", ">="],
)
def parse_ownership_param(param_args: ParameterArgs) -> CardOwnershipCountParam:
    """
    Creates an ownership parameter from the given operator and text
    :param param_args: The parameter arguments
    :return: The colour parameter
    """
    if param_args.context_user.is_anonymous:
        raise ValueError("Cannot search by ownership if you aren't logged in")

    if param_args.operator == ":" and param_args.text == "any":
        return CardOwnershipCountParam(param_args.context_user, ">=", 1)

    if param_args.operator == ":" and param_args.text == "none":
        return CardOwnershipCountParam(param_args.context_user, "=", 0)

    try:
        count = int(param_args.text)
    except (ValueError, TypeError):
        raise ValueError(f'Cannot parse number "{param_args.text}"')

    return CardOwnershipCountParam(param_args.context_user, param_args.operator, count)


@param_parser(name="rarity", keywords=["r", "rarity"], operators=[":", "="])
def parse_rarity_param(param_args: ParameterArgs) -> CardRarityParam:
    """
    Creates a rarity parameter from the given operator and text
    :param param_args: The parameter arguments
    :return: The created mana cost parameter
    """
    rarity = Rarity.objects.get(
        Q(symbol__iexact=param_args.text) | Q(name__iexact=param_args.text)
    )
    return CardRarityParam(rarity)


class CardQueryParser(Parser):
    """
    Parser for parsing a scryfall-style card qquery
    """

    def __init__(self, user: User = None):
        super().__init__()
        self.user: User = user
        all_functions = inspect.getmembers(sys.modules[__name__], inspect.isfunction)
        self.parser_dict: Dict[str, Callable] = {}
        for _, func in all_functions:
            if not hasattr(func, "is_param_parser") or not func.is_param_parser:
                continue

            for param_keyword in func.param_keywords:
                assert param_keyword not in self.parser_dict
                self.parser_dict[param_keyword] = func

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
        if is_negated:
            parameter.negated = not parameter.negated
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

    def parse_param(
        self, parameter_type: str, operator: str, parameter_value: str
    ) -> CardSearchParam:
        """
        Returns a parameter based on the given parameter type
        :param parameter_type: The type of the parameter
        :param operator: The parameter operator
        :param parameter_value: The parameter alue
        :return: The parsed parameter
        """
        if parameter_type not in self.parser_dict:
            raise ValueError(f"Unknown parameter type {parameter_type}")

        parser_func = self.parser_dict[parameter_type]
        assert hasattr(parser_func, "param_operators")
        assert hasattr(parser_func, "param_name")

        if operator not in parser_func.param_operators:
            raise ValueError(
                f"Cannot use {operator} operator for {parser_func.param_name} search"
            )

        param_args = ParameterArgs(
            keyword=parameter_type,
            operator=operator,
            text=parameter_value,
            context_user=self.user,
        )

        return self.parser_dict[parameter_type](param_args)

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
        acceptable_chars = "0-9A-Za-z!$%&*+./;<=>?^_`|~{}[]/-:'"
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
