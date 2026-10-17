# Coverage, cross-checks and known gaps

Dataset built on 2026-10-09 from the sources in [`data/sources.json`](../../data/sources.json).
Run `python scripts/validate.py` to re-check every rule below.

## Coverage

| Dataset | Rows | Official total | Status |
|---|---|---|---|
| States + FCT | 37 | 37 (Constitution s.2–3) | ✅ complete |
| LGAs + FCT area councils | 774 | 768 + 6 = 774 (Constitution s.3(6)) | ✅ complete |
| Wards / registration areas | 8,809 | 8,809 (INEC) | ✅ complete |
| Senatorial districts | 109 | 109 (Constitution s.48) | ✅ complete (INEC IReV) |
| Federal constituencies | 360 | 360 (Constitution s.49) | ✅ complete (INEC IReV) |
| State constituencies | 990 | 990 in INEC's list (often quoted as 993) | ✅ complete as published by INEC; see below |
| Ward → senatorial district, federal and state constituency | 8,809 / 8,809 | INEC IReV | ✅ 14 links flagged `unverified` (see below) |
| Licensed financial institutions | 897 active + 2 historical | CBN register | ✅ complete list; codes partial (see below) |
| Mobile number blocks | 51 blocks, 45 prefixes | NCC table (Dec 2023) | ✅ complete as published |
| Landline area codes | 56 | NCC area code page | ✅ complete as published |
| Allocated number blocks (fixed, mobile, 0700, 0800) | 305 | NCC National Numbering Plan (Oct 2022) | ✅ 2 rows excluded (see below) |
| Plate formats and colours | standard + dealer formats, 13 colour rules | National Road Traffic Regulations 2012 | ⚠️ LGA plate codes not published by FRSC |
| Postcodes | format only | NIPOST NDAPS | ⚠️ records not redistributable |

### Field coverage

