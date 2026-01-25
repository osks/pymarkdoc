# markdoc-py

Python port of [Markdoc](https://markdoc.dev), a Markdown-based authoring framework with custom tags and annotations.

Documentation: https://osks.github.io/markdoc-py/markdocpy.html

## Status

This project is under active development. Core parsing, transforming, and HTML rendering are implemented, with fixture-based tests and JS parity fixtures.

## JS parity notes

The Python port intentionally tracks JS Markdoc behavior, but some differences can exist while parity work is in progress. To see what is currently covered and any known gaps:

- `spec-parity.md` explains the parity scope and lists tracked gaps.
- `tests/spec/manifest.json` marks known JS mismatches with `xfail_js`.
- `tests/test_spec_parity.py` enforces parity against committed JS outputs.

## Requirements

- Python 3.13+
- Node.js (only needed for JS parity fixture generation)

## Install (dev)

```sh
make env
```

## Quick start

```python
import markdocpy as Markdoc

source = \"\"\"
# Hello

{% note title=\"A\" %}
Body
{% /note %}
\"\"\"

ast = Markdoc.parse(source)
content = Markdoc.transform(ast, {\"tags\": {\"note\": {\"render\": \"note\", \"attributes\": {\"title\": {}}}}})
html = Markdoc.renderers.html(content)
```

## API

```python
ast = Markdoc.parse(source)
content = Markdoc.transform(ast, config)
errors = Markdoc.validate(ast, config)
html = Markdoc.renderers.html(content)
```

## Tests

```sh
make test
```

## Lint / format

```sh
make lint
make lint-fix
make format
```

## Docs

```sh
make docs
```

## Fixtures

Python fixtures:

```sh
make fixtures
```

JS parity fixtures (requires Markdoc build):

```sh
cd markdoc
npm install
npm run build

cd pymarkdoc
make fixtures-js
```

## Project layout

```
markdocpy/
  ast/
  parser/
  renderer/
  schema/
  transform/
  validator/
tests/
  fixtures/
  js/
```
