// OpenAPI 3.1 description of the API, served at /v1/openapi.json and rendered at /v1/docs.

const str = { type: "string" } as const;
const nstr = { type: ["string", "null"] } as const;
const strs = { type: "array", items: str } as const;
const num = { type: ["number", "null"] } as const;

const ref = (name: string) => ({ $ref: `#/components/schemas/${name}` });
const one = (name: string) => ({ type: "object", properties: { data: ref(name) }, required: ["data"] });
const many = (name: string) => ({
  type: "object",
  properties: { count: { type: "integer" }, data: { type: "array", items: ref(name) } },
  required: ["count", "data"],
});
const ok = (schema: object, description = "OK") => ({ description, content: { "application/json": { schema } } });
const errors = (...codes: number[]) =>
  Object.fromEntries(codes.map((c) => [String(c), { description: { 400: "Bad request", 404: "Not found", 409: "Ambiguous name", 422: "Invalid value", 429: "Rate limited" }[c], content: { "application/json": { schema: ref("Error") } } }]));
const path = (name: string, description: string, example: string) =>
  ({ name, in: "path", required: true, description, schema: str, example });
const query = (name: string, description: string, example?: string, required = false) =>
  ({ name, in: "query", required, description, schema: str, ...(example ? { example } : {}) });

export function openapi(origin: string, dataVersion: string) {
  return {
    openapi: "3.1.0",
    info: {
      title: "naija-data API",
      version: "1",
      description:
        "Free, read-only API for accurate, sourced Nigerian reference data: states, LGAs, wards (INEC registration areas), " +
        "senatorial districts and federal and state constituencies (INEC), CBN-licensed banks with NUBAN validation, phone numbers (NCC) and vehicle plates. Every record lists its sources. " +
        `Data version ${dataVersion}. Please keep to about 120 requests per minute per IP (enforced on a best-effort basis). Responses may be cached for an hour; for heavy use, ` +
        "install the Python, JavaScript or Go package instead.",
      license: { name: "Data: CC BY 4.0 (Akanji Oluwaseun Gabriel). Code: MIT.", url: "https://github.com/asgatcreation/naija-data/blob/main/ATTRIBUTION.md" },
      contact: { name: "Akanji Oluwaseun Gabriel", url: "https://github.com/asgatcreation/naija-data" },
    },
    servers: [{ url: origin }],
    paths: {
      "/v1/states": { get: { summary: "All 36 states and the FCT", tags: ["Places"], responses: { 200: ok(many("State")) } } },
      "/v1/states/{state}": {
        get: { summary: "One state", tags: ["Places"], parameters: [path("state", "ISO code, INEC code, P-code, slug, name or alias", "LA")],
          responses: { 200: ok(one("State")), ...errors(404) } },
      },
      "/v1/states/{state}/lgas": {
        get: { summary: "LGAs of a state", tags: ["Places"], parameters: [path("state", "Any state identifier", "FCT")],
          responses: { 200: ok(many("LGA")), ...errors(404) } },
      },
      "/v1/lgas": {
        get: { summary: "All 774 LGAs, or those of one state", tags: ["Places"], parameters: [query("state", "Any state identifier", "Kano")],
          responses: { 200: ok(many("LGA")), ...errors(404) } },
      },
      "/v1/lgas/{lga}": {
        get: { summary: "One LGA", tags: ["Places"],
          parameters: [path("lga", "P-code (NG025011), INEC code (24-11) or name", "NG025011"), query("state", "Needed when a name exists in several states", "Lagos")],
          responses: { 200: ok(one("LGA")), ...errors(404, 409) } },
      },
      "/v1/lgas/{lga}/wards": {
        get: { summary: "Wards (INEC registration areas) of an LGA", tags: ["Places"],
          parameters: [path("lga", "P-code, INEC code or name", "NG025011"), query("state", "Needed when a name exists in several states")],
          responses: { 200: ok(many("Ward")), ...errors(404, 409) } },
      },
      "/v1/lgas/{lga}/constituencies": {
        get: { summary: "The senatorial district and federal and state constituencies an LGA lies in", tags: ["Elections"],
          description: "More than one federal or state constituency when the LGA is split (e.g. Surulere, Lagos).",
          parameters: [path("lga", "P-code, INEC code or name", "NG025020"), query("state", "Needed when a name exists in several states", "Lagos")],
          responses: { 200: ok(many("Constituency")), ...errors(404, 409) } },
      },
      "/v1/constituencies": {
        get: { summary: "Senatorial districts, federal constituencies and state constituencies (INEC)", tags: ["Elections"],
          parameters: [query("kind", "senatorial_district, federal_constituency or state_constituency", "federal_constituency"),
            query("state", "Any state identifier", "Lagos"), query("q", "Exact name or alias (ignoring case and punctuation)", "Ikeja")],
          responses: { 200: ok(many("Constituency")), ...errors(400, 404) } },
      },
      "/v1/senatorial-districts": {
        get: { summary: "The 109 senatorial districts (Senate)", tags: ["Elections"], parameters: [query("state", "Any state identifier", "Lagos")],
          responses: { 200: ok(many("Constituency")), ...errors(404) } },
      },
      "/v1/federal-constituencies": {
        get: { summary: "The 360 federal constituencies (House of Representatives)", tags: ["Elections"], parameters: [query("state", "Any state identifier", "Lagos")],
          responses: { 200: ok(many("Constituency")), ...errors(404) } },
      },
      "/v1/state-constituencies": {
        get: { summary: "The 990 state constituencies (State Houses of Assembly; none in the FCT)", tags: ["Elections"],
          parameters: [query("state", "Any state identifier", "Lagos")], responses: { 200: ok(many("Constituency")), ...errors(404) } },
      },
      "/v1/constituencies/{code}": {
        get: { summary: "One senatorial district or constituency", tags: ["Elections"],
          parameters: [path("code", "Code (SD001, FC001, SC001) or INEC code (FC/001/AB)", "FC236")],
          responses: { 200: ok(one("Constituency")), ...errors(404) } },
      },
      "/v1/constituencies/{code}/lgas": {
        get: { summary: "LGAs a unit covers in full or in part", tags: ["Elections"], parameters: [path("code", "Code", "FC236")],
          responses: { 200: ok(many("LGA")), ...errors(404) } },
      },
      "/v1/constituencies/{code}/wards": {
        get: { summary: "Wards that make up a unit", tags: ["Elections"], parameters: [path("code", "Code", "SC001")],
          responses: { 200: ok(many("Ward")), ...errors(404) } },
      },
      "/v1/wards/{ward}": {
        get: { summary: "One ward by INEC code", tags: ["Places"], parameters: [path("ward", "INEC code", "24-11-01")],
          responses: { 200: ok(one("Ward")), ...errors(404) } },
      },
      "/v1/search": {
        get: { summary: "Fuzzy search (typos, aliases, accents)", tags: ["Places"],
          parameters: [query("q", "Search text", "lagso", true), query("kinds", "Comma-separated: state, lga, ward", "state,lga"), query("limit", "1-50, default 10")],
          responses: { 200: ok(many("SearchResult")), ...errors(400) } },
      },
      "/v1/banks": {
        get: { summary: "CBN-licensed institutions", tags: ["Banks"],
          parameters: [query("type", "commercial, merchant, non_interest, payment_service_bank, mobile_money_operator, microfinance, mortgage, development_finance"),
            query("active", "true (default) or false to include merged/revoked"), query("q", "Fuzzy name search", "guaranty"), query("limit", "With q: 1-50")],
          responses: { 200: ok(many("Bank")), ...errors(400) } },
      },
      "/v1/banks/{bank}": {
        get: { summary: "One institution", tags: ["Banks"], parameters: [path("bank", "Id, CBN code, NIP code, name or alias", "058")],
          responses: { 200: ok(one("Bank")), ...errors(404) } },
      },
      "/v1/validate/nuban": {
        get: { summary: "Check a NUBAN account number (CBN check digit)", tags: ["Banks"],
          description: "With `bank`, returns whether the account number is valid for that bank. Without it, lists the banks it could belong to. A valid check digit does not prove the account exists.",
          parameters: [query("account", "10-digit account number", "0000014579", true), query("bank", "Bank id, CBN code or name", "011")],
          responses: { 200: ok({ type: "object" }), ...errors(404, 422) } },
      },
      "/v1/phone/{number}": {
        get: { summary: "Validate and describe a Nigerian phone number", tags: ["Phone"],
          parameters: [path("number", "Any common format", "08031234567")],
          responses: { 200: ok(one("PhoneNumber")), ...errors(422) } },
      },
      "/v1/area-codes": { get: { summary: "The NCC's 56 landline area codes", tags: ["Phone"], responses: { 200: ok({ type: "object" }) } } },
      "/v1/plates": { get: { summary: "Plate colours by category (Road Traffic Regulations 2012)", tags: ["Plates"], responses: { 200: ok({ type: "object" }) } } },
      "/v1/plates/{plate}": {
        get: { summary: "Validate and parse a plate number", tags: ["Plates"], parameters: [path("plate", "Plate number", "KJA-123AB")],
          responses: { 200: ok(one("Plate")), ...errors(422) } },
      },
      "/v1/meta": { get: { summary: "Dataset version, counts and sources", tags: ["About"], responses: { 200: ok({ type: "object" }) } } },
      "/v1/health": { get: { summary: "Health check", tags: ["About"], responses: { 200: ok({ type: "object" }) } } },
    },
    components: {
      schemas: {
        Error: {
          type: "object",
          properties: { error: { type: "object", properties: { code: str, message: str }, required: ["code", "message"] } },
        },
        State: {
          type: "object",
          properties: { code: str, iso_code: str, name: str, slug: str, inec_code: str, pcode: str, capital: str, zone: str,
            created: nstr, lat: num, lon: num, aliases: strs, unverified_fields: strs, sources: strs },
        },
        LGA: {
          type: "object",
          properties: { code: str, state_code: str, inec_code: str, name: str, slug: str, headquarters: nstr, senatorial_district: nstr,
            lat: num, lon: num, aliases: strs, unverified_fields: strs, sources: strs },
        },
        Ward: {
          type: "object",
          properties: { code: str, lga_code: str, state_code: str, name: str, slug: str, senatorial_district: str,
            federal_constituency: str, state_constituency: nstr, aliases: strs, unverified_fields: strs },
        },
        Constituency: {
          type: "object",
          properties: { kind: { enum: ["senatorial_district", "federal_constituency", "state_constituency"] }, code: str, state_code: str,
            inec_code: str, name: str, slug: str, aliases: strs, lga_codes: strs, sources: strs },
        },
        SearchResult: { type: "object", properties: { kind: str, code: str, name: str, state_code: str, score: { type: "integer" }, matched: str } },
        Bank: {
          type: "object",
          properties: { id: str, name: str, short_name: nstr, type: str, cbn_code: nstr, nip_code: nstr, ussd: nstr, status: str,
            status_date: nstr, merged_into: nstr, aliases: strs, unverified_fields: strs, sources: strs },
        },
        PhoneNumber: {
          type: "object",
          properties: { e164: str, local: str, national: str, type: str, prefix: str, area: nstr, network: nstr,
            allocated: { type: "boolean" }, note: nstr },
        },
        Plate: {
          type: "object",
          properties: { compact: str, display: str, format: str, prefix: str, number: str, suffix: str, state_code: nstr, note: nstr },
        },
      },
    },
  };
}
