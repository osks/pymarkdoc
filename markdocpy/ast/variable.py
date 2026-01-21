from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict


@dataclass
class Variable:
    """Reference to a variable to be resolved at transform time."""

    name: str

    def resolve(self, config: Dict[str, Any]) -> Any:
        """Resolve the variable value from the config."""
        return config.get("variables", {}).get(self.name)
