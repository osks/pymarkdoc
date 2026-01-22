from __future__ import annotations

from typing import Any, Dict, List

from ..ast.node import Node
from ..ast.tag import Tag
from ..schema.nodes import nodes as default_nodes
from ..schema.functions import functions as default_functions
from ..schema.tags import tags as default_tags
from ..schema_types import ClassType, IdType


global_attributes = {
    "class": {"type": ClassType, "render": True},
    "id": {"type": IdType, "render": True},
}


def merge_config(config: Dict[str, Any] | None = None) -> Dict[str, Any]:
    """Merge user config with default nodes/tags."""
    config = config or {}
    return {
        **config,
        "nodes": {**default_nodes, **config.get("nodes", {})},
        "tags": {**default_tags, **config.get("tags", {})},
        "functions": {**default_functions, **config.get("functions", {})},
        "global_attributes": {**global_attributes, **config.get("global_attributes", {})},
    }


def transform(node: Node | List[Node], config: Dict[str, Any] | None = None):
    """Transform AST nodes into a renderable tree."""
    cfg = merge_config(config)
    if isinstance(node, list):
        return [transform(child, cfg) for child in node]
    if node.type == "document":
        return [transform(child, cfg) for child in node.children]
    if node.type == "text":
        return node.content or ""
    if node.type == "code_inline":
        return Tag("code", {}, [node.content or ""])
    if node.type in ("variable", "function"):
        return node.attributes.get("value") if node.attributes else None
    if node.type == "softbreak":
        return " "
    if node.type == "code":
        return _render_code(node, None, fenced=False)
    if node.type == "fence":
        return _render_code(node, node.attributes.get("language"), fenced=True)

    schema = _find_schema(node, cfg)
    if schema and callable(schema.get("transform")):
        return schema["transform"](node, cfg)

    if node.type == "list":
        name = "ol" if node.attributes.get("ordered") else "ul"
        return _make_tag(name, {}, _transform_children(node, cfg), schema)
    if node.type == "item":
        children = node.children
        if children and isinstance(children[0], Node) and children[0].type == "paragraph":
            if len(children) == 1:
                return _make_tag(
                    "li",
                    _render_attributes(node, schema, cfg),
                    _transform_children(children[0], cfg),
                    schema,
                )
            flattened = [
                *(_transform_children(children[0], cfg)),
                *[transform(child, cfg) for child in children[1:]],
            ]
            return _make_tag("li", _render_attributes(node, schema, cfg), flattened, schema)
        return _make_tag(
            "li", _render_attributes(node, schema, cfg), _transform_children(node, cfg), schema
        )

    if schema is None:
        if node.type == "tag":
            return _transform_children(node, cfg)
        return ""

    render = schema.get("render")
    if render is False:
        return _transform_children(node, cfg)
    if render is None:
        return _transform_children(node, cfg)

    if isinstance(render, str):
        name = render.format(**node.attributes) if "{" in render else render
        return _make_tag(name, _render_attributes(node, schema, cfg), _transform_children(node, cfg), schema)

    return ""


def _transform_children(node: Node, config: Dict[str, Any]) -> List[Any]:
    return [transform(child, config) for child in node.children]


def _find_schema(node: Node, config: Dict[str, Any]) -> Dict[str, Any] | None:
    if node.type == "tag":
        return config.get("tags", {}).get(node.tag)
    return config.get("nodes", {}).get(node.type)


def _render_attributes(
    node: Node, schema: Dict[str, Any] | None, config: Dict[str, Any]
) -> Dict[str, Any]:
    if not schema:
        return dict(node.attributes)
    rendered: Dict[str, Any] = {}
    schema_attrs = schema.get("attributes", {}) if schema else {}
    attrs = {**global_attributes, **schema_attrs} if isinstance(schema_attrs, dict) else dict(global_attributes)

    for key, attr in attrs.items():
        if isinstance(attr, dict) and attr.get("render") is False:
            continue
        render_as = attr.get("render", True) if isinstance(attr, dict) else True
        name = render_as if isinstance(render_as, str) else key
        value = node.attributes.get(key)
        if value is None and isinstance(attr, dict) and "default" in attr:
            value = attr.get("default")
        if value is None:
            continue
        type_cls = attr.get("type") if isinstance(attr, dict) else None
        if isinstance(type_cls, type):
            instance = type_cls()
            if hasattr(instance, "transform"):
                value = instance.transform(value)
        rendered[name] = value

    if schema.get("slots") and node.slots:
        for key, slot in schema["slots"].items():
            if isinstance(slot, dict) and slot.get("render") is False:
                continue
            name = slot.get("render") if isinstance(slot, dict) else key
            if isinstance(name, str) and key in node.slots:
                rendered[name] = transform(node.slots[key], config)

    return rendered


def _render_code(node: Node, language: str | None, *, fenced: bool):
    """Render fenced or indented code blocks."""
    if fenced:
        attrs: Dict[str, Any] = {}
        if language:
            attrs["data-language"] = language
        return Tag("pre", attrs, [node.content or ""])
    return Tag("pre", {}, [node.content or ""])


def _make_tag(
    name: str | None, attributes: Dict[str, Any], children: List[Any], schema: Dict[str, Any] | None
) -> Tag:
    self_closing = bool(schema.get("self_closing")) if schema else False
    return Tag(name, attributes, children, self_closing=self_closing)
