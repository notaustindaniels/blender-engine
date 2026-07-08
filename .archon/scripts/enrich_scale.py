# /// script
# requires-python = ">=3.11,<3.12"
# dependencies = ["pyyaml>=6"]
# ///
"""enrich_scale.py — heuristic niche mapping at campaign scale (D-008 R46/R52 ingest step).

The thin slice used a hand-curated 24-entry map; 900+ probed add-ons need an automated, DETERMINISTIC,
AUDITABLE pass. For each PASSING/PARTIAL manifest, match the add-on's name+tagline+tags against
taxonomy niche ids + aliases (distinctive tokens + phrase aliases only; a curated stoplist rejects
generic words). Assign the best-matching niche(s) + that niche's taxonomy verbs. Every assignment
cites the matched token in enrich_note and is labeled enriched_by='keyword-heuristic' so it is never
confused with the operator-reviewed thin-slice map. No match -> no niche (honest; not everything maps).

This is niche ASSIGNMENT; the probe already verified the operator WORKS. A card is mintable from either.
Usage: enrich_scale.py [--min-state partial]
"""
import json, glob, pathlib, re, sys
import yaml

ROOT = pathlib.Path(__file__).resolve().parents[2]
TAX = yaml.safe_load(open(ROOT / "inputs/taxonomy.yaml"))
VERBS = set(TAX["meta"]["verb_enum"])
NICHE_VERBS, NICHE_CAT = {}, {}
# distinctive-token -> niches ; phrase-alias -> niche
STOP = {"add", "tool", "tools", "generator", "gen", "blender", "mesh", "object", "node", "nodes",
        "geometry", "the", "and", "for", "with", "pro", "kit", "system", "auto", "easy", "simple",
        "free", "addon", "add-on", "make", "maker", "creator", "create", "edit", "editor", "panel",
        "custom", "helper", "utility", "manager", "set", "pack", "quick", "batch", "smart", "modifier"}
TOKEN_NICHE, PHRASE_NICHE = {}, {}
for c in TAX["categories"]:
    for n in (c.get("niches") or []):
        nid = n["id"]; NICHE_VERBS[nid] = [v for v in (n.get("verbs") or ["generate"]) if v in VERBS] or ["generate"]
        NICHE_CAT[nid] = c["name"]
        # tokens from the niche id (minus generic suffixes) + single-word aliases
        toks = [t for t in re.split(r"[_\s\-]+", nid) if t and t not in STOP and len(t) > 3]
        for t in toks:
            TOKEN_NICHE.setdefault(t, set()).add(nid)
        for al in (n.get("aliases") or []):
            al = al.strip().lower()
            if len(al.split()) >= 2:                    # multi-word alias = a strong phrase signal
                PHRASE_NICHE.setdefault(al, set()).add(nid)
            elif al not in STOP and len(al) > 3:
                TOKEN_NICHE.setdefault(al, set()).add(nid)


def candidate_text():
    txt = {}
    for cf in glob.glob(str(ROOT / "candidates/*.jsonl")):
        for line in open(cf):
            line = line.strip()
            if not line:
                continue
            try:
                d = json.loads(line)
            except Exception:
                continue
            cid = d.get("canonical_id")
            if cid:
                txt[cid] = " ".join(str(d.get(k, "")) for k in ("name", "tagline", "tags")).lower()
    return txt


def match_niches(text):
    hits = {}
    for phrase, niches in PHRASE_NICHE.items():
        if phrase in text:
            for nz in niches:
                hits[nz] = hits.get(nz, 0) + 3          # phrase = strong
    for tok, niches in TOKEN_NICHE.items():
        if re.search(rf"\b{re.escape(tok)}\b", text):
            for nz in niches:
                hits[nz] = hits.get(nz, 0) + 1
    # best niches by score; keep clear winners only
    if not hits:
        return [], ""
    top = sorted(hits.items(), key=lambda kv: -kv[1])
    best = top[0][1]
    # PRECISION over recall (R14: no fabricated coverage). Require a phrase match (score 3) OR 2+ token
    # hits — a single common-word token (paint/magic/path/data/cell...) matches incidentally and produces
    # garbage coverage. Concrete-noun single-token misses (cloth->cloth_sim) are honest UNDER-coverage,
    # surfaced in the gap reports; lift recall later via a curated distinctive-noun allowlist or AI-enrich.
    keep = [nz for nz, s in top if s >= max(2, best)]
    matched = next((t for t in TOKEN_NICHE if re.search(rf"\b{re.escape(t)}\b", text) and keep and keep[0] in TOKEN_NICHE[t]), "")
    return keep[:2], matched


def main():
    min_state = "partial"
    order = {"pass": 3, "partial": 2}
    ctext = candidate_text()
    enriched = skipped = nomatch = 0
    for mp in sorted(glob.glob(str(ROOT / "manifests/*.json"))):
        man = json.loads(open(mp).read())
        cid = man["canonical_id"]
        # never overwrite an enrichment from any authoritative source (reviewed map, shader-probe,
        # asset-probe, etc.); only fill un-enriched manifests + re-do our own heuristic ones
        if man.get("operators_enriched") and man.get("enriched_by") not in (None, "", "keyword-heuristic"):
            skipped += 1; continue
        verify = man.get("verify") or {}
        best = max((order.get((s or {}).get("state"), 0) for s in verify.values()), default=0)
        if best < order[min_state]:
            continue                                     # only working tools get a niche
        text = ctext.get(cid, "")
        niches, matched = match_niches(text)
        if not niches:
            nomatch += 1; continue
        verbs = sorted({v for nz in niches for v in NICHE_VERBS[nz]})
        ops = man.get("operators") or []
        op_id = ops[0] if ops else cid
        man["operators_enriched"] = [{"kind": "gn_node_group" if man.get("artifact_type") in ("gn_pack",) else "bpy_op",
                                      "id": op_id, "verbs": verbs, "niches": niches}]
        man["enriched_by"] = "keyword-heuristic"
        man["enrich_note"] = f"heuristic: '{matched}' in name/tagline -> {niches} ({NICHE_CAT[niches[0]]})."
        pathlib.Path(mp).write_text(json.dumps(man, indent=2))
        enriched += 1
    print(json.dumps({"enriched_heuristic": enriched, "reviewed_skipped": skipped,
                      "passing_no_niche_match": nomatch}))


if __name__ == "__main__":
    main()
