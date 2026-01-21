from __future__ import annotations

from markdown_it import MarkdownIt


class Tokenizer:
    def __init__(self, config: dict | None = None) -> None:
        options = config or {}
        self.parser = MarkdownIt("commonmark", options_update=options) if options else MarkdownIt()
        self.parser.enable("table")
        self.parser.disable(["lheading", "code"])

    def tokenize(self, content: str):
        return self.parser.parse(content, {})
