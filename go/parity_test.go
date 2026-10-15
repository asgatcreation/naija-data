package naija

import (
	"encoding/json"
	"fmt"
	"os"
	"reflect"
	"strings"
	"testing"
)

// Runs the shared parity cases (fixtures/parity.json) against the Go module.

type parityCase struct {
	Fn     string `json:"fn"`
	Args   []any  `json:"args"`
	Expect any    `json:"expect"`
}

var errResult = map[string]any{"error": true}

func str(v any) string {
	if v == nil {
		return ""
	}
	return v.(string)
}

// asJSON round-trips a value through JSON so it compares like the fixture's decoded JSON.
func asJSON(v any) any {
	raw, err := json.Marshal(v)
	if err != nil {
		panic(err)
	}
	var out any
	if err := json.Unmarshal(raw, &out); err != nil {
		panic(err)
	}
	return out
}

func codes[T any](xs []T, get func(T) string) []string {
	out := make([]string, len(xs))
	for i, x := range xs {
		out[i] = get(x)
	}
	return out
}

func lgaCode(l LGA) string   { return l.Code }
func wardCode(w Ward) string { return w.Code }
func bankID(b Bank) string   { return b.ID }

func runCase(c parityCase) any {
	a := c.Args
	switch c.Fn {
	case "states":
		return codes(States(), func(s State) string { return s.Code })
	case "get_state":
		if s := GetState(str(a[0])); s != nil {
			return s.Code
		}
		return nil
	case "state_record":
		return GetState(str(a[0]))
	case "lgas":
		ls, err := LGAs(str(a[0]))
		if err != nil {
			return errResult
		}
		return codes(ls, lgaCode)
	case "find_lgas":
		return codes(FindLGAs(str(a[0])), lgaCode)
	case "get_lga":
		state := ""
		if len(a) > 1 {
			state = str(a[1])
		}
		l, err := GetLGA(str(a[0]), state)
		if err != nil {
			return errResult
		}
		if l == nil {
			return nil
		}
		return l.Code
	case "lga_record":
		l, _ := GetLGA(str(a[0]), "")
		return l
	case "wards":
		ws, err := Wards(str(a[0]), str(a[1]))
		if err != nil {
			return errResult
		}
		return codes(ws, wardCode)
	case "get_ward":
		if w := GetWard(str(a[0])); w != nil {
			return w
		}
		return nil
	case "search":
		kinds := a[1].([]any)
		opts := SearchOptions{Limit: int(a[2].(float64))}
		var rs []SearchResult
		if len(kinds) == 1 && kinds[0] == "ward" {
			rs = SearchWards(str(a[0]), opts)
		} else {
			rs = Search(str(a[0]), opts)
		}
		out := make([][]any, len(rs))
		for i, r := range rs {
			out[i] = []any{r.Kind, r.Code, r.Score, r.Matched}
		}
		return out
	case "get_bank":
		if b := GetBank(str(a[0])); b != nil {
			return b.ID
		}
		return nil
	case "bank_record":
		return GetBank(str(a[0]))
	case "banks":
		bs, err := Banks(str(a[0]), a[1].(bool))
		if err != nil {
			return errResult
		}
		return codes(bs, bankID)
	case "find_banks":
		return codes(FindBanks(str(a[0]), 10), bankID)
	case "nuban_check_digit":
		d, err := NUBANCheckDigit(str(a[0]), str(a[1]))
		if err != nil {
			return errResult
		}
		return d
	case "is_valid_nuban":
		ok, err := IsValidNUBAN(str(a[0]), str(a[1]))
		if err != nil {
			return errResult
		}
		return ok
	case "banks_for_nuban":
		return codes(BanksForNUBAN(str(a[0])), bankID)
	case "normalize_phone":
		if s, ok := NormalizePhone(str(a[0])); ok {
			return s
		}
		return nil
	case "to_local":
		if s, ok := ToLocal(str(a[0])); ok {
			return s
		}
		return nil
	case "lookup_phone":
		info := LookupPhone(str(a[0]))
		if info == nil {
			return nil
		}
		m := asJSON(info).(map[string]any)
		delete(m, "note")
		return m
	case "prefixes":
		return Prefixes(str(a[0]))
	}
	panic("unknown parity fn " + c.Fn)
}

func TestParity(t *testing.T) {
	raw, err := os.ReadFile("../fixtures/parity.json")
	if err != nil {
		t.Skip("parity fixtures only exist in the repository")
	}
	var fx struct {
		DataVersion string       `json:"data_version"`
		Cases       []parityCase `json:"cases"`
	}
	if err := json.Unmarshal(raw, &fx); err != nil {
		t.Fatal(err)
	}
	if fx.DataVersion != Meta().DataVersion {
		t.Fatalf("fixture data_version %s != packaged %s", fx.DataVersion, Meta().DataVersion)
	}
	var failures []string
	for _, c := range fx.Cases {
		got := asJSON(runCase(c))
		if !reflect.DeepEqual(got, c.Expect) {
			args, _ := json.Marshal(c.Args)
			want, _ := json.Marshal(c.Expect)
			gotJSON, _ := json.Marshal(got)
			failures = append(failures, fmt.Sprintf("%s%s: expected %s, got %s", c.Fn, args, want, gotJSON))
		}
	}
	if len(failures) > 0 {
		n := min(len(failures), 15)
		t.Fatalf("%d of %d parity cases failed:\n%s", len(failures), len(fx.Cases), strings.Join(failures[:n], "\n"))
	}
}
