# /// script
# requires-python = ">=3.11,<3.12"
# dependencies = ["httpx>=0.27", "pyyaml>=6"]
# ///
"""L1 enumerator — official Blender extensions platform (SPEC §2.2 L1, §5.3).

The platform exposes the entire catalog in ONE call: GET /api/v1/extensions/ returns
{blocklist, data:[...], version}. Each add-on carries archive_url AND archive_hash
(sha256) — so provenance (PRD zero-fabrication / bar g) is deterministic downstream.

Emits candidates/<lane>.jsonl (one row per unique add-on). For the Stage-1 thin slice,
--categories terrain,vegetation restricts to Terrain/Vegetation-relevant add-ons using a
CURATED two-tier matcher: unambiguous stems (substring, catch compounds like
"terrainmixer") + ambiguous short words (word-boundary, so "ice" does not match "lattice").
The filter is recall-biased but tight; final niche precision happens at enrich+coverage.
Deterministic, no AI.

Usage:
  uv run .archon/scripts/enumerate/l1_extensions.py --out candidates/L1.jsonl \
      [--categories terrain,vegetation] [--limit N]
"""
import argparse, json, re, sys, datetime, pathlib
import httpx

API = "https://extensions.blender.org/api/v1/extensions/"
UA = "blender-vault-harvester/0.1 (Stage-1 research; contact: local)"

# Curated from the taxonomy's terrain/vegetation niches by hand (kept curated rather than
# auto-derived: alias tokens like 'materials'/'formation'/'flow' produced massive noise).
# STEMS: safe as substrings (catch compounds). WORDS: matched at word boundaries only.
TIERS = {
    "terrain": {
        "stems": {"terrain", "landscape", "heightmap", "erosion", "glacier", "volcan",
                  "canyon", "waterfall", "coastline", "asteroid", "geolog", "tectonic"},
        "words": {"ice", "sand", "snow", "rock", "rocks", "cave", "caves", "dune", "dunes",
                  "river", "rivers", "coast", "cliff", "cliffs", "mesa", "crater", "craters",
                  "planet", "boulder", "boulders", "scree", "talus", "mountain", "mountains",
                  "lava", "desert", "fjord", "srtm", "dem", "strata"},
    },
    "vegetation": {
        "stems": {"vegetation", "foliage", "sapling", "bonsai", "botan", "mushroom", "meadow",
                  "ivygen", "orchard", "phyllotaxis", "succulent"},
        "words": {"tree", "trees", "plant", "plants", "grass", "fern", "ferns", "vine",
                  "vines", "ivy", "moss", "leaf", "leaves", "root", "roots", "kelp", "coral",
                  "flower", "flowers", "forest", "forests", "scatter", "scattering",
                  "ecosystem", "hedge", "garden", "bush", "shrub", "petal", "petals"},
    },
}
# keyword-adjacent but definitively NOT generative geometry (node-editor/io/util tools).
# 'bonsai' here is the BlenderBIM/IFC tool (not vegetation); the others match on weak
# tokens like 'root'/'scatter' but are util/import add-ons.
STOPLIST_IDS = {"tree_clipper", "node_tree_screenshot", "matalogue", "node_arrange",
                "node_exporter", "nodesync", "node_annotator", "node_align",
                "improved_node_search", "root_maker", "bonsai", "PlaceHelper",
                "import_mixamo_root_motion", "script_launcher"}
GEO_TAGS = {"Add Mesh", "Add Curve", "Geometry Nodes", "Mesh", "Object"}


def slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", (s or "").lower()).strip("-")


def canonical_id(author: str, name: str) -> str:
    return f"{slug(author)}__{slug(name)}"


def parse_ver(v: str):
    out = []
    for p in re.split(r"[.\-+]", str(v)):
        out.append((0, int(p)) if p.isdigit() else (1, p))
    return tuple(out)


def build_matcher(categories):
    stems, words = set(), set()
    for c in categories:
        t = TIERS.get(c, {})
        stems |= t.get("stems", set())
        words |= t.get("words", set())
    word_re = re.compile(r"\b(" + "|".join(sorted(re.escape(w) for w in words)) + r")\b") if words else None
    return stems, word_re


def match(row, stems, word_re):
    if row["source_id"] in STOPLIST_IDS:
        return None
    blob = " ".join([row["source_id"], row["name"], row.get("tagline", "")] + (row.get("tags") or [])).lower()
    hits = sorted({s for s in stems if s in blob})
    if word_re:
        hits += sorted({m.group(1) for m in word_re.finditer(blob)})
    if not hits:
        return None
    return {"keywords": sorted(set(hits)), "geo_tag": bool(set(row.get("tags") or []) & GEO_TAGS)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--categories", default="")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--include-themes", action="store_true")
    a = ap.parse_args()

    r = httpx.get(API, headers={"User-Agent": UA}, timeout=60, follow_redirects=True)
    r.raise_for_status()
    payload = r.json()
    data = payload.get("data", [])
    blocklist = {b.get("id") if isinstance(b, dict) else b for b in (payload.get("blocklist") or [])}

    best = {}
    for x in data:
        if x.get("type") != "add-on" and not a.include_themes:
            continue
        sid = x.get("id")
        if sid in blocklist:
            continue
        if sid not in best or parse_ver(x.get("version", "0")) > parse_ver(best[sid].get("version", "0")):
            best[sid] = x

    rows = []
    for sid, x in best.items():
        h = x.get("archive_hash", "")
        sha = h.split(":", 1)[1] if h.startswith("sha256:") else h
        rows.append({
            "canonical_id": canonical_id(x.get("maintainer", ""), x.get("name", "")),
            "source_id": sid,
            "name": x.get("name", ""),
            "author": x.get("maintainer", ""),
            "version": x.get("version", ""),
            "addon_type": "extension_manifest",  # refined at acquire/probe (may be gn_pack)
            "lane": "L1",
            "url": x.get("website") or f"https://extensions.blender.org/add-ons/{sid}/",
            "archive_url": x.get("archive_url", ""),
            "sha256": sha,
            "archive_size": x.get("archive_size"),
            "blender_version_min": x.get("blender_version_min", ""),
            "license": x.get("license", []),
            "tags": x.get("tags", []),
            "tagline": x.get("tagline", ""),
            "procedural": None,
            "fetched_at": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
        })

    cats = [c.strip() for c in a.categories.split(",") if c.strip()]
    kept = rows
    if cats:
        stems, word_re = build_matcher(cats)
        out = []
        for row in rows:
            m = match(row, stems, word_re)
            if m:
                row["match"] = m
                out.append(row)
        out.sort(key=lambda r: (not r["match"]["geo_tag"], r["source_id"]))
        kept = out

    if a.limit and len(kept) > a.limit:
        kept = kept[:a.limit]

    pathlib.Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    with open(a.out, "w") as f:
        for row in kept:
            f.write(json.dumps(row) + "\n")

    print(json.dumps({
        "lane": "L1", "catalog_total": len(data), "unique_addons": len(best),
        "categories": cats or "ALL", "candidates_written": len(kept), "out": a.out,
    }))
    print(f"[L1] catalog={len(data)} unique_addons={len(best)} "
          f"categories={cats or 'ALL'} -> {len(kept)} candidates -> {a.out}", file=sys.stderr)


if __name__ == "__main__":
    main()
