from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict


@dataclass
class Variable:
    name: str

    def resolve(self, config: Dict[str, Any]) -> Any:
        return config.get("variables", {}).get(self.name)
