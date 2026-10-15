/**
 * naija-data: accurate, sourced Nigerian reference data.
 *
 *   import { getState, lgas, search, isValidNuban, normalizePhone } from "naija-data";
 *   import { wards } from "naija-data/wards";
 *
 * Data: CC BY 4.0, Akanji Oluwaseun Gabriel (see meta().sources). Code: MIT.
 */
import metaData from "./data/meta.json";
import type { Meta } from "./types";

export { findLgas, getLga, getState, lgas, search, states } from "./admin";
export type { SearchOptions } from "./admin";
export { BANK_TYPES, banks, banksForNuban, findBanks, getBank, isValidNuban, nubanCheckDigit } from "./banks";
export { PORTING_NOTE, lookupPhone, networks, normalizePhone, prefixes, toLocal } from "./phone";
export { norm } from "./text";
export type * from "./types";

/** Dataset version, row counts, licence, attribution and sources. */
export function meta(): Meta {
  return metaData as Meta;
}
