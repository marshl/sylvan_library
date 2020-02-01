"""
Example parser for JSON
"""

from typing import Union, Tuple
from cardsearch.parser.base_parser import Parser, ParseError


class JSONParser(Parser):
    """
    Parses json
    """

    def eat_whitespace(self) -> None:
        """
        Overrides the base whitespace eater to eat single and multiline comments
        """
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
        """
        Starts parsing
        :return: The parse result
        """
        return self.match("any_type")

    def any_type(self) -> Union[str, dict, list]:
        """
        Parses any value type
        :return: The parsed value
        """
        return self.match("complex_type", "primitive_type")

    def primitive_type(self) -> Union[None, bool, str]:
        """
        Parses any primitive type
        :return: The parsed value
        """
        return self.match("null", "boolean", "quoted_string", "unquoted")

    def complex_type(self) -> Union[list, dict]:
        """
        Parses any complex type
        :return: The parsed complex type
        """
        return self.match("list", "map")

    def list(self) -> list:
        """
        Attempts to parse a list
        :return: The parsed list
        """
        result = []

        self.keyword("[")
        while True:
            item = self.maybe_match("any_type")
            if item is None:
                break

            result.append(item)

            if not self.maybe_keyword(","):
                break

        self.keyword("]")
        return result

    def map(self) -> dict:
        """
        Attempts to parse a map/dict or str/Any key/value pairs
        :return: The parsed map
        """
        result = {}
        self.keyword("{")
        while True:
            item = self.maybe_match("pair")
            if item is None:
                break

            result[item[0]] = item[1]

            if not self.maybe_keyword(","):
                break

        self.keyword("}")
        return result

    def pair(self) -> Tuple[str, Union[str, dict, list]]:
        """
        Attempts to parse a key/value pair
        where the key is a string and the value can be a string dict or list
        :return: The key/value pair
        """
        key = self.match("quoted_string", "unquoted")

        if isinstance(key, str):
            raise ParseError(
                self.pos + 1, "Expected string but got number", self.text[self.pos + 1]
            )

        self.keyword(":")
        value = self.match("any_type")

        return key, value

    def null(self) -> None:
        """
        Attempts to parse a null value
        :return: The null value
        """
        self.keyword("null")

    def boolean(self) -> bool:
        """
        Attempts to parse a single boolean value
        :return: The boolean value
        """
        boolean = self.keyword("true", "false")
        return boolean[0] == "t"

    def unquoted(self) -> Union[str, float]:
        """
        Attempts to parse an unquoted string
        :return: The unquoted string
        """
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

        result = "".join(chars).rstrip(" \t")
        try:
            return number_type(result)
        except ValueError:
            return result

    def quoted_string(self) -> str:
        """
        Attempts to parse a double quoted string
        :return: The double quoted string
        """
        quote = self.char("\"'")
        chars = []

        escape_sequences = {"b": "\b", "f": "\f", "n": "\n", "r": "\r", "t": "\t"}

        while True:
            char = self.char()
            if char == quote:
                break

            if char == "\\":
                escape = self.char()
                if escape == "u":
                    code_point = []
                    for _ in range(4):
                        code_point.append(self.char("0-9a-fA-F"))

                    chars.append(chr(int("".join(code_point), 16)))
                else:
                    chars.append(escape_sequences.get(char, char))
            else:
                chars.append(char)

        return "".join(chars)
