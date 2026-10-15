package naija

import "strings"

// Text matching shared by lookups and fuzzy search. Same rules as the Python and JS packages
// (see fixtures/README.md); only integer arithmetic is used so scores are identical everywhere.

// Norm returns the comparison key: "Akwa-Ibom State" -> "akwaibom", "Ikeja LGA" -> "ikeja".
func Norm(text string) string {
	var b strings.Builder
	for _, r := range text {
		switch {
		case r < 0x80:
			b.WriteRune(r)
		default:
			b.WriteString(foldTable[r]) // accents and compatibility forms; others are dropped
		}
	}
	ascii := strings.ReplaceAll(strings.ToLower(b.String()), "&", " and ")
	words := strings.FieldsFunc(ascii, func(r rune) bool {
		return !(r >= 'a' && r <= 'z' || r >= '0' && r <= '9')
	})
	for len(words) > 1 && (words[len(words)-1] == "state" || words[len(words)-1] == "lga") {
		words = words[:len(words)-1]
	}
	return strings.Join(words, "")
}

// distance is the optimal string alignment distance between two ASCII strings.
func distance(a, b string) int {
	if a == b {
		return 0
	}
	la, lb := len(a), len(b)
	if la == 0 || lb == 0 {
		return max(la, lb)
	}
	prev2 := make([]int, lb+1)
	prev := make([]int, lb+1)
	for j := range prev {
		prev[j] = j
	}
	for i := 1; i <= la; i++ {
		cur := make([]int, lb+1)
		cur[0] = i
		for j := 1; j <= lb; j++ {
			cost := 1
			if a[i-1] == b[j-1] {
				cost = 0
			}
			cur[j] = min(prev[j]+1, cur[j-1]+1, prev[j-1]+cost)
			if i > 1 && j > 1 && a[i-1] == b[j-2] && a[i-2] == b[j-1] {
				cur[j] = min(cur[j], prev2[j-2]+1)
			}
		}
		prev2, prev = prev, cur
	}
	return prev[lb]
}

// score is the similarity of two normalised strings, 0..1000.
func score(query, term string) int {
	if query == "" || term == "" {
		return 0
	}
	if query == term {
		return 1000
	}
	if len(query) >= 2 && strings.HasPrefix(term, query) {
		return 900 + (99*len(query))/len(term)
	}
	longest := max(len(query), len(term))
	return ((longest - distance(query, term)) * 800) / longest
}
