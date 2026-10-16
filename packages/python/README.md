# naija-data (Python)

Accurate, sourced Nigerian reference data: 36 states + FCT, 774 LGAs, 8,809 wards, CBN-licensed
banks with NUBAN validation, and mobile phone helpers. Zero dependencies.

Website and playground: https://naija-data.asgatcreation.workers.dev · REST API: https://naija-data-api.asgatcreation.workers.dev/v1

```bash
pip install naija-data
```

```python
import naija_data as ng

ng.get_state("lagos").capital           # 'Ikeja'
[l.name for l in ng.lgas("FCT")]       # ['Abaji', 'Abuja Municipal', 'Bwari', ...]
ng.search("lagso")[0].name              # 'Lagos'  (typo-tolerant, knows aliases)
ng.wards("Ikeja", state="Lagos")[0].name  # 'Anifowoshe/Ikeja'

ng.get_bank("058").name                 # 'Guaranty Trust Bank Plc'
ng.is_valid_nuban("0000014579", "011")  # True  (CBN check-digit algorithm)
[b.name for b in ng.banks_for_nuban("0000014579")]  # banks this number could belong to

ng.normalize_phone("0803 123 4567")     # '+2348031234567'
ng.parse_phone("08031234567").network   # 'MTN' (allocation; numbers can be ported)
ng.parse_phone("01 269 1531").area      # 'Lagos' (landlines, 0800 toll-free and 0700 too)
ng.phone_error("0900 123 4567")         # 'reserved' (why a number is invalid)
ng.parse_plate("kja 123 ab").display    # 'KJA-123AB'
```

For Django and DRF fields see [django-naija](https://github.com/asgatcreation/naija-data/tree/main/packages/django).

Command line:

```bash
naija lga lagos
naija bank 058
naija nuban 0000014579
naija phone 08031234567
naija plate DKN 135 3
```

Every record carries its `sources` and lists any `unverified_fields`. Full documentation, data
sources and known gaps: https://github.com/asgatcreation/naija-data

Code: MIT. Data: CC BY 4.0 — credit "naija-data by Akanji Oluwaseun Gabriel".
