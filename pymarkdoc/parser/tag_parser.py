from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Tuple

from ..ast.function import Function
from ..ast.variable import Variable


@dataclass
class TagInfo:
    kind: str
    name: str | None = None
    attributes: Dict[str, Any] | None = None
    value: Any | None = None


@dataclass
class Token:
    type: str
    value: Any


def parse_tag_content(content: str) -> TagInfo:
    trimmed = content.strip()
    if not trimmed:
        return TagInfo("error")

    if trimmed.startswith("/"):
        name = trimmed[1:].strip().split()[0] if trimmed[1:].strip() else None
        return TagInfo("close", name=name)

    self_closing = trimmed.endswith("/")
    if self_closing:
        trimmed = trimmed[:-1].strip()

    tokens = _tokenize(trimmed)
    if not tokens:
        return TagInfo("error")

    interp = _parse_interpolation(tokens)
    if interp is not None:
        return interp

    name = None
    idx = 0
    if tokens and tokens[0].type == "ident":
        next_token = tokens[1] if len(tokens) > 1 else None
        if not next_token or next_token.value not in ("=", "("):
            name = tokens[0].value
            idx = 1

    attributes: Dict[str, Any] = {}
    class_list: List[str] = []

    if name and idx < len(tokens):
        token = tokens[idx]
        next_token = tokens[idx + 1] if idx + 1 < len(tokens) else None
        if token.value not in (".", "#") and not (
            token.type == "ident" and next_token and next_token.value == "="
        ):
            value, next_idx = _parse_value(tokens, idx)
            if value is not None:
                attributes["primary"] = value
                idx = next_idx

    idx = _parse_attributes(tokens, idx, attributes, class_list)

    if class_list:
        attributes["class"] = " ".join(class_list)

    if name is None and attributes:
        return TagInfo("annotation", attributes=attributes)

    kind = "self" if self_closing or name == "else" else "open"
    return TagInfo(kind, name=name, attributes=attributes)


def _parse_interpolation(tokens: List[Token]) -> TagInfo | None:
    if tokens[0].type == "dollar" and len(tokens) >= 2 and tokens[1].type == "ident":
        return TagInfo("interpolation", value=Variable(tokens[1].value))

    if len(tokens) >= 3 and tokens[0].type == "ident" and tokens[1].value == "(":
        func, idx = _parse_function(tokens, 0)
        if func and idx == len(tokens):
            return TagInfo("interpolation", value=func)

    return None


def _parse_attributes(
    tokens: List[Token],
    idx: int,
    attributes: Dict[str, Any],
    class_list: List[str],
) -> int:
    while idx < len(tokens):
        token = tokens[idx]
        if token.value in (".", "#"):
            if idx + 1 < len(tokens) and tokens[idx + 1].type == "ident":
                value = tokens[idx + 1].value
                if token.value == ".":
                    class_list.append(value)
                else:
                    attributes["id"] = value
                idx += 2
                continue
            idx += 1
            continue

        if token.type == "ident" and idx + 1 < len(tokens) and tokens[idx + 1].value == "=":
            key = token.value
            value, next_idx = _parse_value(tokens, idx + 2)
            if value is not None:
                attributes[key] = value
                idx = next_idx
                continue
        idx += 1

    return idx


def _parse_value(tokens: List[Token], idx: int) -> Tuple[Any | None, int]:
    if idx >= len(tokens):
        return None, idx
    token = tokens[idx]

    if token.type == "string":
        return token.value, idx + 1
    if token.type == "number":
        return token.value, idx + 1
    if token.type == "boolean":
        return token.value, idx + 1
    if token.type == "null":
        return None, idx + 1
    if token.type == "dollar" and idx + 1 < len(tokens) and tokens[idx + 1].type == "ident":
        return Variable(tokens[idx + 1].value), idx + 2
    if token.type == "ident":
        if idx + 1 < len(tokens) and tokens[idx + 1].value == "(":
            func, next_idx = _parse_function(tokens, idx)
            return func, next_idx
        return token.value, idx + 1
    if token.value == "[":
        return _parse_array(tokens, idx + 1)
    if token.value == "{":
        return _parse_object(tokens, idx + 1)

    return None, idx


def _parse_array(tokens: List[Token], idx: int) -> Tuple[List[Any], int]:
    items: List[Any] = []
    while idx < len(tokens):
        if tokens[idx].value == "]":
            return items, idx + 1
        value, idx = _parse_value(tokens, idx)
        if value is not None:
            items.append(value)
        if idx < len(tokens) and tokens[idx].value == ",":
            idx += 1
    return items, idx


