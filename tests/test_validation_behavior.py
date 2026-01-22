import re

import markdocpy as Markdoc


def test_inline_tag_placement_error_for_block_tag():
    source = "Hello {% note %}world{% /note %}"
    ast = Markdoc.parse(source)
    config = {"tags": {"note": {"inline": False}}}
    errors = Markdoc.validate(ast, config)
    assert any(err["id"] == "tag-placement-invalid" for err in errors)


def test_block_tag_placement_error_for_inline_tag():
    source = "{% pill %}\n\nHi\n\n{% /pill %}"
    ast = Markdoc.parse(source)
    config = {"tags": {"pill": {"inline": True}}}
    errors = Markdoc.validate(ast, config)
    assert any(err["id"] == "tag-placement-invalid" for err in errors)


def test_attribute_missing_and_undefined_errors():
    source = '{% note tone="loud" %}Text{% /note %}'
    ast = Markdoc.parse(source)
    config = {
        "tags": {
            "note": {
                "attributes": {
                    "title": {"required": True},
                }
            }
        }
    }
    errors = Markdoc.validate(ast, config)
    ids = {err["id"] for err in errors}
    assert "attribute-missing-required" in ids
    assert "attribute-undefined" in ids


def test_attribute_matches_regex():
    source = '{% note tone="bad" %}Text{% /note %}'
    ast = Markdoc.parse(source)
    config = {
        "tags": {
            "note": {
                "attributes": {
                    "tone": {"type": str, "matches": re.compile(r"^(info|warn)$")},
                }
            }
        }
    }
    errors = Markdoc.validate(ast, config)
    assert any(err["id"] == "attribute-value-invalid" for err in errors)


def test_function_validation_unknown_function():
    source = "Result {% sum(1, 2) %}"
    ast = Markdoc.parse(source)
    errors = Markdoc.validate(ast, {"validation": {"validateFunctions": True}})
    assert any(err["id"] == "function-undefined" for err in errors)


def test_function_parameter_validation():
    source = "Result {% sum(count=1) %}"
    ast = Markdoc.parse(source)
    config = {
        "validation": {"validateFunctions": True},
        "functions": {"sum": {"parameters": {"count": {"type": str, "required": True}}}},
    }
    errors = Markdoc.validate(ast, config)
    ids = {err["id"] for err in errors}
    assert "parameter-type-invalid" in ids


def test_function_positional_parameter_validation():
    source = "Result {% sum(1) %}"
    ast = Markdoc.parse(source)
    config = {
        "validation": {"validateFunctions": True},
        "functions": {"sum": {"parameters": {0: {"type": str}}}},
    }
    errors = Markdoc.validate(ast, config)
    assert any(err["id"] == "parameter-type-invalid" for err in errors)


def test_variable_validation_unknown_variable():
    source = "Hello {% $name %}"
    ast = Markdoc.parse(source)
    errors = Markdoc.validate(ast, {"variables": {}})
    assert any(err["id"] == "variable-undefined" for err in errors)


def test_attribute_function_validation_unknown_function():
    source = '{% note count=sum(1, 2) %}Text{% /note %}'
    ast = Markdoc.parse(source)
    config = {
        "validation": {"validateFunctions": True},
        "tags": {"note": {"attributes": {"count": {"type": "Number"}}}},
    }
    errors = Markdoc.validate(ast, config)
    assert any(err["id"] == "function-undefined" for err in errors)


def test_attribute_variable_validation_unknown_variable():
    source = '{% note count=$total %}Text{% /note %}'
    ast = Markdoc.parse(source)
    config = {"tags": {"note": {"attributes": {"count": {"type": "Number"}}}}, "variables": {}}
    errors = Markdoc.validate(ast, config)
    assert any(err["id"] == "variable-undefined" for err in errors)


def test_slot_validation_required_and_undefined():
    source = """{% card %}
{% slot "title" %}
Title
{% /slot %}
{% /card %}"""
    ast = Markdoc.parse(source, slots=True)
    config = {
        "tags": {
            "card": {"slots": {"title": {"required": True}, "body": {"required": True}}},
        }
    }
    errors = Markdoc.validate(ast, config)
    ids = {err["id"] for err in errors}
    assert "slot-missing-required" in ids


def test_slot_validation_unknown_slot():
    source = """{% card %}
{% slot "body" %}
Body
{% /slot %}
{% /card %}"""
    ast = Markdoc.parse(source, slots=True)
    config = {"tags": {"card": {"slots": {"title": {"required": False}}}}}
    errors = Markdoc.validate(ast, config)
    assert any(err["id"] == "slot-undefined" for err in errors)
