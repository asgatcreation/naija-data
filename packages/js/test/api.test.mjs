import assert from "node:assert/strict";
import { createRequire } from "node:module";
import { test } from "node:test";
import { getBank, getLga, getState, isValidNuban, lgas, normalizePhone, parsePhone, parsePlate, phoneError, search } from "naija-data";
import { wards } from "naija-data/wards";

test("ESM: states, LGAs and search", () => {
  assert.equal(getState("lagos").capital, "Ikeja");
  assert.equal(getState("Abuja").code, "FC");
  assert.deepEqual(lgas("FCT").map((l) => l.name), ["Abaji", "Abuja Municipal", "Bwari", "Gwagwalada", "Kuje", "Kwali"]);
  assert.equal(getLga("Surulere"), null);
  assert.equal(search("lagso")[0].name, "Lagos");
});

test("ESM: wards subpath", () => {
  assert.equal(wards("Ikeja", "Lagos").length, 10);
});

test("ESM: NUBAN examples from the CBN standard", () => {
  assert.equal(isValidNuban("0000014579", "011"), true);
  assert.equal(isValidNuban("0000214579", "50547"), true);
  assert.equal(isValidNuban("0000014578", "011"), false);
  assert.equal(getBank("GTB").cbn_code, "058");
});

test("ESM: phone", () => {
  assert.equal(normalizePhone("0803 123 4567"), "+2348031234567");
  assert.equal(parsePhone("08031234567").network, "MTN");
  assert.equal(parsePhone("01 269 1531").area, "Lagos");
  assert.equal(phoneError("0900 123 4567"), "reserved");
  assert.equal(parsePlate("DKN 135 3").state_code, "KN");
});

test("CommonJS require works for both entry points", () => {
  const require = createRequire(import.meta.url);
  const cjs = require("naija-data");
  const cjsWards = require("naija-data/wards");
  assert.equal(cjs.getState("kano").name, "Kano");
  assert.equal(cjsWards.wards("Ikeja", "Lagos").length, 10);
});
