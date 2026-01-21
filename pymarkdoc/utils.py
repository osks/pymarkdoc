from __future__ import annotations


def find_tag_end(content: str, start: int = 0) -> int | None:
    state = "normal"
    pos = start
    while pos < len(content):
        char = content[pos]
        if state == "string":
            if char == "\\":
                state = "escape"
            elif char == '"':
                state = "normal"
        elif state == "escape":
            state = "string"
        else:
            if char == '"':
                state = "string"
            elif content.startswith("%}", pos):
                return pos
        pos += 1
    return None
