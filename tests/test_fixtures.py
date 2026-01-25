import json
from pathlib import Path

import markdocpy as Markdoc
from tests.fixtures.utils import fixture_configs, normalize_html, serialize_node

FIXTURES_DIR = Path(__file__).parent / "fixtures"
EXPECTED_DIR = FIXTURES_DIR / "expected"
JS_DIR = FIXTURES_DIR / "js"


def load_manifest():
    return json.loads((FIXTURES_DIR / "manifest.json").read_text())


def test_fixtures_ast_and_html():
    configs = fixture_configs()
    for entry in load_manifest():
        name = entry["name"]
        config = configs.get(entry.get("config"))
        source = (FIXTURES_DIR / f"{name}.md").read_text()

        ast = Markdoc.parse(source)
        expected_ast_path = EXPECTED_DIR / f"{name}.ast.json"
        if expected_ast_path.exists():
            expected_ast = json.loads(expected_ast_path.read_text())
            assert serialize_node(ast) == expected_ast

        content = Markdoc.transform(ast, config or {})
        html = normalize_html(Markdoc.renderers.html(content))
        expected_html_path = EXPECTED_DIR / f"{name}.html"
        if expected_html_path.exists():
            expected_html = normalize_html(expected_html_path.read_text())
            assert html == expected_html

        js_html_path = JS_DIR / f"{name}.html"
        if js_html_path.exists() and not entry.get("skip_js_html"):
            js_html = normalize_html(js_html_path.read_text())
            js_html = js_html.replace(" </", "</")
            assert html == js_html
