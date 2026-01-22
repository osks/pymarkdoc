from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .function import Function
from .variable import Variable


@dataclass
class Node:
    """AST node for parsed Markdoc content."""

    type: str
    children: List["Node"] = field(default_factory=list)
    attributes: Dict[str, Any] = field(default_factory=dict)
    tag: Optional[str] = None
    content: Optional[str] = None
    slots: Dict[str, "Node"] = field(default_factory=dict)
    inline: bool = False

    def resolve(self, config: Any) -> "Node":
        """Resolve variables/functions in this node and its children."""
        self.attributes = _resolve_value(self.attributes, config)
        resolved_children = []
        for child in self.children:
            if isinstance(child, Node):
                resolved_children.append(child.resolve(config))
            else:
                resolved_children.append(_resolve_value(child, config))
        self.children = resolved_children
        return self

    def transform(self, config: Any) -> Any:
        """Transform the node into a renderable tree."""
        from ..transform.transformer import transform

        return transform(self, config)


def _resolve_value(value: Any, config: Any) -> Any:
    if isinstance(value, Variable) or isinstance(value, Function):
        return value.resolve(config)
    if isinstance(value, list):
        return [_resolve_value(item, config) for item in value]
    if isinstance(value, dict):
        return {key: _resolve_value(val, config) for key, val in value.items()}
    return value
