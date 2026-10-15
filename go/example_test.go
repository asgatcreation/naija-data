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

func ExampleParsePhone() {
	mobile := naija.ParsePhone("0803 123 4567")
	fmt.Println(mobile.E164, mobile.Type, *mobile.Network)
	lagos := naija.ParsePhone("01 269 1531")
	fmt.Println(lagos.Type, *lagos.Area)
	fmt.Println(naija.PhoneError("0900 123 4567"))
	// Output:
	// +2348031234567 mobile MTN
	// fixed Lagos
	// reserved
}

func ExampleParsePlate() {
	fmt.Println(naija.ParsePlate("kja 123 ab").Display)
	dealer := naija.ParsePlate("DKN 135 3")
	fmt.Println(dealer.Format, *dealer.StateCode)
	// Output:
	// KJA-123AB
	// dealer KN
}

func ExampleWards() {
	wards, _ := naija.Wards("Ikeja", "Lagos")
	fmt.Println(len(wards), wards[0].Name)
	// Output: 10 Anifowoshe/Ikeja
}
