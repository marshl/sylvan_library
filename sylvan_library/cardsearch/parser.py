from typing import List, Optional, Any, Dict


# https://www.booleanworld.com/building-recursive-descent-parsers-definitive-guide/
class ParseError(Exception):
    def __init__(self, pos: int, msg: str, *args):
        self.pos = pos
        self.msg = msg
        self.args = args

    def __str__(self) -> str:
        return "%s at position %s" % (self.msg % self.args, self.pos)


class Parser:
    def __init__(self):
        self.cache: Dict[str, List[str]] = {}
        self.text: str = ""
        self.pos: int = -1
        self.len: int = 0

    def parse(self, text: str) -> Any:
        self.text = text
        self.pos = -1
        self.len = len(text) - 1
        result = self.start()
        self.assert_end()
        return result

    def start(self) -> Any:
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

    def match(self, *rules) -> Any:
        self.eat_whitespace()
        last_error_pos: int = -1
        last_exception: Optional[Exception] = None
        last_error_rules: List[str] = []

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

    def maybe_match(self, *rules: str) -> Optional[Any]:
        try:
            return self.match(*rules)
        except ParseError:
            return None

    def maybe_keyword(self, *keywords: str) -> Optional[Any]:
        try:
            return self.keyword(*keywords)
        except ParseError:
            return None
