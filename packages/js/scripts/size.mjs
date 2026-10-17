// Measures what a user's bundle grows by for typical imports (minified + gzipped), using esbuild
// (installed with tsup). Run after `npm run build`: npm run size
import { build } from "esbuild";
import { gzipSync } from "node:zlib";

const cases = {
  "phone validation (parsePhone, normalizePhone)": `import { normalizePhone, parsePhone } from "naija-data"; console.log(normalizePhone, parsePhone);`,
  "plate validation (parsePlate)": `import { parsePlate } from "naija-data"; console.log(parsePlate);`,
  "states only (getState, states)": `import { getState, states } from "naija-data"; console.log(getState, states);`,
  "states + LGAs + search": `import { getState, lgas, search } from "naija-data"; console.log(getState, lgas, search);`,
  "banks + NUBAN": `import { getBank, isValidNuban, banksForNuban } from "naija-data"; console.log(getBank, isValidNuban, banksForNuban);`,
  "everything in naija-data": `import * as ng from "naija-data"; console.log(ng);`,
  "naija-data/wards": `import { wards } from "naija-data/wards"; console.log(wards);`,
  "naija-data/constituencies": `import { federalConstituencies, lgaConstituencies } from "naija-data/constituencies"; console.log(federalConstituencies, lgaConstituencies);`,
  "naija-data/zod (without zod itself)": `import { phoneSchema } from "naija-data/zod"; console.log(phoneSchema);`,
};

const rows = [];
for (const [label, code] of Object.entries(cases)) {
  const out = await build({
    stdin: { contents: code, resolveDir: process.cwd(), loader: "js" },
    bundle: true, minify: true, format: "esm", write: false, platform: "browser", external: ["zod"],
  });
  const bytes = out.outputFiles[0].contents;
  rows.push([label, (bytes.length / 1024).toFixed(1), (gzipSync(bytes).length / 1024).toFixed(1)]);
}
console.log("| Import | Minified | Gzipped |\n|---|---|---|");
for (const [label, min, gz] of rows) console.log(`| ${label} | ${min} KB | ${gz} KB |`);
