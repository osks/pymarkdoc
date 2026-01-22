import markdocpy as Markdoc


def test_slots_render_into_attributes():
    source = """{% card %}
{% slot "title" %}
Hello
{% /slot %}
{% /card %}"""
    ast = Markdoc.parse(source, slots=True)
    card = ast.children[0]
    assert "title" in card.slots
    slot = card.slots["title"]
    assert slot.tag == "slot"
    assert slot.children[0].children[0].content == "Hello"
