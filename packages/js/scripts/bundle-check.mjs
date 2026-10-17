// Bundles typical imports the way an app bundler would (tree-shaken, "sideEffects": false) and runs
// the result, to prove tree-shaking never drops code the functions need. Run after `npm run build`.
import { build } from "esbuild";
import assert from "node:assert/strict";

const cases = {
  phone: [`import { parsePhone } from "naija-data"; export default parsePhone("01 269 1531").area;`, "Lagos"],
  plate: [`import { parsePlate } from "naija-data"; export default parsePlate("DKN 135 3").state_code;`, "KN"],
  state: [`import { getState } from "naija-data"; export default getState("Abuja").code;`, "FC"],
  search: [`import { search } from "naija-data"; export default search("lagso")[0].name;`, "Lagos"],
  nuban: [`import { isValidNuban } from "naija-data"; export default String(isValidNuban("0000014579", "First Bank"));`, "true"],
  wards: [`import { wards } from "naija-data/wards"; export default String(wards("Ikeja", "Lagos").length);`, "10"],
  constituencies: [`import { lgaConstituencies } from "naija-data/constituencies"; export default lgaConstituencies("Ikeja", "Lagos")[1].name;`, "Ikeja"],
  constituencyWards: [`import { constituencyWards } from "naija-data/wards"; export default String(constituencyWards("SC001").length);`, "9"],
  zod: [`import { phoneSchema } from "naija-data/zod"; export default phoneSchema().parse("0803 123 4567");`, "+2348031234567"],
};

for (const [name, [code, expected]] of Object.entries(cases)) {
  const out = await build({
    stdin: { contents: code, resolveDir: process.cwd(), loader: "js" },
    bundle: true, minify: true, format: "esm", write: false, platform: "node", logLevel: "error",
  });
  const url = "data:text/javascript;base64," + Buffer.from(out.outputFiles[0].text).toString("base64");
  const { default: got } = await import(url);
  assert.equal(got, expected, `${name}: bundled code returned ${got}`);
  console.log(`ok  ${name}`);
}
