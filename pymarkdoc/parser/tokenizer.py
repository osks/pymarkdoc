from __future__ import annotations

from markdown_it import MarkdownIt


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
        is_tag_line = stripped.startswith("{%") and stripped.endswith("%}") and stripped != "{%%}"
        if is_tag_line:
            if output and output[-1].strip() != "":
                output.append("")
            output.append(line)
            if idx + 1 < len(lines) and lines[idx + 1].strip() != "":
                output.append("")
            continue
        output.append(line)
    return "\n".join(output)
