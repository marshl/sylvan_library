"""
Module for the card query recursive descent parser
"""

from typing import Union, Optional, Callable, List, Type

from cardsearch.parameters.base_parameters import (
    CardSearchTreeNode,
    CardSearchOr,
    CardSearchAnd,
    ParameterArgs,
    CardSearchParameter,
)
from cardsearch.parameters.card_artist_parameters import CardArtistParam
from cardsearch.parameters.card_colour_parameters import (
    CardMulticolouredOnlyParam,
    CardComplexColourParam,
)
from cardsearch.parameters.card_flavour_parameters import (
    CardFlavourTextParam,
)
from cardsearch.parameters.card_game_parameters import CardGameParam
from cardsearch.parameters.card_mana_cost_parameters import (
    CardManaValueParam,
    CardManaCostComplexParam,
    CardColourCountParam,
)
from cardsearch.parameters.card_misc_parameters import (
    CardHasColourIndicatorParam,
    CardHasWatermarkParam,
    CardIsPhyrexianParam,
    CardIsReprintParam,
    CardIsHybridParam,
    CardIsCommanderParam,
    CardLayoutParameter,
    CardIsVanillaParam,
    CardCollectorNumberParam,
)
from cardsearch.parameters.card_name_parameters import CardNameParam
from cardsearch.parameters.card_ownership_parameters import (
    CardOwnershipCountParam,
    CardUsageCountParam,
    CardMissingPauperParam,
)
from cardsearch.parameters.card_power_toughness_parameters import (
    CardNumToughnessParam,
    CardNumPowerParam,
    CardNumLoyaltyParam,
)
from cardsearch.parameters.card_price_parameters import CardPriceParam
from cardsearch.parameters.card_rarity_parameter import CardRarityParam
from cardsearch.parameters.card_rules_text_parameter import (
    CardRulesTextParam,
    CardWatermarkParam,
    CardProducesManaParam,
    CardOriginalRulesTextParam,
)
from cardsearch.parameters.card_set_parameters import (
    CardSetParam,
    CardBlockParam,
    CardLegalityParam,
    CardDateParam,
    CardUniversesBeyondParam,
)
from cardsearch.parameters.card_type_parameters import (
    CardGenericTypeParam,
    CardOriginalTypeParam,
)
from cardsearch.parameters.sort_parameters import (
    CardColourSortParam,
    CardCollectorNumSortParam,
    CardManaValueSortParam,
    CardNameSortParam,
    CardPowerSortParam,
    CardPriceSortParam,
    CardRandomSortParam,
    CardRaritySortParam,
    CardReleaseDateSortParam,
    CardSuperKeySortParam,
)
from cardsearch.parser.base_parser import Parser, ParseError

SEARCH_PARAMETERS: List[Type[CardSearchParameter]] = [
    CardArtistParam,
    CardBlockParam,
    CardCollectorNumSortParam,
    CardCollectorNumberParam,
    CardColourCountParam,
    CardColourSortParam,
    CardComplexColourParam,
    CardDateParam,
    CardFlavourTextParam,
    CardGameParam,
    CardGenericTypeParam,
    CardHasColourIndicatorParam,
    CardHasWatermarkParam,
    CardIsCommanderParam,
    CardIsHybridParam,
    CardIsPhyrexianParam,
    CardIsReprintParam,
    CardIsVanillaParam,
    CardLayoutParameter,
    CardLegalityParam,
    CardManaCostComplexParam,
    CardManaValueParam,
    CardManaValueSortParam,
    CardMissingPauperParam,
    CardMulticolouredOnlyParam,
    CardNameParam,
    CardNameSortParam,
    CardNumLoyaltyParam,
    CardNumPowerParam,
    CardNumToughnessParam,
    CardOriginalRulesTextParam,
    CardOriginalTypeParam,
    CardOwnershipCountParam,
    CardPowerSortParam,
    CardPriceParam,
    CardPriceSortParam,
    CardProducesManaParam,
    CardRandomSortParam,
    CardRarityParam,
    CardRaritySortParam,
    CardReleaseDateSortParam,
    CardRulesTextParam,
    CardSetParam,
    CardSuperKeySortParam,
    CardUniversesBeyondParam,
    CardUsageCountParam,
    CardWatermarkParam,
]


