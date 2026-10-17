package naija

import (
	"fmt"
	"regexp"
	"sort"
	"strings"
)

// ConstituencyKinds lists the kinds of electoral unit, in the order results use.
var ConstituencyKinds = []string{"senatorial_district", "federal_constituency", "state_constituency"}

var spaceRe = regexp.MustCompile(`\s`)

func kindIndex(kind string) int {
	for i, k := range ConstituencyKinds {
		if k == kind {
			return i
		}
	}
	return -1
}

// Constituencies returns electoral units of one kind (kind == "" for all), optionally in one state
// (state == "" for all), in INEC code order.
func Constituencies(kind, state string) ([]Constituency, error) {
	if kind != "" && kindIndex(kind) < 0 {
		return nil, fmt.Errorf("naija: unknown constituency kind %q (use one of %s)", kind, strings.Join(ConstituencyKinds, ", "))
	}
	code := ""
	if state != "" {
		s, err := requireState(state)
		if err != nil {
			return nil, err
		}
		code = s.Code
	}
	loadUnits()
	out := []Constituency{}
	for _, u := range allUnits {
		if (kind == "" || u.Kind == kind) && (code == "" || u.StateCode == code) {
			out = append(out, u)
		}
	}
	return out, nil
}

// SenatorialDistricts returns the 109 senatorial districts (3 per state, 1 for the FCT), or those of one state.
func SenatorialDistricts(state string) ([]Constituency, error) {
	return Constituencies("senatorial_district", state)
}

// FederalConstituencies returns the 360 federal constituencies (House of Representatives seats), or those of one state.
func FederalConstituencies(state string) ([]Constituency, error) {
	return Constituencies("federal_constituency", state)
}

// StateConstituencies returns the 990 state constituencies (House of Assembly seats), or those of
// one state. The FCT has none: it has no House of Assembly.
func StateConstituencies(state string) ([]Constituency, error) {
	return Constituencies("state_constituency", state)
}

// GetConstituency finds a unit by code ("SD001", "FC001", "SC001") or INEC code ("FC/001/AB").
// It returns nil if unknown.
func GetConstituency(code string) *Constituency {
	loadUnits()
	c := strings.ToUpper(spaceRe.ReplaceAllString(code, ""))
	for i := range allUnits {
		if allUnits[i].Code == c || allUnits[i].INECCode == c {
			return &allUnits[i]
		}
	}
	return nil
}

// FindConstituencies returns every unit whose name or alias matches exactly (ignoring case and
// punctuation), e.g. "Lagos West". kind and state may be "".
func FindConstituencies(name, kind, state string) ([]Constituency, error) {
	units, err := Constituencies(kind, state)
	if err != nil {
		return nil, err
	}
	q := Norm(name)
	out := []Constituency{}
	for _, u := range units {
		for _, t := range append([]string{u.Name, u.Slug}, u.Aliases...) {
			if Norm(t) == q {
				out = append(out, u)
				break
			}
		}
	}
	return out, nil
}

func requireConstituency(code string) (*Constituency, error) {
	u := GetConstituency(code)
	if u == nil {
		return nil, fmt.Errorf("naija: unknown constituency %q", code)
	}
	return u, nil
}

// ConstituencyLGAs returns the LGAs a unit covers in full or in part, sorted by name. A few LGAs
// are split between constituencies (e.g. Surulere I and II in Lagos): use ConstituencyWards for
// the exact area.
func ConstituencyLGAs(code string) ([]LGA, error) {
	u, err := requireConstituency(code)
	if err != nil {
		return nil, err
	}
	in := map[string]bool{}
	for _, c := range u.LGACodes {
		in[c] = true
	}
	all, _ := LGAs("")
	out := []LGA{}
	for _, l := range all {
		if in[l.Code] {
			out = append(out, l)
		}
	}
	return out, nil
}

// ConstituencyWards returns the wards (INEC registration areas) that make up a unit, in INEC code order.
func ConstituencyWards(code string) ([]Ward, error) {
	u, err := requireConstituency(code)
	if err != nil {
		return nil, err
	}
	loadWards()
	out := []Ward{}
	for _, w := range allWards {
		var c string
		switch u.Kind {
		case "senatorial_district":
			c = w.SenatorialDistrict
		case "federal_constituency":
			c = w.FederalConstituency
		default:
			if w.StateConstituency != nil {
				c = *w.StateConstituency
			}
		}
		if c == u.Code {
			out = append(out, w)
		}
	}
	return out, nil
}

// LGAConstituencies returns the senatorial district, federal constituencies and state
// constituencies an LGA lies in (more than one when the LGA is split), ordered by kind then code.
// state may be "" unless the LGA name exists in several states.
func LGAConstituencies(lga, state string) ([]Constituency, error) {
	l, err := requireLGA(lga, state)
	if err != nil {
		return nil, err
	}
	loadUnits()
	out := []Constituency{}
	for _, u := range allUnits {
		for _, c := range u.LGACodes {
			if c == l.Code {
				out = append(out, u)
				break
			}
		}
	}
	sort.SliceStable(out, func(i, j int) bool {
		if ki, kj := kindIndex(out[i].Kind), kindIndex(out[j].Kind); ki != kj {
			return ki < kj
		}
		return out[i].Code < out[j].Code
	})
	return out, nil
}
