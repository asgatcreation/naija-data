package naija

import (
	"regexp"
	"sort"
	"strings"
	"unicode"
)

// Nigerian phone numbers: strict validation, number type, normalisation and network lookup.
// Same rules as the Python and JS packages (see packages/python/src/naija_data/phone.py).

// PortingNote explains why a mobile number's network is only a guess.
const PortingNote = "Numbers can be ported between networks, so the prefix shows the network the number " +
	"was first allocated to, not necessarily its network today."

// PhoneTypes lists the number types.
var PhoneTypes = []string{"mobile", "fixed", "toll_free", "non_toll_free"}

// PhoneErrors lists the reasons PhoneError can return.
var PhoneErrors = []string{"empty", "invalid_characters", "not_nigerian", "bad_length", "unknown_prefix",
	"unallocated", "reserved", "unknown_area_code"}

// PhoneNumber describes a valid Nigerian phone number.
type PhoneNumber struct {
	E164      string  `json:"e164"`      // +2348031234567
	Local     string  `json:"local"`     // 08031234567
	National  string  `json:"national"`  // 8031234567
	Type      string  `json:"type"`      // mobile, fixed, toll_free, non_toll_free
	Prefix    string  `json:"prefix"`    // "0803", "0800" or a fixed-line area code ("01")
	Area      *string `json:"area"`      // fixed lines: NCC primary centre
	Network   *string `json:"network"`   // mobile: allocated network; others: allottee
	Allocated bool    `json:"allocated"` // inside an NCC-allocated block
	Note      *string `json:"note"`      // mobile: porting caveat
}

// AreaCode is one of the NCC's geographic (landline) area codes.
type AreaCode struct {
	AreaCode         string   `json:"area_code"`
	PrimaryCentre    string   `json:"primary_centre"`
	NCCZone          string   `json:"ncc_zone"`
	UnverifiedFields []string `json:"unverified_fields"`
}

type mobileBlock struct {
	Prefix     string  `json:"prefix"`
	RangeStart string  `json:"range_start"`
	RangeEnd   string  `json:"range_end"`
	Operator   *string `json:"operator"`
	Status     string  `json:"status"`
}

type planBlock struct {
	NumberType string `json:"number_type"`
	RangeStart string `json:"range_start"`
	RangeEnd   string `json:"range_end"`
	Allottee   string `json:"allottee"`
}

var phoneData struct {
	Mobile    []mobileBlock `json:"mobile"`
	Blocks    []planBlock   `json:"blocks"`
	AreaCodes []AreaCode    `json:"area_codes"`
}

var digitsRe = regexp.MustCompile(`^[0-9]*$`)

func loadPhone() { loadPhoneO.Do(func() { mustLoad("phone", &phoneData) }) }

func strPtr(s string) *string { return &s }

func shortNetwork(allottee string) string {
	low := strings.ToLower(allottee)
	for _, p := range [][2]string{{"mtn", "MTN"}, {"airtel", "Airtel"}, {"glo", "Glo"}, {"9mobile", "9mobile"},
		{"smile", "Smile"}, {"mafab", "MAFAB"}, {"ntel", "nTel"}} {
		if strings.Contains(low, p[0]) {
			return p[1]
		}
	}
	return allottee
}

func inPlan(nsn, numberType string) *planBlock {
	for i := range phoneData.Blocks {
		b := &phoneData.Blocks[i]
		if b.NumberType == numberType && len(b.RangeStart) == len(nsn) && b.RangeStart <= nsn && nsn <= b.RangeEnd {
			return b
		}
	}
	return nil
}

func national(text string) (string, string) {
	s := strings.Map(func(r rune) rune {
		if unicode.IsSpace(r) || strings.ContainsRune("-.()/", r) {
			return -1
		}
		return r
	}, strings.TrimSpace(text))
	if s == "" {
		return "", "empty"
	}
	if strings.HasPrefix(s, "+") {
		s = s[1:]
		if !digitsRe.MatchString(s) {
			return "", "invalid_characters"
		}
		if !strings.HasPrefix(s, "234") {
			return "", "not_nigerian"
		}
	} else if strings.HasPrefix(s, "00") {
		if !digitsRe.MatchString(s) {
			return "", "invalid_characters"
		}
		if !strings.HasPrefix(s, "00234") {
			return "", "not_nigerian"
		}
		s = s[2:]
	}
	if !digitsRe.MatchString(s) {
		return "", "invalid_characters"
	}
	if strings.HasPrefix(s, "2340") { // "+234 (0) 803 ..." with the trunk 0
		s = "234" + s[4:]
	}
	switch {
	case strings.HasPrefix(s, "234") && (len(s) == 11 || len(s) == 13):
		return s[3:], ""
	case strings.HasPrefix(s, "0") && (len(s) == 9 || len(s) == 11):
		return s[1:], ""
	case len(s) == 10 && strings.ContainsRune("789", rune(s[0])):
		return s, ""
	}
	return "", "bad_length"
}

