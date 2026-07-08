# /// script
# requires-python = ">=3.11,<3.12"
# ///
"""l6_blenderkit.py — enumerate the BlenderKit free-tier procedural catalog (D-008 R46 Wave 3).

HYBRID classification (D-008): materials + node-groups are PROCEDURAL -> gate-eligible; models are
ASSETS -> A-lane ledger (never coverage). Orders by promise (score/downloads) but excludes nothing
(R11) up to a documented ceiling per asset_type; the long tail past the ceiling is logged, not dropped.
Reads BLENDERKIT_API_KEY from env (R2 — never printed). Emits candidates/L6.jsonl (one row per asset)
with per-asset license (cc0/royalty_free) captured (R26) + the Article-5 constraint note.

The download+probe of these happens in a later wave (bk download flow: scene_uuid + BlenderKit UA);
this step is pure enumeration (metadata), cheap and automatable.
Usage: l6_blenderkit.py [--ceiling 600] [--types material,nodegroup]
"""
import json, os, urllib.request, urllib.parse, sys, argparse, pathlib

ROOT = pathlib.Path(__file__).resolve().parents[3]


def key():
    for line in open(ROOT / ".archon/.env"):
        if line.startswith("BLENDERKIT_API_KEY="):
            return line.split("=", 1)[1].strip().strip('"').strip("'")
    return os.environ.get("BLENDERKIT_API_KEY", "")


def api(url, hdr):
    try:
        return json.load(urllib.request.urlopen(urllib.request.Request(url, headers=hdr), timeout=40))
    except Exception as e:
        return {"_error": str(e)}


def sweep(asset_type, ceiling, hdr):
    """Paginate the search API for free assets of one type, ordered by score. Stops at the ceiling;
    reports how many remain in the tail (logged, not silently dropped — R11)."""
    rows, url, page = [], (
        "https://www.blenderkit.com/api/v1/search/?query="
        + urllib.parse.quote(f"asset_type:{asset_type} is_free:true order:-score") + "&page_size=100"), 0
    total = None
    while url and len(rows) < ceiling:
        d = api(url, hdr)
        if d.get("_error"):
            print(f"  [L6] {asset_type} page {page} error: {d['_error']}", file=sys.stderr); break
        total = d.get("count", total)
        for m in d.get("results", []):
            lic = (m.get("license") or "").lower()
            rows.append({
                "canonical_id": f"bk__{asset_type}__{m.get('assetBaseId', m.get('id'))}",
                "source_id": m.get("assetBaseId"), "name": m.get("name"), "author": (m.get("author") or {}).get("fullName") if isinstance(m.get("author"), dict) else None,
                "lane": "L6", "asset_type": asset_type,
                "classification": "procedural" if asset_type in ("material", "nodegroup") else "asset",
                "usage_license": lic or None, "score": m.get("score"), "can_download": m.get("canDownload"),
                "url": f"https://www.blenderkit.com/asset-gallery-detail/{m.get('assetBaseId')}/",
                "constraint": "BlenderKit Article-5: rendered-video only, no 3D-export (R26)",
                "procedural": asset_type in ("material", "nodegroup")})
        url = d.get("next"); page += 1
    return rows, total


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ceiling", type=int, default=600)
    ap.add_argument("--types", default="material,nodegroup")
    ap.add_argument("--out", default=str(ROOT / "candidates/L6.jsonl"))
    a = ap.parse_args()
    k = key()
    if not k:
        print("BLENDERKIT_API_KEY missing (env-only, R2) — cannot enumerate L6", file=sys.stderr); sys.exit(2)
    hdr = {"Authorization": f"Bearer {k}", "Accept": "application/json"}
    allrows, tails = [], {}
    for t in [x.strip() for x in a.types.split(",") if x.strip()]:
        rows, total = sweep(t, a.ceiling, hdr)
        allrows += rows
        tails[t] = {"enumerated": len(rows), "catalog_total": total,
                    "tail_deferred": max(0, (total or 0) - len(rows))}
    with open(a.out, "w") as f:
        for r in allrows:
            f.write(json.dumps(r) + "\n")
    print(json.dumps({"lane": "L6", "enumerated": len(allrows), "by_type": tails, "out": a.out,
                      "note": "R11: ordered by score; tail_deferred logged, not dropped — revisit for full sweep"}))


if __name__ == "__main__":
    main()
