from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List

from ..ast.function import Function
from ..ast.variable import Variable


@dataclass
class Position:
    offset: int
    line: int
    column: int


@dataclass
class Location:
    start: Position
    end: Position


class TagSyntaxError(Exception):
    def __init__(self, message: str, location: Location):
        super().__init__(message)
        self.message = message
        self.location = location


@dataclass
class TagInfo:
    """Parsed information about a Markdoc tag or annotation."""

    kind: str
    name: str | None = None
    attributes: Dict[str, Any] | None = None
    value: Any | None = None
    error: Dict[str, Any] | None = None


@dataclass
class Token:
    """Token produced by the tag lexer."""

    type: str
    value: Any
    start: Position
    end: Position


class Lexer:
    def __init__(self, content: str):
        self.content = content
        self.offset = 0
        self.line = 1
        self.column = 1

    def eof(self) -> bool:
        return self.offset >= len(self.content)

    def peek(self) -> str:
        if self.eof():
            return ""
        return self.content[self.offset]

    def advance(self) -> str:
        char = self.peek()
        if not char:
            return ""
        self.offset += 1
        if char == "\n":
            self.line += 1
            self.column = 1
        else:
            self.column += 1
        return char

    def position(self) -> Position:
        return Position(self.offset, self.line, self.column)

    def skip_whitespace(self) -> None:
        while not self.eof() and self.peek().isspace():
            self.advance()

    def next_token(self) -> Token | None:
        self.skip_whitespace()
        if self.eof():
            return None

        start = self.position()
        char = self.peek()

        if char in "=,[](){}:.#":
            self.advance()
            return Token("symbol", char, start, self.position())

        if char == "/":
            self.advance()
            return Token("slash", "/", start, self.position())

        if char == "$":
            self.advance()
            return Token("dollar", "$", start, self.position())

        if char in ('"', "'"):
            value = self.read_string()
            return Token("string", value, start, self.position())

        if char.isdigit() and self._peek_is_ident_tail():
            ident = self.read_identifier()
            if ident == "true":
                return Token("boolean", True, start, self.position())
            if ident == "false":
                return Token("boolean", False, start, self.position())
            if ident == "null":
                return Token("null", None, start, self.position())
            return Token("ident", ident, start, self.position())

        if char.isdigit() or (char == "-" and self._peek_is_digit()):
            value = self.read_number()
            return Token("number", value, start, self.position())

        if char.isalpha() or char in "_-":
            ident = self.read_identifier()
            if ident == "true":
                return Token("boolean", True, start, self.position())
            if ident == "false":
                return Token("boolean", False, start, self.position())
            if ident == "null":
                return Token("null", None, start, self.position())
            return Token("ident", ident, start, self.position())

        message = f"Unexpected character '{char}'"
        raise TagSyntaxError(message, Location(start, self.position()))

    def _peek_is_digit(self) -> bool:
        if self.offset + 1 >= len(self.content):
            return False
        return self.content[self.offset + 1].isdigit()

    def _peek_is_ident_tail(self) -> bool:
        if self.offset + 1 >= len(self.content):
            return False
        nxt = self.content[self.offset + 1]
        return nxt.isalpha() or nxt in "_-"

    def read_identifier(self) -> str:
        value = []
        while not self.eof() and (self.peek().isalnum() or self.peek() in "_-"):
            value.append(self.advance())
        return "".join(value)

    def read_number(self) -> int | float:
        start_offset = self.offset
        if self.peek() == "-":
            self.advance()
        while not self.eof() and self.peek().isdigit():
            self.advance()
        if not self.eof() and self.peek() == ".":
            self.advance()
            while not self.eof() and self.peek().isdigit():
                self.advance()
        if not self.eof() and self.peek() in "eE":
            self.advance()
            if not self.eof() and self.peek() in "+-":
                self.advance()
            while not self.eof() and self.peek().isdigit():
                self.advance()
        text = self.content[start_offset : self.offset]
        return float(text) if any(ch in text for ch in ".eE") else int(text)

    def read_string(self) -> str:
        quote = self.advance()
        value = []
        while not self.eof():
            char = self.advance()
            if char == quote:
                return "".join(value)
            if char == "\\" and not self.eof():
                nxt = self.advance()
                if nxt == "n":
                    value.append("\n")
                elif nxt == "r":
                    value.append("\r")
                elif nxt == "t":
                    value.append("\t")
                else:
                    value.append(nxt)
                continue
            value.append(char)
        message = "Unterminated string"
        end = self.position()
        raise TagSyntaxError(message, Location(end, end))


