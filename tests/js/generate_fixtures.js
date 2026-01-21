const fs = require("fs");
const path = require("path");

const root = path.resolve(__dirname, "..", "..");
const fixturesDir = path.join(root, "tests", "fixtures");
const outputDir = path.join(fixturesDir, "js");
const manifest = JSON.parse(
  fs.readFileSync(path.join(fixturesDir, "manifest.json"), "utf8")
);

const markdocPath =
  process.env.MARKDOC_JS_PATH || path.resolve(root, "..", "markdoc");
const markdocDist = path.join(markdocPath, "dist", "index.js");
if (!fs.existsSync(markdocDist)) {
  console.error(
    `Markdoc dist not found at ${markdocDist}. Run 'npm install && npm run build' in ${markdocPath}.`
  );
  process.exit(1);
}

const Markdoc = require(markdocDist);

function fixtureConfigs() {
  return {
    interpolation: {
      variables: { name: "Ada" },
      functions: {
        sum: {
          transform: (parameters) => {
            const values = Object.values(parameters || {});
            const numbers = values.filter((value) => typeof value === "number");
            return numbers.reduce((total, value) => total + value, 0);
          },
        },
      },
    },
    custom_tag: {
      tags: { note: { render: "note", attributes: { title: {} } } },
    },
  };
}

function serializeValue(value) {
  if (!value || typeof value !== "object") return value;
  if (value.$$mdtype === "Variable") {
    return { $type: "Variable", name: value.name };
  }
  if (value.$$mdtype === "Function") {
    return {
      $type: "Function",
      name: value.name,
      parameters: value.parameters || {},
    };
  }
  if (Array.isArray(value)) return value.map(serializeValue);
  const output = {};
  for (const [key, val] of Object.entries(value)) {
    output[key] = serializeValue(val);
  }
  return output;
}

function serializeNode(node) {
  return {
    type: node.type,
    tag: node.tag,
    content: node.content,
    attributes: serializeValue(node.attributes),
    children: (node.children || []).map(serializeNode),
  };
}

fs.mkdirSync(outputDir, { recursive: true });
const configs = fixtureConfigs();

for (const entry of manifest) {
  const name = entry.name;
  const config = configs[entry.config] || {};
  const source = fs.readFileSync(path.join(fixturesDir, `${name}.md`), "utf8");

  const ast = Markdoc.parse(source);
  fs.writeFileSync(
    path.join(outputDir, `${name}.ast.json`),
    JSON.stringify(serializeNode(ast), null, 2) + "\n"
  );

  const content = Markdoc.transform(ast, config);
  const html = Markdoc.renderers.html(content).trim();
  fs.writeFileSync(path.join(outputDir, `${name}.html`), `${html}\n`);
}
