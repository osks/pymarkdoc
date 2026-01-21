from __future__ import annotations

from typing import Any, Dict, List


def transform_class(value: Any) -> Any:
    if value is None or isinstance(value, str):
        return value
    if isinstance(value, dict):
        classes = [key for key, enabled in value.items() if enabled]
        return " ".join(classes)
    return value


def validate_class(value: Any, key: str) -> List[Dict[str, Any]]:
    if isinstance(value, (str, dict)):
        return []
    return [
        {
            "id": "attribute-type-invalid",
            "level": "error",
            "message": f"Attribute '{key}' must be type 'string | object'",
        }
    ]


class ClassType:
    def transform(self, value: Any) -> Any:
        return transform_class(value)

    def validate(self, value: Any, _config: Dict[str, Any], key: str):
        return validate_class(value, key)