class Parser:
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.index = 0

    def peek(self) -> Token | None:
        if self.index >= len(self.tokens):
            return None
        return self.tokens[self.index]

    def advance(self) -> Token | None:
        token = self.peek()
        if token is not None:
            self.index += 1
        return token

    def expect(self, type_: str, value: str | None = None) -> Token:
        token = self.peek()
        if token is None:
            raise TagSyntaxError("Unexpected end of input", self._end_location())
        if token.type != type_:
            raise TagSyntaxError(f"Expected {type_}", Location(token.start, token.end))
        if value is not None and token.value != value:
            raise TagSyntaxError(f"Expected '{value}'", Location(token.start, token.end))
        return self.advance()

    def _end_location(self) -> Location:
        if self.tokens:
            last = self.tokens[-1]
            return Location(last.end, last.end)
        pos = Position(0, 1, 1)
        return Location(pos, pos)

    def parse_value(self) -> Any:
        token = self.peek()
        if token is None:
            raise TagSyntaxError("Expected value", self._end_location())

        if token.type in ("string", "number", "boolean", "null"):
            self.advance()
            return token.value

        if token.type == "dollar":
            return self.parse_variable()

        if token.type == "ident":
            next_token = self._peek_next()
            if next_token and next_token.type == "symbol" and next_token.value == "(":
                return self.parse_function()
            self.advance()
            return token.value

        if token.type == "symbol" and token.value == "[":
            return self.parse_array()

        if token.type == "symbol" and token.value == "{":
            return self.parse_object()

        raise TagSyntaxError("Expected value", Location(token.start, token.end))

    def parse_array(self) -> List[Any]:
        items: List[Any] = []
        self.expect("symbol", "[")
        while True:
            token = self.peek()
            if token is None:
                raise TagSyntaxError("Expected ']'", self._end_location())
            if token.type == "symbol" and token.value == "]":
                self.advance()
                return items
            items.append(self.parse_value())
            token = self.peek()
            if token and token.type == "symbol" and token.value == ",":
                self.advance()
                continue

    def parse_object(self) -> Dict[str, Any]:
        output: Dict[str, Any] = {}
        self.expect("symbol", "{")
        while True:
            token = self.peek()
            if token is None:
                raise TagSyntaxError("Expected '}'", self._end_location())
            if token.type == "symbol" and token.value == "}":
                self.advance()
                return output
            key_token = self.expect("ident") if token.type == "ident" else self.expect("string")
            self.expect("symbol", ":")
            output[key_token.value] = self.parse_value()
            token = self.peek()
            if token and token.type == "symbol" and token.value == ",":
                self.advance()
                continue

    def parse_function(self) -> Function:
        name_token = self.expect("ident")
        self.expect("symbol", "(")
        args: List[Any] = []
        kwargs: Dict[str, Any] = {}
        while True:
            token = self.peek()
            if token is None:
                raise TagSyntaxError("Expected ')'", self._end_location())
            if token.type == "symbol" and token.value == ")":
                self.advance()
                return Function(name_token.value, args, kwargs)
            if token.type == "ident" and self._peek_is_symbol("="):
                key = self.advance().value
                self.expect("symbol", "=")
                kwargs[key] = self.parse_value()
            else:
                args.append(self.parse_value())
            token = self.peek()
            if token and token.type == "symbol" and token.value == ",":
                self.advance()

    def parse_attributes(self, attributes: Dict[str, Any], class_list: List[str]) -> None:
        while self.peek() is not None:
            token = self.peek()
            if token.type == "symbol" and token.value in (".", "#"):
                self.advance()
                ident_token = self.peek()
                if ident_token is None or ident_token.type not in ("ident", "number"):
                    raise TagSyntaxError("Invalid attribute", self._end_location())
                ident = self.advance()
                if token.value == ".":
                    class_list.append(str(ident.value))
                else:
                    attributes["id"] = str(ident.value)
                continue
            if token.type == "ident":
                name = token.value
                if self._peek_is_symbol("="):
                    self.advance()
                    self.expect("symbol", "=")
                    attributes[name] = self.parse_value()
                    continue
            raise TagSyntaxError("Invalid attribute", Location(token.start, token.end))

    def _peek_next(self) -> Token | None:
        if self.index + 1 >= len(self.tokens):
            return None
        return self.tokens[self.index + 1]

    def _peek_is_symbol(self, value: str) -> bool:
        next_token = self._peek_next()
        return next_token is not None and next_token.type == "symbol" and next_token.value == value

    def parse_variable(self) -> Variable:
        self.expect("dollar")
        path: List[Any] = []
        token = self.peek()
        if token is None:
            raise TagSyntaxError("Expected variable", self._end_location())
        if token.type == "ident":
            path.append(self.advance().value)
        elif token.type == "symbol" and token.value == "[":
            self.advance()
            path.append(self.parse_value())
            self.expect("symbol", "]")
        else:
            raise TagSyntaxError("Expected variable", Location(token.start, token.end))

        while True:
            token = self.peek()
            if token is None:
                break
            if token.type == "symbol" and token.value == ".":
                self.advance()
                ident = self.expect("ident")
                path.append(ident.value)
                continue
            if token.type == "symbol" and token.value == "[":
                self.advance()
                path.append(self.parse_value())
                self.expect("symbol", "]")
                continue
            break

        return Variable(path)


