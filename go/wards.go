package naija

import "strings"

// Wards returns the wards (INEC registration areas) of an LGA in INEC code order. state may be ""
// unless the LGA name exists in several states.
func Wards(lga, state string) ([]Ward, error) {
	l, err := requireLGA(lga, state)
	if err != nil {
		return nil, err
	}
	loadWards()
	return append([]Ward{}, wardsByLGA[l.Code]...), nil
}

// GetWard finds a ward by its INEC code, e.g. "24-11-01". It returns nil if unknown.
func GetWard(code string) *Ward {
	loadWards()
	c := strings.TrimSpace(code)
	for i := range allWards {
		if allWards[i].Code == c {
			return &allWards[i]
		}
	}
	return nil
}

// SearchWards does a fuzzy search across all 8,809 wards.
func SearchWards(query string, opts SearchOptions) []SearchResult {
	loadWards()
	cands := make([]candidate, len(allWards))
	for i, w := range allWards {
		cands[i] = candidate{"ward", w.Code, w.Name, w.StateCode, append([]string{w.Name}, w.Aliases...)}
	}
	return rank(query, cands, opts)
}
