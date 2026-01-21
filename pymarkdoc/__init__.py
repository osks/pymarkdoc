from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List

from .ast.function import Function
from .ast.node import Node
from .ast.tag import Tag
from .ast.variable import Variable
from .parser.parser import parse as _parse_tokens
from .parser.tokenizer import Tokenizer
from .renderer.html import render as _render_html
from .schema.nodes import nodes
from .schema.tags import tags, truthy
from .transform.transformer import merge_config, transform as _transform
from .validator.validator import validate_tree


@dataclass
class _Renderers:
    html = staticmethod(_render_html)


renderers = _Renderers()


def parse(content: str, *, file: str | None = None, slots: bool = False, location: bool = False) -> Node:
    _ = file, slots, location
    tokenizer = Tokenizer()
    tokens = tokenizer.tokenize(content)
    return _parse_tokens(tokens)


def resolve(content: Node | List[Node], config: Dict[str, Any]):
    if isinstance(content, list):
        return [child.resolve(config) for child in content]
    return content.resolve(config)


def transform(content: Node | List[Node], config: Dict[str, Any] | None = None):
    merged = merge_config(config)
    resolved = resolve(content, merged)
    return _transform(resolved, merged)


def validate(content: Node | List[Node], config: Dict[str, Any] | None = None):
    return validate_tree(content, config)


def create_element(name: str | Dict[str, Any], attributes: Dict[str, Any] | None = None, *children: Any) -> Tag:
    if isinstance(name, dict):
        attributes = name
        name = attributes.get("name")
    return Tag(name, attributes or {}, list(children))


class Markdoc:
    Tokenizer = Tokenizer
    Tag = Tag
    renderers = renderers
    nodes = nodes
    tags = tags
    truthy = truthy

    def __init__(self, config: Dict[str, Any]):
        self.config = config

    def parse(self, content: str) -> Node:
        return parse(content)

    def resolve(self, content: Node | List[Node]):
        return resolve(content, self.config)

    def transform(self, content: Node | List[Node]):
        return transform(content, self.config)

    def validate(self, content: Node | List[Node]):
        return validate(content, self.config)


__all__ = [
    "Node",
    "Tag",
    "Tokenizer",
    "Variable",
    "Function",
    "parse",
    "resolve",
    "transform",
    "validate",
    "create_element",
    "renderers",
    "nodes",
    "tags",
    "truthy",
    "Markdoc",
]
