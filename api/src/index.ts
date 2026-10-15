// naija-data public REST API (Cloudflare Worker). Read-only, JSON, CORS-enabled, versioned under /v1.
// All answers come from the naija-data package, so they match the Python, JS and Go packages.
import {
  BANK_TYPES, areaCodes, banks, banksForNuban, findBanks, getBank, getLga, findLgas, getState, isValidNuban, lgas, meta,
  parsePhone, parsePlate, phoneError, plateCategories, plateError, search, states,
  type Bank, type BankType, type SearchResult,
} from "naija-data";
import { getWard, searchWards, wards } from "naija-data/wards";
import { openapi } from "./openapi";

export interface Env {
  /** Cloudflare rate-limiting binding (see wrangler.jsonc). Absent in local tests. */
  RATE_LIMITER?: { limit(options: { key: string }): Promise<{ success: boolean }> };
  /** Set by the deploy workflow to the git commit, shown by /v1/health. */
  API_VERSION?: string;
}

const DATA_VERSION = meta().data_version;
const CACHE_CONTROL = "public, max-age=3600, s-maxage=86400, stale-while-revalidate=604800";
const SWAGGER_UI = "https://unpkg.com/swagger-ui-dist@5.17.14";

class HttpError extends Error {
  constructor(readonly status: number, readonly code: string, message: string, readonly extra: object = {}) {
    super(message);
  }
}

const notFound = (what: string, value: string) => new HttpError(404, "not_found", `No ${what} matches "${value}".`);

function json(body: unknown, status = 200, headers: Record<string, string> = {}): Response {
  return new Response(JSON.stringify(body, null, 2), {
    status,
    headers: { "content-type": "application/json; charset=utf-8", ...headers },
  });
}

function intParam(url: URL, name: string, fallback: number, min: number, max: number): number {
  const raw = url.searchParams.get(name);
  if (raw === null) return fallback;
  const n = Number(raw);
  if (!Number.isInteger(n) || n < min || n > max) {
    throw new HttpError(400, "invalid_parameter", `"${name}" must be a whole number from ${min} to ${max}.`);
  }
  return n;
}

function boolParam(url: URL, name: string, fallback: boolean): boolean {
  const raw = url.searchParams.get(name);
  if (raw === null) return fallback;
  if (raw === "true" || raw === "1") return true;
  if (raw === "false" || raw === "0") return false;
  throw new HttpError(400, "invalid_parameter", `"${name}" must be true or false.`);
}

function requireState(value: string) {
  const s = getState(value);
  if (!s) throw notFound("state", value);
  return s;
}

function requireLga(value: string, state?: string | null) {
  const lga = getLga(value, state ?? undefined);
  if (lga) return lga;
  const matches = findLgas(value);
  if (matches.length > 1 && !state) {
    throw new HttpError(409, "ambiguous", `Several LGAs are called "${value}". Add ?state= or use an LGA code.`, {
      candidates: matches.map((l) => ({ code: l.code, name: l.name, state_code: l.state_code })),
    });
  }
  throw notFound("LGA", value);
}

function requireBank(value: string): Bank {
  const b = getBank(value);
  if (!b) throw notFound("bank", value);
  return b;
}

const list = <T>(data: T[]) => ({ count: data.length, data });

