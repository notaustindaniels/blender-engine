# /// script
# requires-python = ">=3.11,<3.12"
# dependencies = ["pyyaml>=6", "numpy>=1.26"]
# ///
"""corpus_cli.py — the consumption interface for the Blender Vault (D-008 R54), CLI twin of the MCP
server. Six verbs over corpus_kb.db (retrieval + graph) + corpus.db (authoritative registry). Enacts
the R53 doctrine: RETRIEVAL PROPOSES (search_capabilities routes to canonical ids), THE REGISTRY
DISPOSES (query_registry is a deterministic facet query resolved through corpus.db verification state
+ license before anything is invocable). recipe_unverified and graveyard are returned LABELED and are
never `resolvable=True`.

Verbs:
  search_capabilities <nl> [--medium m] [--verb v] [--near key]   # proposes cards (hybrid RAG)
  query_registry [--verb v] [--medium m] [--niche n] [--quality-min q] [--license-class c] [--blender-ver x]
  get_card <id>            # Tier-1 card
  get_usage <id>           # Tier-2 full manifest
  find_substitutes <id|niche>
  plan_recipe <niche>

All output is JSON. Env: RAG_DB=corpus_kb.db, RAG_EMBED=ollama, RAG_EMBED_MODEL=bge-m3.
"""
import json, os, sys, sqlite3, subprocess, pathlib, argparse

ROOT = pathlib.Path(__file__).resolve().parents[2]
KB = str(pathlib.Path(os.environ.get("RAG_DB", ROOT / "corpus_kb.db")).resolve())
REG = str((ROOT / "corpus.db").resolve())
TEMPLATE = ROOT / "tools" / "hybrid-rag-template"
CARDS = ROOT / "cards"
MANIFESTS = ROOT / "manifests"
QUALITY_RANK = {"asset_fed_minimal": 1, "composed": 2, "partial": 2, "full_generator": 3}
RESOLVABLE_STATES = {"pass", "partial"}          # verified in the registry
NON_RESOLVABLE_TIERS = {"recipe_unverified"}     # claims, never render-time (R53)


def _kb():
    con = sqlite3.connect(KB); con.row_factory = sqlite3.Row; return con


def _reg():
    con = sqlite3.connect(REG); con.row_factory = sqlite3.Row; return con


# ---- RETRIEVAL PROPOSES ----------------------------------------------------
def search_capabilities(nl, medium=None, verb=None, near=None, k=8):
    """Hybrid RAG over the KB. Returns proposed cards — NOT a selection. Routes to canonical ids."""
    env = dict(os.environ, RAG_DB=KB, RAG_EMBED=os.environ.get("RAG_EMBED", "ollama"),
               RAG_EMBED_MODEL=os.environ.get("RAG_EMBED_MODEL", "bge-m3"))
    cmd = [sys.executable, "retrieve.py", "search", nl, "--k", str(k), "--json"]
    if near:
        cmd += ["--near", near]
    r = subprocess.run(cmd, cwd=TEMPLATE, env=env, capture_output=True, text=True)
    try:
        res = (json.loads(r.stdout).get("results") or [])
    except Exception:
        res = []
    con = _kb()
    out = []
    for h in res:
        node = h.get("node") or ""
        nrow = con.execute("SELECT type,props FROM nodes WHERE key=?", (node,)).fetchone()
        props = json.loads(nrow["props"]) if nrow else {}
        # graph-resolve covered niches + media for optional filtering
        niches = [x["key"].split("/", 1)[1] for x in con.execute(
            """SELECT n2.key FROM nodes n1 JOIN edges e ON e.src_id=n1.id JOIN nodes n2 ON n2.id=e.dst_id
               WHERE n1.key=? AND e.type='COVERS'""", (node,))]
        media = [x["key"].split("/", 1)[1] for x in con.execute(
            """SELECT DISTINCT nm.key FROM nodes n1 JOIN edges e ON e.src_id=n1.id
               JOIN nodes nn ON nn.id=e.dst_id AND e.type='COVERS'
               JOIN edges e2 ON e2.src_id=nn.id AND e2.type='IN_MEDIUM'
               JOIN nodes nm ON nm.id=e2.dst_id WHERE n1.key=?""", (node,))]
        if medium and medium not in media:
            continue
        item = {"id": node, "type": h.get("node_type"), "label": h.get("label"),
                "score": h.get("score"), "snippet": h.get("snippet"),
                "covers_niches": niches, "media": media,
                "state": props.get("state"), "quality": props.get("quality"),
                "note": "PROPOSED by retrieval — resolve via query_registry before invoking (R53)"}
        if props.get("state") == "graveyard":
            item["note"] = "GRAVEYARD — dead tool, findable-as-dead, NEVER resolvable (R53)"
        out.append(item)
    return {"query": nl, "proposes": out, "doctrine": "RETRIEVAL PROPOSES — selection is query_registry's"}


