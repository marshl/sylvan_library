"""
Module for the numeric calculator parser
"""
from cardsearch.parser.base_parser import Parser


class CalcParser(Parser):
    """
    Example recursive descent parser for numerical calculation
    """

    def start(self) -> float:
        """
        Starts parsing the query
        :return:
        """
        return self.expression()

    def expression(self) -> float:
        """
        Parses a +/- expression
        :return: The result value
        """
        result = self.match("term")
        while True:
            operator = self.maybe_keyword("+", "-")
            if operator is None:
                break

            term = self.match("term")
            if operator == "+":
                result += term
            else:
                result -= term

        return result

    def term(self) -> float:
        """
        Matches a group of multiplied or divided values (tighter binding than "expressions"
        :return: The numerical result
        """
        result: float = self.match("factor")
        while True:
            operator = self.maybe_keyword("*", "/")
            if operator is None:
                break

            term = self.match("factor")
            if operator == "*":
                result *= term
            else:
                result /= term

        return result

    def factor(self) -> float:
        """
        Attempts to parse either a grouped/parenthesised expression or a single number
        :return: The parsed value
        """
        if self.maybe_keyword("("):
            result = self.match("expression")
            self.keyword(")")

            return result

        return self.match("number")

    def number(self) -> float:
        """
        Attempts to parse a decimal or floating point number
        :return: The parsed number
        """
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

        return float("".join(chars))
