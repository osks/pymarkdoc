import markdocpy as Markdoc


def _render(source: str) -> str:
    ast = Markdoc.parse(source)
    return Markdoc.renderers.html(Markdoc.transform(ast))


def test_builtin_and_or_not_equals():
    source = "{% if and(true, not(false), equals(1, 1)) %}Yes{% /if %}"
    assert _render(source) == "<p>Yes</p>"


def test_builtin_default():
    source = "{% if default($flag, true) %}On{% /if %}"
    ast = Markdoc.parse(source)
    html = Markdoc.renderers.html(Markdoc.transform(ast, {"variables": {}}))
    assert html == "<p>On</p>"


def test_builtin_debug():
    source = "Value: {% debug($data) %}"
    ast = Markdoc.parse(source)
    html = Markdoc.renderers.html(Markdoc.transform(ast, {"variables": {"data": {"a": 1}}}))
    assert "&quot;a&quot;: 1" in html