function route(url: URL): unknown {
  const parts = url.pathname.replace(/\/+$/, "").split("/").slice(1).map(decodeURIComponent);
  if (parts[0] !== "v1") throw new HttpError(404, "not_found", "Unknown path. The API lives under /v1 (see /v1/docs).");
  const [, resource, id, sub] = parts;

  switch (resource) {
    case undefined:
      return {
        name: "naija-data API",
        version: "v1",
        data_version: DATA_VERSION,
        docs: "/v1/docs",
        openapi: "/v1/openapi.json",
        endpoints: ["/v1/states", "/v1/lgas", "/v1/wards/{code}", "/v1/search?q=", "/v1/banks",
          "/v1/validate/nuban?account=&bank=", "/v1/phone/{number}", "/v1/plates/{plate}", "/v1/area-codes", "/v1/health"],
        source: "https://github.com/asgatcreation/naija-data",
        licence: "Data CC BY 4.0, Akanji Oluwaseun Gabriel. Code MIT.",
      };
    case "meta":
      return meta();
    case "states":
      if (!id) return list(states());
      if (!sub) return { data: requireState(id) };
      if (sub === "lgas") return list(lgas(requireState(id)));
      break;
    case "lgas": {
      const state = url.searchParams.get("state");
      if (!id) return list(state ? lgas(requireState(state)) : lgas());
      const lga = requireLga(id, state);
      if (!sub) return { data: lga };
      if (sub === "wards") return list(wards(lga));
      break;
    }
    case "wards":
      if (id && !sub) {
        const w = getWard(id);
        if (!w) throw notFound("ward", id);
        return { data: w };
      }
      if (!id) throw new HttpError(400, "missing_parameter", "Use /v1/lgas/{code}/wards to list the wards of an LGA.");
      break;
    case "search": {
      const q = url.searchParams.get("q") ?? "";
      if (!q.trim()) throw new HttpError(400, "missing_parameter", 'Add a search term, e.g. /v1/search?q=lagos.');
      const limit = intParam(url, "limit", 10, 1, 50);
      const kinds = (url.searchParams.get("kinds") ?? "state,lga").split(",").map((k) => k.trim());
      const unknown = kinds.filter((k) => !["state", "lga", "ward"].includes(k));
      if (unknown.length) throw new HttpError(400, "invalid_parameter", `Unknown kinds: ${unknown.join(", ")}. Use state, lga, ward.`);
      const results: SearchResult[] = [];
      if (kinds.includes("state") || kinds.includes("lga")) {
        results.push(...search(q, { limit: 50 }).filter((r) => kinds.includes(r.kind)));
      }
      if (kinds.includes("ward")) results.push(...searchWards(q, { limit }));
      // Same order as the packages: score, then state < lga < ward, then name.
      const order = { state: 0, lga: 1, ward: 2 } as const;
      results.sort((a, b) => b.score - a.score || order[a.kind] - order[b.kind] || (a.name < b.name ? -1 : a.name > b.name ? 1 : 0));
      return list(results.slice(0, limit));
    }
    case "banks": {
      if (id && !sub) return { data: requireBank(id) };
      if (id) break;
      const type = url.searchParams.get("type");
      if (type && !BANK_TYPES.includes(type as BankType)) {
        throw new HttpError(400, "invalid_parameter", `Unknown type "${type}". Use one of: ${BANK_TYPES.join(", ")}.`);
      }
      const activeOnly = boolParam(url, "active", true);
      const q = url.searchParams.get("q");
      if (q) return list(findBanks(q, intParam(url, "limit", 10, 1, 50), activeOnly).filter((b) => !type || b.type === type));
      return list(banks(type as BankType | null, activeOnly));
    }
    case "validate":
      if (id === "nuban" && !sub) {
        const account = (url.searchParams.get("account") ?? "").replace(/[\s-]/g, "");
        if (!/^\d{10}$/.test(account)) {
          throw new HttpError(422, "invalid_account", "The account number must have 10 digits.");
        }
        const bankParam = url.searchParams.get("bank");
        if (!bankParam) {
          const candidates = banksForNuban(account);
          return { data: { account, candidates: candidates.map((b) => ({ id: b.id, name: b.name, cbn_code: b.cbn_code })) } };
        }
        const bank = requireBank(bankParam);
        if (!bank.cbn_code) throw new HttpError(422, "no_cbn_code", `naija-data has no CBN code for ${bank.name} yet.`);
        return { data: { account, bank: { id: bank.id, name: bank.name, cbn_code: bank.cbn_code }, valid: isValidNuban(account, bank.cbn_code) } };
      }
      break;
    case "phone":
      if (id && !sub) {
        const p = parsePhone(id);
        if (!p) throw new HttpError(422, phoneError(id)!, `Not a valid Nigerian phone number (${phoneError(id)}).`);
        return { data: p };
      }
      break;
    case "plates":
      if (!id) return list(plateCategories());
      if (!sub) {
        const p = parsePlate(id);
        if (!p) throw new HttpError(422, plateError(id)!, `Not a valid plate number (${plateError(id)}).`);
        return { data: p };
      }
      break;
    case "area-codes":
      if (!id) return list(areaCodes());
      break;
    case "health":
      return { status: "ok" };
    case "openapi.json":
      return openapi(url.origin, DATA_VERSION);
  }
  throw new HttpError(404, "not_found", "Unknown path. See /v1/docs for the list of endpoints.");
}

