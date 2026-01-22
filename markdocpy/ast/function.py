from __future__ import annotations

from dataclasses import dataclass, field
import inspect
from typing import Any, Dict, List

from .variable import Variable


@dataclass
class Function:
    """Reference to a function to be resolved at transform time."""

    name: str
    args: List[Any] = field(default_factory=list)
    kwargs: Dict[str, Any] = field(default_factory=dict)

    def resolve(self, config: Dict[str, Any]) -> Any:
        """Resolve the function with args/kwargs using the config."""
        fn = config.get("functions", {}).get(self.name)
        if fn is None:
            return None
        resolved_args = [_resolve_value(arg, config) for arg in self.args]
        resolved_kwargs = {key: _resolve_value(val, config) for key, val in self.kwargs.items()}
        parameters = {index: value for index, value in enumerate(resolved_args)}
        parameters.update(resolved_kwargs)
        if callable(fn):
            return fn(*resolved_args, **resolved_kwargs)
        transform = fn.get("transform") if isinstance(fn, dict) else None
        if callable(transform):
            return _call_transform(transform, parameters, config)
        return None


def _call_transform(transform, parameters: Dict[Any, Any], config: Dict[str, Any]) -> Any:
    try:
        arity = len(inspect.signature(transform).parameters)
    except (ValueError, TypeError):
        arity = 1
    if arity >= 2:
        return transform(parameters, config)
    return transform(parameters)


def _resolve_value(value: Any, config: Dict[str, Any]) -> Any:
    if isinstance(value, (Variable, Function)):
        return value.resolve(config)
    if isinstance(value, list):
        return [_resolve_value(item, config) for item in value]
    if isinstance(value, dict):
        return {key: _resolve_value(val, config) for key, val in value.items()}
    return value
