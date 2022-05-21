"""
Module for the base recursive descent parser
"""

import re
from abc import ABC
from typing import List, Optional, Any, Dict, Tuple


# https://www.booleanworld.com/building-recursive-descent-parsers-definitive-guide/
class ParseError(Exception):
    """
    Class for an that occurs during parsing
    """

    def __init__(self, pos: int, msg: str, *args: Any):
        super().__init__()
        self.pos: int = pos
        self.msg: str = msg
        self.args: Tuple[Any, ...] = args

    def __str__(self) -> str:
        return f"{self.msg % self.args} at position {self.pos}"


class Parser(ABC):
    """
    Generic recursive descent parser
    """

    def __init__(self) -> None:
        self.cache: Dict[str, List[str]] = {}
        self.text: str = ""
        self.pos: int = -1
        self.len: int = 0

    def parse(self, text: str) -> Any:
        """
        Parses the given text
        :param text:
        :return:
        """
        self.text = text
        self.pos = -1
        self.len = len(text) - 1
        result = self.start()
        self.assert_end()
        return result

    def start(self) -> Any:
        """
        How the parse should start parsing the query string
        :return: The parse result
        """
        raise NotImplementedError(f"Please implement {type(self).__name__}.start")

    def assert_end(self) -> None:
        """
        Ensures that the parser has completed parsing the text
        """
        if self.pos < self.len:
            raise ParseError(
                self.pos + 1,
                "Expected end of string but got %s",
                self.text[self.pos + 1],
            )

    def eat_whitespace(self) -> None:
        """
        Consumes whitespace without parsing any of them
        """
        while self.pos < self.len and self.text[self.pos + 1] in " \f\v\r\t\n":
            self.pos += 1

    def split_char_ranges(self, chars: str) -> List[str]:
        """
        Takes in a string and expands any char ranges (e.g. a-z becomes abcdef..)
        :param chars: The chars the expand
        :return: The string with any char ranges expanded
        """
        try:
            return self.cache[chars]
        except KeyError:
            pass

        result: List[str] = []
        index: int = 0
        length: int = len(chars)

        while index < length:
            if index + 2 < length and chars[index + 1] == "-":
                if chars[index] >= chars[index + 2]:
                    raise ValueError("Bad character range")
                result.append(chars[index : index + 3])
                index += 3
            else:
                result.append(chars[index])
                index += 1
        self.cache[chars] = result
        return result

    def pattern(self, pattern: str) -> str:
        """
        Attempts to parse a single char
        :param chars: The list of potential characters to parse
        :return: The character that was parsed
        """
        if self.pos >= self.len:
            raise ParseError(self.pos, "Expected %s but got end of string", pattern)

        next_char = self.text[self.pos + 1]
        if re.match(pattern, next_char):
            self.pos += 1
            return next_char

        raise ParseError(self.pos + 1, "Expected %s but got %s", pattern, next_char)

    def char(self, chars: Optional[str] = None) -> str:
        """
        Attempts to parse a single char
        :param chars: The list of potential characters to parse
        :return: The character that was parsed
        """
        if self.pos >= self.len:
            raise ParseError(
                self.pos,
                "Expected %s but got end of string",
                "character" if chars is None else f"[{chars}]",
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
            "character" if chars is None else f"[{chars}]",
            next_char,
        )

    def keyword(self, *keywords: str) -> str:
        """
        Attempts to parse a single keyword from the given list
        :param keywords: The list of keywords to attempt
        :return: The parsed keyword if successful
        """
        self.eat_whitespace()
        if self.pos >= self.len:
            raise ParseError(
                self.pos + 1, "Expected %s but got end of string", ",".join(keywords)
            )

        for keyword in keywords:
            low = self.pos + 1
            high = low + len(keyword)

            if self.text[low:high].lower() == keyword.lower():
                self.pos += len(keyword)
                self.eat_whitespace()
                return keyword

        raise ParseError(
            self.pos + 1,
            "Expected %s but got %s",
            ",".join(keywords),
            self.text[self.pos + 1],
        )

    def match(self, *rules: str) -> Any:
        """
        Attempts to parse any of the given rules in roder
        :param rules: Methods names on this object that should be attempted (in order)
        :return: The parse result
        """
        self.eat_whitespace()
        last_error_pos: int = -1
        last_exception: Optional[Exception] = None
        last_error_rules: List[str] = []

        for rule in rules:
            initial_pos = self.pos
            try:
                result = getattr(self, rule)()
                self.eat_whitespace()
                return result
            except ParseError as ex:
                self.pos = initial_pos
                if ex.pos > last_error_pos:
                    last_exception = ex
                    last_error_pos = ex.pos
                    last_error_rules.clear()
                    last_error_rules.append(rule)
                elif ex.pos == last_error_pos:
                    last_error_rules.append(rule)

        if len(last_error_rules) == 1 and last_exception:
            raise last_exception

        raise ParseError(
            last_error_pos,
            "Expected %s but got %s",
            ",".join(last_error_rules),
            self.text[last_error_pos],
        )

    def maybe_char(self, chars: Optional[str] = None) -> Optional[str]:
        """
        Tries to get a single character from the given list of characters
        :param chars: The allowable characters
        :return: The character if it matched
        """
        try:
            return self.char(chars)
        except ParseError:
            return None

    def maybe_pattern(self, pattern: str) -> Optional[str]:
        """
        Tries to get a pattern match
        :param pattern: The allowable pattern
        :return: The pattern if it matches
        """
        try:
            return self.pattern(pattern)
        except ParseError:
            return None

    def maybe_match(self, *rules: str) -> Optional[Any]:
        """
        Attempts to match any of the given parser methods (in order)
        :param rules: The method rule names to try
        :return: The parse result if successful, otherwise None
        """
        try:
            return self.match(*rules)
        except ParseError:
            return None

    def maybe_keyword(self, *keywords: str) -> Optional[Any]:
        """
        Attempts to match any of the given keywords
        :param keywords: The keywords to try
        :return: The parse result if successful, otherwise None
        """
        try:
            return self.keyword(*keywords)
        except ParseError:
            return None