func classify(nsn string) (*PhoneNumber, string) {
	loadPhone()
	p := &PhoneNumber{E164: "+234" + nsn, Local: "0" + nsn, National: nsn}
	switch len(nsn) {
	case 10:
		lead := nsn[:3]
		if lead == "900" {
			return nil, "reserved"
		}
		if lead == "800" || lead == "700" {
			p.Type, p.Prefix = "non_toll_free", "0"+lead
			if lead == "800" {
				p.Type = "toll_free"
			}
			if b := inPlan(nsn, p.Type); b != nil {
				p.Network, p.Allocated = strPtr(b.Allottee), true
			}
			return p, ""
		}
		prefix, subscriber := "0"+lead, nsn[3:]
		inTable := false
		var hit *mobileBlock
		for i := range phoneData.Mobile {
			b := &phoneData.Mobile[i]
			if b.Prefix != prefix {
				continue
			}
			inTable = true
			if hit == nil && b.RangeStart <= subscriber && subscriber <= b.RangeEnd {
				hit = b
			}
		}
		if hit != nil && hit.Status == "allocated" {
			p.Network = hit.Operator
		} else {
			plan := inPlan(nsn, "mobile")
			if plan == nil {
				if inTable {
					return nil, "unallocated"
				}
				return nil, "unknown_prefix"
			}
			p.Network = strPtr(shortNetwork(plan.Allottee))
		}
		p.Type, p.Prefix, p.Allocated, p.Note = "mobile", prefix, true, strPtr(PortingNote)
		return p, ""
	case 8:
		code := "0" + nsn[:2]
		if strings.ContainsRune("129", rune(nsn[0])) {
			code = "0" + nsn[:1]
		}
		for _, a := range phoneData.AreaCodes {
			if a.AreaCode == code {
				p.Type, p.Prefix, p.Area = "fixed", code, strPtr(a.PrimaryCentre)
				if b := inPlan(nsn, "fixed"); b != nil {
					p.Network, p.Allocated = strPtr(b.Allottee), true
				}
				return p, ""
			}
		}
		return nil, "unknown_area_code"
	}
	return nil, "bad_length"
}

// PhoneError returns why text is not a valid Nigerian phone number (one of PhoneErrors), or "" if
// it is valid.
func PhoneError(text string) string {
	nsn, err := national(text)
	if err != "" {
		return err
	}
	_, err = classify(nsn)
	return err
}

// ParsePhone validates and describes a Nigerian phone number (mobile, fixed line, 0800 toll-free or
// 0700). It returns nil if the number is not valid.
func ParsePhone(text string) *PhoneNumber {
	nsn, err := national(text)
	if err != "" {
		return nil
	}
	p, _ := classify(nsn)
	return p
}

// IsValidPhone reports whether text is a valid Nigerian number, optionally only of the given types
// (nil or empty means any type).
func IsValidPhone(text string, types []string) bool {
	p := ParsePhone(text)
	return p != nil && (len(types) == 0 || contains(types, p.Type))
}

// NormalizePhone returns the number in international (E.164) form, "+2348031234567". ok is false
// if the number is not valid.
func NormalizePhone(text string) (e164 string, ok bool) {
	if p := ParsePhone(text); p != nil {
		return p.E164, true
	}
	return "", false
}

// ToLocal returns the number in local form, "08031234567". ok is false if the number is not valid.
func ToLocal(text string) (local string, ok bool) {
	if p := ParsePhone(text); p != nil {
		return p.Local, true
	}
	return "", false
}

// Networks returns the names of networks with allocated mobile prefixes.
func Networks() []string {
	loadPhone()
	set := map[string]bool{}
	for _, b := range phoneData.Mobile {
		if b.Operator != nil {
			set[*b.Operator] = true
		}
	}
	return sortedKeys(set)
}

// Prefixes returns the mobile prefixes ("0803", ...) allocated to a network (case-insensitive), or
// all prefixes when network is "".
func Prefixes(network string) []string {
	loadPhone()
	want := strings.ToLower(network)
	set := map[string]bool{}
	for _, b := range phoneData.Mobile {
		op := ""
		if b.Operator != nil {
			op = strings.ToLower(*b.Operator)
		}
		if want == "" || op == want {
			set[b.Prefix] = true
		}
	}
	return sortedKeys(set)
}

// AreaCodes returns the NCC's 56 geographic (landline) area codes.
func AreaCodes() []AreaCode {
	loadPhone()
	return append([]AreaCode(nil), phoneData.AreaCodes...)
}

func sortedKeys(set map[string]bool) []string {
	out := make([]string, 0, len(set))
	for k := range set {
		out = append(out, k)
	}
	sort.Strings(out)
	return out
}
