import markdocpy as Markdoc


def test_milestone_05_simple_parse_transform():
    source = "# Hello\n\nThis is {% note %}important{% /note %}."
    ast = Markdoc.parse(source)
    content = Markdoc.transform(ast)
    html = Markdoc.renderers.html(content)
    assert html == "<h1>Hello</h1><p>This is <note>important</note>.</p>"