def _parse_object(tokens: List[Token], idx: int) -> Tuple[Dict[str, Any], int]:
    output: Dict[str, Any] = {}
    while idx < len(tokens):
        if tokens[idx].value == "}":
            return output, idx + 1
        key_token = tokens[idx]
        key = None
        if key_token.type in ("ident", "string"):
            key = key_token.value
            idx += 1
        if key is None or idx >= len(tokens) or tokens[idx].value != ":":
            idx += 1
            continue
        idx += 1
        value, idx = _parse_value(tokens, idx)
        if key is not None:
            output[key] = value
        if idx < len(tokens) and tokens[idx].value == ",":
            idx += 1
    return output, idx


def _parse_function(tokens: List[Token], idx: int) -> Tuple[Function | None, int]:
    if idx >= len(tokens) or tokens[idx].type != "ident":
        return None, idx
    name = tokens[idx].value
    idx += 1
    if idx >= len(tokens) or tokens[idx].value != "(":
        return None, idx
    idx += 1
    args: List[Any] = []
    kwargs: Dict[str, Any] = {}
    while idx < len(tokens):
        if tokens[idx].value == ")":
            return Function(name, args, kwargs), idx + 1
        if (
            tokens[idx].type == "ident"
            and idx + 1 < len(tokens)
            and tokens[idx + 1].value == "="
        ):
            key = tokens[idx].value
            value, idx = _parse_value(tokens, idx + 2)
            kwargs[key] = value
        else:
            value, idx = _parse_value(tokens, idx)
            if value is not None:
                args.append(value)
        if idx < len(tokens) and tokens[idx].value == ",":
            idx += 1
    return Function(name, args, kwargs), idx


def _tokenize(content: str) -> List[Token]:
    tokens: List[Token] = []
    i = 0
    while i < len(content):
        char = content[i]
        if char.isspace():
            i += 1
            continue

        if char in "=,[](){}:":
            tokens.append(Token("symbol", char))
            i += 1
            continue

        if char in ".#":
            if i + 1 < len(content) and content[i + 1].isdigit():
                number, i = _read_number(content, i)
                tokens.append(Token("number", number))
            else:
                tokens.append(Token("symbol", char))
                i += 1
            continue

        if char == "$":
            tokens.append(Token("dollar", char))
            i += 1
            continue

        if char in "\"'":
            value, i = _read_string(content, i)
            tokens.append(Token("string", value))
            continue

        if char.isdigit() or (char == "-" and i + 1 < len(content) and content[i + 1].isdigit()):
            number, i = _read_number(content, i)
            tokens.append(Token("number", number))
            continue

        if char.isalpha() or char in "_-":
            ident, i = _read_identifier(content, i)
            if ident == "true":
                tokens.append(Token("boolean", True))
            elif ident == "false":
                tokens.append(Token("boolean", False))
            elif ident == "null":
                tokens.append(Token("null", None))
            else:
                tokens.append(Token("ident", ident))
            continue

        i += 1

    return tokens


def _read_identifier(content: str, idx: int) -> Tuple[str, int]:
    start = idx
    while idx < len(content) and (content[idx].isalnum() or content[idx] in "_-"):
        idx += 1
    return content[start:idx], idx


def _read_number(content: str, idx: int) -> Tuple[int | float, int]:
    start = idx
    if content[idx] == "-":
        idx += 1
    while idx < len(content) and content[idx].isdigit():
        idx += 1
    if idx < len(content) and content[idx] == ".":
        idx += 1
        while idx < len(content) and content[idx].isdigit():
            idx += 1
    if idx < len(content) and content[idx] in "eE":
        idx += 1
        if idx < len(content) and content[idx] in "+-":
            idx += 1
        while idx < len(content) and content[idx].isdigit():
            idx += 1
    text = content[start:idx]
    return (float(text) if any(ch in text for ch in ".eE") else int(text)), idx


def _read_string(content: str, idx: int) -> Tuple[str, int]:
    quote = content[idx]
    idx += 1
    value = []
    while idx < len(content):
        char = content[idx]
        if char == quote:
            return "".join(value), idx + 1
        if char == "\\" and idx + 1 < len(content):
            nxt = content[idx + 1]
            if nxt == "n":
                value.append("\n")
            elif nxt == "r":
                value.append("\r")
            elif nxt == "t":
                value.append("\t")
            else:
                value.append(nxt)
            idx += 2
            continue
        value.append(char)
        idx += 1
    return "".join(value), idx
