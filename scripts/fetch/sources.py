"""Download the raw upstream files that data/ is built from.

Everything lands in .cache/raw/ (git-ignored) together with manifest.json, which records
each file's URL, retrieval date and SHA-256, so any build can be audited and repeated.
INEC wards come from a separate, slower crawler: scripts/fetch/inec_cvr.py.

Run:  python scripts/fetch/sources.py
"""

from __future__ import annotations

import hashlib
import json
import time
import urllib.request
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / ".cache" / "raw"
UA = "Mozilla/5.0 (compatible; naija-data/0.1; +https://github.com/asgatcreation/naija-data)"

HDX = "https://data.humdata.org/dataset"
GEOB = "https://github.com/wmgeolab/geoBoundaries/raw/9469f09/releaseData/gbOpen/NGA"
CBN = "https://www.cbn.gov.ng/api"

FILES = {
    # source id in data/sources.json -> {local path: url}
    "ocha-cod-ab-nga": {
        "codab/nga_admin_boundaries.xlsx": f"{HDX}/81ac1d38-f603-4a98-804d-325c658599a3/resource/f1865f35-a07e-4de3-9183-e4222e475527/download/nga_admin_boundaries.xlsx",
    },
    "geoboundaries-nga": {
        "geob/ADM1.geojson": f"{GEOB}/ADM1/geoBoundaries-NGA-ADM1.geojson",
        "geob/ADM2.geojson": f"{GEOB}/ADM2/geoBoundaries-NGA-ADM2.geojson",
    },
    "ncc-mobile-allocation": {
        "ncc/mobile-number-allocation-table.html": "https://ncc.gov.ng/operators/mobile-number-allocation-table",
    },
    "cbn-financial-institutions": {
        f"cbn/{name}.json": f"{CBN}/Get{name}"
        for name in ("DMBs", "MBs", "NIBs", "MFBs", "MMOs", "PSBs", "DFIs", "PMIs")
    },
}


def download(url: str, dest: Path) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                body = r.read()
            break
        except OSError as e:  # DNS or network hiccup: back off and retry
            if attempt == 3:
                raise
            print(f"  retry {attempt + 1} for {url}: {e}")
            time.sleep(10 * (attempt + 1))
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(body)
    return hashlib.sha256(body).hexdigest()


def main() -> None:
    manifest_path = RAW / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else {}
    for source_id, files in FILES.items():
        for rel, url in files.items():
            sha = download(url, RAW / rel)
            manifest[rel] = {"source": source_id, "url": url, "retrieved": date.today().isoformat(), "sha256": sha}
            print(f"{rel}  {sha[:12]}")
            time.sleep(1)
    manifest_path.write_text(json.dumps(manifest, indent=1, sort_keys=True), encoding="utf-8")


if __name__ == "__main__":
    main()
