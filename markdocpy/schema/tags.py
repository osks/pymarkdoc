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


class PartialFile:
    def validate(self, value: Any, config: Dict[str, Any], _key: str):
        partials = config.get("partials", {})
        if not isinstance(partials, dict) or value not in partials:
            return [
                {
                    "id": "attribute-value-invalid",
                    "level": "error",
                    "message": f"Partial `{value}` not found. The 'file' attribute must be set in `config.partials`",
                }
            ]
        return []


def _transform_partial(node: Node, config: Dict[str, Any]):
    from ..transform.transformer import transform

    partials = config.get("partials", {})
    file = node.attributes.get("file")
    partial = partials.get(file) if isinstance(partials, dict) else None
    if not partial:
        return None

    variables = node.attributes.get("variables") or {}
    scoped = {
        **config,
        "variables": {
            **(config.get("variables") or {}),
            **(variables if isinstance(variables, dict) else {}),
            "$$partial:filename": file,
        },
    }

    def transform_part(part: Node):
        resolved = part.resolve(scoped)
        if resolved.type == "document":
            return [transform(child, scoped) for child in resolved.children]
        return transform(resolved, scoped)

    if isinstance(partial, list):
        output = []
        for part in partial:
            rendered = transform_part(part)
            if rendered is None:
                continue
            if isinstance(rendered, list):
                output.extend(rendered)
            else:
                output.append(rendered)
        return output
    return transform_part(partial)


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
    "partial": {
        "inline": False,
        "self_closing": True,
        "attributes": {
            "file": {"type": PartialFile, "render": False, "required": True},
            "variables": {"type": dict, "render": False},
        },
        "transform": _transform_partial,
    },
    "slot": {
        "render": False,
    },
}
