import json
from pathlib import Path

import markdocpy as Markdoc

SPEC_DIR = Path(__file__).parent / "spec"
EXPECTED_DIR = SPEC_DIR / "expected"
JS_DIR = SPEC_DIR / "js"


def load_manifest():
    return json.loads((SPEC_DIR / "manifest.json").read_text())


def spec_configs():
    return {
        "interpolation": {
            "variables": {"name": "Ada"},
            "functions": {"add": {"transform": lambda params: sum(params.values())}},
        },
        "variables_paths": {"variables": {"user": {"name": "Ada"}, "flags": ["on"]}},
        "functions_params": {"variables": {"missing": None}},
        "validator_rules": {
            "tags": {
                "panel": {
                    "render": "panel",
                    "children": ["paragraph"],
                    "attributes": {"title": {"required": True}},
                    "errorLevel": "error",
                },
                "note": {"render": "note"},
            }
        },
        "renderer_basics": {"tags": {"note": {"render": "note"}, "icon": {"render": "icon", "self_closing": True}}},
        "schema_defaults": {},
        "syntax_tags": {"tags": {"note": {"render": "note"}}},
        "annotations": {},
        "values": {"tags": {"note": {"render": "note"}}},
    }


def serialize_node(node: Markdoc.Node):
    from tests.fixtures.utils import serialize_node as _serialize

    return _serialize(node)


def normalize_html(value: str) -> str:
    value = value.replace("\r\n", "\n").strip()
    return value.replace(" </", "</")


def test_spec_parity_ast_and_html():
    configs = spec_configs()
    expected_mismatches = {
        entry["name"] for entry in load_manifest() if entry.get("xfail_js")
    }
    actual_mismatches = set()
    for entry in load_manifest():
        name = entry["name"]
        config = configs.get(name, {})
        source = (SPEC_DIR / f"{name}.md").read_text()

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
        if js_html_path.exists():
            js_html = normalize_html(js_html_path.read_text())
            js_html = js_html.replace(" </", "</")
            if html != js_html:
                actual_mismatches.add(name)
                if not entry.get("xfail_js"):
                    raise AssertionError(
                        f"Spec mismatch for {name}: expected JS parity, got different HTML"
                    )
    if expected_mismatches != actual_mismatches:
        missing = expected_mismatches - actual_mismatches
        extra = actual_mismatches - expected_mismatches
        raise AssertionError(
            f"Spec mismatch tracking out of date. missing={sorted(missing)} extra={sorted(extra)}"
        )
