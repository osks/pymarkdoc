import markdocpy as Markdoc


def test_multiline_block_tag_parses():
    source = """{% note
  title="A"
%}

Body

{% /note %}"""
    ast = Markdoc.parse(source)
    html = Markdoc.renderers.html(
        Markdoc.transform(ast, {"tags": {"note": {"render": "note", "attributes": {"title": {}}}}})
    )
    assert html == '<note title="A"><p>Body</p></note>'


def test_multiline_annotation_on_paragraph():
    source = "Title {%\n  .hero\n%}"
    ast = Markdoc.parse(source)
    html = Markdoc.renderers.html(Markdoc.transform(ast))
    assert html == '<p class="hero">Title</p>'


def test_inline_tag_spans_softbreaks():
    source = "Hello {% badge\n  color=\"green\" %}OK{% /badge %}"
    ast = Markdoc.parse(source)
    html = Markdoc.renderers.html(
        Markdoc.transform(ast, {"tags": {"badge": {"render": "badge", "attributes": {"color": {}}}}})
    )
    assert html == '<p>Hello <badge color="green">OK</badge></p>'


def test_inline_tag_only_line_does_not_break_paragraph():
    source = "{% if true %}Yes{% /if %}\nAfter"
    ast = Markdoc.parse(source)
    html = Markdoc.renderers.html(Markdoc.transform(ast))
    assert html == "<p>Yes After</p>"


def test_single_quote_with_tag_end_sequence():
    source = "{% note title='50%} ok' %}Body{% /note %}"
    ast = Markdoc.parse(source)
    html = Markdoc.renderers.html(
        Markdoc.transform(ast, {"tags": {"note": {"render": "note", "attributes": {"title": {}}}}})
    )
    assert html == '<p><note title="50%} ok">Body</note></p>'


def test_annotation_on_paragraph():
    source = "Hello {% .hero %}"
    ast = Markdoc.parse(source)
    html = Markdoc.renderers.html(Markdoc.transform(ast))
    assert html == '<p class="hero">Hello</p>'


def test_slot_with_nested_tag_content():
    source = """{% card %}
{% slot "title" %}
Hello {% badge %}New{% /badge %}
{% /slot %}
{% /card %}"""
    ast = Markdoc.parse(source, slots=True)
    card = ast.children[0]
    assert "title" in card.slots
    slot = card.slots["title"]
    paragraph = slot.children[0]
    tag = paragraph.children[1]
    assert tag.tag == "badge"


def test_complex_attribute_values():
    source = "{% note data={foo: [1, 2], bar: $name} count=sum(1, 2) %}Body{% /note %}"
    ast = Markdoc.parse(source)
    note = ast.children[0].children[0]
    data = note.attributes["data"]
    assert data["foo"] == [1, 2]
    assert isinstance(data["bar"], Markdoc.Variable)
    assert isinstance(note.attributes["count"], Markdoc.Function)
