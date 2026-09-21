#!/usr/bin/env python3
"""Generate locations.json from the iso-codes package (ISO 3166-1 / 3166-2).

Arch: pacman -S iso-codes   Debian/Ubuntu: apt install iso-codes

The server keeps only the codes — it validates that a country exists and that a
subdivision belongs to it — while the plugin renders the names in its pickers.
Both read the same file so the two cannot disagree about what exists, which is
why --also writes a second copy into the plugin checkout.

First-level subdivisions only: ISO 3166-2 entries carrying a "parent" are
nested below another subdivision, which Pulse deliberately does not model.
"""

import argparse
import json
import pathlib
import sys

SRC = pathlib.Path("/usr/share/iso-codes/json")


def build() -> dict:
    countries = json.loads((SRC / "iso_3166-1.json").read_text())["3166-1"]
    subs = json.loads((SRC / "iso_3166-2.json").read_text())["3166-2"]

    by_country: dict[str, list[dict[str, str]]] = {}
    for s in subs:
        if "parent" in s:
            continue
        by_country.setdefault(s["code"].split("-", 1)[0], []).append(
            {"code": s["code"], "name": s["name"]}
        )

    return {
        "source": "iso-codes (ISO 3166-1, ISO 3166-2)",
        "countries": [
            {
                "code": c["alpha_2"],
                "name": c["name"],
                "subdivisions": sorted(
                    by_country.get(c["alpha_2"], []), key=lambda s: s["name"]
                ),
            }
            for c in sorted(countries, key=lambda c: c["name"])
        ],
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default="locations.json", help="where to write the catalog")
    ap.add_argument(
        "--also",
        action="append",
        default=[],
        help="an additional path to receive the same bytes (e.g. the plugin checkout)",
    )
    args = ap.parse_args()

    if not SRC.is_dir():
        sys.exit(f"{SRC} not found — install the iso-codes package")

    catalog = build()
    blob = json.dumps(catalog, ensure_ascii=False, separators=(",", ":")) + "\n"

    for raw in [args.out, *args.also]:
        target = pathlib.Path(raw).expanduser()
        if not target.parent.is_dir():
            print(f"skipped {target}: {target.parent} does not exist", file=sys.stderr)
            continue
        target.write_text(blob, encoding="utf-8")
        print(f"wrote {target}")

    n_sub = sum(len(c["subdivisions"]) for c in catalog["countries"])
    print(f"{len(catalog['countries'])} countries, {n_sub} subdivisions, {len(blob)} bytes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
