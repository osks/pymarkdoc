import pymarkdoc as Markdoc


def test_block_tag_wraps_paragraph():
    source = "{% note %}\n\nHello\n\n{% /note %}"
    ast = Markdoc.parse(source)
    content = Markdoc.transform(ast)
    html = Markdoc.renderers.html(content)
    assert html == "<note><p>Hello</p></note>"


def test_annotation_applies_to_heading():
    source = "# Title {% .hero %}"
    ast = Markdoc.parse(source)
    content = Markdoc.transform(ast)
    html = Markdoc.renderers.html(content)
    assert html == '<h1 class="hero">Title</h1>'


def test_variable_interpolation():
    source = "Hello {% $name %}"
    ast = Markdoc.parse(source)
    content = Markdoc.transform(ast, {"variables": {"name": "Ada"}})
    html = Markdoc.renderers.html(content)
    assert html == "<p>Hello Ada</p>"


def test_function_interpolation():
    source = "Total {% sum(1, 2) %}"

    def sum_fn(a, b):
        return a + b

    ast = Markdoc.parse(source)
    content = Markdoc.transform(ast, {"functions": {"sum": sum_fn}})
    html = Markdoc.renderers.html(content)
    assert html == "<p>Total 3</p>"


def test_markdown_table():
    source = "| a | b |\n| - | - |\n| c | d |"
    ast = Markdoc.parse(source)
    content = Markdoc.transform(ast)
    html = Markdoc.renderers.html(content)
    assert "<table>" in html
    assert "<th>" in html
    assert "<td>" in html


def test_if_else_tag():
    source = "{% if $flag %}Yes{% else %}No{% /if %}"
    ast = Markdoc.parse(source)
    content = Markdoc.transform(ast, {"variables": {"flag": True}})
    html = Markdoc.renderers.html(content)
    assert html == "<p>Yes</p>"
