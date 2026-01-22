from __future__ import annotations

from html import escape
from typing import Any

from ..ast.tag import Tag

_VOID_ELEMENTS = {
    "area",
    "base",
    "br",
    "col",
    "embed",
    "hr",
    "img",
    "input",
    "link",
    "meta",
    "param",
    "source",
    "track",
    "wbr",
}


def render(node: Any) -> str:
    if isinstance(node, (str, int, float)):
        return escape(str(node), quote=True)
    if isinstance(node, list):
        return "".join(render(child) for child in node)
    if node is None or not Tag.is_tag(node):
        return ""

    name = node.name
    attributes = node.attributes or {}
    children = node.children or []

    if not name:
        return render(children)

    output = [f"<{name}"]
    for key, value in attributes.items():
        if value is True:
            output.append(f" {key.lower()}")
            continue
        if value is False or value is None:
            continue
        output.append(f' {key.lower()}="{escape(str(value), quote=True)}"')
    output.append(">")

    if name in _VOID_ELEMENTS or getattr(node, "self_closing", False):
        return "".join(output)

    if children:
        output.append(render(children))
    output.append(f"</{name}>")

    return "".join(output)
