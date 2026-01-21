# markdoc-py: Python port of Markdoc (spec)

## Goals
- Provide a Python library with a user-facing API equivalent to the JS Markdoc core.
- Support Markdoc syntax: tags, annotations, variables, functions, and validation.
- Provide HTML renderer and an extensible renderer interface.
- Keep dependencies minimal and widely adopted.

## Non-goals (initial release)
- Full parity with React renderer or Next.js integrations.
- CLI or docs site scaffolding.
- Custom Markdown parser plugins beyond required tag/annotation support.

## Proposed dependencies
- markdown-it-py: CommonMark-compatible Markdown parser with token stream access.
  - Enable markdown-it-py table rule by default to match Markdoc table support.

## Package layout
- markdocpy/__init__.py
- markdocpy/ast/
  - node.py
  - tag.py
  - function.py
  - variable.py
- markdocpy/parser/
  - tokenizer.py
  - parser.py
- markdocpy/schema/
  - nodes.py
  - tags.py
  - types.py
- markdocpy/renderer/
  - html.py
  - base.py
- markdocpy/transform/
  - transformer.py
  - transforms.py
- markdocpy/validator/
  - validator.py
- markdocpy/utils.py

## User-facing API (module-level)
These mirror the JS surface, with Python naming conventions.

```python
import markdocpy as Markdoc

ast = Markdoc.parse(source, *, file=None, slots=False, location=False)
resolved = Markdoc.resolve(ast, config)
content = Markdoc.transform(ast, config)
errors = Markdoc.validate(ast, config)
html = Markdoc.renderers.html(content)
```

### Module exports
- parse(source: str | list[Token], **parser_args) -> Node
- resolve(node_or_nodes: Node | list[Node], config: Config) -> Node | list[Node]
- transform(node_or_nodes: Node | list[Node], config: Config | None = None) -> Renderable
- validate(node_or_nodes: Node | list[Node], config: Config | None = None) -> list[ValidateError]
- create_element(name: str | dict, attributes: dict = None, *children) -> Tag
- renderers: object with html renderer function
- nodes, tags, functions: default schema dictionaries
- global_attributes, transforms
- classes: Ast, Node, Tag, Tokenizer

### Class-based API
```python
markdoc = Markdoc.Markdoc(config)
markdoc.parse(source)
markdoc.transform(ast)
markdoc.validate(ast)
```

## Config model
Mirror JS Config structure and semantics.

```python
class Config(TypedDict, total=False):
    nodes: dict[str, Schema]
    tags: dict[str, Schema]
    variables: dict[str, Any]
    functions: dict[str, ConfigFunction]
    partials: dict[str, Any]
    validation: dict[str, Any]
```

Schema:
- render: str | None
- children: list[str] | None
- attributes: dict[str, SchemaAttribute]
- slots: dict[str, SchemaSlot]
- self_closing: bool
- inline: bool
- transform(node, config) -> Renderable
- validate(node, config) -> list[ValidationError]

## Renderable tree
- Tag(name, attributes, children)
- Scalars: None, bool, int, float, str, list, dict

## Parsing and AST
- Tokenizer wraps markdown-it-py and captures tokens + Markdoc tags.
- Parser builds AST nodes similar to JS (document, paragraph, heading, list, table, tag, text, etc).
- Tag parsing follows Markdoc syntax spec (docs/spec/index.md).

## Transform pipeline
- resolve() applies variables/functions and normalizes tree.
- transform() walks AST nodes, finds schema, returns renderable tree.
- HTML renderer converts renderable tree to HTML string (void elements respected).

## Validation
- validate() returns list of ValidateError with id, level, message, and location.
- SchemaAttribute supports type checking and custom validators.
- Leverage line/column from tokenizer tokens when location=True.

## Compatibility notes
- API mirrors JS with snake_case in Python, but keep names as close as practical.
- Markdoc.Markdoc class as convenience wrapper, matching JS default export.

## Milestones
### 0.5 (bootstrap)
- Parse a simple valid Markdoc document.
- Produce a minimal AST and transformed renderable tree that matches expected output.
- HTML renderer supports basic elements (paragraph, heading, text, inline tags).

### 1.0 (core parity)
- Full tag/annotation parsing per spec.
- Default schema, transforms, and validator parity with JS core.
- Tables enabled by default.

## Implementation plan
1) Build a minimal end-to-end slice: parse a simple valid Markdoc document and verify the AST/transform output matches expected results.
2) Build tokenizer using markdown-it-py, including Markdoc tag scanning.
3) Port AST node classes and tag/variable/function resolution logic.
4) Implement parser to convert token stream into AST with Markdoc tags/annotations.
5) Implement transformer and default schema (nodes/tags/functions).
6) Implement HTML renderer and create_element helper.
7) Implement validator with schema attribute checks.
8) Add tests for parsing, tags, transform, and HTML output using JS fixtures.

## Open questions
- How close should the Python renderer behavior match JS for edge-case escaping?
- Should we ship a markdown-it-py plugin for Markdoc tags or keep it internal?
