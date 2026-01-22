import markdocpy as Markdoc


def test_parent_validation_warns_when_missing():
    source = "{% note %}Body{% /note %}"
    ast = Markdoc.parse(source)
    config = {"tags": {"note": {"parents": ["section"]}}}
    errors = Markdoc.validate(ast, config)
    assert any(err["id"] == "parent-invalid" for err in errors)


def test_parent_validation_allows_allowed_parent():
    source = "{% section %}\n\n{% note %}Body{% /note %}\n\n{% /section %}"
    ast = Markdoc.parse(source)
    config = {
        "tags": {"note": {"parents": ["section"]}, "section": {"render": "section"}}
    }
    errors = Markdoc.validate(ast, config)
    assert not any(err["id"] == "parent-invalid" for err in errors)


def test_children_error_level_override():
    source = "{% panel %}Body{% /panel %}"
    ast = Markdoc.parse(source)
    config = {"tags": {"panel": {"children": ["heading"], "errorLevel": "error"}}}
    errors = Markdoc.validate(ast, config)
    assert any(err["id"] == "child-invalid" and err["level"] == "error" for err in errors)


def test_inline_error_level_override():
    source = "{% pill %}\n\nText\n\n{% /pill %}"
    ast = Markdoc.parse(source)
    config = {"tags": {"pill": {"inline": True, "errorLevel": "error"}}}
    errors = Markdoc.validate(ast, config)
    assert any(err["id"] == "tag-placement-invalid" and err["level"] == "error" for err in errors)
