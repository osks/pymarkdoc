from markdocpy.parser.tag_parser import parse_tag_content


def test_tag_parse_error_location():
    tag = parse_tag_content("note title=")
    assert tag.kind == "error"
    assert tag.error is not None
    assert tag.error["location"]["start"]["offset"] >= 0
    assert tag.error["message"]