| Field | Coverage | Confidence |
|---|---|---|
| State ISO 3166-2 code, INEC code, P-code, capital, zone, centroid | 37 / 37 | verified |
| State creation date | 36 / 36 (+ FCT) | **unverified**: single secondary source |
| LGA INEC code, P-code, centroid | 774 / 774 | verified |
| LGA senatorial district | 774 / 774 | INEC IReV (replaces UN COD-AB, which differed for 10 LGAs) |
| LGA headquarters | 629 / 774 | 6 verified (FCT, Constitution); 623 **unverified** (UN COD-AB only) |
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
- 14 LGAs have two or more candidate headquarters, and 4 "headquarters" are garbled or are rivers ("Moro, River" for Ilorin West, "Jamao?Çoare" for Jama'are); all are left empty rather than guessed.

### INEC Result Viewing portal (IReV): electoral units
- **990, not 993, state constituencies.** INEC's own list for the 2023 House of Assembly elections numbers
  them SC/001 to SC/990, and every one of the 8,809 wards is linked to one of them (FCT wards to a nameless
  placeholder, dropped because the FCT has no House of Assembly). The figure of 993 that circulates in the
  press is not in INEC's list; no source naming the 3 extra constituencies was found.
- **Three duplicated codes**, corrected from the sequence (`SC_CODE_FIXES` in `scripts/build/import_electoral.py`):
  Ika South (Delta) typed SC/252 → SC/251; Billiri West (Gombe) typed SC/076 → SC/376; Remo North (Ogun) typed SC/941 → SC/741.
- **Misspelled names**: "Ademawa", "Deltal" and "Nassarawa" in senatorial district names (→ Adamawa, Delta,
  Nasarawa); "Ugwuna Agbo L.G.A" → Ugwunagbo; two Ogun names missing a closing bracket. INEC's spelling stays an alias.
- **14 suspected ward mislinks**, kept as INEC has them but marked `unverified_fields: state_constituency`:
  each is a ward whose state constituency lies, for all its other wards, in a different federal
  constituency, and in most cases a ward of the same name exists in the neighbouring LGA (for example the
  "Tarauni" ward of Gabasawa LGA is linked to the Tarauni constituency, and the "Tarauni" ward of Tarauni LGA
  to Gabasawa). Wards: Umuhu/Ezechi and Umuhu (Abia); Ten (Calabar Municipal); Tarauni ×2, Goron Dutse ×2 and
  Falgore (Kano); Takware (Kebbi); Oji-Aji ×2 (Kogi); Port Harcourt Township and Rumuwoji (One) (Rivers).
- **Real splits, not errors**: Surulere, Lagos Island, Mushin and Oshodi/Isolo (Lagos) and Port Harcourt
  (Rivers) are each split between two federal constituencies; Obingwa/Ugwunagbo/Osisioma (Abia) and
  Gezawa/Gabasawa (Kano) federal constituencies span two senatorial districts; and the Boripe/Boluwaduro
  state constituency (Osun) crosses a federal constituency boundary.
- **UN COD-AB senatorial districts differ from INEC for 10 LGAs**: Osisioma Ngwa, Kaga, Biase, Kajuru, Kauru,
  Jega, Karaye, Offa, Damaturu and Talata Mafara. INEC, which runs the elections, is followed.

### Constitution (government-hosted transcription)
- Typing errors ("Tqngaza", "Ogbmosho", "Matazuu") and missing commas merge or split LGAs ("Kaura, Namoda"), so a naive parse finds 764 of 768 LGAs. Used for capitals and aliases, not as the master list.

### NCC documents (phone numbering)
- The area code page lists **Benin as 053 and Warri as 052**; the National Numbering Plan has
  **Benin 052 and Warri 053**. Both codes are valid either way; the centre name for these two codes is
  marked `unverified`.
- Numbering Plan rows 306 and 308 (Vezeti Services, access codes 887 and 889) give the range
  888 0000–888 9999, which belongs to access code 888; they are excluded.
- The block 9301 0000–9301 4999 (Abuja) is listed twice, as "Nationwave Telecom Nig. Limited" and
  "Nationwaves Telcom Nigeria Limited"; it is kept once.
- Row 255 (MTN, 0704 7xx) says 3,000,000 lines for a range of 1,000,000 numbers; the range is kept.
- The 2022 plan allocates 0702 6xx xxxx to MTN (former Visafone), but the 2023 mobile table does not list
  it. A mobile number is accepted if either document allocates its block, so real numbers are not rejected.

### Payment providers' bank lists
- **Paystack gives code 51253 to two different microfinance banks** (Stellas MFB and YCT MFB). With one source we cannot tell which is right, so the code is left empty for both.
- Paystack's `code` mixes CBN codes, NIP codes and its own codes ("MFB50094", "035A" for ALAT by Wema, 3-digit codes for microfinance banks). Only codes whose format fits the institution's type are used; 114 Paystack entries were not used.
- "Access Bank (Diamond)" carries **063**, Diamond Bank's old code. Diamond Bank is kept as a `merged` institution (into Access, 2019-04-01); old 063 accounts still route to Access.
- Monnify still lists **Diamond** and **Heritage** banks. Status therefore comes only from the CBN register (Heritage: licence revoked 2024-06-03, CBN press release).

## Known gaps (help wanted)

1. **Bank codes for most microfinance, mortgage and finance institutions.** Only 99 of 796 microfinance banks have a CBN code, and most are single-source. NIBSS does not publish its NIP institution list. Contributions with a NIBSS or CBN document are very welcome.
2. **NIP codes** are confirmed by two sources for only one institution. They are flagged `unverified`.
3. **LGA headquarters**: 145 LGAs have none, and 623 come only from the UN dataset, which has known errors. Official state government sources are needed.
4. **State creation dates** come from one news source and are ambiguous for states that were split or renamed. A gazette or decree reference is needed for each.
5. **State nicknames/slogans** ("Centre of Excellence"...) are not included yet: no authoritative list was found, and slogans change between administrations.
6. **Bank websites and full merger history** (beyond Diamond and Heritage) are not included yet.
7. **Postcodes**: NIPOST's 11-character digital postcodes are only available through a gated API with no open licence; no redistributable list of the old 6-digit codes was found. naija-data will validate the postcode *format* and link to the official lookup.
8. **Phone prefixes** are as published by the NCC "as at December 2023" (mobile table) and October 2022
   (numbering plan). Prefixes such as 0910, 0914 and 0917–0919 appear in neither document, so numbers using
   them are reported as `unknown_prefix` until the NCC publishes an allocation.
9. **Abia and Delta wards** were not cross-checked against the 2015 directory (files not archived).
10. **Ward boundaries** are not included: the only good dataset (GRID3) is CC BY-SA and covers 24 states.
11. **Vehicle plate LGA codes** (e.g. KJA for Ikeja) are not included. The Road Traffic Regulations 2012 say
    FRSC sets the codes (reg. 39(5)), and FRSC does not publish them; the only full lists online are on
    commercial sites with no stated source. naija-data validates the plate **format** only. A request to
    FRSC is drafted in [docs/requests/frsc-plate-codes.md](../requests/frsc-plate-codes.md).
12. **Government, armed forces, paramilitary and diplomatic plate formats** are not validated: the sample
    plate images in the available copy of the Regulations are missing.
13. **State constituency count.** naija-data has the 990 state constituencies in INEC's list; if INEC
    publishes the 3 further constituencies often quoted (993), they will be added with their source.
14. **Electoral boundaries change.** INEC can review constituencies (Constitution s.73 and s.113); the data is
    from the 2023 general elections and later by-elections in IReV.
