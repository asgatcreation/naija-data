---
title: Go
description: Use naija-data from Go.
---

Go 1.21 or newer. The data is embedded with `go:embed`; the module has no dependencies.

```bash
go get github.com/asgatcreation/naija-data/go
```

```go
import naija "github.com/asgatcreation/naija-data/go"

s := naija.GetState("lagos")                   // *State, nil if unknown
fmt.Println(s.Capital)                         // Ikeja

lgas, err := naija.LGAs("FCT")                 // "" for all 774
lga, err := naija.GetLGA("Surulere", "Oyo")    // state "" = any state; ambiguous names return nil
wards, err := naija.Wards("Ikeja", "Lagos")

results := naija.Search("lagso", naija.SearchOptions{Limit: 5})
wardHits := naija.SearchWards("anifowoshe", naija.SearchOptions{})

bank := naija.GetBank("058")                   // *Bank
ok, err := naija.IsValidNUBAN("0000014579", "011")
candidates := naija.BanksForNUBAN("0000014579")

p := naija.ParsePhone("0803 123 4567")         // *PhoneNumber, nil if invalid
reason := naija.PhoneError("0900 123 4567")    // "reserved" ("" when valid)

plate := naija.ParsePlate("kja 123 ab")        // plate.Display == "KJA-123AB"
```

Struct fields marshal to JSON with the dataset's field names (`iso_code`, `cbn_code`), identical to the
Python and JavaScript packages and the API. See the full API on
[pkg.go.dev](https://pkg.go.dev/github.com/asgatcreation/naija-data/go).
