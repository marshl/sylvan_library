from cardsearch.parser.base_parser import Parser


class CalcParser(Parser):
    def start(self) -> float:
        return self.expression()

    def expression(self) -> float:
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

    def term(self) -> float:
        result = self.match("factor")
        while True:
            op = self.maybe_keyword("*", "/")
            if op is None:
                break

            term = self.match("factor")
            if op == "*":
                result *= term
            else:
                result /= term

        return result

    def factor(self) -> float:
        if self.maybe_keyword("("):
            result = self.match("expression")
            self.keyword(")")

            return result

        return self.match("number")

    def number(self) -> float:
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
