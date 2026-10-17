/**
 * naija-data: accurate, sourced Nigerian reference data.
 *
 *   import { getState, lgas, search, isValidNuban, normalizePhone } from "naija-data";
 *   import { wards } from "naija-data/wards";
 *   import { federalConstituencies, lgaConstituencies } from "naija-data/constituencies";
 *
 * Data: CC BY 4.0, Akanji Oluwaseun Gabriel (see meta().sources). Code: MIT.
 */
import metaData from "./data/meta.json";
import type { Meta } from "./types";

export { findLgas, getLga, getState, lgas, search, states } from "./admin";
export type { SearchOptions } from "./admin";
export { BANK_TYPES, banks, banksForNuban, findBanks, getBank, isValidNuban, nubanCheckDigit } from "./banks";
export {
  PHONE_ERRORS, PHONE_TYPES, PORTING_NOTE, areaCodes, isValidPhone, networks, normalizePhone, parsePhone, phoneError,
  prefixes, toLocal,
} from "./phone";
export { LGA_CODE_NOTE, PLATE_ERRORS, PLATE_FORMATS, isValidPlate, parsePlate, plateCategories, plateError } from "./plates";
export { norm } from "./text";
export type * from "./types";

/** Dataset version, row counts, licence, attribution and sources. */
export function meta(): Meta {
  return metaData as Meta;
}
