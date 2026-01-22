import markdocpy as Markdoc


def test_partial_renders_content_with_variables():
    partial = Markdoc.parse("# Title\n\nHello {% $name %}")
    source = '{% partial file="header.md" variables={name: "Ada"} /%}'
    ast = Markdoc.parse(source)
    html = Markdoc.renderers.html(
        Markdoc.transform(ast, {"partials": {"header.md": partial}, "variables": {"name": "Base"}})
    )
    assert html == "<h1>Title</h1><p>Hello Ada</p>"


def test_partial_missing_reports_error():
    source = '{% partial file="missing.md" /%}'
    ast = Markdoc.parse(source)
    errors = Markdoc.validate(ast, {"partials": {}})
    assert any(err["id"] == "attribute-value-invalid" for err in errors)