def param_parser(
    name: str, keywords: List[str], operators: List[str]
) -> Callable[
    [Callable[[ParameterArgs], CardSearchTreeNode]],
    Callable[[ParameterArgs], CardSearchTreeNode],
]:
    """
    Decorator for parameter parsing functions
    Only functions with this decorator can be used to parse parameters
    :param name: The friendly name of the operator for warning messages
    :param keywords: The keywords that can be used for the parameter (e.g. oracle, o)
    :param operators: The operators that are allowed for the parameter
    :return:
    """

    def decorator(function: Callable[[ParameterArgs], CardSearchTreeNode]):
        function.is_param_parser = True
        function.param_name = name
        function.param_keywords = keywords
        function.param_operators = operators
        return function

    return decorator


class CardQueryParser(Parser):
    """
    Parser for parsing a scryfall-style card qquery
    """

    def start(self) -> CardSearchTreeNode:
        """
        Starts matching with the text
        :return: The root parameter node
        """
        return self.or_group()

    def or_group(self) -> CardSearchTreeNode:
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
                or_group = CardSearchOr()
                or_group.add_parameter(subgroup)
            or_group.add_parameter(param_group)

        return or_group or subgroup

    def and_group(self) -> CardSearchTreeNode:
        """
        Attempts to parse a list of parameters separated by "and"s
        :return: The CardSearchAnd group, or the single parameter if there is only one
        """
        result = self.match("parameter_group")
        and_group = None
        while True:
            self.maybe_keyword("and")
            param_group = self.maybe_match("parameter_group")
            if not param_group:
                break

            if and_group is None:
                and_group = CardSearchAnd()
                and_group.add_parameter(result)
            and_group.add_parameter(param_group)

        return and_group or result

    def parameter_group(self) -> Optional[CardSearchTreeNode]:
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
            "simple_word_group_parameter",
            "quoted_name_parameter",
            "regex_parameter",
            "normal_parameter",
            "unquoted_name_parameter",
        )
        if parameter is None:
            return None
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

    def normal_parameter(self) -> CardSearchTreeNode:
        """
        Attempts to parse a parameter with a type, operator and value
        :return: THe parsed parameter
        """
        parameter_type = self.match("param_type")
        operator = self.match("operator")
        parameter_value = self.match("quoted_string", "unquoted_complex")
        return self.parse_param(parameter_type, operator, parameter_value)

    def regex_parameter(self) -> CardSearchTreeNode:
        """
        Attempts to parse a parameter with a type, operator and value
        :return: THe parsed parameter
        """
        parameter_type = self.match("param_type")
        operator = self.match("operator")
        parameter_value = self.match("regex_string")
        return self.parse_param(
            parameter_type, operator, parameter_value, is_regex=True
        )

    def quoted_name_parameter(self) -> CardSearchTreeNode:
        """
        Attempts to parse a parameter that is just a quoted string
        :return: The name parameter
        """
        parameter_value = self.match("quoted_string")
        return self.parse_param("name", ":", parameter_value)

    def simple_word_group_parameter(self) -> CardSearchTreeNode:
        """
        Attempts to parse a parameter that has a list of words inside parentheses
        For example "oracle:(foo bar)"
        :return: An CardSearchAnd containing the parameters. All the parameters will be of
        the type specified before the colon at the start of the string
        """
        parameter_type = self.match("param_type")
        operator = self.match("operator")
        param_values = self.maybe_match("or_word_group")
        if param_values:
            base_param = CardSearchOr()
        else:
            param_values = self.match("and_word_group")
            base_param = CardSearchAnd()

        for value in param_values:
            param = self.parse_param(parameter_type, operator, value)
            base_param.add_parameter(param)
        return base_param

    def unquoted_name_parameter(self) -> Optional[CardSearchTreeNode]:
        """
        Attempts to parse a parameter that is just an unquoted string
        :return: The name parameter
        """
        parameter_value = self.match("unquoted_complex")
        if parameter_value and parameter_value.lower() in ("or", "and"):
            raise ParseError(
                self.pos + 1,
                'Expected a parameter but got "%s" instead',
                parameter_value,
            )
        return self.parse_param("name", ":", parameter_value)

    def parse_param(
        self,
        keyword: str,
        operator: str,
        value: str,
        is_regex: bool = False,
    ) -> Optional[CardSearchTreeNode]:
        """
        Returns a parameter based on the given parameter type
        :param keyword: The type of the parameter
        :param operator: The parameter operator
        :param value: The parameter alue
        :param is_regex: Whether the parameter contains a regular expression string or not
        :return: The parsed parameter
        """
        param_args = ParameterArgs(
            keyword=keyword.lower(),
            operator=operator,
            value=value,
            is_regex=is_regex,
        )

        matching_parameters = [
            param for param in SEARCH_PARAMETERS if param.matches_param_args(param_args)
        ]
        if not matching_parameters:
            raise ValueError(f'Unknown keyword "{keyword}"')

        if len(matching_parameters) > 1:
            raise ValueError(
                f'Too many parameters match the keyword "{keyword}" '
                f"({'.'.join(param.get_parameter_name() for param in matching_parameters)}"
            )
        parameter_type = matching_parameters[0]

        param = parameter_type(param_args)
        return param

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
        acceptable_chars = "0-9A-Za-z!$%&*+.,/;<=>?^_`|~{}[]/:'\\-"
        chars = [self.char(acceptable_chars)]

        while True:
            char = self.maybe_char(acceptable_chars)
            if char is None:
                break
            chars.append(char)

        return "".join(chars).rstrip(" \t")

    def unquoted_complex(self) -> Union[str, float]:
        """
        Parses an unquoted series of characters
        :return: The unquoted complex string
        """
        pattern = r"[^\s()]"
        chars = [self.pattern(pattern)]
        while True:
            char = self.maybe_pattern(pattern)
            if char is None:
                break
            chars.append(char)

        return "".join(chars).rstrip(" \t")

    def quoted_string(self) -> str:
        """
        Attempts to parse a double-quoted string
        Spaces are allowed inside the string
        :return: The contents of the double-quoted string (including the quotes)
        """
        quote = self.char("\"'")
        return self.generic_string(quote)

    def regex_string(self) -> str:
        """
        Attempts to parse a double-quoted string
        Spaces are allowed inside the string
        :return: The contents of the double-quoted string (including the quotes)
        """
        quote = self.char("/")
        return self.generic_string(quote)

    def generic_string(self, quote: str):
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

    def and_word_group(self) -> List[str]:
        """
        Attempts to parse a list of words in parentheses, for example "(foo bar)"
        :return: The words inside the parentheses
        """
        return self.word_group("(", ")")

    def or_word_group(self) -> List[str]:
        """
        Attempts to parse a list of words in parentheses, for example "(foo bar)"
        :return: The words inside the parentheses
        """
        return self.word_group("[", "]")

    def word_group(self, opening_bracket: str, closing_bracket: str) -> List[str]:
        """

        :param opening_bracket:
        :param closing_bracket:
        :return:
        """
        assert len(opening_bracket) == 1
        assert len(closing_bracket) == 1
        self.char(opening_bracket)
        chars: List[str] = []
        words: List[str] = []
        while True:
            char = self.char()
            if char in (" ", closing_bracket):
                if chars:
                    words.append("".join(chars))
                    chars = []
                if char == closing_bracket:
                    break
            else:
                chars.append(char)
        return words
