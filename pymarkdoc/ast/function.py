from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class Function:
    name: str
    args: List[Any] = field(default_factory=list)
    kwargs: Dict[str, Any] = field(default_factory=dict)

    def resolve(self, config: Dict[str, Any]) -> Any:
        fn = config.get("functions", {}).get(self.name)
        if fn is None:
            return None
        if callable(fn):
            return fn(*self.args, **self.kwargs)
        transform = fn.get("transform") if isinstance(fn, dict) else None
        if callable(transform):
            return transform(self.kwargs or {"args": self.args}, config)
        return None
