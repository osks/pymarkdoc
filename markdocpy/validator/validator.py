from __future__ import annotations

from typing import Any, Dict, List

from ..ast.node import Node
from ..schema_types import ClassType, IdType
from ..transform.transformer import merge_config


def validate_tree(
    node: Node | List[Node], config: Dict[str, Any] | None = None
) -> List[Dict[str, Any]]:
    """Validate nodes against schema rules."""
    cfg = merge_config(config)
    errors: List[Dict[str, Any]] = []
    for child, parents in _walk_with_parents(node):
        updated = {**cfg, "validation": {**cfg.get("validation", {}), "parents": parents}}
        _validate_node(child, updated, errors)
    return errors


def _validate_node(node: Node | List[Node], config: Dict[str, Any], errors: List[Dict[str, Any]]):
    """Recursively validate nodes and collect errors."""
    if isinstance(node, list):
        for child in node:
            _validate_node(child, config, errors)
        return

    schema = _find_schema(node, config)
    if schema:
        _validate_placement(node, schema, errors)
        _validate_parents(node, schema, config, errors)
        _validate_attributes(node, schema, config, errors)
        _validate_slots(node, schema, errors)
        _validate_children(node, schema, errors)
        if callable(schema.get("validate")):
            errors.extend(schema["validate"](node, config))

    if node.type == "function":
        errors.extend(_validate_function(node, config))
    if node.type == "variable":
        errors.extend(_validate_variable(node, config))


def _find_schema(node: Node, config: Dict[str, Any]) -> Dict[str, Any] | None:
    if node.type == "tag":
        return config.get("tags", {}).get(node.tag)
    return config.get("nodes", {}).get(node.type)


def _validate_attributes(
    node: Node, schema: Dict[str, Any], config: Dict[str, Any], errors: List[Dict[str, Any]]
):
    schema_attrs = schema.get("attributes", {}) if schema else {}
    if not isinstance(schema_attrs, dict):
        return
    attrs = {**{"class": {"type": ClassType}, "id": {"type": IdType}}, **schema_attrs}

    for key in node.attributes.keys():
        if key not in attrs:
            errors.append(
                {
                    "id": "attribute-undefined",
                    "level": "error",
                    "message": f"Invalid attribute: '{key}'",
                }
            )

    for key, definition in attrs.items():
        if not isinstance(definition, dict):
            continue
        if definition.get("required") and key not in node.attributes:
            errors.append(
                {
                    "id": "attribute-missing-required",
                    "level": "error",
                    "message": f"Missing required attribute: '{key}'",
                }
            )
            continue
        if key not in node.attributes:
            continue

        expected = definition.get("type")
        if expected is None:
            continue
        if isinstance(expected, type) and hasattr(expected, "validate"):
            instance = expected()
            errors.extend(instance.validate(node.attributes.get(key), config, key))
            continue
        if config.get("validation", {}).get("validateFunctions") and _is_function(
            node.attributes.get(key)
        ):
            errors.extend(_validate_function_value(node.attributes.get(key), config))
            continue
        if _is_variable(node.attributes.get(key)):
            errors.extend(_validate_variable_value(node.attributes.get(key), config))
            continue
        if not _check_type(node.attributes.get(key), expected):
            errors.append(
                {
                    "id": "attribute-type-invalid",
                    "level": definition.get("errorLevel", "error"),
                    "message": f"Attribute '{key}' must be type of '{_type_to_string(expected)}'",
                }
            )
            continue

        matches = definition.get("matches")
        if callable(matches):
            matches = matches(config)
        if matches is not None and not _check_matches(node.attributes.get(key), matches):
            errors.append(
                {
                    "id": "attribute-value-invalid",
                    "level": definition.get("errorLevel", "error"),
                    "message": f"Invalid value for attribute '{key}'",
                }
            )

        if callable(definition.get("validate")):
            errors.extend(definition["validate"](node.attributes.get(key), config, key))


def _validate_slots(node: Node, schema: Dict[str, Any], errors: List[Dict[str, Any]]):
    slots = schema.get("slots")
    if not slots:
        return
    for key in node.slots.keys():
        if key not in slots:
            errors.append(
                {
                    "id": "slot-undefined",
                    "level": "error",
                    "message": f"Invalid slot: '{key}'",
                }
            )
    for key, slot in slots.items():
        if isinstance(slot, dict) and slot.get("required") and key not in node.slots:
            errors.append(
                {
                    "id": "slot-missing-required",
                    "level": "error",
                    "message": f"Missing required slot: '{key}'",
                }
            )


def _validate_children(node: Node, schema: Dict[str, Any], errors: List[Dict[str, Any]]):
    allowed = schema.get("children")
    if not allowed:
        return
    for child in node.children:
        if child.type != "error" and child.type not in allowed:
            errors.append(
                {
                    "id": "child-invalid",
                    "level": schema.get("errorLevel", "warning"),
                    "message": f"Can't nest '{child.type}' in '{node.tag or node.type}'",
                }
            )


