import markdocpy as Markdoc


def test_class_dict_transforms_to_string():
    source = "# Title {% .hero %}"
    ast = Markdoc.parse(source)
    html = Markdoc.renderers.html(Markdoc.transform(ast))
    assert html == '<h1 class="hero">Title</h1>'


def test_id_validation_reports_error():
    source = "# Title {% #1bad %}"
    ast = Markdoc.parse(source)
    errors = Markdoc.validate(ast)
    assert any(err["id"] == "attribute-value-invalid" for err in errors)


def test_child_validation_warns():
    source = "{% note %}Text{% /note %}"
    ast = Markdoc.parse(source)
    config = {"tags": {"note": {"render": "note", "children": ["heading"]}}}
    errors = Markdoc.validate(ast, config)
    assert any(err["id"] == "child-invalid" for err in errors)
