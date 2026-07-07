# /// script
# requires-python = ">=3.11,<3.12"
# dependencies = ["httpx>=0.27"]
# ///
"""A1 Sketchfab asset-lane discovery (D-004 R25–R29). Uses the official Data API to find
CC-LICENSED, downloadable models. Reads SKETCHFAB_TOKEN from env ONLY (never printed). Captures
usage_license + author + attribution + "provided by Sketchfab" per item (R26). Writes an ASSET
inventory — these are NEVER coverage (R25) and NEVER displace the L5 batch (R29, discovery-only here).

Usage: SKETCHFAB_TOKEN in env.  uv run .archon/scripts/a1_sketchfab.py \
         [--queries coral,kelp,sea-anemone] [--per 8] [--out reports/asset-inventory.json]
"""
import argparse, os, sys, json, time, datetime, pathlib
import httpx

TOKEN = os.environ.get("SKETCHFAB_TOKEN", "")
if not TOKEN:
    print(json.dumps({"lane": "A1", "status": "error", "note": "SKETCHFAB_TOKEN not in env"}))
    print("[A1] ERROR: SKETCHFAB_TOKEN not in env — reporting plainly, not working around.", file=sys.stderr)
    sys.exit(2)
H = {"Authorization": f"Token {TOKEN}"}
API = "https://api.sketchfab.com/v3"
# Sketchfab search results carry license.LABEL (not slug). Map label -> (slug, usable?). NC/ND are
# acquired-but-SEGREGATED per R26; usable = cc0/by/by-sa (commercial-OK, attribution/share-alike).
LABEL_MAP = {
    "CC0 Public Domain": ("cc0", True), "CC0": ("cc0", True),
    "CC Attribution": ("by", True),
    "CC Attribution-ShareAlike": ("by-sa", True),
    "CC Attribution-NoDerivs": ("by-nd", False),
    "CC Attribution-NonCommercial": ("by-nc", False),
    "CC Attribution-NonCommercial-ShareAlike": ("by-nc-sa", False),
    "CC Attribution-NonCommercial-NoDerivs": ("by-nc-nd", False),
}


def classify(label):
    slug, usable = LABEL_MAP.get(label or "", ("unknown", False))
    segregate = slug in ("by-nc", "by-nc-sa", "by-nc-nd", "by-nd")
    return slug, usable, segregate


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--queries", default="coral,kelp,sea anemone")   # R25 marine-trio experiment
    ap.add_argument("--per", type=int, default=8)
    ap.add_argument("--out", default="reports/asset-inventory.json")
    a = ap.parse_args()
    client = httpx.Client(headers=H, timeout=30)

    now = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")
    inventory, seg = [], 0
    for q in [x.strip() for x in a.queries.split(",") if x.strip()]:
        try:
            r = client.get(f"{API}/search", params={"type": "models", "q": q, "downloadable": "true",
                                                    "count": a.per, "sort_by": "-likeCount"})
            r.raise_for_status()
            results = r.json().get("results", [])
        except Exception as e:
            print(f"[A1] search failed for '{q}': {e}", file=sys.stderr)
            continue
        for m in results:
            lic = m.get("license") or {}
            label = lic.get("label") if isinstance(lic, dict) else None
            slug, usable, segregate = classify(label)
            user = m.get("user", {}) or {}
            author = user.get("displayName") or user.get("username")
            if segregate:
                seg += 1
            entry = {
                "lane": "A1", "entry_type": "asset_pack", "procedural": False,
                "query": q, "sketchfab_uid": m.get("uid"), "name": m.get("name"),
                "usage_license": slug, "license_label": label, "usable_commercial": usable,
                "author": author,
                "attribution": f'"{m.get("name")}" by {author} — licensed {label or slug} — provided by Sketchfab',
                "download_api": f"{API}/models/{m.get('uid')}/download",
                "viewer_url": m.get("viewerUrl"),
                "segregated": segregate,     # R26: NC/ND acquired-but-segregated
                "scene_asset_category": q, "seen_at": now,
            }
            inventory.append(entry)
        time.sleep(0.8)

    out = pathlib.Path(a.out); out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(inventory, indent=2))
    lic_counts = {}
    for e in inventory:
        lic_counts[e["usage_license"]] = lic_counts.get(e["usage_license"], 0) + 1
    print(json.dumps({"lane": "A1", "status": "discovery_ok", "assets_found": len(inventory),
                      "by_license": lic_counts, "segregated_nc_nd": seg, "out": str(out),
                      "note": "assets NOT coverage (R25); acquisition via asset probe R27 after owner go"}))
    print(f"[A1] {len(inventory)} CC-downloadable assets discovered ({lic_counts}); "
          f"{seg} NC/ND segregated. Assets, not coverage.", file=sys.stderr)


if __name__ == "__main__":
    main()
