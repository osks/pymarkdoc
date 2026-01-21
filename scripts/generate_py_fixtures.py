from __future__ import annotations

import json
from pathlib import Path

import pymarkdoc as Markdoc
from tests.fixtures.utils import fixture_configs, normalize_html, serialize_node

ROOT = Path(__file__).resolve().parents[1]
FIXTURES_DIR = ROOT / "tests" / "fixtures"
EXPECTED_DIR = FIXTURES_DIR / "expected"


def main() -> None:
    manifest = json.loads((FIXTURES_DIR / "manifest.json").read_text())
    configs = fixture_configs()
    EXPECTED_DIR.mkdir(parents=True, exist_ok=True)

    for entry in manifest:
        name = entry["name"]
        config = configs.get(entry.get("config"))
        source = (FIXTURES_DIR / f"{name}.md").read_text()

        ast = Markdoc.parse(source)
        (EXPECTED_DIR / f"{name}.ast.json").write_text(
            json.dumps(serialize_node(ast), indent=2, sort_keys=True) + "\n"
        )

        content = Markdoc.transform(ast, config or {})
        html = normalize_html(Markdoc.renderers.html(content))
        (EXPECTED_DIR / f"{name}.html").write_text(html + "\n")


if __name__ == "__main__":
    main()
