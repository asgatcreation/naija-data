"""Download INEC's current State -> LGA -> Registration Area (ward) lists.

Source: INEC Continuous Voter Registration portal, polling unit locator
(https://cvr.inecnigeria.org/pu). The page fills its dropdowns from the public
endpoints used below. We only read the same lists a visitor sees, one request
at a time with a pause between them.

Output: .cache/raw/inec-cvr/{states,lgas,wards}.json (raw responses, for audit)

Run:  python scripts/fetch/inec_cvr.py
"""

from __future__ import annotations

import json
import re
import time
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / ".cache" / "raw" / "inec-cvr"
PAGE = "https://cvr.inecnigeria.org/pu"
API = "https://cvr.inecnigeria.org/PublicApi"
HEADERS = {
    "User-Agent": "naija-data/0.1 (+https://github.com/asgatcreation/naija-data)",
    "X-Requested-With": "XMLHttpRequest",
}
DELAY_SECONDS = 0.6


def get(url: str, params: dict | None = None) -> str:
    if params:
        url += "?" + urllib.parse.urlencode(params)
    for attempt in range(4):
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=60) as r:
                body = r.read().decode("utf-8")
            time.sleep(DELAY_SECONDS)
            return body
        except Exception as e:  # network hiccup: back off and retry
            if attempt == 3:
                raise
            print(f"  retry {attempt + 1} after error: {e}")
            time.sleep(5 * (attempt + 1))
    raise RuntimeError("unreachable")


def options(body: str) -> dict[str, str]:
    """Turn the endpoint's [{"id": "NN - NAME", ...}] response into {id: label}."""
    data = json.loads(body)[0]
    return {k: v for k, v in data.items() if k not in ("0", "selected")}


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    html = get(PAGE)
    states = dict(re.findall(r'<option value="(\d+)">(\d+ - [^<]+)</option>', html.split('id="SearchStateId"')[1].split("</select>")[0]))
    print(f"{len(states)} states")

    lgas: dict[str, dict[str, str]] = {}
    for sid, label in states.items():
        lgas[sid] = options(get(f"{API}/lgas/1/Search", {"data[Search][state_id]": sid}))
        print(f"{label}: {len(lgas[sid])} LGAs")

    wards: dict[str, dict[str, str]] = {}
    total = sum(len(v) for v in lgas.values())
    done = 0
    for sid, lga_map in lgas.items():
        for lid in lga_map:
            wards[lid] = options(get(f"{API}/wards/1/Search", {"data[Search][local_government_id]": lid}))
            done += 1
            if done % 50 == 0:
                print(f"  wards: {done}/{total} LGAs fetched")

    meta = {"source": PAGE, "retrieved": date.today().isoformat()}
    for name, obj in (("states", states), ("lgas", lgas), ("wards", wards)):
        (OUT / f"{name}.json").write_text(json.dumps({"meta": meta, "data": obj}, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"Done: {len(states)} states, {total} LGAs, {sum(len(v) for v in wards.values())} registration areas")


if __name__ == "__main__":
    main()
