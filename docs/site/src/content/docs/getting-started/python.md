---
title: Python
description: Install and use naija-data in Python.
---

Python 3.9 or newer. No dependencies.

```bash
pip install naija-data
```

## States, LGAs and wards

```python
import naija_data as ng

lagos = ng.get_state("lagos")          # also "LA", "NG-LA", "24", "Lagos State"
lagos.capital, lagos.zone              # ('Ikeja', 'South-West')
ng.get_state("Abuja").name             # 'Federal Capital Territory'

[l.name for l in ng.lgas("FCT")]       # ['Abaji', 'Abuja Municipal', 'Bwari', ...]
ng.get_lga("Surulere")                 # None: Lagos and Oyo both have one
ng.get_lga("Surulere", state="Oyo")    # LGA(code='NG031033', ...)
ng.find_lgas("Surulere")               # both

ng.wards("Ikeja", state="Lagos")[0].name   # 'Anifowoshe/Ikeja'
```

Records are frozen dataclasses with the dataset's field names; `record.to_dict()` gives a plain dict.

## Fuzzy search

```python
ng.search("lagso")[0].name             # 'Lagos'
ng.search("yenegoa")[0].name           # 'Yenagoa' (old spelling)
ng.search("Ọ̀yọ́")[0].name               # 'Oyo'
ng.search_wards("anifowoshe")[0].code  # '24-11-01'
```

## Banks and NUBAN

```python
ng.get_bank("058").name                # 'Guaranty Trust Bank Plc' (also "GTB", "gtbank", "000013")
ng.banks("microfinance")               # active microfinance banks
ng.is_valid_nuban("0000014579", "011") # True (CBN check-digit algorithm)
ng.banks_for_nuban("0000014579")       # banks this number could belong to
```

A valid check digit does not prove an account exists. Use it to catch typos before calling a
name-enquiry service.

## Phone numbers

```python
p = ng.parse_phone("0803 123 4567")
p.e164, p.type, p.network              # ('+2348031234567', 'mobile', 'MTN')
ng.parse_phone("01 269 1531").area     # 'Lagos'
ng.phone_error("0900 123 4567")        # 'reserved'
ng.is_valid_phone("01 269 1531", types=["mobile"])  # False
```

The network comes from the NCC allocation tables. Numbers can be ported, so it is the network the number
was first allocated to.

## Plates

```python
ng.parse_plate("kja 123 ab").display   # 'KJA-123AB'
ng.parse_plate("DKN 135 3").state_code # 'KN' (dealer plate)
ng.plate_error("AB-123-CD")            # 'unknown_format'
```

## Command line

```bash
naija lga lagos
naija bank 058
naija nuban 0000014579
naija phone 08031234567
naija plate KJA 123 AB
```

Add `--json` to any command for machine-readable output.
