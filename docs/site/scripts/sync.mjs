// Builds the "Data" and "Changelog" pages from the repository's own files, so the website never
// drifts from the data: data/sources.json, docs/data/coverage-and-gaps.md, ATTRIBUTION.md,
// CONTRIBUTING.md and CHANGELOG.md. Run automatically by `npm run dev` and `npm run build`.
import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = join(dirname(fileURLToPath(import.meta.url)), "..", "..", "..");
const OUT = join(dirname(fileURLToPath(import.meta.url)), "..", "src", "content", "docs");
const REPO = "https://github.com/asgatcreation/naija-data/blob/main/";

const read = (path) => readFileSync(join(ROOT, path), "utf8");
const write = (path, title, description, body) => {
  mkdirSync(dirname(join(OUT, path)), { recursive: true });
  const front = `---\ntitle: ${JSON.stringify(title)}\ndescription: ${JSON.stringify(description)}\n---\n\n`;
  writeFileSync(join(OUT, path), front + body.trim() + "\n");
};

/** Drop the file's own "# Title" and rewrite repository-relative links to GitHub. */
function adapt(markdown, fromDir) {
  return markdown
    .replace(/^# .*\n+/, "")
    .replace(/\]\((?!https?:|#|mailto:)([^)]+)\)/g, (_, link) => {
      const parts = [...fromDir.split("/").filter(Boolean), ...link.split("/")];
      const stack = [];
      for (const p of parts) p === ".." ? stack.pop() : p !== "." && stack.push(p);
      return `](${REPO}${stack.join("/")})`;
    });
}

const cell = (s) => String(s ?? "").replace(/\|/g, "\\|").replace(/\n/g, " ");

// ---- Sources and methodology
const sources = JSON.parse(read("data/sources.json"));
const table = [
  "| Source | Publisher | Licence | Retrieved | Notes |",
  "|---|---|---|---|---|",
  ...sources.map((s) => `| [${cell(s.name)}](${s.url}) | ${cell(s.publisher)} | ${cell(s.licence)} | ${s.retrieved} | ${cell(s.notes)} |`),
].join("\n");
write("data/sources.md", "Sources and methodology", "Where every record in naija-data comes from, and how it is checked.", `
naija-data only publishes data it can trace to a source. Every record carries a \`sources\` list with ids from
the table below, and any value that rests on a single or secondary source is listed in \`unverified_fields\`.

## How the data is built

1. **Download** the upstream files (official PDFs, the regulators' own lists and APIs) and record a SHA-256 for each.
2. **Extract** and clean them with scripts kept in the repository (\`scripts/\`), so anyone can rebuild the data.
3. **Cross-check** every source against the others: counts, codes and names. Disagreements are resolved with a
   written rule or left out, never guessed. Each one is listed on the [coverage page](/data/coverage/).
4. **Validate** in CI on every change: JSON Schemas, unique codes, parent/child links, official totals
   (37 states and FCT, 774 LGAs, 8,809 wards), overlapping number ranges, garbled text.
5. **Generate** the Python, JavaScript and Go packages and the API from the same files, and check with 6,000+
   shared test cases that all of them give identical answers.

## Sources (${sources.length})

Licence values: \`facts-only\` means the source publishes no open licence, so naija-data uses only plain facts
(names, codes, numbers) and copies no text; \`public-law\` means legislation or gazetted regulations;
\`not-redistributable\` means only the published format is described.

${table}

## Licences and credit

${adapt(read("ATTRIBUTION.md"), "")}
`);

// ---- Coverage and gaps
write("data/coverage.md", "Coverage and known gaps", "What naija-data covers, upstream errors it found, and what is still missing.",
  adapt(read("docs/data/coverage-and-gaps.md"), "docs/data"));

// ---- Contributing
write("data/contributing.md", "Contributing a correction", "How to report wrong data with a source, or contribute code.",
  adapt(read("CONTRIBUTING.md"), ""));

// ---- Changelog
write("changelog.md", "Changelog", "Changes to the code and the data.", adapt(read("CHANGELOG.md"), ""));

console.log(`sync: wrote sources (${sources.length}), coverage, contributing and changelog pages`);
