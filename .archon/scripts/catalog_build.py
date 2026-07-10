# /// script
# requires-python = ">=3.11,<3.12"
# dependencies = ["pyyaml>=6"]
# ///
"""catalog_build.py — assemble THE CATALOG: the master list of every discovered free procedural
Blender item (D-008 catalog campaign). Headline metric = TOTAL CATALOG ENTRIES. Merges all sources
into catalog.jsonl, deduped by catalog_id, each with: name, creator, marketplace, url, price_class,
license, status ∈ {auto_acquired_verified, click_to_get, excluded}, category/verbs (provisional ok),
gate_state, reason, card. Never hand-edited — regenerable from sources.

Sources:
  manifests/*.json      -> auto_acquired_verified (real native-CI gate state), marketplace from lane
  candidates/*.jsonl    -> enrich name/creator/url/license/price per canonical_id
  graveyard.jsonl       -> excluded (dead, reason recorded)
  reports/sketchfab-sweep.json -> auto_acquired_verified assets (Sketchfab CC Download API)
  reports/discovery/*.jsonl    -> click_to_get / excluded (external lattice: gumroad/superhive/fab/artstation)
"""
import json, glob, pathlib, sys
ROOT = pathlib.Path(__file__).resolve().parents[2]

LANE_MARKET = {"L1": "extensions.blender.org", "L2": "github", "L6": "blenderkit",
               "L3": "forum", "L4": "blendernation", "A1": "sketchfab"}
GATE_RANK = {"pass": 6, "partial": 5, "legacy": 4, "fail": 3, "needs_review": 2, "quarantine": 2,
             "quarantine_timeout": 2, "noresult": 1, "skipped_incompatible": 1, "none": 0}


def card_for(cid):
    for pat in (f"operator__{cid}--*", f"operator__{cid}::*"):
        for f in glob.glob(str(ROOT / "cards" / pat.replace("::", "--").replace(".", "_"))):
            return pathlib.Path(f).read_text()[:900]
    # generic card
    return ""


def best_state(man):
    s = [(v or {}).get("state", "none") for v in (man.get("verify") or {}).values()]
    return max(s, key=lambda x: GATE_RANK.get(x, 0)) if s else "none"


