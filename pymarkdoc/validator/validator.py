from __future__ import annotations

from typing import Any, Dict, List

from ..ast.node import Node
from ..transform.transformer import merge_config


def validate_tree(node: Node | List[Node], config: Dict[str, Any] | None = None) -> List[Dict[str, Any]]:
    cfg = merge_config(config)
    errors: List[Dict[str, Any]] = []
    _validate_node(node, cfg, errors)
    return errors


def _validate_node(node: Node | List[Node], config: Dict[str, Any], errors: List[Dict[str, Any]]):
    if isinstance(node, list):
        for child in node:
            _validate_node(child, config, errors)
        return

    schema = _find_schema(node, config)
    if schema:
        _validate_attributes(node, schema, errors)

    for child in node.children:
        if isinstance(child, Node):
            _validate_node(child, config, errors)


def _find_schema(node: Node, config: Dict[str, Any]) -> Dict[str, Any] | None:
    if node.type == "tag":
        return config.get("tags", {}).get(node.tag)
    return config.get("nodes", {}).get(node.type)


def _validate_attributes(node: Node, schema: Dict[str, Any], errors: List[Dict[str, Any]]):
    schema_attrs = schema.get("attributes", {}) if schema else {}
    if not isinstance(schema_attrs, dict):
        return
    for key, definition in schema_attrs.items():
        if not isinstance(definition, dict):
            continue
        if definition.get("required") and key not in node.attributes:
            errors.append(
                {
                    "id": "missing-attribute",
                    "level": "error",
                    "message": f"Missing required attribute '{key}'",
                }
            )
            continue
        if key not in node.attributes:
            continue
        expected = definition.get("type")
        if expected is None:
            continue
        if not _check_type(node.attributes.get(key), expected):
            errors.append(
                {
                    "id": "invalid-attribute",
                    "level": "error",
                    "message": f"Invalid type for attribute '{key}'",
                }
            )


def _check_type(value: Any, expected: Any) -> bool:
    if isinstance(expected, (list, tuple)):
        return any(_check_type(value, item) for item in expected)
    if expected in (str, "String"):
        return isinstance(value, str)
    if expected in (int, float, "Number"):
        return isinstance(value, (int, float))
    if expected in (bool, "Boolean"):
        return isinstance(value, bool)
    if expected in (dict, "Object"):
        return isinstance(value, dict)
    if expected in (list, "Array"):
        return isinstance(value, list)
    return True