# ---- THE REGISTRY DISPOSES -------------------------------------------------
def query_registry(verb=None, medium=None, niche=None, quality_min=None,
                   license_class=None, blender_ver=None):
    """Deterministic facet query over corpus.db (authoritative). Returns ONLY resolvable, verified,
    license-tagged operators/recipes. This is where tool selection TERMINATES (R53)."""
    reg = _reg(); kb = _kb()
    idx = json.loads((CARDS / "_index.json").read_text()) if (CARDS / "_index.json").exists() else {}
    # niche set: explicit, or all niches in a medium (via KB), else all
    niches = None
    if niche:
        niches = {niche}
    elif medium:
        niches = {x["key"].split("/", 1)[1] for x in kb.execute(
            """SELECT n.key FROM nodes n JOIN edges e ON e.src_id=n.id
               JOIN nodes m ON m.id=e.dst_id AND e.type='IN_MEDIUM' WHERE m.key=?""", (f"medium/{medium}",))}
    rows = reg.execute(
        """SELECT c.niche_id, c.canonical_id, c.operator_id, c.blender_ver, c.state,
                  a.license, o.verbs_json
           FROM coverage c LEFT JOIN addons a ON a.canonical_id=c.canonical_id
           LEFT JOIN operators o ON o.canonical_id=c.canonical_id AND o.op_id=c.operator_id
           WHERE c.state IN ('pass','partial')""").fetchall()
    qmin = QUALITY_RANK.get(quality_min, 0) if quality_min else 0
    dedup = {}   # (niche, cid, op) -> row, aggregating versions
    for r in rows:
        if niches and r["niche_id"] not in niches:
            continue
        if blender_ver and r["blender_ver"] != blender_ver:
            continue
        # coverage.operator_id is '{cid}:{opid}'; the card key is 'operator/{cid}::{opid}' — de-prefix
        cid = r["canonical_id"]
        raw_op = r["operator_id"] or ""
        opid = raw_op[len(cid) + 1:] if raw_op.startswith(cid + ":") else raw_op
        ckey = f"operator/{cid}::{opid}"
        cprops = idx.get(ckey, {})
        # verbs: prefer the card index (from operators_enriched) — corpus.db verbs_json under-joins
        verbs = cprops.get("verbs") or (json.loads(r["verbs_json"]) if r["verbs_json"] else [])
        if verb and verb not in verbs:
            continue
        quality = cprops.get("quality") or ("full_generator" if r["state"] == "pass" else "partial")
        if QUALITY_RANK.get(quality, 0) < qmin:
            continue
        # license: registry addons.license first, but empty-string is "missing" -> fall back to card meta
        lic = (r["license"] or "").strip() or cprops.get("license")
        lc = _lic_class(lic)
        if license_class and lc != license_class:
            continue
        dk = (r["niche_id"], cid, opid)
        if dk in dedup:
            dedup[dk]["blender_vers"] = sorted(set(dedup[dk]["blender_vers"] + [r["blender_ver"]]))
            continue
        dedup[dk] = {"niche": r["niche_id"], "id": ckey, "canonical_id": cid,
                     "operator": opid, "verbs": verbs, "blender_vers": [r["blender_ver"]],
                     "state": r["state"], "quality": quality, "license_class": lc,
                     "license_obligation": _lic_oblig(lc), "resolvable": True}
    out = list(dedup.values())
    # recipes for the niche(s), tier-labeled (recipe_verified resolvable; unverified labeled-not)
    import yaml
    for rc in yaml.safe_load(open(ROOT / "inputs" / "recipes.yaml"))["recipes"]:
        if niches and rc["niche"] not in niches:
            continue
        tier = rc.get("tier")
        out.append({"niche": rc["niche"], "id": f"recipe/{rc['niche']}", "recipe": True,
                    "tier": tier, "quality": "asset_fed_minimal" if any("import_asset" in s for s in rc.get("steps", [])) else "composed",
                    "resolvable": tier == "recipe_verified",
                    "note": None if tier == "recipe_verified" else "recipe_unverified — CLAIM, never render-time (R53)"})
    out.sort(key=lambda x: -QUALITY_RANK.get(x.get("quality"), 0))
    return {"facets": {"verb": verb, "medium": medium, "niche": niche, "quality_min": quality_min,
                       "license_class": license_class, "blender_ver": blender_ver},
            "resolvable": [o for o in out if o.get("resolvable")],
            "labeled_unresolvable": [o for o in out if not o.get("resolvable")]}


