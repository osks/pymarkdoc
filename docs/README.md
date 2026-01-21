# API docs (pdoc)

Generate API documentation with pdoc:

```sh
uv run pdoc -o docs/api pymarkdoc
```

The generated HTML will be in `docs/api/`.

## Fixture generation

Regenerate Python and JS fixtures (requires Node + built Markdoc dist):

```sh
uv run pymarkdoc-fixtures
```

## Fixture parity with JS Markdoc

Generate JS fixture outputs (AST + HTML) for parity tests:

```sh
cd /Volumes/Dev/priv/markdoc/markdoc
npm install
npm run build
```

Then in this repo:

```sh
MARKDOC_JS_PATH=/Volumes/Dev/priv/markdoc/markdoc node tests/js/generate_fixtures.js
```
