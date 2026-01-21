from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable, List, Mapping, Optional


@dataclass
class Tag:
    """Renderable tag node produced by the transformer."""
    name: Optional[str]
    attributes: Mapping[str, Any] = field(default_factory=dict)
    children: List[Any] = field(default_factory=list)

    @staticmethod
    def is_tag(value: Any) -> bool:
        return isinstance(value, Tag)

    def with_children(self, children: Iterable[Any]) -> "Tag":
        return Tag(self.name, dict(self.attributes), list(children))