def _lic_class(license_):
    l = (license_ or "").lower()
    if l in ("by", "cc-by"): return "cc-by"
    if l == "cc0": return "cc0"
    if "royalty" in l: return "royalty_free"
    if l.startswith("gpl"): return "gpl"
    if l in ("", "assumed", "unknown", "none", None): return "unrecorded"
    return l


def _lic_oblig(lc):
    return {"cc-by": "visible attribution required in render credits",
            "cc0": "no attribution required",
            "royalty_free": "BlenderKit: rendered-video only, no 3D-export, incorporation-only",
            "gpl": "GPL applies to add-on code, not render output",
            "unrecorded": "license unrecorded — verify before commercial use"}.get(lc, f"{lc}: verify")


def get_card(id_):
    safe = id_.replace("/", "__").replace("::", "--").replace(".", "_")
    p = CARDS / f"{safe}.md"
    return {"id": id_, "card": p.read_text()} if p.exists() else {"id": id_, "error": "no card"}


def get_usage(id_):
    cid = id_.split("/", 1)[-1].split("::")[0] if "/" in id_ else id_
    p = MANIFESTS / f"{cid}.json"
    return {"id": id_, "manifest": json.loads(p.read_text())} if p.exists() else {"id": id_, "error": "no manifest"}


def find_substitutes(id_or_niche):
    con = _kb()
    key = id_or_niche if id_or_niche.startswith(("operator/", "recipe/", "niche/")) else None
    if not key:
        # try niche, then operator
        if con.execute("SELECT 1 FROM nodes WHERE key=?", (f"niche/{id_or_niche}",)).fetchone():
            key = f"niche/{id_or_niche}"
        else:
            row = con.execute("SELECT key FROM nodes WHERE key LIKE ? AND type='operator' LIMIT 1",
                              (f"operator/%{id_or_niche}%",)).fetchone()
            key = row["key"] if row else None
    if not key:
        return {"query": id_or_niche, "error": "not found"}
    sys.path.insert(0, str(TEMPLATE)); import ragdb
    if key.startswith("niche/"):
        subs = [n for n in ragdb.neighbors(con, key, "COVERS", 1, "in")]
    else:
        subs = [n for n in ragdb.neighbors(con, key, "SUBSTITUTES", 1, "both")]
    return {"query": id_or_niche, "substitutes": [{"id": s["key"], "label": s["label"]} for s in subs]}


def plan_recipe(niche):
    import yaml
    recipes = [r for r in yaml.safe_load(open(ROOT / "inputs" / "recipes.yaml"))["recipes"] if r["niche"] == niche]
    return {"niche": niche, "recipes": recipes,
            "resolvable": any(r.get("tier") == "recipe_verified" for r in recipes)}


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("search_capabilities"); s.add_argument("nl"); s.add_argument("--medium"); s.add_argument("--verb"); s.add_argument("--near"); s.add_argument("--k", type=int, default=8)
    q = sub.add_parser("query_registry")
    for f in ("verb", "medium", "niche", "quality-min", "license-class", "blender-ver"):
        q.add_argument(f"--{f}")
    for name in ("get_card", "get_usage", "find_substitutes", "plan_recipe"):
        p = sub.add_parser(name); p.add_argument("id")
    a = ap.parse_args()
    if a.cmd == "search_capabilities":
        r = search_capabilities(a.nl, a.medium, a.verb, a.near, a.k)
    elif a.cmd == "query_registry":
        r = query_registry(a.verb, a.medium, a.niche, getattr(a, "quality_min"), getattr(a, "license_class"), getattr(a, "blender_ver"))
    elif a.cmd == "get_card":
        r = get_card(a.id)
    elif a.cmd == "get_usage":
        r = get_usage(a.id)
    elif a.cmd == "find_substitutes":
        r = find_substitutes(a.id)
    elif a.cmd == "plan_recipe":
        r = plan_recipe(a.id)
    print(json.dumps(r, indent=1))


if __name__ == "__main__":
    main()
