package naija

import (
	"regexp"
	"strings"
	"sync"
	"unicode"
)

// Vehicle number plates: format validation and parsing, from the National Road Traffic Regulations
// 2012 (Official Gazette No. 101, S.I. 61), regulations 37-39 and Schedule 5. FRSC sets the LGA
// plate codes (reg. 39(5)) but does not publish them, so plates are not mapped to LGAs.

// PlateFormats lists the plate formats this package validates.
var PlateFormats = []string{"standard", "dealer"}

// PlateErrors lists the reasons PlateError can return.
var PlateErrors = []string{"empty", "invalid_characters", "unknown_format", "unknown_state"}

// LGACodeNote explains why standard plates are not mapped to LGAs.
const LGACodeNote = "The first three letters are the Local Government code. FRSC does not publish the list of " +
	"codes, so naija-data does not map them to LGAs yet."

// Plate is a parsed plate number.
type Plate struct {
	Compact   string  `json:"compact"`    // KJA123AB
	Display   string  `json:"display"`    // KJA-123AB
	Format    string  `json:"format"`     // standard or dealer
	Prefix    string  `json:"prefix"`     // standard: LGA code; dealer: "D" + state code
	Number    string  `json:"number"`     // the three digits
	Suffix    string  `json:"suffix"`     // standard: series letters; dealer: final character
	StateCode *string `json:"state_code"` // dealer plates only
	Note      *string `json:"note"`
}

// PlateCategory gives plate colours by category, as set by the Regulations.
type PlateCategory struct {
	Category         string `json:"category"`
	Vehicle          string `json:"vehicle"` // vehicle or motorcycle
	LetteringColour  string `json:"lettering_colour"`
	BackgroundColour string `json:"background_colour"`
	Provision        string `json:"provision"`
}

var (
	standardRe   = regexp.MustCompile(`^([A-Z]{3})(\d{3})([A-Z]{2})$`)
	dealerRe     = regexp.MustCompile(`^D([A-Z]{2})(\d{3})([A-Z0-9])$`)
	plateASCIIRe = regexp.MustCompile(`^[A-Za-z0-9]+$`)
	loadPlatesO  sync.Once
	plateData    struct {
		Categories []PlateCategory `json:"categories"`
	}
)

func parsePlate(text string) (*Plate, string) {
	s := strings.Map(func(r rune) rune {
		if unicode.IsSpace(r) || r == '-' || r == '.' {
			return -1
		}
		return r
	}, strings.TrimSpace(text))
	if s == "" {
		return nil, "empty"
	}
	// Check for plain ASCII before upper-casing: languages upper-case some letters differently.
	if !plateASCIIRe.MatchString(s) {
		return nil, "invalid_characters"
	}
	s = strings.ToUpper(s)
	if m := standardRe.FindStringSubmatch(s); m != nil {
		return &Plate{Compact: s, Display: m[1] + "-" + m[2] + m[3], Format: "standard", Prefix: m[1], Number: m[2],
			Suffix: m[3], Note: strPtr(LGACodeNote)}, ""
	}
	if m := dealerRe.FindStringSubmatch(s); m != nil {
		if GetState(m[1]) == nil || GetState(m[1]).Code != m[1] {
			return nil, "unknown_state"
		}
		return &Plate{Compact: s, Display: "D" + m[1] + " " + m[2] + " " + m[3], Format: "dealer", Prefix: "D" + m[1],
			Number: m[2], Suffix: m[3], StateCode: strPtr(m[1])}, ""
	}
	return nil, "unknown_format"
}

// PlateError returns why text is not a valid plate number (one of PlateErrors), or "" if valid.
func PlateError(text string) string {
	_, err := parsePlate(text)
	return err
}

// ParsePlate validates and splits a plate number ("kja 123 ab" -> KJA-123AB; dealer "DKN 135 3").
// It returns nil if the plate is not valid.
func ParsePlate(text string) *Plate {
	p, _ := parsePlate(text)
	return p
}

// IsValidPlate reports whether text is a valid plate number, optionally only of the given formats.
func IsValidPlate(text string, formats []string) bool {
	p := ParsePlate(text)
	return p != nil && (len(formats) == 0 || contains(formats, p.Format))
}

// PlateCategories returns plate colours by category (National Road Traffic Regulations 2012).
func PlateCategories() []PlateCategory {
	loadPlatesO.Do(func() { mustLoad("plates", &plateData) })
	return append([]PlateCategory(nil), plateData.Categories...)
}
