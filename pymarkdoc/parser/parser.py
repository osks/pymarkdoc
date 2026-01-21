from __future__ import annotations

from typing import Dict, List, Tuple

from markdown_it.token import Token

from ..ast.node import Node
from ..utils import find_tag_end
from ..ast.function import Function
from ..ast.variable import Variable
from .tag_parser import TagInfo, parse_tag_content


def parse(tokens: List[Token]) -> Node:
    """Parse markdown-it-py tokens into a Markdoc AST."""
    root = Node("document", children=[])
    stack: List[Node] = [root]
    tag_stack: List[Node] = []

    i = 0
    while i < len(tokens):
        token = tokens[i]

        if token.type == "inline":
            inline_nodes = _parse_inline_tokens(token.children or [])
            if stack[-1].type in ("paragraph", "heading"):
                inline_nodes = _apply_annotations(stack[-1], inline_nodes)
            stack[-1].children.extend(inline_nodes)
            i += 1
            continue

        if token.type == "paragraph_open":
            inline_token = tokens[i + 1] if i + 1 < len(tokens) else None
            inline_text = inline_token.content if inline_token else ""
            if _is_single_tag_line(inline_text):
                tag_info = _parse_block_tag(inline_text)
                _apply_block_tag(tag_info, inline_text, stack, tag_stack)
                i += 3
                continue

        if token.nesting == 1:
            node = _node_from_open_token(token)
            stack[-1].children.append(node)
            stack.append(node)
            i += 1
            continue

        if token.nesting == -1:
            if len(stack) > 1:
                stack.pop()
            i += 1
            continue

        node = _node_from_single_token(token)
        if node is not None:
            stack[-1].children.append(node)
        i += 1

    return root


def _apply_block_tag(
    tag_info: TagInfo, text: str, stack: List[Node], tag_stack: List[Node]
) -> None:
    if tag_info.kind == "open":
        node = Node("tag", tag=tag_info.name, attributes=tag_info.attributes or {}, children=[])
        stack[-1].children.append(node)
        stack.append(node)
        tag_stack.append(node)
        return
    if tag_info.kind == "self":
        node = Node("tag", tag=tag_info.name, attributes=tag_info.attributes or {}, children=[])
        stack[-1].children.append(node)
        return
    if tag_info.kind == "close":
        if tag_stack and tag_stack[-1].tag == tag_info.name:
            tag_stack.pop()
            if stack and stack[-1].type == "tag" and stack[-1].tag == tag_info.name:
                stack.pop()
        return

    inline_nodes = _parse_inline_text(text)
    node = Node("paragraph")
    node.children = _apply_annotations(node, inline_nodes)
    stack[-1].children.append(node)


def _node_from_open_token(token: Token) -> Node:
    if token.type == "heading_open":
        level = int(token.tag[1:]) if token.tag.startswith("h") else 1
        return Node("heading", attributes={"level": level})
    if token.type == "paragraph_open":
        return Node("paragraph")
    if token.type == "blockquote_open":
        return Node("blockquote")
    if token.type == "bullet_list_open":
        return Node("list", attributes={"ordered": False})
    if token.type == "ordered_list_open":
        return Node("list", attributes={"ordered": True})
    if token.type == "list_item_open":
        return Node("item")
    if token.type == "table_open":
        return Node("table")
    if token.type == "thead_open":
        return Node("thead")
    if token.type == "tbody_open":
        return Node("tbody")
    if token.type == "tr_open":
        return Node("tr")
    if token.type == "th_open":
        return Node("th")
    if token.type == "td_open":
        return Node("td")
    return Node(token.type)


def _node_from_single_token(token: Token) -> Node | None:
    if token.type == "fence":
        return Node("fence", content=token.content, attributes={"language": token.info.strip()})
    if token.type == "code_block":
        return Node("code", content=token.content)
    if token.type == "hr":
        return Node("hr")
    return None


