# Spec Parity Matrix

This matrix tracks parity with the Markdoc JS spec and core defaults. Each item should have at least one spec fixture in `tests/spec` and be verified against JS output.

## How to read parity status
- Spec fixtures: `tests/spec/*.md` are the sources that define expected behavior.
- JS snapshots: `tests/spec/js/*.html` and `tests/spec/js/*.ast.json` are generated from the JS Markdoc implementation and committed.
- Python snapshots: `tests/spec/expected/*.html` and `tests/spec/expected/*.ast.json` are generated from the Python implementation and committed.
- Known gaps: `tests/spec/manifest.json` entries with `xfail_js` are accepted JS mismatches until fixed.

## Parser + Syntax
- Tags: open/close/self-closing (block vs inline)
- Annotations: inline application, class/id merging, standalone behavior
- Interpolation: variables/functions inline; malformed tags with locations
- Values: primitives, arrays, objects, variables, functions
- Variables: path segments with dot/bracket notation
- Functions: positional + named parameters

## Transformer + Schema Defaults
- Document wrapper defaults (JS uses `<article>`)
- Core node defaults (heading/paragraph/blockquote/list/item/table/thead/tbody/tr/th/td/hr/em/strong/s/code/link/image/fence/inline)
- Attribute defaults, render aliases, required attributes
- Self-closing behavior for custom tags

## Validator
- Parents/children constraints
- Inline vs block placement validation
- Attribute type checking + matches
- Variable and function validation

## Renderer
- Attribute escaping + boolean attributes
- Void elements + custom self-closing tags
- HTML output parity with JS renderer

## Fixtures
- Each section above should have a fixture in `tests/spec`
- JS output should be generated once and committed

## Known gaps (tracked as xfail in tests/spec/manifest.json)
- `functions_params`: inline-tag-only line split into its own paragraph due to block-tag normalization
