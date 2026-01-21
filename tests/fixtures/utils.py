from __future__ import annotations

from typing import Any

import pymarkdoc as Markdoc


def fixture_configs():
    def sum_fn(a, b):
        return a + b

    return {
        "interpolation": {"variables": {"name": "Ada"}, "functions": {"sum": sum_fn}},
    }


def serialize_value(value: Any):
    if isinstance(value, Markdoc.Variable):
        return {"$type": "Variable", "name": value.name}
    if isinstance(value, Markdoc.Function):
        parameters = {"args": [serialize_value(v) for v in value.args]}
        parameters.update({k: serialize_value(v) for k, v in value.kwargs.items()})
        return {
            "$type": "Function",
            "name": value.name,
            "parameters": parameters,
        }
    if isinstance(value, list):
        return [serialize_value(v) for v in value]
    if isinstance(value, dict):
        return {k: serialize_value(v) for k, v in value.items()}
    return value


def serialize_node(node: Markdoc.Node):
    return {
        "type": node.type,
        "tag": node.tag,
        "content": node.content,
        "attributes": serialize_value(node.attributes),
        "children": [serialize_node(child) for child in node.children],
    }


def normalize_html(value: str) -> str:
    return value.replace("\r\n", "\n").strip()