def _parse_inline_tokens(tokens: List[Token]) -> List[Node]:
    """Parse inline tokens into a list of AST nodes."""
    output: List[Node] = []
    stack: List[Tuple[Node, List[Node]]] = []

    def append_node(node: Node) -> None:
        if stack:
            stack[-1][1].append(node)
        else:
            output.append(node)

    def close_inline(expected_type: str) -> None:
        if not stack:
            return
        node, children = stack.pop()
        node.children = children
        append_node(node)

    i = 0
    while i < len(tokens):
        token = tokens[i]
        if token.type == "text":
            for node in _parse_inline_text(token.content):
                append_node(node)
        elif token.type == "softbreak":
            append_node(Node("softbreak", content="\n"))
        elif token.type == "hardbreak":
            append_node(Node("hardbreak", content="\n"))
        elif token.type == "code_inline":
            append_node(Node("text", content=token.content))
        elif token.type == "em_open":
            stack.append((Node("em"), []))
        elif token.type == "em_close":
            close_inline("em")
        elif token.type == "strong_open":
            stack.append((Node("strong"), []))
        elif token.type == "strong_close":
            close_inline("strong")
        elif token.type == "link_open":
            attrs = _attrs_to_dict(token.attrs)
            stack.append((Node("link", attributes=attrs), []))
        elif token.type == "link_close":
            close_inline("link")
        elif token.type == "image":
            attrs = _attrs_to_dict(token.attrs)
            attrs["alt"] = token.content
            append_node(Node("image", attributes=attrs))
        i += 1

    while stack:
        node, children = stack.pop()
        node.children = children
        output.append(node)

    return output


def _apply_annotations(node: Node, children: List[Node]) -> List[Node]:
    """Apply annotation attributes to a block-level node."""
    attrs = dict(node.attributes or {})
    class_list: List[str] = []
    output: List[Node] = []
    found_annotation = False
    for child in children:
        if child.type != "annotation":
            output.append(child)
            continue
        found_annotation = True
        for key, value in (child.attributes or {}).items():
            if key == "class":
                if isinstance(value, str):
                    class_list.extend(value.split())
            elif key == "id":
                attrs["id"] = value
            else:
                attrs[key] = value
    if class_list:
        existing = attrs.get("class")
        combined = []
        if isinstance(existing, str) and existing:
            combined.append(existing)
        combined.append(" ".join(class_list))
        attrs["class"] = " ".join([c for c in combined if c])
    node.attributes = attrs
    if found_annotation and output:
        last = output[-1]
        if last.type == "text" and isinstance(last.content, str):
            last.content = last.content.rstrip()
    return output


def _attrs_to_dict(attrs) -> Dict[str, str]:
    if not attrs:
        return {}
    if isinstance(attrs, dict):
        return dict(attrs)
    return {key: value for key, value in attrs}


def _parse_inline_text(text: str) -> List[Node]:
    """Parse inline Markdoc tag syntax in a text run."""
    result: List[Node] = []
    stack: List[Tuple[str, Dict[str, object], List[Node]]] = []
    pos = 0

    def add_text(value: str) -> None:
        if not value:
            return
        node = Node("text", content=value)
        if stack:
            stack[-1][2].append(node)
        else:
            result.append(node)

    def add_node(node: Node) -> None:
        if stack:
            stack[-1][2].append(node)
        else:
            result.append(node)

    while pos < len(text):
        start = text.find("{%", pos)
        if start == -1:
            add_text(text[pos:])
            break
        if start > pos:
            add_text(text[pos:start])
        end = find_tag_end(text, start)
        if end is None:
            add_text(text[start:])
            break
        inner = text[start + 2 : end]
        tag = parse_tag_content(inner)
        if tag.kind == "self":
            add_node(Node("tag", tag=tag.name, attributes=tag.attributes or {}))
        elif tag.kind == "open":
            stack.append((tag.name or "", tag.attributes or {}, []))
        elif tag.kind == "close":
            if stack and stack[-1][0] == tag.name:
                name, attributes, children = stack.pop()
                add_node(Node("tag", tag=name, attributes=attributes, children=children))
            else:
                add_text(text[start : end + 2])
        elif tag.kind == "annotation":
            add_node(Node("annotation", attributes=tag.attributes or {}))
        elif tag.kind == "interpolation":
            if isinstance(tag.value, Variable):
                add_node(Node("variable", attributes={"value": tag.value}))
            elif isinstance(tag.value, Function):
                add_node(Node("function", attributes={"value": tag.value}))
        else:
            add_text(text[start : end + 2])
        pos = end + 2

    while stack:
        name, attributes, children = stack.pop(0)
        add_node(Node("tag", tag=name, attributes=attributes, children=children))

    return result


def _is_single_tag_line(text: str) -> bool:
    stripped = text.strip()
    if not stripped.startswith("{%"): 
        return False
    if not stripped.endswith("%}"):
        return False
    inner = stripped[2:-2]
    tag_end = find_tag_end(stripped, 0)
    return tag_end is not None and tag_end + 2 == len(stripped)


def _parse_block_tag(text: str) -> TagInfo:
    stripped = text.strip()
    inner = stripped[2:-2]
    return parse_tag_content(inner)
