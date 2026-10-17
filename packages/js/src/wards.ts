// Wards (INEC registration areas) live in their own entry point, "naija-data/wards", because the
// table is large (8,809 rows). Import it only when you need wards.

import wardData from "./data/wards.json";
import { rank, requireLga, type Candidate, type SearchOptions } from "./admin";
import { requireConstituency } from "./constituencies";
import type { Constituency, LGA, SearchResult, State, Ward } from "./types";

type Row = [string, string, string, string, string, string, string, string | null, string[], string[]];

let all: Ward[] | undefined;
let byLga: Map<string, Ward[]> | undefined;

function load(): Ward[] {
  if (!all) {
    all = (wardData.rows as Row[]).map(
      ([code, lga_code, state_code, name, slug, senatorial_district, federal_constituency, state_constituency, aliases,
        unverified_fields]) => ({
        code, lga_code, state_code, name, slug, senatorial_district, federal_constituency, state_constituency, aliases,
        unverified_fields,
      }),
    );
    byLga = new Map();
    for (const w of all) {
      const list = byLga.get(w.lga_code) ?? [];
      list.push(w);
      byLga.set(w.lga_code, list);
    }
  }
  return all;
}

/** Wards of an LGA, in INEC code order. Throws for an unknown or ambiguous LGA. */
export function wards(lga: string | LGA, state?: string | State | null): Ward[] {
  load();
  return [...(byLga!.get(requireLga(lga, state).code) ?? [])];
}

/** Find a ward by its INEC code, e.g. "24-11-01". */
export function getWard(code: string): Ward | null {
  const c = code.trim();
  return load().find((w) => w.code === c) ?? null;
}

/** Fuzzy search across all 8,809 wards. */
export function searchWards(query: string, options: SearchOptions = {}): SearchResult[] {
  return rank(
    query,
    load().map((w): Candidate => ["ward", w.code, w.name, w.state_code, [w.name, ...w.aliases]]),
    options.limit ?? 10,
    options.minScore ?? 600,
  );
}

/** Wards (INEC registration areas) that make up a senatorial district or constituency, in INEC code order. */
export function constituencyWards(code: string | Constituency): Ward[] {
  const u = requireConstituency(code);
  return load().filter((w) => w[u.kind] === u.code); // ward fields are named after the kinds
}

export type { Ward } from "./types";
