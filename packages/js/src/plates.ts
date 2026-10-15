// Vehicle number plates: format validation and parsing, from the National Road Traffic Regulations
// 2012 (Official Gazette No. 101, S.I. 61), regulations 37-39 and Schedule 5. FRSC sets the LGA
// plate codes (reg. 39(5)) but does not publish them, so plates are not mapped to LGAs.
import plateData from "./data/plates.json";
import stateData from "./data/states.json";
import type { Plate, PlateCategory, PlateError, PlateFormat } from "./types";

let stateCodes: Set<string> | undefined; // built on first use, so unused code can be tree-shaken
const STATE_CODES = () => (stateCodes ??= new Set((stateData as { code: string }[]).map((s) => s.code)));

export const PLATE_FORMATS: readonly PlateFormat[] = ["standard", "dealer"];
export const PLATE_ERRORS: readonly PlateError[] = ["empty", "invalid_characters", "unknown_format", "unknown_state"];

export const LGA_CODE_NOTE =
  "The first three letters are the Local Government code. FRSC does not publish the list of codes, so " +
  "naija-data does not map them to LGAs yet.";

function parse(text: string): [Plate | null, PlateError | null] {
  let s = text.trim().replace(/[\s\-.]/g, "");
  if (!s) return [null, "empty"];
  // Check for plain ASCII before upper-casing: languages upper-case some letters differently ("ß").
  if (!/^[A-Za-z0-9]+$/.test(s)) return [null, "invalid_characters"];
  s = s.toUpperCase();
  let m = /^([A-Z]{3})(\d{3})([A-Z]{2})$/.exec(s);
  if (m) {
    return [{ compact: s, display: `${m[1]}-${m[2]}${m[3]}`, format: "standard", prefix: m[1], number: m[2], suffix: m[3],
      state_code: null, note: LGA_CODE_NOTE }, null];
  }
  m = /^D([A-Z]{2})(\d{3})([A-Z0-9])$/.exec(s);
  if (m) {
    if (!STATE_CODES().has(m[1])) return [null, "unknown_state"];
    return [{ compact: s, display: `D${m[1]} ${m[2]} ${m[3]}`, format: "dealer", prefix: "D" + m[1], number: m[2],
      suffix: m[3], state_code: m[1], note: null }, null];
  }
  return [null, "unknown_format"];
}

/** Why `text` is not a valid plate number, or null if it is valid. */
export function plateError(text: string): PlateError | null {
  return parse(text)[1];
}

/** Validate and split a plate number ("kja 123 ab" -> KJA-123AB; dealer "DKN 135 3"), or null. */
export function parsePlate(text: string): Plate | null {
  return parse(text)[0];
}

/** True if `text` is a valid plate number, optionally only of the given formats. */
export function isValidPlate(text: string, formats?: readonly PlateFormat[] | null): boolean {
  const p = parsePlate(text);
  return p !== null && (formats == null || formats.includes(p.format));
}

/** Plate colours by category, as set by the National Road Traffic Regulations 2012. */
export function plateCategories(): PlateCategory[] {
  return (plateData as { categories: PlateCategory[] }).categories.map((c) => ({ ...c }));
}
