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
	Code                string   `json:"code"`
	LGACode             string   `json:"lga_code"`
	StateCode           string   `json:"state_code"`
	Name                string   `json:"name"`
	Slug                string   `json:"slug"`
	SenatorialDistrict  string   `json:"senatorial_district"`  // code, e.g. "SD001"
	FederalConstituency string   `json:"federal_constituency"` // code, e.g. "FC001"
	StateConstituency   *string  `json:"state_constituency"`   // code, e.g. "SC001"; nil in the FCT (no House of Assembly)
	Aliases             []string `json:"aliases"`
	UnverifiedFields    []string `json:"unverified_fields"`
}

// Constituency is a senatorial district (Senate), federal constituency (House of Representatives)
// or state constituency (State House of Assembly), as delimited by INEC.
type Constituency struct {
	Kind      string   `json:"kind"` // "senatorial_district", "federal_constituency" or "state_constituency"
	Code      string   `json:"code"` // "SD001", "FC001", "SC001"
	StateCode string   `json:"state_code"`
	INECCode  string   `json:"inec_code"` // INEC's code, e.g. "FC/001/AB"
	Name      string   `json:"name"`
	Slug      string   `json:"slug"`
	Aliases   []string `json:"aliases"`
	LGACodes  []string `json:"lga_codes"` // LGAs it covers in full or in part
	Sources   []string `json:"sources"`
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
	loadUnitsO sync.Once
	allUnits   []Constituency
	loadBanksO sync.Once
	allBanks   []Bank
	loadPhoneO sync.Once
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
			for i, dst := range []any{&w.Code, &w.LGACode, &w.StateCode, &w.Name, &w.Slug, &w.SenatorialDistrict,
				&w.FederalConstituency, &w.StateConstituency, &w.Aliases, &w.UnverifiedFields} {
				if err := json.Unmarshal(r[i], dst); err != nil {
					panic(fmt.Sprintf("naija: ward row invalid: %v", err))
				}
			}
			allWards = append(allWards, w)
			wardsByLGA[w.LGACode] = append(wardsByLGA[w.LGACode], w)
		}
	})
}

func loadUnits() { loadUnitsO.Do(func() { mustLoad("constituencies", &allUnits) }) }

func loadBanks() { loadBanksO.Do(func() { mustLoad("banks", &allBanks) }) }

// Meta returns the dataset version, row counts, licence, attribution and sources.
func Meta() MetaInfo {
	loadMetaO.Do(func() { mustLoad("meta", &meta) })
	return meta
}
