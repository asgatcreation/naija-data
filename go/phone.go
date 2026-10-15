package naija

import (
	"regexp"
	"sort"
	"strings"
	"unicode"
)

// PortingNote explains why the network is only a guess.
const PortingNote = "Numbers can be ported between networks, so the prefix shows the network the number " +
	"was first allocated to, not necessarily its network today."

var mobileRe = regexp.MustCompile(`^[789][01]\d{8}$`)

// national returns the 10-digit national number (without the leading 0), or "".
func national(text string) string {
	s := strings.Map(func(r rune) rune {
		if unicode.IsSpace(r) || r == '-' || r == '.' || r == '(' || r == ')' {
			return -1
		}
		return r
	}, strings.TrimSpace(text))
	if strings.HasPrefix(s, "+") {
		s = s[1:]
		if !strings.HasPrefix(s, "234") {
			return ""
		}
	}
	if strings.HasPrefix(s, "2340") { // "+234 (0) 803 ..." written with the trunk 0
		s = "234" + s[4:]
	}
	if strings.HasPrefix(s, "234") && len(s) == 13 {
		s = s[3:]
	} else if strings.HasPrefix(s, "0") && len(s) == 11 {
		s = s[1:]
	}
	if mobileRe.MatchString(s) {
		return s
	}
	return ""
}

// NormalizePhone returns the number in international (E.164) form, "+2348031234567". ok is false
// if it is not a well-formed Nigerian mobile number.
func NormalizePhone(text string) (e164 string, ok bool) {
	if n := national(text); n != "" {
		return "+234" + n, true
	}
	return "", false
}

// ToLocal returns the number in local form, "08031234567".
func ToLocal(text string) (local string, ok bool) {
	if n := national(text); n != "" {
		return "0" + n, true
	}
	return "", false
}

// LookupPhone normalises a mobile number and looks up the network its number block was allocated
// to. Because of number portability the network is a guess (see PortingNote). It returns nil if
// the number is not a well-formed Nigerian mobile number.
func LookupPhone(text string) *PhoneInfo {
	n := national(text)
	if n == "" {
		return nil
	}
	loadPhone()
	prefix, subscriber := "0"+n[:3], n[3:]
	info := &PhoneInfo{E164: "+234" + n, Local: "0" + n, Prefix: prefix, Note: PortingNote}
	for _, b := range allBlocks {
		if b.Prefix == prefix && b.RangeStart <= subscriber && subscriber <= b.RangeEnd {
			status := b.Status
			info.Network, info.Status = b.Operator, &status
			break
		}
	}
	return info
}

// Networks returns the names of networks with allocated mobile prefixes.
func Networks() []string {
	loadPhone()
	set := map[string]bool{}
	for _, b := range allBlocks {
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
	for _, b := range allBlocks {
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

func sortedKeys(set map[string]bool) []string {
	out := make([]string, 0, len(set))
	for k := range set {
		out = append(out, k)
	}
	sort.Strings(out)
	return out
}
