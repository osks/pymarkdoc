from __future__ import annotations

from typing import Any, Dict, Iterable, List

from ..ast.node import Node
from ..ast.tag import Tag
from ..schema.nodes import nodes as default_nodes
from ..schema.tags import tags as default_tags


def merge_config(config: Dict[str, Any] | None = None) -> Dict[str, Any]:
    """Merge user config with default nodes/tags."""
    config = config or {}
    return {
        **config,
        "nodes": {**default_nodes, **config.get("nodes", {})},
        "tags": {**default_tags, **config.get("tags", {})},
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
    if node.type in ("variable", "function"):
        return node.attributes.get("value") if node.attributes else None
    if node.type == "softbreak":
        return "\n"
    if node.type == "code":
        return _render_code(node, None)
    if node.type == "fence":
        return _render_code(node, node.attributes.get("language"))

    schema = _find_schema(node, cfg)
    if schema and callable(schema.get("transform")):
        return schema["transform"](node, cfg)

    if node.type == "list":
        name = "ol" if node.attributes.get("ordered") else "ul"
        return Tag(name, _render_attributes(node, schema), _transform_children(node, cfg))

    if schema is None:
        if node.type == "tag":
            return Tag(node.tag, _render_attributes(node, schema), _transform_children(node, cfg))
        return ""

    render = schema.get("render")
    if render is False:
        return _transform_children(node, cfg)
    if render is None:
        return _transform_children(node, cfg)

    if isinstance(render, str):
        name = render.format(**node.attributes) if "{" in render else render
        return Tag(name, _render_attributes(node, schema), _transform_children(node, cfg))

    return ""


def _transform_children(node: Node, config: Dict[str, Any]) -> List[Any]:
    return [transform(child, config) for child in node.children]


def _find_schema(node: Node, config: Dict[str, Any]) -> Dict[str, Any] | None:
    if node.type == "tag":
        return config.get("tags", {}).get(node.tag)
    return config.get("nodes", {}).get(node.type)


def _render_attributes(node: Node, schema: Dict[str, Any] | None) -> Dict[str, Any]:
    if not node.attributes:
        return {}
    if not schema:
        return dict(node.attributes)
    rendered: Dict[str, Any] = {}
    schema_attrs = schema.get("attributes", {}) if schema else {}
    for key, value in node.attributes.items():
        config = schema_attrs.get(key, {}) if isinstance(schema_attrs, dict) else {}
        render_as = config.get("render", True)
        if render_as is False:
            continue
        if isinstance(render_as, str):
            rendered[render_as] = value
        else:
            rendered[key] = value
    return rendered


def _render_code(node: Node, language: str | None):
    """Render fenced or indented code blocks."""
    code_attrs: Dict[str, Any] = {}
    if language:
        code_attrs["class"] = f"language-{language}"
    return Tag("pre", {}, [Tag("code", code_attrs, [node.content or ""])])
