// Nigerian phone numbers: strict validation, number type, normalisation and network lookup.
// Same rules as the Python and Go packages (see packages/python/src/naija_data/phone.py).
import phoneData from "./data/phone.json";
import type { AreaCode, PhoneError, PhoneNumber, PhoneType } from "./types";

interface MobileBlock {
  prefix: string;
  range_start: string;
  range_end: string;
  operator: string | null;
  status: string;
}
interface PlanBlock {
  number_type: PhoneType;
  range_start: string;
  range_end: string;
  allottee: string;
}
interface AreaRow {
  area_code: string;
  primary_centre: string;
  ncc_zone: string;
  unverified_fields: string[];
}

const DATA = phoneData as { mobile: MobileBlock[]; blocks: PlanBlock[]; area_codes: AreaRow[] };
let areas: Map<string, AreaRow> | undefined; // built on first use, so unused code can be tree-shaken
const AREAS = () => (areas ??= new Map(DATA.area_codes.map((a) => [a.area_code, a])));

export const PORTING_NOTE =
  "Numbers can be ported between networks, so the prefix shows the network the number was first " +
  "allocated to, not necessarily its network today.";

export const PHONE_TYPES: readonly PhoneType[] = ["mobile", "fixed", "toll_free", "non_toll_free"];
export const PHONE_ERRORS: readonly PhoneError[] = [
  "empty", "invalid_characters", "not_nigerian", "bad_length", "unknown_prefix", "unallocated", "reserved", "unknown_area_code",
];

const SEPARATORS = /[\s\-.()/]/g;
const DIGITS = /^[0-9]*$/;

function shortNetwork(allottee: string): string {
  const pairs: [string, string][] = [["mtn", "MTN"], ["airtel", "Airtel"], ["glo", "Glo"], ["9mobile", "9mobile"],
    ["smile", "Smile"], ["mafab", "MAFAB"], ["ntel", "nTel"]];
  const low = allottee.toLowerCase();
  return pairs.find(([k]) => low.includes(k))?.[1] ?? allottee;
}

function inPlan(nsn: string, type: PhoneType): PlanBlock | null {
  return DATA.blocks.find((b) => b.number_type === type && b.range_start.length === nsn.length && b.range_start <= nsn && nsn <= b.range_end) ?? null;
}

function national(text: string): [string | null, PhoneError | null] {
  let s = text.trim().replace(SEPARATORS, "");
  if (!s) return [null, "empty"];
  if (s.startsWith("+")) {
    s = s.slice(1);
    if (!DIGITS.test(s)) return [null, "invalid_characters"];
    if (!s.startsWith("234")) return [null, "not_nigerian"];
  } else if (s.startsWith("00")) {
    if (!DIGITS.test(s)) return [null, "invalid_characters"];
    if (!s.startsWith("00234")) return [null, "not_nigerian"];
    s = s.slice(2);
  }
  if (!DIGITS.test(s)) return [null, "invalid_characters"];
  if (s.startsWith("2340")) s = "234" + s.slice(4); // "+234 (0) 803 ..." with the trunk 0
  if (s.startsWith("234") && (s.length === 11 || s.length === 13)) return [s.slice(3), null];
  if (s.startsWith("0") && (s.length === 9 || s.length === 11)) return [s.slice(1), null];
  if (s.length === 10 && "789".includes(s[0])) return [s, null];
  return [null, "bad_length"];
}

function classify(nsn: string): [PhoneNumber | null, PhoneError | null] {
  const local = "0" + nsn;
  const e164 = "+234" + nsn;
  if (nsn.length === 10) {
    const lead = nsn.slice(0, 3);
    if (lead === "900") return [null, "reserved"];
    if (lead === "800" || lead === "700") {
      const type: PhoneType = lead === "800" ? "toll_free" : "non_toll_free";
      const block = inPlan(nsn, type);
      return [{ e164, local, national: nsn, type, prefix: "0" + lead, area: null, network: block ? block.allottee : null,
        allocated: block !== null, note: null }, null];
    }
    const prefix = "0" + lead;
    const subscriber = nsn.slice(3);
    const table = DATA.mobile.filter((b) => b.prefix === prefix);
    const hit = table.find((b) => b.range_start <= subscriber && subscriber <= b.range_end);
    let network: string | null;
    if (hit && hit.status === "allocated") network = hit.operator;
    else {
      const plan = inPlan(nsn, "mobile");
      if (!plan) return [null, table.length ? "unallocated" : "unknown_prefix"];
      network = shortNetwork(plan.allottee);
    }
    return [{ e164, local, national: nsn, type: "mobile", prefix, area: null, network, allocated: true, note: PORTING_NOTE }, null];
  }
  if (nsn.length === 8) {
    const code = "129".includes(nsn[0]) ? "0" + nsn[0] : "0" + nsn.slice(0, 2);
    const area = AREAS().get(code);
    if (!area) return [null, "unknown_area_code"];
    const block = inPlan(nsn, "fixed");
    return [{ e164, local, national: nsn, type: "fixed", prefix: code, area: area.primary_centre,
      network: block ? block.allottee : null, allocated: block !== null, note: null }, null];
  }
  return [null, "bad_length"];
}

/** Why `text` is not a valid Nigerian phone number, or null if it is valid. */
export function phoneError(text: string): PhoneError | null {
  const [nsn, err] = national(text);
  return err ?? classify(nsn!)[1];
}

/**
 * Validate and describe a Nigerian phone number (mobile, fixed line, 0800 toll-free or 0700),
 * or return null if it is not valid. Strict: mobile numbers must be in an NCC-allocated block,
 * fixed lines must use one of the NCC's 56 area codes.
 */
export function parsePhone(text: string): PhoneNumber | null {
  const [nsn, err] = national(text);
  return err ? null : classify(nsn!)[0];
}

/** True if `text` is a valid Nigerian number, optionally only of the given types (e.g. ["mobile"]). */
export function isValidPhone(text: string, types?: readonly PhoneType[] | null): boolean {
  const p = parsePhone(text);
  return p !== null && (types == null || types.includes(p.type));
}

/** International (E.164) form, "+2348031234567", or null if the number is not valid. */
export function normalizePhone(text: string): string | null {
  return parsePhone(text)?.e164 ?? null;
}

/** Local form, "08031234567", or null if the number is not valid. */
export function toLocal(text: string): string | null {
  return parsePhone(text)?.local ?? null;
}

/** Names of networks with allocated mobile prefixes. */
export function networks(): string[] {
  return [...new Set(DATA.mobile.map((b) => b.operator).filter((o): o is string => !!o))].sort();
}

/** Mobile prefixes ("0803", ...) allocated to a network (case-insensitive), or all prefixes. */
export function prefixes(network?: string | null): string[] {
  const want = network ? network.toLowerCase() : null;
  return [...new Set(DATA.mobile.filter((b) => want === null || (b.operator ?? "").toLowerCase() === want).map((b) => b.prefix))].sort();
}

/** The NCC's 56 geographic (landline) area codes. */
export function areaCodes(): AreaCode[] {
  return DATA.area_codes.map((a) => ({ ...a, unverified_fields: [...a.unverified_fields] }));
}