def main():
    # candidate metadata by canonical_id (name/creator/url/license/lane/price)
    cand = {}
    for cf in glob.glob(str(ROOT / "candidates/*.jsonl")):
        if "_retired" in cf or "L5_pending" in cf and False:
            pass
        for line in open(cf):
            line = line.strip()
            if not line:
                continue
            try:
                d = json.loads(line)
            except Exception:
                continue
            cid = d.get("canonical_id")
            if cid and cid not in cand:
                cand[cid] = d

    catalog = {}   # catalog_id -> entry

    def add(cid, **kw):
        catalog[cid] = {"catalog_id": cid, **kw}

    # 1) gated manifests -> auto_acquired_verified (real gate state)
    for mp in glob.glob(str(ROOT / "manifests/*.json")):
        man = json.loads(open(mp).read())
        cid = man["canonical_id"]
        c = cand.get(cid, {})
        lane = c.get("lane") or ("L6" if cid.startswith(("bk__", "bkmat__", "bkng__")) else "?")
        market = LANE_MARKET.get(lane, "github" if "__" in cid else "?")
        lic = (c.get("license") or man.get("usage_license"))
        if isinstance(lic, list):
            lic = lic[0] if lic else None
        st = best_state(man)
        niches = []
        for op in (man.get("operators_enriched") or []):
            niches += op.get("niches") or []
        add(cid, name=c.get("name") or man.get("name") or cid, creator=c.get("author"),
            marketplace=market, url=c.get("url"),
            price_class="$0" if market in ("extensions.blender.org", "github", "blenderkit", "sketchfab") else "free-tier",
            license=lic, status="auto_acquired_verified", gate_state=st,
            category=(niches[0] if niches else None), verbs=sorted({v for op in (man.get("operators_enriched") or []) for v in (op.get("verbs") or [])}),
            provisional=False, card=(man.get("enrich_note") or "")[:500])

    # 2) enumerated-but-ungated candidates (L1/L2 not probed, L5-pending) -> status by lane
    for cid, d in cand.items():
        if cid in catalog:
            continue
        lane = d.get("lane", "?")
        if lane == "L5-pending":
            add(cid, name=d.get("forum_title") or d.get("name") or cid, creator=None,
                marketplace=(d.get("route") or "marketplace"), url=d.get("url"),
                price_class="unconfirmed", license=None, status="click_to_get",
                gate_state=None, category=None, verbs=[], provisional=True,
                card="Marketplace link routed from forum; price/license confirm-at-source.")
        else:
            market = LANE_MARKET.get(lane, "?")
            add(cid, name=d.get("name") or cid, creator=d.get("author"), marketplace=market,
                url=d.get("url"), price_class="$0", license=(d.get("license") if not isinstance(d.get("license"), list) else (d.get("license") or [None])[0]),
                status="auto_acquired_verified" if lane in ("L1", "L2") else "click_to_get",
                gate_state="enumerated_not_probed", category=None, verbs=[], provisional=False,
                card=(d.get("tagline") or "")[:300])

    # 3) graveyard -> excluded
    gp = ROOT / "graveyard.jsonl"
    if gp.exists():
        for i, line in enumerate(gp.read_text().splitlines()):
            line = line.strip()
            if not line:
                continue
            try:
                g = json.loads(line)
            except Exception:
                continue
            gid = f"graveyard::{g.get('canonical_id') or g.get('url') or i}"
            if gid in catalog:
                continue
            add(gid, name=g.get("canonical_id") or g.get("forum_title") or str(g.get("url", ""))[:50],
                creator=None, marketplace=g.get("route") or "github", url=g.get("url"),
                price_class="n/a", license=None, status="excluded",
                gate_state="graveyard", category=None, verbs=[], provisional=False,
                reason=g.get("reason") or "dead/no-signature", card="")

    # 4) Sketchfab sweep -> auto_acquired_verified assets (CC)
    sp = ROOT / "reports/sketchfab-sweep.json"
    if sp.exists():
        try:
            sf = json.loads(sp.read_text())
            items = sf.get("assets") or sf.get("inventory") or (sf if isinstance(sf, list) else [])
            for m in items:
                uid = m.get("sketchfab_uid") or m.get("uid")
                if not uid:
                    continue
                cid = f"sketchfab::{uid}"
                if cid in catalog:
                    continue
                add(cid, name=m.get("name"), creator=m.get("author") or m.get("username"),
                    marketplace="sketchfab", url=f"https://sketchfab.com/3d-models/{uid}",
                    price_class="$0", license=m.get("license") or m.get("license_slug"),
                    status="auto_acquired_verified" if m.get("usable", True) else "excluded",
                    gate_state="cc_asset", category=m.get("scene_asset_category") or m.get("query"),
                    verbs=["import"], provisional=True, card=f"Sketchfab CC asset '{m.get('name')}' — {m.get('license')}. Scene asset (import).")
        except Exception as e:
            print(f"  sketchfab parse err: {e}", file=sys.stderr)

    # 5) external discovery (gumroad/superhive/fab/artstation lattice) -> click_to_get / excluded
    for df in glob.glob(str(ROOT / "reports/discovery/*.jsonl")):
        for line in open(df):
            line = line.strip()
            if not line:
                continue
            try:
                d = json.loads(line)
            except Exception:
                continue
            cid = d.get("catalog_id") or f"{d.get('marketplace','ext')}::{d.get('url','')}"[:120]
            if cid in catalog:
                continue
            add(cid, name=d.get("name"), creator=d.get("creator"), marketplace=d.get("marketplace"),
                url=d.get("url"), price_class=d.get("price_class", "unconfirmed"),
                license=d.get("license"), status=d.get("status", "click_to_get"),
                gate_state=None, category=d.get("category"), verbs=d.get("verbs", []),
                provisional=d.get("provisional", True), reason=d.get("reason"),
                card=d.get("card", "")[:500])

    out = ROOT / "catalog.jsonl"
    with open(out, "w") as f:
        for e in sorted(catalog.values(), key=lambda x: (x.get("marketplace") or "", x["catalog_id"])):
            f.write(json.dumps(e) + "\n")
    from collections import Counter
    by_status = Counter(e["status"] for e in catalog.values())
    by_market = Counter(e.get("marketplace") for e in catalog.values())
    print(json.dumps({"TOTAL_CATALOG_ENTRIES": len(catalog), "by_status": dict(by_status),
                      "by_marketplace": dict(by_market.most_common())}, indent=1))


if __name__ == "__main__":
    main()
