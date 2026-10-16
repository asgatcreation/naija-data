"""Set the release version everywhere, or check that everything matches a tag.

    python scripts/release/set_version.py 0.1.0            # update all files + CHANGELOG
    python scripts/release/set_version.py --check v0.1.0   # used by the release workflow

Files: packages/python (pyproject + __version__), packages/django (pyproject + __version__),
packages/js (package.json + package-lock.json), CHANGELOG.md ("Unreleased" -> "[x.y.z] - date").
The Go module is versioned by its git tag (go/vX.Y.Z), which the release workflow creates.
"""

from __future__ import annotations

import json
import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SEMVER = re.compile(r"\d+\.\d+\.\d+(?:-(?:alpha|beta|rc)\.\d+)?")

FILES = {
    "python": (ROOT / "packages/python/pyproject.toml", r'(?m)^version = "([^"]+)"'),
    "python-init": (ROOT / "packages/python/src/naija_data/__init__.py", r'(?m)^__version__ = "([^"]+)"'),
    "django": (ROOT / "packages/django/pyproject.toml", r'(?m)^version = "([^"]+)"'),
    "django-init": (ROOT / "packages/django/src/django_naija/__init__.py", r'(?m)^__version__ = "([^"]+)"'),
}


def pep440(version: str) -> str:
    """npm/semver "1.0.0-rc.1" -> Python "1.0.0rc1"."""
    m = re.fullmatch(r"(\d+\.\d+\.\d+)(?:-(alpha|beta|rc)\.(\d+))?", version)
    if not m:
        raise SystemExit(f"Not a release version: {version!r} (use 1.2.3 or 1.2.3-rc.1)")
    base, kind, n = m.groups()
    return base + ({"alpha": "a", "beta": "b", "rc": "rc"}[kind] + n if kind else "")


def current() -> dict[str, str]:
    found = {name: re.search(rx, path.read_text(encoding="utf-8")).group(1) for name, (path, rx) in FILES.items()}
    found["js"] = json.loads((ROOT / "packages/js/package.json").read_text(encoding="utf-8"))["version"]
    return found


def check(tag: str) -> int:
    version = tag.removeprefix("v")
    want_py = pep440(version)
    have = current()
    expected = {name: (version if name == "js" else want_py) for name in have}
    wrong = {k: v for k, v in have.items() if v != expected[k]}
    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    if f"## [{version}]" not in changelog:
        wrong["CHANGELOG.md"] = f'no "## [{version}]" section'
    if wrong:
        print(f"Versions do not match tag {tag}:")
        for k, v in wrong.items():
            print(f"  {k}: {v} (expected {expected.get(k, version)})")
        return 1
    print(f"All versions match {tag}.")
    return 0


def set_version(version: str) -> None:
    py = pep440(version)
    for name, (path, rx) in FILES.items():
        text = path.read_text(encoding="utf-8")
        m = re.search(rx, text)
        path.write_text(text[: m.start(1)] + py + text[m.end(1):], encoding="utf-8", newline="\n")
    # django-naija is released together with naija-data and needs at least the same version.
    dj = ROOT / "packages/django/pyproject.toml"
    dj.write_text(re.sub(r'"naija-data>=[^",]+,<2"', f'"naija-data>={py},<2"', dj.read_text(encoding="utf-8")),
                  encoding="utf-8", newline="\n")
    for path in (ROOT / "packages/js/package.json", ROOT / "packages/js/package-lock.json"):
        data = json.loads(path.read_text(encoding="utf-8"))
        data["version"] = version
        if path.name == "package-lock.json":
            data["packages"][""]["version"] = version
        path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8", newline="\n")
    # The API and the docs site use the local package; their lock files record its version.
    for lock in (ROOT / "api/package-lock.json", ROOT / "docs/site/package-lock.json"):
        data = json.loads(lock.read_text(encoding="utf-8"))
        for key, entry in data.get("packages", {}).items():
            if key.endswith("packages/js") and entry.get("name") == "naija-data":
                entry["version"] = version
        lock.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8", newline="\n")
    cl = ROOT / "CHANGELOG.md"
    text = cl.read_text(encoding="utf-8")
    if f"## [{version}]" not in text:
        if "## [Unreleased]" not in text:
            raise SystemExit("CHANGELOG.md has no '## [Unreleased]' section")
        text = text.replace("## [Unreleased]", f"## [Unreleased]\n\n## [{version}] - {date.today().isoformat()}", 1)
        cl.write_text(text, encoding="utf-8", newline="\n")
    print(f"Set version {version} (Python {py}). Next: commit, then create the tag v{version}.")


def main() -> int:
    args = sys.argv[1:]
    if len(args) == 2 and args[0] == "--check":
        return check(args[1])
    if len(args) == 1 and SEMVER.fullmatch(args[0]):
        set_version(args[0])
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main())
