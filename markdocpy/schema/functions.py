from __future__ import annotations

import json
from typing import Any, Dict

from ..ast.variable import MISSING


def _truthy(value: Any) -> bool:
    return value is not False and value is not None and value is not MISSING


def _values(parameters: Dict[Any, Any]) -> list[Any]:
    if not isinstance(parameters, dict):
        return [parameters]
    return list(parameters.values())


def _and(parameters: Dict[Any, Any]) -> bool:
    return all(_truthy(value) for value in _values(parameters))


def _or(parameters: Dict[Any, Any]) -> bool:
    return any(_truthy(value) for value in _values(parameters))


def _not(parameters: Dict[Any, Any]) -> bool:
    return not _truthy(parameters.get(0) if isinstance(parameters, dict) else parameters)


def _equals(parameters: Dict[Any, Any]) -> bool:
    values = _values(parameters)
    if not values:
        return True
    first = values[0]
    return all(value == first for value in values)


def _default(parameters: Dict[Any, Any]) -> Any:
    if not isinstance(parameters, dict):
        return parameters
    first = parameters.get(0)
    if first is MISSING:
        return parameters.get(1)
    return first


def _debug(parameters: Dict[Any, Any]) -> str:
    value = parameters.get(0) if isinstance(parameters, dict) else parameters
    if value is MISSING:
        return None
    return json.dumps(value, indent=2)


functions = {
    "and": {"transform": _and},
    "or": {"transform": _or},
    "not": {"transform": _not, "parameters": {0: {"required": True}}},
    "equals": {"transform": _equals},
    "default": {"transform": _default},
    "debug": {"transform": _debug},
}
