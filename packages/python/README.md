# naija-data (Python)

Accurate, sourced Nigerian reference data: 36 states + FCT, 774 LGAs, 8,809 wards, CBN-licensed
banks with NUBAN validation, and mobile phone helpers. Zero dependencies.

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
ng.lookup_phone("08031234567").network  # 'MTN' (allocation; numbers can be ported)
```

Command line:

```bash
naija lga lagos
naija bank 058
naija nuban 0000014579
naija phone 08031234567
```

Every record carries its `sources` and lists any `unverified_fields`. Full documentation, data
sources and known gaps: https://github.com/asgatcreation/naija-data

Code: MIT. Data: CC BY 4.0 — credit "naija-data by Akanji Oluwaseun Gabriel".
