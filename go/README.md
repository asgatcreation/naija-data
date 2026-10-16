# naija-data (Go)

Website and playground: https://naija-data.asgatcreation.workers.dev · REST API: https://naija-data-api.asgatcreation.workers.dev/v1

```bash
go get github.com/asgatcreation/naija-data/go
```

```go
import naija "github.com/asgatcreation/naija-data/go"

naija.GetState("lagos").Capital                        // "Ikeja"
lgas, _ := naija.LGAs("FCT")                           // 6 area councils
naija.Search("lagso", naija.SearchOptions{})[0].Name   // "Lagos"
wards, _ := naija.Wards("Ikeja", "Lagos")              // 10 wards
ok, _ := naija.IsValidNUBAN("0000014579", "011")       // true
naija.ParsePhone("0803 123 4567").E164                 // "+2348031234567"
naija.PhoneError("0900 123 4567")                      // "reserved"
naija.ParsePlate("kja 123 ab").Display                 // "KJA-123AB"
```

The data is embedded with `go:embed`; the module has no dependencies. Same API and results as the
Python and JavaScript packages (checked by shared parity tests). See the
[main README](https://github.com/asgatcreation/naija-data) for sources and known gaps.

Code: MIT. Data: CC BY 4.0 — credit "naija-data by Akanji Oluwaseun Gabriel".
