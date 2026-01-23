from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Iterable, List


@dataclass
class Variable:
    """Reference to a variable to be resolved at transform time."""

    path: List[Any] = field(default_factory=list)

    def __init__(self, path: str | Iterable[Any] | None = None):
        if path is None:
            self.path = []
        elif isinstance(path, str):
            self.path = [path]
        else:
            self.path = list(path)

    @property
    def name(self) -> str:
        return _path_to_string(self.path)

    def resolve(self, config: Dict[str, Any]) -> Any:
        """Resolve the variable value from the config."""
        variables = config.get("variables", {})
        if callable(variables):
            return variables(self.path)
        current = variables
        for segment in self.path:
            if isinstance(current, dict):
                if segment not in current:
                    return None
                current = current[segment]
                continue
            if isinstance(current, (list, tuple)):
                if not isinstance(segment, int) or segment < 0 or segment >= len(current):
                    return None
                current = current[segment]
                continue
            return None
        return current


def _path_to_string(path: List[Any]) -> str:
    parts: List[str] = []
    for segment in path:
        if isinstance(segment, str) and segment.isidentifier():
            parts.append(segment)
        else:
            parts.append(f"[{segment!r}]")
    return ".".join(parts) if parts else ""
