import markdocpy as Markdoc


def test_variable_path_dot_and_bracket():
    source = "User: {% $user.name %} Flag: {% $flags[0] %}"
    ast = Markdoc.parse(source)
    html = Markdoc.renderers.html(
        Markdoc.transform(ast, {"variables": {"user": {"name": "Ada"}, "flags": ["on"]}})
    )
    assert html == "<p>User: Ada Flag: on</p>"


def test_variable_missing_path_reports_error():
    source = "Value: {% $user.name %}"
    ast = Markdoc.parse(source)
    errors = Markdoc.validate(ast, {"variables": {"user": {}}})
    assert any(err["id"] == "variable-undefined" for err in errors)
