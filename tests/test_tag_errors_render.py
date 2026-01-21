import markdocpy as Markdoc


def test_error_nodes_do_not_render():
    source = "{% note title= %}"
    ast = Markdoc.parse(source)
    html = Markdoc.renderers.html(Markdoc.transform(ast))
    assert html == ""