def _tokenize(content: str) -> List[Token]:
    lexer = Lexer(content)
    tokens: List[Token] = []
    while True:
        token = lexer.next_token()
        if token is None:
            break
        tokens.append(token)
    return tokens


def _strip_self_closing(content: str) -> tuple[str, bool]:
    trimmed = content.rstrip()
    if not trimmed:
        return trimmed, False
    if trimmed.endswith("/"):
        return trimmed[:-1].rstrip(), True
    return content, False


def parse_tag_content(content: str) -> TagInfo:
    """Parse the interior of a {% ... %} tag."""
    try:
        trimmed = content.strip()
        if not trimmed:
            raise TagSyntaxError("Empty tag", _empty_location())

        if trimmed.startswith("/"):
            inner = trimmed[1:].strip()
            tokens = _tokenize(inner)
            parser = Parser(tokens)
            if not tokens:
                raise TagSyntaxError("Missing tag name", _empty_location())
            name = parser.expect("ident").value
            if parser.peek() is not None:
                raise TagSyntaxError("Unexpected token", Location(parser.peek().start, parser.peek().end))
            return TagInfo("close", name=name)

        normalized, self_closing = _strip_self_closing(trimmed)
        tokens = _tokenize(normalized)
        if not tokens:
            raise TagSyntaxError("Empty tag", _empty_location())

        parser = Parser(tokens)
        first = parser.peek()
        if first and first.type == "dollar":
            value = parser.parse_value()
            if parser.peek() is not None:
                raise TagSyntaxError("Unexpected token", Location(parser.peek().start, parser.peek().end))
            return TagInfo("interpolation", value=value)

        if first and first.type == "ident" and parser._peek_is_symbol("("):
            value = parser.parse_function()
            if parser.peek() is not None:
                raise TagSyntaxError("Unexpected token", Location(parser.peek().start, parser.peek().end))
            return TagInfo("interpolation", value=value)

        name = None
        if first and first.type == "ident":
            next_token = parser._peek_next()
            if not next_token or not (next_token.type == "symbol" and next_token.value in ("=", "(")):
                name = parser.advance().value

        attributes: Dict[str, Any] = {}
        class_list: List[str] = []

        if name and parser.peek() is not None:
            token = parser.peek()
            if token and not (token.type == "symbol" and token.value in (".", "#")):
                if not (token.type == "ident" and parser._peek_is_symbol("=")):
                    attributes["primary"] = parser.parse_value()

        if parser.peek() is not None:
            parser.parse_attributes(attributes, class_list)

        if class_list:
            attributes["class"] = " ".join(class_list)

        if name is None:
            if not attributes:
                raise TagSyntaxError("Missing tag name", _empty_location())
            return TagInfo("annotation", attributes=attributes)

        kind = "self" if self_closing or name == "else" else "open"
        return TagInfo(kind, name=name, attributes=attributes)
    except TagSyntaxError as exc:
        return TagInfo(
            "error",
            error={
                "message": exc.message,
                "location": {
                    "start": {"offset": exc.location.start.offset, "line": exc.location.start.line, "column": exc.location.start.column},
                    "end": {"offset": exc.location.end.offset, "line": exc.location.end.line, "column": exc.location.end.column},
                },
            },
        )


def _empty_location() -> Location:
    pos = Position(0, 1, 1)
    return Location(pos, pos)
