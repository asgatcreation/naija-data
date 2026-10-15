import lgaData from "./data/lgas.json";
import stateData from "./data/states.json";
import { cmp, norm, score } from "./text";
import type { LGA, SearchKind, SearchResult, State } from "./types";

const STATES = stateData as State[];
const LGAS = lgaData as LGA[];

export const KIND_ORDER: Record<SearchKind, number> = { state: 0, lga: 1, ward: 2 };

let stateIndex: Map<string, State> | undefined;
let lgaNameIndex: Map<string, LGA[]> | undefined;

function getStateIndex(): Map<string, State> {
  if (!stateIndex) {
    stateIndex = new Map();
    for (const s of STATES) {
      for (const term of [s.name, s.slug, ...s.aliases]) {
        const k = norm(term);
        if (!stateIndex.has(k)) stateIndex.set(k, s);
      }
    }
  }
  return stateIndex;
}

function getLgaNameIndex(): Map<string, LGA[]> {
  if (!lgaNameIndex) {
    lgaNameIndex = new Map();
    for (const l of LGAS) {
      for (const k of new Set([l.name, l.slug, ...l.aliases].map(norm))) {
        const list = lgaNameIndex.get(k) ?? [];
        list.push(l);
        lgaNameIndex.set(k, list);
      }
    }
  }
  return lgaNameIndex;
}

// ------------------------------------------------------------------ states

/** All 36 states and the FCT, sorted by name. */
export function states(): State[] {
  return [...STATES];
}

/**
 * Find a state by ISO code ("LA", "NG-LA"), INEC code ("24"), P-code ("NG025"), slug, name or
 * alias ("Lagos", "lagos state", "Abuja", "FCT", "Akwa-Ibom"). Returns null if unknown.
 */
export function getState(query: string | State): State | null {
  if (typeof query !== "string") return query;
  const q = query.trim();
  const up = q.toUpperCase();
  for (const s of STATES) {
    if (up === s.code || up === s.iso_code || up === s.pcode || q === s.inec_code) return s;
  }
  return getStateIndex().get(norm(q)) ?? null;
}

function requireState(state: string | State): State {
  const s = getState(state);
  if (!s) throw new Error(`Unknown state: ${JSON.stringify(state)}`);
  return s;
}

// ------------------------------------------------------------------ LGAs

/** All 774 LGAs, or the LGAs of one state, sorted by name. Throws for an unknown state. */
export function lgas(state?: string | State | null): LGA[] {
  if (state == null) return [...LGAS].sort((a, b) => cmp(a.name, b.name) || cmp(a.code, b.code));
  const code = requireState(state).code;
  return LGAS.filter((l) => l.state_code === code);
}

/** Every LGA whose name or alias matches exactly (several states share names, e.g. "Surulere"). */
export function findLgas(name: string): LGA[] {
  return [...(getLgaNameIndex().get(norm(name)) ?? [])];
}

/**
 * Find an LGA by P-code ("NG025011"), INEC code ("24-11"), or name/alias. A name shared by LGAs
 * in several states returns null unless `state` is given.
 */
export function getLga(query: string | LGA, state?: string | State | null): LGA | null {
  if (typeof query !== "string") return query;
  const q = query.trim();
  if (/^ng\d{6}$/i.test(q)) return LGAS.find((l) => l.code === q.toUpperCase()) ?? null;
  if (/^\d{2}-\d{2}$/.test(q)) return LGAS.find((l) => l.inec_code === q) ?? null;
  let matches = findLgas(q);
  if (state != null) {
    const code = requireState(state).code;
    matches = matches.filter((l) => l.state_code === code);
  }
  return matches.length === 1 ? matches[0] : null;
}

export function requireLga(lga: string | LGA, state?: string | State | null): LGA {
  const l = getLga(lga, state);
  if (!l) throw new Error(`Unknown or ambiguous LGA: ${JSON.stringify(lga)}${state ? "" : " (pass state to choose)"}`);
  return l;
}

// ------------------------------------------------------------------ search

export interface SearchOptions {
  limit?: number;
  minScore?: number;
}

export type Candidate = [kind: SearchKind, code: string, name: string, stateCode: string, terms: string[]];

export function rank(query: string, candidates: Iterable<Candidate>, limit = 10, minScore = 600): SearchResult[] {
  const q = norm(query);
  if (!q) return [];
  const results: SearchResult[] = [];
  for (const [kind, code, name, state_code, terms] of candidates) {
    let best = 0;
    let matched = "";
    for (const term of terms) {
      const s = score(q, norm(term));
      if (s > best) {
        best = s;
        matched = term;
      }
    }
    if (best >= minScore) results.push({ kind, code, name, state_code, score: best, matched });
  }
  results.sort((a, b) => b.score - a.score || KIND_ORDER[a.kind] - KIND_ORDER[b.kind] || cmp(a.name, b.name) || cmp(a.code, b.code));
  return results.slice(0, limit);
}

function* adminCandidates(): Generator<Candidate> {
  for (const s of STATES) yield ["state", s.code, s.name, s.code, [s.name, s.code, ...s.aliases]];
  for (const l of LGAS) yield ["lga", l.code, l.name, l.state_code, [l.name, ...l.aliases]];
}

/**
 * Fuzzy search across states and LGAs. Handles case, punctuation, aliases and typos ("lagso",
 * "akwa-ibom", "abuja", "ikeja lga"). For wards use `searchWards` from "naija-data/wards".
 */
export function search(query: string, options: SearchOptions = {}): SearchResult[] {
  return rank(query, adminCandidates(), options.limit ?? 10, options.minScore ?? 600);
}
