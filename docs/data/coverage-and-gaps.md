# Coverage, cross-checks and known gaps

Dataset built on 2026-10-09 from the sources in [`data/sources.json`](../../data/sources.json).
Run `python scripts/validate.py` to re-check every rule below.

## Coverage

| Dataset | Rows | Official total | Status |
|---|---|---|---|
| States + FCT | 37 | 37 (Constitution s.2–3) | ✅ complete |
| LGAs + FCT area councils | 774 | 768 + 6 = 774 (Constitution s.3(6)) | ✅ complete |
| Wards / registration areas | 8,809 | 8,809 (INEC) | ✅ complete |
| Licensed financial institutions | 897 active + 2 historical | CBN register | ✅ complete list; codes partial (see below) |
| Mobile number blocks | 51 blocks, 45 prefixes | NCC table (Dec 2023) | ✅ complete as published |
| Postcodes | format only | NIPOST NDAPS | ⚠️ records not redistributable |

### Field coverage

| Field | Coverage | Confidence |
|---|---|---|
| State ISO 3166-2 code, INEC code, P-code, capital, zone, centroid | 37 / 37 | verified |
| State creation date | 36 / 36 (+ FCT) | **unverified**: single secondary source |
| LGA INEC code, P-code, senatorial district, centroid | 774 / 774 | verified |
| LGA headquarters | 633 / 774 | 6 verified (FCT, Constitution); 627 **unverified** (UN COD-AB only) |
| LGA aliases (other spellings) | 89 aliases on 76 LGAs | from INEC 2015, COD-AB and Constitution |
| Ward names cross-checked with INEC 2015 directory | 8,355 / 8,809 | Abia (184) and Delta (270) not cross-checked: their 2015 files were not archived |
| Bank `cbn_code` (used for NUBAN validation) | 142 institutions | 22 verified by two sources |
| Bank `nip_code` | 50 institutions | 1 verified by two sources |
| Bank USSD code | 18 institutions | all single-source |

## Mismatches found between sources

These are real errors in upstream data that naija-data detected and resolved.

### INEC live list (cvr.inecnigeria.org)
- **Duplicate ward.** "09 – Mbaikyaan" in Gwer East (Benue) appears twice (second copy has internal id 8810), giving 8,810 instead of INEC's published 8,809. The duplicate is removed.
- **Roman numerals typed as digits.** For example "Abak Urban 11", "Eastern Obolo V111" and "1tak". Repaired only where the 2015 directory confirms the correct spelling ("Abak Urban II", "Eastern Obolo VIII", "Itak").
- **Abbreviated, truncated or misspelled LGA labels**, corrected with a reason recorded in `scripts/build/import_admin.py` (`LGA_NAME_FIXES`):
  "Maiduguri M. C." → Maiduguri; "Municipal" → Abuja Municipal; "Kogi . K. K." → Kogi; "S/Birni" → Sabon Birni;
  "Yalmaltu/ Deba" → Yamaltu/Deba; "Malufashi" → Malumfashi; "Karasawa" → Karasuwa; "Uhunmwode" → Uhunmwonde;
  "Esit Eket (Uquo)" → Esit Eket; "Osisioma" → Osisioma Ngwa; "Mopa Moro" → Mopa-Muro; "Ogori Mangogo" → Ogori/Magongo;
  "Arewa" → Arewa Dandi; "Calabar Municipality" → Calabar Municipal.

### INEC 2015 vs INEC today
- 50 LGAs are spelled differently. Today's INEC spelling is kept (e.g. **Yenagoa** not "Yenegoa", **Aliero** not "Aleiro", **Somolu** not "Shomolu", **Ilesa** not "Ilesha", **Oorelope** not "Orelope", **Munya** not "Muya") and the old spelling becomes an alias, so searches find both.
- Ekiti LGA 07 is "Aiyekire" today and "Gboyin" in 2015; both (and "Gbonyin") are searchable.
- 140 wards were renamed or respelled since 2015; the 2015 name is kept as an alias.
- Ward counts per LGA are identical in both (after removing the duplicate above).

### UN COD-AB (OSGOF data)
- Anambra's capital spelled **"Akwa"** (should be Awka).
- **Lagos appears twice** among state capitals (Ikeja and Lagos); FCT has none.
- LGA name typos: "Obia/Akpor" (Obio/Akpor), "Markafi" (Makarfi), "Atigbo" (Atisbo).
- 14 LGAs have two or more candidate headquarters; these are left empty rather than guessed.

### Constitution (government-hosted transcription)
- Typing errors ("Tqngaza", "Ogbmosho", "Matazuu") and missing commas merge or split LGAs ("Kaura, Namoda"), so a naive parse finds 764 of 768 LGAs. Used for capitals and aliases, not as the master list.

### Payment providers' bank lists
- **Paystack gives code 51253 to two different microfinance banks** (Stellas MFB and YCT MFB). With one source we cannot tell which is right, so the code is left empty for both.
- Paystack's `code` mixes CBN codes, NIP codes and its own codes ("MFB50094", "035A" for ALAT by Wema, 3-digit codes for microfinance banks). Only codes whose format fits the institution's type are used; 114 Paystack entries were not used.
- "Access Bank (Diamond)" carries **063**, Diamond Bank's old code. Diamond Bank is kept as a `merged` institution (into Access, 2019-04-01); old 063 accounts still route to Access.
- Monnify still lists **Diamond** and **Heritage** banks. Status therefore comes only from the CBN register (Heritage: licence revoked 2024-06-03, CBN press release).

## Known gaps (help wanted)

1. **Bank codes for most microfinance, mortgage and finance institutions.** Only 99 of 796 microfinance banks have a CBN code, and most are single-source. NIBSS does not publish its NIP institution list. Contributions with a NIBSS or CBN document are very welcome.
2. **NIP codes** are confirmed by two sources for only one institution. They are flagged `unverified`.
3. **LGA headquarters**: 141 LGAs have none, and 627 come only from the UN dataset, which has known errors. Official state government sources are needed.
4. **State creation dates** come from one news source and are ambiguous for states that were split or renamed. A gazette or decree reference is needed for each.
5. **State nicknames/slogans** ("Centre of Excellence"...) are not included yet: no authoritative list was found, and slogans change between administrations.
6. **Bank websites and full merger history** (beyond Diamond and Heritage) are not included yet.
7. **Postcodes**: NIPOST's 11-character digital postcodes are only available through a gated API with no open licence; no redistributable list of the old 6-digit codes was found. naija-data will validate the postcode *format* and link to the official lookup.
8. **Phone prefixes** are as published by the NCC "as at December 2023". Prefixes such as 0910, 0914 and 0917–0919 do not appear in the NCC table and are not included.
9. **Abia and Delta wards** were not cross-checked against the 2015 directory (files not archived).
10. **Ward boundaries** are not included: the only good dataset (GRID3) is CC BY-SA and covers 24 states.
