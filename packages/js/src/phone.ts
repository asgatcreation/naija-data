import phoneData from "./data/phone.json";
import type { PhoneInfo } from "./types";

interface Block {
  prefix: string;
  range_start: string;
  range_end: string;
  operator: string | null;
  status: string;
}

const BLOCKS = phoneData as Block[];
const MOBILE = /^[789][01]\d{8}$/;

export const PORTING_NOTE =
  "Numbers can be ported between networks, so the prefix shows the network the number was first " +
  "allocated to, not necessarily its network today.";

/** The 10-digit national number (without the leading 0), or null. */
function national(text: string): string | null {
  let s = text.trim().replace(/[\s\-.()]/g, "");
  if (s.startsWith("+")) {
    s = s.slice(1);
    if (!s.startsWith("234")) return null;
  }
  if (s.startsWith("2340")) s = "234" + s.slice(4); // "+234 (0) 803 ..." with the trunk 0
  if (s.startsWith("234") && s.length === 13) s = s.slice(3);
  else if (s.startsWith("0") && s.length === 11) s = s.slice(1);
  return MOBILE.test(s) ? s : null;
}

/**
 * International (E.164) form, "+2348031234567", or null if it is not a well-formed Nigerian mobile
 * number. Accepts "0803 123 4567", "+234 803-123-4567", "2348031234567", "+234 (0) 803 123 4567".
 */
export function normalizePhone(text: string): string | null {
  const n = national(text);
  return n ? `+234${n}` : null;
}

/** Local form, "08031234567", or null. */
export function toLocal(text: string): string | null {
  const n = national(text);
  return n ? `0${n}` : null;
}

/** Normalise a mobile number and look up the network its number block was allocated to. */
export function lookupPhone(text: string): PhoneInfo | null {
  const n = national(text);
  if (!n) return null;
  const prefix = "0" + n.slice(0, 3);
  const subscriber = n.slice(3);
  const block = BLOCKS.find((b) => b.prefix === prefix && b.range_start <= subscriber && subscriber <= b.range_end);
  return {
    e164: `+234${n}`,
    local: `0${n}`,
    prefix,
    network: block ? block.operator : null,
    status: block ? block.status : null,
    note: PORTING_NOTE,
  };
}

/** Names of networks with allocated mobile prefixes. */
export function networks(): string[] {
  return [...new Set(BLOCKS.map((b) => b.operator).filter((o): o is string => !!o))].sort();
}

/** Mobile prefixes ("0803", ...) allocated to a network (case-insensitive), or all prefixes. */
export function prefixes(network?: string | null): string[] {
  const want = network ? network.toLowerCase() : null;
  return [...new Set(BLOCKS.filter((b) => want === null || (b.operator ?? "").toLowerCase() === want).map((b) => b.prefix))].sort();
}
