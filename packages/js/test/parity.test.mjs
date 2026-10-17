// Runs the shared parity cases (fixtures/parity.json) against the built ESM package.
import assert from "node:assert/strict";
import { existsSync, readFileSync } from "node:fs";
import { test } from "node:test";
import * as ng from "../dist/index.js";
import * as wd from "../dist/wards.js";
import * as cd from "../dist/constituencies.js";

const FIXTURE = new URL("../../../fixtures/parity.json", import.meta.url);

const codes = (xs) => xs.map((x) => x.code);
const ids = (xs) => xs.map((x) => x.id);

function run(fn, args) {
  try {
    switch (fn) {
      case "states": return codes(ng.states());
      case "get_state": return ng.getState(args[0])?.code ?? null;
      case "state_record": return ng.getState(args[0]);
      case "lgas": return codes(ng.lgas(args[0]));
      case "find_lgas": return codes(ng.findLgas(args[0]));
      case "get_lga": return ng.getLga(args[0], args[1])?.code ?? null;
      case "lga_record": return ng.getLga(args[0]);
      case "wards": return codes(wd.wards(args[0], args[1]));
      case "get_ward": return wd.getWard(args[0]);
      case "search": {
        const [q, kinds, limit] = args;
        const rows = kinds.length === 1 && kinds[0] === "ward" ? wd.searchWards(q, { limit }) : ng.search(q, { limit });
        return rows.map((r) => [r.kind, r.code, r.score, r.matched]);
      }
      case "get_bank": return ng.getBank(args[0])?.id ?? null;
      case "bank_record": return ng.getBank(args[0]);
      case "banks": return ids(ng.banks(args[0], args[1]));
      case "find_banks": return ids(ng.findBanks(args[0]));
      case "nuban_check_digit": return ng.nubanCheckDigit(...args);
      case "is_valid_nuban": return ng.isValidNuban(...args);
      case "banks_for_nuban": return ids(ng.banksForNuban(args[0]));
      case "normalize_phone": return ng.normalizePhone(args[0]);
      case "to_local": return ng.toLocal(args[0]);
      case "parse_phone": return ng.parsePhone(args[0]);
      case "phone_error": return ng.phoneError(args[0]);
      case "is_valid_phone": return ng.isValidPhone(args[0], args[1]);
      case "parse_plate": return ng.parsePlate(args[0]);
      case "plate_error": return ng.plateError(args[0]);
      case "is_valid_plate": return ng.isValidPlate(args[0], args[1]);
      case "area_codes": return ng.areaCodes();
      case "plate_categories": return ng.plateCategories();
      case "search_wards": return wd.searchWards(args[0], { limit: args[1] }).map((r) => [r.kind, r.code, r.score, r.matched]);
      case "prefixes": return ng.prefixes(args[0]);
      case "constituencies": return codes(cd.constituencies(args[0], args[1]));
      case "get_constituency": return cd.getConstituency(args[0])?.code ?? null;
      case "constituency_record": return cd.getConstituency(args[0]);
      case "find_constituencies": return codes(cd.findConstituencies(args[0], args[1], args[2]));
      case "constituency_lgas": return codes(cd.constituencyLgas(args[0]));
      case "constituency_wards": return codes(wd.constituencyWards(args[0]));
      case "lga_constituencies": return codes(cd.lgaConstituencies(args[0], args[1]));
      default: throw new TypeError(`Unknown parity fn ${fn}`);
    }
  } catch (e) {
    if (e instanceof TypeError) throw e;
    return { error: true };
  }
}

test("parity fixtures", { skip: !existsSync(FIXTURE) }, () => {
  const { data_version, cases } = JSON.parse(readFileSync(FIXTURE, "utf8"));
  assert.equal(data_version, ng.meta().data_version);
  const failures = [];
  for (const c of cases) {
    const got = run(c.fn, c.args);
    try {
      assert.deepStrictEqual(got, c.expect);
    } catch {
      failures.push(`${c.fn}(${JSON.stringify(c.args)}): expected ${JSON.stringify(c.expect)}, got ${JSON.stringify(got)}`);
    }
  }
  assert.equal(failures.length, 0, `${failures.length} of ${cases.length} cases failed:\n${failures.slice(0, 15).join("\n")}`);
});
