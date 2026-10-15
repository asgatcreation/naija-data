package naija_test

import (
	"fmt"

	naija "github.com/asgatcreation/naija-data/go"
)

func ExampleGetState() {
	s := naija.GetState("lagos")
	fmt.Println(s.Name, s.Capital, s.ISOCode)
	fmt.Println(naija.GetState("Abuja").Name)
	// Output:
	// Lagos Ikeja NG-LA
	// Federal Capital Territory
}

func ExampleLGAs() {
	lgas, _ := naija.LGAs("FCT")
	for _, l := range lgas {
		fmt.Println(l.Name)
	}
	// Output:
	// Abaji
	// Abuja Municipal
	// Bwari
	// Gwagwalada
	// Kuje
	// Kwali
}

func ExampleSearch() {
	r := naija.Search("lagso", naija.SearchOptions{Limit: 1})
	fmt.Println(r[0].Name, r[0].Kind)
	// Output: Lagos state
}

func ExampleIsValidNUBAN() {
	ok, _ := naija.IsValidNUBAN("0000014579", "011") // example from the CBN NUBAN standard
	fmt.Println(ok)
	// Output: true
}

func ExampleLookupPhone() {
	info := naija.LookupPhone("0803 123 4567")
	fmt.Println(info.E164, *info.Network)
	// Output: +2348031234567 MTN
}

func ExampleWards() {
	wards, _ := naija.Wards("Ikeja", "Lagos")
	fmt.Println(len(wards), wards[0].Name)
	// Output: 10 Anifowoshe/Ikeja
}
