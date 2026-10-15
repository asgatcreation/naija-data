package naija

import (
	"fmt"
	"regexp"
	"sort"
	"strings"
)

// BankTypes lists the institution types.
var BankTypes = []string{"commercial", "merchant", "non_interest", "payment_service_bank",
	"mobile_money_operator", "microfinance", "mortgage", "development_finance"}

// CBN Revised Standards on NUBAN: weights for the 6-digit institution code + 9-digit serial.
var nubanWeights = [15]int{3, 7, 3, 3, 7, 3, 3, 7, 3, 3, 7, 3, 3, 7, 3}

var (
	cbnCodeRe = regexp.MustCompile(`^(\d{3}|\d{5})$`)
	nipCodeRe = regexp.MustCompile(`^\d{6}$`)
	serialRe  = regexp.MustCompile(`^\d{9}$`)
	accountRe = regexp.MustCompile(`^\d{10}$`)
)

func bankTerms(b Bank) []string {
	terms := []string{b.Name}
	if b.ShortName != nil && *b.ShortName != "" {
		terms = append(terms, *b.ShortName)
	}
	return append(terms, b.Aliases...)
}

// Banks returns licensed institutions, optionally of one type (typ == "" for all). Inactive ones
// (merged, licence revoked) are included only when activeOnly is false.
func Banks(typ string, activeOnly bool) ([]Bank, error) {
	if typ != "" && !contains(BankTypes, typ) {
		return nil, fmt.Errorf("naija: unknown bank type %q, use one of %s", typ, strings.Join(BankTypes, ", "))
	}
	loadBanks()
	out := []Bank{}
	for _, b := range allBanks {
		if (typ == "" || b.Type == typ) && (b.Active() || !activeOnly) {
			out = append(out, b)
		}
	}
	return out, nil
}

// GetBank finds an institution by id ("gtbank"), CBN code ("058", "50211"), NIP code ("000013"),
// name, short name or alias ("GTB"). Active institutions win ties. It returns nil if unknown.
func GetBank(query string) *Bank {
	loadBanks()
	q := strings.TrimSpace(query)
	if q == "" {
		return nil
	}
	var hits []*Bank
	add := func(pred func(Bank) bool) {
		for i := range allBanks {
			if pred(allBanks[i]) {
				hits = append(hits, &allBanks[i])
			}
		}
	}
	switch {
	case cbnCodeRe.MatchString(q):
		add(func(b Bank) bool { return b.CBNCode != nil && *b.CBNCode == q })
	case nipCodeRe.MatchString(q):
		add(func(b Bank) bool { return b.NIPCode != nil && *b.NIPCode == q })
	default:
		add(func(b Bank) bool { return b.ID == strings.ToLower(q) })
		if len(hits) == 0 {
			key := Norm(q)
			add(func(b Bank) bool {
				for _, t := range bankTerms(b) {
					if Norm(t) == key {
						return true
					}
				}
				return false
			})
		}
	}
	for _, b := range hits {
		if b.Active() {
			return b
		}
	}
	if len(hits) > 0 {
		return hits[0]
	}
	return nil
}

// FindBanks does a fuzzy search of active institutions by name, short name or alias, best first.
// limit <= 0 means 10.
func FindBanks(query string, limit int) []Bank {
	loadBanks()
	if limit <= 0 {
		limit = 10
	}
	q := Norm(query)
	out := []Bank{}
	if q == "" {
		return out
	}
	type hit struct {
		score int
		bank  Bank
	}
	var hits []hit
	for _, b := range allBanks {
		if !b.Active() {
			continue
		}
		best := 0
		for _, t := range bankTerms(b) {
			best = max(best, score(q, Norm(t)))
		}
		if best >= 600 {
			hits = append(hits, hit{best, b})
		}
	}
	sort.SliceStable(hits, func(i, j int) bool {
		a, b := hits[i], hits[j]
		if a.score != b.score {
			return a.score > b.score
		}
		if a.bank.Name != b.bank.Name {
			return a.bank.Name < b.bank.Name
		}
		return a.bank.ID < b.bank.ID
	})
	for i := 0; i < len(hits) && i < limit; i++ {
		out = append(out, hits[i].bank)
	}
	return out
}

func institutionCode(cbnCode string) (string, error) {
	switch {
	case regexp.MustCompile(`^\d{3}$`).MatchString(cbnCode):
		return "000" + cbnCode, nil // deposit money banks
	case regexp.MustCompile(`^\d{5}$`).MatchString(cbnCode):
		return "9" + cbnCode, nil // other financial institutions
	}
	return "", fmt.Errorf("naija: a CBN bank code has 3 digits (banks) or 5 digits (other institutions): %q", cbnCode)
}

// NUBANCheckDigit returns the check digit for a 9-digit account serial at the bank with this CBN code.
func NUBANCheckDigit(bankCode, serial string) (int, error) {
	if !serialRe.MatchString(serial) {
		return 0, fmt.Errorf("naija: the NUBAN serial must be 9 digits: %q", serial)
	}
	inst, err := institutionCode(bankCode)
	if err != nil {
		return 0, err
	}
	digits := inst + serial
	total := 0
	for i := 0; i < 15; i++ {
		total += int(digits[i]-'0') * nubanWeights[i]
	}
	return (10 - total%10) % 10, nil
}

func cleanAccount(account string) string {
	return strings.NewReplacer(" ", "", "-", "", "\t", "").Replace(account)
}

// IsValidNUBAN reports whether the 10-digit account number has a correct check digit for this
// bank. bank is a CBN code ("058") or anything GetBank understands. It does not prove the account
// exists.
func IsValidNUBAN(account, bank string) (bool, error) {
	acct := cleanAccount(account)
	if !accountRe.MatchString(acct) {
		return false, nil
	}
	code := strings.TrimSpace(bank)
	if !cbnCodeRe.MatchString(code) {
		b := GetBank(bank)
		if b == nil || b.CBNCode == nil {
			return false, fmt.Errorf("naija: no CBN code known for bank %q", bank)
		}
		code = *b.CBNCode
	}
	d, err := NUBANCheckDigit(code, acct[:9])
	if err != nil {
		return false, err
	}
	return d == int(acct[9]-'0'), nil
}

// BanksForNUBAN returns the active institutions for which this account number has a valid check
// digit. About 1 in 10 banks match any number, so use it to narrow a bank picker.
func BanksForNUBAN(account string) []Bank {
	loadBanks()
	acct := cleanAccount(account)
	out := []Bank{}
	if !accountRe.MatchString(acct) {
		return out
	}
	check := int(acct[9] - '0')
	for _, b := range allBanks {
		if b.CBNCode == nil || !b.Active() {
			continue
		}
		if d, err := NUBANCheckDigit(*b.CBNCode, acct[:9]); err == nil && d == check {
			out = append(out, b)
		}
	}
	return out
}

func contains(list []string, s string) bool {
	for _, x := range list {
		if x == s {
			return true
		}
	}
	return false
}
