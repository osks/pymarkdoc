import markdocpy as Markdoc


def test_html_escapes_text():
    html = Markdoc.renderers.html('<tag> & "quote"')
    assert html == "&lt;tag&gt; &amp; &quot;quote&quot;"


def test_html_escapes_attribute_values():
    node = Markdoc.create_element("note", {"title": "A & B"}, "Body")
    html = Markdoc.renderers.html(node)
    assert html == '<note title="A &amp; B">Body</note>'


def test_void_elements_do_not_close():
    source = "![Alt](https://example.com/img.png)"
    ast = Markdoc.parse(source)
    html = Markdoc.renderers.html(Markdoc.transform(ast))
    assert "<img" in html
    assert "</img>" not in html


def test_nested_tags_render():
    source = "{% note %}Hello {% tag %}World{% /tag %}{% /note %}"
    ast = Markdoc.parse(source)
    html = Markdoc.renderers.html(Markdoc.transform(ast))
    assert html == "<p><note>Hello <tag>World</tag></note></p>"
