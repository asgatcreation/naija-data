// Package naija provides accurate, sourced Nigerian reference data: states, LGAs, wards, banks with
// NUBAN validation, and mobile phone helpers. The data is embedded; there are no dependencies.
//
// Data: CC BY 4.0, Akanji Oluwaseun Gabriel (see Meta().Sources). Code: MIT.
package naija

import (
	"embed"
	"encoding/json"
	"fmt"
	"sync"
)

//go:embed data/*.json
var dataFS embed.FS

// State is one of the 36 states or the FCT. Field names match the dataset.
type State struct {
	Code             string   `json:"code"`
	ISOCode          string   `json:"iso_code"`
	Name             string   `json:"name"`
	Slug             string   `json:"slug"`
	INECCode         string   `json:"inec_code"`
	PCode            string   `json:"pcode"`
	Capital          string   `json:"capital"`
	Zone             string   `json:"zone"`
	Created          *string  `json:"created"`
	Lat              *float64 `json:"lat"`
	Lon              *float64 `json:"lon"`
	Aliases          []string `json:"aliases"`
	UnverifiedFields []string `json:"unverified_fields"`
	Sources          []string `json:"sources"`
}

// LGA is a Local Government Area (or FCT Area Council).
type LGA struct {
	Code               string   `json:"code"`
	StateCode          string   `json:"state_code"`
	INECCode           string   `json:"inec_code"`
	Name               string   `json:"name"`
	Slug               string   `json:"slug"`
	Headquarters       *string  `json:"headquarters"`
	SenatorialDistrict *string  `json:"senatorial_district"`
	Lat                *float64 `json:"lat"`
	Lon                *float64 `json:"lon"`
	Aliases            []string `json:"aliases"`
	UnverifiedFields   []string `json:"unverified_fields"`
	Sources            []string `json:"sources"`
}

// Ward is an INEC registration area.
type Ward struct {
	Code      string   `json:"code"`
	LGACode   string   `json:"lga_code"`
	StateCode string   `json:"state_code"`
	Name      string   `json:"name"`
	Slug      string   `json:"slug"`
	Aliases   []string `json:"aliases"`
}

// Bank is a CBN-licensed institution (or a historical one: merged or licence revoked).
type Bank struct {
	ID               string   `json:"id"`
	Name             string   `json:"name"`
	ShortName        *string  `json:"short_name"`
	Type             string   `json:"type"`
	CBNCode          *string  `json:"cbn_code"`
	NIPCode          *string  `json:"nip_code"`
	USSD             *string  `json:"ussd"`
	Status           string   `json:"status"`
	StatusDate       *string  `json:"status_date"`
	MergedInto       *string  `json:"merged_into"`
	Aliases          []string `json:"aliases"`
	UnverifiedFields []string `json:"unverified_fields"`
	Sources          []string `json:"sources"`
}

// Active reports whether the institution is currently licensed.
func (b Bank) Active() bool { return b.Status == "active" }

// SearchResult is one fuzzy-search hit. Score is 0..1000.
type SearchResult struct {
	Kind      string `json:"kind"`
	Code      string `json:"code"`
	Name      string `json:"name"`
	StateCode string `json:"state_code"`
	Score     int    `json:"score"`
	Matched   string `json:"matched"`
}

// PhoneInfo describes a normalised mobile number.
type PhoneInfo struct {
	E164    string  `json:"e164"`
	Local   string  `json:"local"`
	Prefix  string  `json:"prefix"`
	Network *string `json:"network"`
	Status  *string `json:"status"`
	Note    string  `json:"note"`
}

// MetaInfo describes the dataset.
type MetaInfo struct {
	DataVersion string         `json:"data_version"`
	Counts      map[string]int `json:"counts"`
	Licence     string         `json:"licence"`
	Attribution string         `json:"attribution"`
	Sources     []struct {
		ID        string `json:"id"`
		Name      string `json:"name"`
		URL       string `json:"url"`
		Retrieved string `json:"retrieved"`
		Licence   string `json:"licence"`
	} `json:"sources"`
}

type phoneBlock struct {
	Prefix     string  `json:"prefix"`
	RangeStart string  `json:"range_start"`
	RangeEnd   string  `json:"range_end"`
	Operator   *string `json:"operator"`
	Status     string  `json:"status"`
}

func mustLoad(name string, v any) {
	raw, err := dataFS.ReadFile("data/" + name + ".json")
	if err != nil {
		panic(fmt.Sprintf("naija: embedded data %s missing: %v", name, err))
	}
	if err := json.Unmarshal(raw, v); err != nil {
		panic(fmt.Sprintf("naija: embedded data %s invalid: %v", name, err))
	}
}

var (
	loadAdmin  sync.Once
	allStates  []State
	allLGAs    []LGA
	loadWardsO sync.Once
	allWards   []Ward
	wardsByLGA map[string][]Ward
	loadBanksO sync.Once
	allBanks   []Bank
	loadPhoneO sync.Once
	allBlocks  []phoneBlock
	loadMetaO  sync.Once
	meta       MetaInfo
)

func admin() {
	loadAdmin.Do(func() {
		mustLoad("states", &allStates)
		mustLoad("lgas", &allLGAs)
	})
}

func loadWards() {
	loadWardsO.Do(func() {
		var raw struct {
			Rows [][]json.RawMessage `json:"rows"`
		}
		mustLoad("wards", &raw)
		allWards = make([]Ward, 0, len(raw.Rows))
		wardsByLGA = map[string][]Ward{}
		for _, r := range raw.Rows {
			var w Ward
			for i, dst := range []any{&w.Code, &w.LGACode, &w.StateCode, &w.Name, &w.Slug, &w.Aliases} {
				if err := json.Unmarshal(r[i], dst); err != nil {
					panic(fmt.Sprintf("naija: ward row invalid: %v", err))
				}
			}
			allWards = append(allWards, w)
			wardsByLGA[w.LGACode] = append(wardsByLGA[w.LGACode], w)
		}
	})
}

func loadBanks() { loadBanksO.Do(func() { mustLoad("banks", &allBanks) }) }
func loadPhone() { loadPhoneO.Do(func() { mustLoad("phone", &allBlocks) }) }

// Meta returns the dataset version, row counts, licence, attribution and sources.
func Meta() MetaInfo {
	loadMetaO.Do(func() { mustLoad("meta", &meta) })
	return meta
}
