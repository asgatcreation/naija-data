"""Download INEC's electoral units from the INEC Result Viewing portal (IReV).

Source: https://www.inecelectionresults.ng. The portal fills its pages from the public JSON API
below. Each ward record there carries the ids of its senatorial district, federal constituency and
state constituency, and each election names its district or constituency. We read:

- the election lists for the senatorial, House of Representatives and House of Assembly elections,
  one state at a time (names and INEC codes of every district and constituency);
- the LGAs and wards of the 2023 presidential election, one state at a time (the ward -> state
  constituency -> federal constituency -> senatorial district links).

One request at a time with a pause between them.

Output: .cache/raw/inec-irev/{election_types,elections,wards}.json (raw responses, for audit)

Run:  python scripts/fetch/inec_irev.py
"""

from __future__ import annotations

import json
import time
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / ".cache" / "raw" / "inec-irev"
PORTAL = "https://www.inecelectionresults.ng"
API = "https://dolphin-app-sleqh.ondigitalocean.app/api/v1/"  # the portal's API (see its main.*.js)
HEADERS = {"User-Agent": "naija-data/0.1 (+https://github.com/asgatcreation/naija-data)"}
DELAY_SECONDS = 0.6
IREV_STATE_IDS = range(1, 38)  # IReV numbers the 36 states and the FCT 1-37
TYPES = {"SEN": "senatorial", "REPS": "federal", "ASSEMBLY": "state"}
PRESIDENTIAL_2023 = "2023-02-25"


def get(path: str, params: dict | None = None) -> list | dict:
    url = API + path + ("?" + urllib.parse.urlencode(params) if params else "")
    for attempt in range(4):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=HEADERS), timeout=90) as r:
                body = json.loads(r.read().decode("utf-8"))
            time.sleep(DELAY_SECONDS)
            if not body.get("success"):
                raise RuntimeError(f"{url}: {body.get('message')}")
            return body["data"]
        except Exception as e:  # network hiccup: back off and retry
            if attempt == 3:
                raise
            print(f"  retry {attempt + 1} after error: {e}")
            time.sleep(5 * (attempt + 1))
    raise RuntimeError("unreachable")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    types = get("election-types")
    type_ids = {t["code"]: t["_id"] for t in types}

    elections: dict[str, dict[str, list]] = {}
    for code in TYPES:
        elections[code] = {}
        for sid in IREV_STATE_IDS:
            elections[code][str(sid)] = get("elections", {"election_type": type_ids[code], "state_id": sid})
        print(f"{code}: {sum(len(v) for v in elections[code].values())} elections")

    pres = [e for e in get("elections", {"election_type": type_ids["PRES"]})
            if e["election_date"].startswith(PRESIDENTIAL_2023)]
    if len(pres) != 1:
        raise SystemExit(f"expected one {PRESIDENTIAL_2023} presidential election, found {len(pres)}")
    wards: dict[str, list] = {}
    for sid in IREV_STATE_IDS:
        wards[str(sid)] = get(f"elections/{pres[0]['_id']}/lga/state/{sid}")
        n = sum(len(lga.get("wards") or []) for lga in wards[str(sid)])
        print(f"state {sid}: {len(wards[str(sid)])} LGAs, {n} wards")

    meta = {"source": PORTAL, "api": API, "retrieved": date.today().isoformat(),
            "presidential_election": pres[0]["_id"]}
    for name, obj in (("election_types", types), ("elections", elections), ("wards", wards)):
        (OUT / f"{name}.json").write_text(json.dumps({"meta": meta, "data": obj}, ensure_ascii=False, indent=1),
                                          encoding="utf-8")
    print("Done")


if __name__ == "__main__":
    main()
