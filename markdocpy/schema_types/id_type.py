from __future__ import annotations

from typing import Any, Dict, List


def validate_id(value: Any) -> List[Dict[str, Any]]:
    if isinstance(value, str) and value[:1].isalpha():
        return []
    return [
        {
            "id": "attribute-value-invalid",
            "level": "error",
            "message": "The 'id' attribute must start with a letter",
        }
    ]


class IdType:
    def validate(self, value: Any, _config: Dict[str, Any], _key: str):
        return validate_id(value)
