from __future__ import annotations

from typing import Any, Dict

from ..ast.node import Node


def truthy(value: Any) -> bool:
    return value is not False and value is not None


def _render_conditions(node: Node):
    conditions = [{"condition": node.attributes.get("primary"), "children": []}]
    for child in node.children:
        if child.type == "tag" and child.tag == "else":
            conditions.append(
                {
                    "condition": child.attributes.get("primary", True),
                    "children": [],
                }
            )
        else:
            conditions[-1]["children"].append(child)
    return conditions


def _transform_if(node: Node, config: Dict[str, Any]):
    from ..transform.transformer import transform

    for condition in _render_conditions(node):
        if truthy(condition["condition"]):
            return [transform(child, config) for child in condition["children"]]
    return []


def _transform_tag(node: Node, config: Dict[str, Any]):
    from ..ast.tag import Tag
    from ..transform.transformer import transform

    return Tag(
        node.tag, node.attributes or {}, [transform(child, config) for child in node.children]
    )


tags = {
    "if": {
        "attributes": {"primary": {"render": False}},
        "transform": _transform_if,
    },
    "else": {
        "self_closing": True,
        "attributes": {"primary": {"render": False}},
    },
    "table": {
        "transform": _transform_tag,
    },
    "slot": {
        "render": False,
    },
}