def _validate_placement(node: Node, schema: Dict[str, Any], errors: List[Dict[str, Any]]):
    inline = schema.get("inline")
    if inline is None:
        return
    if bool(node.inline) != bool(inline):
        errors.append(
            {
                "id": "tag-placement-invalid",
                "level": schema.get("errorLevel", "critical"),
                "message": f"'{node.tag}' tag should be {'inline' if inline else 'block'}",
            }
        )


def _validate_parents(
    node: Node, schema: Dict[str, Any], config: Dict[str, Any], errors: List[Dict[str, Any]]
):
    allowed = schema.get("parents")
    if not allowed:
        return
    parents = config.get("validation", {}).get("parents", [])
    if not parents:
        errors.append(
            {
                "id": "parent-invalid",
                "level": schema.get("errorLevel", "warning"),
                "message": f"'{node.tag or node.type}' cannot be at the document root",
            }
        )
        return
    for parent in reversed(parents):
        if (parent.tag and parent.tag in allowed) or parent.type in allowed:
            return
        if parent.type not in ("paragraph",):
            break
    errors.append(
        {
            "id": "parent-invalid",
            "level": schema.get("errorLevel", "warning"),
            "message": f"'{node.tag or node.type}' cannot be nested in '{parents[-1].tag or parents[-1].type}'",
        }
    )


def _validate_function(node: Node, config: Dict[str, Any]) -> List[Dict[str, Any]]:
    value = node.attributes.get("value")
    if not _is_function(value):
        return []
    if not config.get("validation", {}).get("validateFunctions"):
        return []
    return _validate_function_value(value, config)


def _validate_function_value(value: Any, config: Dict[str, Any]) -> List[Dict[str, Any]]:
    errors: List[Dict[str, Any]] = []
    fn = config.get("functions", {}).get(value.name)
    if fn is None:
        return [
            {
                "id": "function-undefined",
                "level": "critical",
                "message": f"Undefined function: '{value.name}'",
            }
        ]

    schema = fn if isinstance(fn, dict) else {}
    parameters = _function_parameters(value)
    param_schema = schema.get("parameters", {}) if isinstance(schema, dict) else {}

    for key, param_value in parameters.items():
        if key not in param_schema:
            errors.append(
                {
                    "id": "parameter-undefined",
                    "level": "error",
                    "message": f"Invalid parameter: '{key}'",
                }
            )
            continue
        expected = param_schema[key].get("type")
        if expected and not _check_type(param_value, expected):
            errors.append(
                {
                    "id": "parameter-type-invalid",
                    "level": "error",
                    "message": f"Parameter '{key}' must be type of '{_type_to_string(expected)}'",
                }
            )

    for key, definition in param_schema.items():
        if definition.get("required") and key not in parameters:
            errors.append(
                {
                    "id": "parameter-missing-required",
                    "level": "error",
                    "message": f"Missing required parameter: '{key}'",
                }
            )

    return errors


def _function_parameters(value: Any) -> Dict[str, Any]:
    params = {index: arg for index, arg in enumerate(value.args)}
    params.update(value.kwargs)
    return params


def _validate_variable(node: Node, config: Dict[str, Any]) -> List[Dict[str, Any]]:
    value = node.attributes.get("value")
    if not _is_variable(value):
        return []
    return _validate_variable_value(value, config)


def _validate_variable_value(value: Any, config: Dict[str, Any]) -> List[Dict[str, Any]]:
    variables = config.get("variables")
    if not isinstance(variables, dict):
        return []
    if value.name not in variables:
        return [
            {
                "id": "variable-undefined",
                "level": "error",
                "message": f"Undefined variable: '{value.name}'",
            }
        ]
    return []


def _is_function(value: Any) -> bool:
    return hasattr(value, "name") and hasattr(value, "args") and hasattr(value, "kwargs")


def _is_variable(value: Any) -> bool:
    return hasattr(value, "name") and not hasattr(value, "args")


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


def _type_to_string(expected: Any) -> str:
    if isinstance(expected, (list, tuple)):
        return " | ".join(_type_to_string(item) for item in expected)
    if isinstance(expected, str):
        return expected
    return expected.__name__


def _check_matches(value: Any, matches: Any) -> bool:
    if matches is None:
        return True
    if hasattr(matches, "search"):
        return bool(matches.search(str(value)))
    if isinstance(matches, (list, tuple)):
        return value in matches
    return True


def _walk_with_parents(node: Node | List[Node], parents: List[Node] | None = None):
    if parents is None:
        parents = []
    if isinstance(node, list):
        for child in node:
            yield from _walk_with_parents(child, parents)
        return
    yield node, parents
    for child in [*node.children, *node.slots.values()]:
        yield from _walk_with_parents(child, [*parents, node])
