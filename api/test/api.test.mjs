// Calls the bundled Worker with real Request objects (built by `npm test`).
import assert from "node:assert/strict";
import { test } from "node:test";
import { handle } from "../.test/worker.mjs";

const call = async (path, init = {}, env = {}) => {
  const res = await handle(new Request(`https://api.example.test${path}`, init), env);
  const text = await res.text();
  return { res, body: text && res.headers.get("content-type")?.includes("json") ? JSON.parse(text) : text };
};

test("index and health", async () => {
  const { body } = await call("/v1");
  assert.equal(body.version, "v1");
  const health = await call("/v1/health");
  assert.equal(health.body.status, "ok");
  assert.equal(health.body.counts.lgas, 774);
  assert.equal(health.res.headers.get("cache-control"), "no-store");
  const root = await call("/");
  assert.equal(root.res.status, 302);
});

test("states and LGAs", async () => {
  assert.equal((await call("/v1/states")).body.count, 37);
  assert.equal((await call("/v1/states/Abuja")).body.data.code, "FC");
  assert.equal((await call("/v1/states/lagos/lgas")).body.count, 20);
  assert.equal((await call("/v1/lgas")).body.count, 774);
  assert.equal((await call("/v1/lgas?state=Kano")).body.count, 44);
  assert.equal((await call("/v1/lgas/NG025011")).body.data.name, "Ikeja");
  assert.equal((await call("/v1/lgas/24-11/wards")).body.count, 10);
  assert.equal((await call("/v1/wards/24-11-01")).body.data.name, "Anifowoshe/Ikeja");
});

test("ambiguous LGA names give 409 with candidates, or resolve with ?state=", async () => {
  const { res, body } = await call("/v1/lgas/Surulere");
  assert.equal(res.status, 409);
  assert.deepEqual(body.error.candidates.map((c) => c.state_code).sort(), ["LA", "OY"]);
  assert.equal((await call("/v1/lgas/Surulere?state=Oyo")).body.data.state_code, "OY");
});

test("search", async () => {
  assert.equal((await call("/v1/search?q=lagso")).body.data[0].name, "Lagos");
  const mixed = (await call("/v1/search?q=ikeja&kinds=lga,ward&limit=3")).body.data;
  assert.equal(mixed[0].kind, "lga");
  assert.equal((await call("/v1/search?q=")).res.status, 400);
  assert.equal((await call("/v1/search?q=x&kinds=city")).res.status, 400);
  assert.equal((await call("/v1/search?q=x&limit=500")).res.status, 400);
});

test("banks and NUBAN", async () => {
  assert.equal((await call("/v1/banks/058")).body.data.id, "gtbank");
  assert.equal((await call("/v1/banks?type=commercial")).body.count, 28);
  assert.equal((await call("/v1/banks?type=shop")).res.status, 400);
  assert.equal((await call("/v1/banks?q=guaranty")).body.data[0].id, "gtbank");
  const valid = (await call("/v1/validate/nuban?account=0000014579&bank=First%20Bank")).body.data;
  assert.equal(valid.valid, true);
  const candidates = (await call("/v1/validate/nuban?account=0000014579")).body.data.candidates;
  assert.ok(candidates.some((b) => b.id === "first-bank"));
  assert.equal((await call("/v1/validate/nuban?account=123")).res.status, 422);
});

test("phone and plates", async () => {
  const mobile = (await call("/v1/phone/0803%20123%204567")).body.data;
  assert.equal(mobile.e164, "+2348031234567");
  assert.equal(mobile.network, "MTN");
  assert.equal((await call("/v1/phone/012691531")).body.data.area, "Lagos");
  const bad = await call("/v1/phone/09001234567");
  assert.equal(bad.res.status, 422);
  assert.equal(bad.body.error.code, "reserved");
  assert.equal((await call("/v1/plates/kja-123ab")).body.data.display, "KJA-123AB");
  assert.equal((await call("/v1/plates")).body.count, 13);
  assert.equal((await call("/v1/area-codes")).body.count, 56);
});

test("CORS, caching, ETag, read-only, 404", async () => {
  const { res } = await call("/v1/states");
  assert.equal(res.headers.get("access-control-allow-origin"), "*");
  assert.match(res.headers.get("cache-control"), /s-maxage=86400/);
  const etag = res.headers.get("etag");
  assert.equal((await call("/v1/states", { headers: { "if-none-match": etag } })).res.status, 304);
  assert.equal((await call("/v1/states", { method: "OPTIONS" })).res.status, 204);
  assert.equal((await call("/v1/states", { method: "POST" })).res.status, 405);
  assert.equal((await call("/v1/nothing")).res.status, 404);
  assert.equal((await call("/v2/states")).res.status, 404);
});

test("rate limiting", async () => {
  const limiter = { limit: async () => ({ success: false }) };
  const { res, body } = await call("/v1/states", {}, { RATE_LIMITER: limiter });
  assert.equal(res.status, 429);
  assert.equal(body.error.code, "rate_limited");
  assert.equal((await call("/v1/health", {}, { RATE_LIMITER: limiter })).res.status, 200); // health is never limited
});

test("OpenAPI spec and docs page", async () => {
  const spec = (await call("/v1/openapi.json")).body;
  assert.equal(spec.openapi, "3.1.0");
  assert.ok(spec.paths["/v1/validate/nuban"]);
  const docs = await call("/v1/docs");
  assert.match(docs.body, /swagger-ui/);
});

test("constituencies", async () => {
  assert.equal((await call("/v1/senatorial-districts")).body.count, 109);
  assert.equal((await call("/v1/federal-constituencies")).body.count, 360);
  assert.equal((await call("/v1/state-constituencies")).body.count, 990);
  assert.equal((await call("/v1/state-constituencies?state=fct")).body.count, 0);
  assert.equal((await call("/v1/constituencies?kind=federal_constituency&state=Lagos")).body.count, 24);
  assert.equal((await call("/v1/constituencies?kind=ward")).res.status, 400);
  assert.equal((await call("/v1/constituencies?q=Ikeja")).body.data[0].code, "FC236");
  const fc = (await call("/v1/constituencies/FC/001/AB")).body.data;
  assert.equal(fc.name, "Aba North/Aba South");
  assert.equal((await call("/v1/constituencies/FC%2F001%2FAB")).body.data.code, "FC001");
  assert.equal((await call("/v1/constituencies/fc001/lgas")).body.count, 2);
  assert.equal((await call("/v1/constituencies/SC001/wards")).body.count, 9);
  assert.equal((await call("/v1/constituencies/XX001")).res.status, 404);
  const units = (await call("/v1/lgas/Surulere/constituencies?state=Lagos")).body.data;
  assert.deepEqual(units.map((u) => u.name), ["Lagos Central", "Surulere I", "Surulere II", "Surulere I", "Surulere II"]);
  assert.equal((await call("/v1/lgas/Surulere/constituencies")).res.status, 409);
  assert.equal((await call("/v1/wards/24-11-01")).body.data.federal_constituency.slice(0, 2), "FC");
});