function docsPage(): Response {
  const html = `<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>naija-data API</title><link rel="stylesheet" href="${SWAGGER_UI}/swagger-ui.css"></head>
<body><div id="ui"></div><script src="${SWAGGER_UI}/swagger-ui-bundle.js" crossorigin></script>
<script>SwaggerUIBundle({ url: "/v1/openapi.json", dom_id: "#ui" });</script></body></html>`;
  return new Response(html, { headers: { "content-type": "text/html; charset=utf-8", "cache-control": CACHE_CONTROL } });
}

const CORS = {
  "access-control-allow-origin": "*",
  "access-control-allow-methods": "GET, HEAD, OPTIONS",
  "access-control-allow-headers": "content-type, if-none-match",
  "access-control-max-age": "86400",
};

export async function handle(request: Request, env: Env): Promise<Response> {
  const url = new URL(request.url);
  if (request.method === "OPTIONS") return new Response(null, { status: 204, headers: CORS });
  if (request.method !== "GET" && request.method !== "HEAD") {
    return json({ error: { code: "method_not_allowed", message: "This API is read-only: use GET." } }, 405, { ...CORS, allow: "GET, HEAD, OPTIONS" });
  }
  if (url.pathname === "/" ) return Response.redirect(`${url.origin}/v1`, 302);
  if (url.pathname.replace(/\/+$/, "") === "/v1/docs") return docsPage();

  if (url.pathname !== "/v1/health" && env.RATE_LIMITER) {
    const ip = request.headers.get("cf-connecting-ip") ?? "unknown";
    const { success } = await env.RATE_LIMITER.limit({ key: ip });
    if (!success) {
      return json({ error: { code: "rate_limited", message: "Too many requests. Please slow down (about 120 requests per minute per IP), or install a naija-data package for heavy use." } },
        429, { ...CORS, "retry-after": "60" });
    }
  }

  try {
    let body = route(url);
    if (url.pathname.replace(/\/+$/, "") === "/v1/health") {
      body = { status: "ok", data_version: DATA_VERSION, api_version: env.API_VERSION ?? "dev", counts: meta().counts };
      return json(body, 200, { ...CORS, "cache-control": "no-store" });
    }
    const etag = `W/"${DATA_VERSION}-${env.API_VERSION ?? "dev"}"`;
    if (request.headers.get("if-none-match") === etag) {
      return new Response(null, { status: 304, headers: { ...CORS, etag, "cache-control": CACHE_CONTROL } });
    }
    return json(body, 200, { ...CORS, etag, "cache-control": CACHE_CONTROL });
  } catch (e) {
    if (e instanceof HttpError) {
      return json({ error: { code: e.code, message: e.message, ...e.extra } }, e.status, { ...CORS, "cache-control": "public, max-age=300" });
    }
    console.error(e);
    return json({ error: { code: "internal_error", message: "Something went wrong. Please report it on GitHub." } }, 500, CORS);
  }
}

export default {
  async fetch(request: Request, env: Env, ctx: { waitUntil(p: Promise<unknown>): void }): Promise<Response> {
    // Serve repeated GETs from Cloudflare's edge cache (the data only changes when we deploy).
    const cache = (globalThis as unknown as { caches?: { default: Cache } }).caches?.default;
    const cacheable = request.method === "GET" && !new URL(request.url).pathname.startsWith("/v1/health");
    if (cache && cacheable && !request.headers.get("if-none-match")) {
      const hit = await cache.match(request);
      if (hit) return hit;
    }
    const response = await handle(request, env);
    if (cache && cacheable && response.status === 200) ctx.waitUntil(cache.put(request, response.clone()));
    return response;
  },
};
