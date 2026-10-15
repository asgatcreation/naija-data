import assert from "node:assert/strict";
import { test } from "node:test";
import { z } from "zod";
import { nubanSchema, nubanWithBankSchema, phoneSchema, plateSchema } from "naija-data/zod";

test("phoneSchema parses to E.164 and explains failures", () => {
  assert.equal(phoneSchema().parse("0803 123 4567"), "+2348031234567");
  assert.equal(phoneSchema().parse("01 269 1531"), "+23412691531");
  const bad = phoneSchema().safeParse("0900 123 4567");
  assert.equal(bad.success, false);
  assert.match(bad.error.issues[0].message, /reserved/);
  const mobileOnly = phoneSchema({ types: ["mobile"] }).safeParse("01 269 1531");
  assert.equal(mobileOnly.success, false);
  assert.match(mobileOnly.error.issues[0].message, /not accepted/);
});

test("plateSchema", () => {
  assert.equal(plateSchema().parse("kja 123 ab"), "KJA-123AB");
  assert.equal(plateSchema({ formats: ["dealer"] }).safeParse("kja 123 ab").success, false);
  assert.equal(plateSchema().safeParse("AB-123-CD").success, false);
});

test("nubanSchema and nubanWithBankSchema (CBN example numbers)", () => {
  assert.equal(nubanSchema().parse("000 001 4579"), "0000014579");
  assert.equal(nubanSchema({ bank: "011" }).safeParse("0000014578").success, false);
  const Form = z.object({ payout: nubanWithBankSchema() });
  assert.equal(Form.safeParse({ payout: { account: "0000014579", bank: "First Bank" } }).success, true);
  const wrong = Form.safeParse({ payout: { account: "0000014578", bank: "011" } });
  assert.equal(wrong.success, false);
  assert.deepEqual(wrong.error.issues[0].path, ["payout", "account"]);
  assert.equal(Form.safeParse({ payout: { account: "0000014579", bank: "Atlantis Bank" } }).error.issues[0].path[1], "bank");
});
