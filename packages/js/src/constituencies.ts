// Electoral units from INEC: senatorial districts, federal constituencies and state constituencies.
// Their own entry point, "naija-data/constituencies". The wards of a unit come from
// constituencyWards in "naija-data/wards".

import unitData from "./data/constituencies.json";
import { lgas, requireLga, requireState } from "./admin";
import { cmp, norm } from "./text";
import type { Constituency, ConstituencyKind, LGA, State } from "./types";

const UNITS = unitData as Constituency[];

export const CONSTITUENCY_KINDS: readonly ConstituencyKind[] = [
  "senatorial_district", "federal_constituency", "state_constituency",
];

let byCode: Map<string, Constituency> | undefined;

function codeIndex(): Map<string, Constituency> {
  if (!byCode) {
    byCode = new Map();
    for (const u of UNITS) {
      byCode.set(u.code, u);
      byCode.set(u.inec_code, u);
    }
  }
  return byCode;
}

/** Electoral units of one kind (or all), optionally in one state, in INEC code order. */
export function constituencies(kind?: ConstituencyKind | null, state?: string | State | null): Constituency[] {
  if (kind != null && !CONSTITUENCY_KINDS.includes(kind)) {
    throw new Error(`Unknown constituency kind: ${JSON.stringify(kind)} (use one of ${CONSTITUENCY_KINDS.join(", ")})`);
  }
  const code = state != null ? requireState(state).code : null;
  return UNITS.filter((u) => (kind == null || u.kind === kind) && (code === null || u.state_code === code));
}

/** The 109 senatorial districts (3 per state, 1 for the FCT), or those of one state. */
export function senatorialDistricts(state?: string | State | null): Constituency[] {
  return constituencies("senatorial_district", state);
}

/** The 360 federal constituencies (House of Representatives seats), or those of one state. */
export function federalConstituencies(state?: string | State | null): Constituency[] {
  return constituencies("federal_constituency", state);
}

/** The 990 state constituencies (House of Assembly seats), or those of one state. The FCT has none. */
export function stateConstituencies(state?: string | State | null): Constituency[] {
  return constituencies("state_constituency", state);
}

/** Find a unit by code ("SD001", "FC001", "SC001") or INEC code ("FC/001/AB"). Null if unknown. */
export function getConstituency(code: string | Constituency): Constituency | null {
  if (typeof code !== "string") return code;
  return codeIndex().get(code.replace(/\s/g, "").toUpperCase()) ?? null;
}

/** Every unit whose name or alias matches exactly (ignoring case and punctuation), e.g. "Lagos West". */
export function findConstituencies(name: string, kind?: ConstituencyKind | null, state?: string | State | null): Constituency[] {
  const q = norm(name);
  return constituencies(kind, state).filter((u) => [u.name, u.slug, ...u.aliases].some((t) => norm(t) === q));
}

export function requireConstituency(code: string | Constituency): Constituency {
  const u = getConstituency(code);
  if (!u) throw new Error(`Unknown constituency: ${JSON.stringify(code)}`);
  return u;
}

/**
 * LGAs a unit covers in full or in part, sorted by name. A few LGAs are split between
 * constituencies (e.g. Surulere I and II in Lagos): use constituencyWards for the exact area.
 */
export function constituencyLgas(code: string | Constituency): LGA[] {
  const codes = new Set(requireConstituency(code).lga_codes);
  return lgas().filter((l) => codes.has(l.code));
}

/**
 * The senatorial district, federal constituencies and state constituencies an LGA lies in (more
 * than one when the LGA is split), ordered by kind then code.
 */
export function lgaConstituencies(lga: string | LGA, state?: string | State | null): Constituency[] {
  const code = requireLga(lga, state).code;
  return UNITS.filter((u) => u.lga_codes.includes(code)).sort(
    (a, b) => CONSTITUENCY_KINDS.indexOf(a.kind) - CONSTITUENCY_KINDS.indexOf(b.kind) || cmp(a.code, b.code),
  );
}

export type { Constituency, ConstituencyKind } from "./types";
