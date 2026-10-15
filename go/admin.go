package naija

import (
	"fmt"
	"regexp"
	"sort"
	"strings"
)

var (
	pcodeRe   = regexp.MustCompile(`(?i)^ng\d{6}$`)
	inecLGARe = regexp.MustCompile(`^\d{2}-\d{2}$`)
)

var kindOrder = map[string]int{"state": 0, "lga": 1, "ward": 2}

// States returns all 36 states and the FCT, sorted by name.
func States() []State {
	admin()
	return append([]State(nil), allStates...)
}

// GetState finds a state by ISO code ("LA", "NG-LA"), INEC code ("24"), P-code ("NG025"), slug,
// name or alias ("Lagos", "lagos state", "Abuja", "FCT", "Akwa-Ibom"). It returns nil if unknown.
func GetState(query string) *State {
	admin()
	q := strings.TrimSpace(query)
	up := strings.ToUpper(q)
	for i := range allStates {
		s := &allStates[i]
		if up == s.Code || up == s.ISOCode || up == s.PCode || q == s.INECCode {
			return s
		}
	}
	key := Norm(q)
	for i := range allStates {
		s := &allStates[i]
		for _, t := range append([]string{s.Name, s.Slug}, s.Aliases...) {
			if Norm(t) == key {
				return s
			}
		}
	}
	return nil
}

func requireState(state string) (*State, error) {
	s := GetState(state)
	if s == nil {
		return nil, fmt.Errorf("naija: unknown state %q", state)
	}
	return s, nil
}

// LGAs returns all 774 LGAs (state == "") or the LGAs of one state, sorted by name.
func LGAs(state string) ([]LGA, error) {
	admin()
	if state == "" {
		out := append([]LGA(nil), allLGAs...)
		sort.SliceStable(out, func(i, j int) bool {
			if out[i].Name != out[j].Name {
				return out[i].Name < out[j].Name
			}
			return out[i].Code < out[j].Code
		})
		return out, nil
	}
	s, err := requireState(state)
	if err != nil {
		return nil, err
	}
	var out []LGA
	for _, l := range allLGAs {
		if l.StateCode == s.Code {
			out = append(out, l)
		}
	}
	return out, nil
}

// FindLGAs returns every LGA whose name or alias matches exactly (ignoring case and punctuation).
// Several states share LGA names, e.g. "Surulere" (Lagos and Oyo).
func FindLGAs(name string) []LGA {
	admin()
	key := Norm(name)
	out := []LGA{}
	for _, l := range allLGAs {
		for _, t := range append([]string{l.Name, l.Slug}, l.Aliases...) {
			if Norm(t) == key {
				out = append(out, l)
				break
			}
		}
	}
	return out
}

// GetLGA finds an LGA by P-code ("NG025011"), INEC code ("24-11"), or name/alias. A name shared by
// LGAs in several states returns nil unless state is given (state == "" means any state).
func GetLGA(query, state string) (*LGA, error) {
	admin()
	q := strings.TrimSpace(query)
	if pcodeRe.MatchString(q) {
		return findLGA(func(l LGA) bool { return l.Code == strings.ToUpper(q) }), nil
	}
	if inecLGARe.MatchString(q) {
		return findLGA(func(l LGA) bool { return l.INECCode == q }), nil
	}
	matches := FindLGAs(q)
	if state != "" {
		s, err := requireState(state)
		if err != nil {
			return nil, err
		}
		var kept []LGA
		for _, l := range matches {
			if l.StateCode == s.Code {
				kept = append(kept, l)
			}
		}
		matches = kept
	}
	if len(matches) == 1 {
		return &matches[0], nil
	}
	return nil, nil
}

func findLGA(pred func(LGA) bool) *LGA {
	for i := range allLGAs {
		if pred(allLGAs[i]) {
			return &allLGAs[i]
		}
	}
	return nil
}

func requireLGA(lga, state string) (*LGA, error) {
	l, err := GetLGA(lga, state)
	if err != nil {
		return nil, err
	}
	if l == nil {
		return nil, fmt.Errorf("naija: unknown or ambiguous LGA %q", lga)
	}
	return l, nil
}

// SearchOptions controls Search and SearchWards. Zero values mean Limit 10 and MinScore 600.
type SearchOptions struct {
	Limit    int
	MinScore int
}

type candidate struct {
	kind, code, name, stateCode string
	terms                       []string
}

func rank(query string, cands []candidate, opts SearchOptions) []SearchResult {
	limit, minScore := opts.Limit, opts.MinScore
	if limit == 0 {
		limit = 10
	}
	if minScore == 0 {
		minScore = 600
	}
	q := Norm(query)
	results := []SearchResult{}
	if q == "" {
		return results
	}
	for _, c := range cands {
		best, matched := 0, ""
		for _, t := range c.terms {
			if s := score(q, Norm(t)); s > best {
				best, matched = s, t
			}
		}
		if best >= minScore {
			results = append(results, SearchResult{c.kind, c.code, c.name, c.stateCode, best, matched})
		}
	}
	sort.SliceStable(results, func(i, j int) bool {
		a, b := results[i], results[j]
		if a.Score != b.Score {
			return a.Score > b.Score
		}
		if kindOrder[a.Kind] != kindOrder[b.Kind] {
			return kindOrder[a.Kind] < kindOrder[b.Kind]
		}
		if a.Name != b.Name {
			return a.Name < b.Name
		}
		return a.Code < b.Code
	})
	if len(results) > limit {
		results = results[:limit]
	}
	return results
}

// Search does a fuzzy search across states and LGAs. It handles case, punctuation, aliases and
// typos ("lagso", "akwa-ibom", "abuja", "ikeja lga"). Use SearchWards for wards.
func Search(query string, opts SearchOptions) []SearchResult {
	admin()
	cands := make([]candidate, 0, len(allStates)+len(allLGAs))
	for _, s := range allStates {
		cands = append(cands, candidate{"state", s.Code, s.Name, s.Code, append([]string{s.Name, s.Code}, s.Aliases...)})
	}
	for _, l := range allLGAs {
		cands = append(cands, candidate{"lga", l.Code, l.Name, l.StateCode, append([]string{l.Name}, l.Aliases...)})
	}
	return rank(query, cands, opts)
}
