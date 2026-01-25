from __future__ import annotations

from markdown_it import MarkdownIt

from ..utils import find_tag_end


class Tokenizer:
    def __init__(self, config: dict | None = None) -> None:
        options = config or {}
        self.parser = MarkdownIt("commonmark", options_update=options) if options else MarkdownIt()
        self.parser.enable("table")
        self.parser.disable(["lheading", "code"])

    def tokenize(self, content: str):
        normalized = _normalize_block_tags(content)
        return self.parser.parse(normalized, {})


def _normalize_block_tags(content: str) -> str:
    lines = content.splitlines()
    output: list[str] = []
    for idx, line in enumerate(lines):
        stripped = line.strip()
        is_tag_line = _is_single_tag_line(stripped)
        if is_tag_line:
            if output and output[-1].strip() != "":
                output.append("")
            output.append(line)
            if idx + 1 < len(lines) and lines[idx + 1].strip() != "":
                output.append("")
            continue
        output.append(line)
    return "\n".join(output)


def _is_single_tag_line(stripped: str) -> bool:
    if not stripped.startswith("{%") or not stripped.endswith("%}"):
        return False
    if stripped == "{%%}":
        return False
    tag_end = find_tag_end(stripped, 0)
    if tag_end is None:
        return False
    return tag_end + 2 == len(stripped)
