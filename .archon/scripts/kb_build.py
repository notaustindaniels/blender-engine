# /// script
# requires-python = ">=3.11,<3.12"
# dependencies = ["pyyaml>=6", "numpy>=1.26"]
# ///
"""kb_build.py — build corpus_kb.db, the second DERIVED database (D-008 R51).

Rebuilt deterministically from the SAME JSON manifests + taxonomy + recipes + graveyard that build
corpus.db — never hand-edited. Uses the vendored hybrid-RAG template (ragdb.py) AS-IS. Populates the
fixed-vocabulary graph (nodes/edges) and ingests Tier-1 operator/recipe cards as chunks. The graveyard
is ingested labeled state=graveyard (findable-as-dead, R53). Embedding model pinned in meta.

Node types: addon operator recipe asset niche verb medium category license
Edge types: PROVIDES COVERS PERFORMS IN_MEDIUM COMPOSES LICENSED PART_OF SUBSTITUTES

Usage: RAG_DB=corpus_kb.db uv run .archon/scripts/kb_build.py
"""
import json, glob, pathlib, sys, os
import yaml

sys.path.insert(0, str(pathlib.Path("tools/hybrid-rag-template").resolve()))
import ragdb  # vendored, as-is

os.environ.setdefault("RAG_DB", "corpus_kb.db")
EMBED_MODEL = os.environ.get("RAG_EMBED_MODEL", "bge-m3")   # local/open, $0 (ollama); mock in CI

TAX = yaml.safe_load(open("inputs/taxonomy.yaml"))
MEDIUM = yaml.safe_load(open("inputs/niche-medium.yaml"))["medium"]
RECIPES = yaml.safe_load(open("inputs/recipes.yaml"))["recipes"]
VERBS = TAX["meta"]["verb_enum"]
CARDS = json.loads(open("cards/_index.json").read()) if pathlib.Path("cards/_index.json").exists() else {}


def lic_class(license_):
    l = (license_ or "").lower()
    if l in ("by", "cc-by", "cc_by"): return "cc-by"
    if l == "cc0": return "cc0"
    if l == "by-sa": return "cc-by-sa"
    if "royalty" in l: return "royalty_free"
    if l.startswith("gpl"): return "gpl"
    if l in ("", "assumed", "unknown", "none"): return "unrecorded"
    return l


def card_text(key):
    safe = key.replace("/", "__").replace("::", "--").replace(".", "_")
    p = pathlib.Path(f"cards/{safe}.md")
    return p.read_text() if p.exists() else ""


def main():
    con = ragdb.connect()
    ragdb.init_db(con)
    con.execute("DELETE FROM edges"); con.execute("DELETE FROM chunks"); con.execute("DELETE FROM nodes")
    con.execute("INSERT OR REPLACE INTO meta(k,v) VALUES('embed_model',?)", (EMBED_MODEL,))
    con.execute("INSERT OR REPLACE INTO meta(k,v) VALUES('built_from','manifests+taxonomy+recipes+graveyard')")
    con.execute("INSERT OR REPLACE INTO meta(k,v) VALUES('doctrine','RETRIEVAL PROPOSES / REGISTRY DISPOSES (R53)')")

    N = lambda *a, **k: ragdb.upsert_node(con, *a, **k)
    # ---- scaffold: category, niche, verb, medium, license nodes ----
    for m in sorted(set(MEDIUM.values())):
        N(f"medium/{m}", "medium", m)
    for v in VERBS:
        N(f"verb/{v}", "verb", v)
    for lc in ("cc-by", "cc0", "cc-by-sa", "royalty_free", "gpl", "unrecorded"):
        N(f"license/{lc}", "license", lc)
    niche_cat = {}
    for cat in TAX["categories"]:
        N(f"category/{cat['name']}", "category", cat["name"])
        for n in (cat.get("niches") or []):
            nid = n["id"]; niche_cat[nid] = cat["name"]
            N(f"niche/{nid}", "niche", nid,
              summary="; ".join(n.get("aliases") or []),
              props={"wave": int(n.get("wave", 1)), "core": bool(n.get("core", False))})
            ragdb.add_edge(con, f"niche/{nid}", f"category/{cat['name']}", "PART_OF")
            med = MEDIUM.get(nid)
            if med:
                ragdb.add_edge(con, f"niche/{nid}", f"medium/{med}", "IN_MEDIUM")

    def ensure_niche(nid):
        if not ragdb.node_by_key(con, f"niche/{nid}"):
            N(f"niche/{nid}", "niche", nid, props={"wave": 0, "core": False})

    def ensure_license(lc):
        if not ragdb.node_by_key(con, f"license/{lc}"):
            N(f"license/{lc}", "license", lc)

    # ---- addons + operators from manifests ----
    niche_ops = {}
    for mp in sorted(glob.glob("manifests/*.json")):
        man = json.loads(open(mp).read())
        cid = man["canonical_id"]
        verify = man.get("verify") or {}
        passing = sorted(k for k, s in verify.items() if (s or {}).get("state") in ("pass", "partial"))
        # find the vault meta for license
        lic = None
        for g in glob.glob(f"vault/{cid}/*/meta.json"):
            md = json.loads(open(g).read()); lic = md.get("usage_license") or md.get("license"); break
        addon_type = "asset" if man.get("artifact_type") in ("asset_pack",) else "addon"
        N(f"addon/{cid}", addon_type, cid,
          summary=(man.get("enrich_note") or man.get("name") or "")[:200],
          props={"artifact_type": man.get("artifact_type"), "passing": passing,
                 "license": lic, "state": "verified" if passing else "unverified"})
        ensure_license(lic_class(lic))
        ragdb.add_edge(con, f"addon/{cid}", f"license/{lic_class(lic)}", "LICENSED")
        for op in (man.get("operators_enriched") or []):
            opid = op.get("id", cid)
            okey = f"operator/{cid}::{opid}"
            N(okey, "operator", opid,
              summary=(man.get("enrich_note") or "")[:200],
              props={"cid": cid, "kind": op.get("kind"), "quality": (CARDS.get(okey, {}) or {}).get("quality"),
                     "versions": passing})
            ragdb.add_edge(con, f"addon/{cid}", okey, "PROVIDES")
            for v in (op.get("verbs") or []):
                if ragdb.node_by_key(con, f"verb/{v}"):
                    ragdb.add_edge(con, okey, f"verb/{v}", "PERFORMS")
            for nid in (op.get("niches") or []):
                ensure_niche(nid)
                ragdb.add_edge(con, okey, f"niche/{nid}", "COVERS")
                niche_ops.setdefault(nid, []).append(okey)
            # Tier-1 card chunk
            txt = card_text(okey)
            if txt:
                nid_row = ragdb.node_by_key(con, okey)
                ragdb.insert_chunk(con, nid_row["id"], "card", txt,
                                   context_header=f"operator {opid} > {cid}", symbol=opid)

    # ---- recipes ----
    for r in RECIPES:
        niche = r["niche"]; rkey = f"recipe/{niche}"
        ensure_niche(niche)
        N(rkey, "recipe", niche, summary=(r.get("note") or "")[:200],
          props={"tier": r.get("tier"), "quality": (CARDS.get(rkey, {}) or {}).get("quality")})
        ragdb.add_edge(con, rkey, f"niche/{niche}", "COVERS")
        niche_ops.setdefault(niche, []).append(rkey)
        for s in (r.get("steps") or []):
            if "op" in s and s.get("artifact_cid"):
                tgt = f"addon/{s['artifact_cid']}"
                if ragdb.node_by_key(con, tgt):
                    ragdb.add_edge(con, rkey, tgt, "COMPOSES")
            elif "import_asset" in s:
                parts = s["import_asset"].split("/")
                if len(parts) >= 4:
                    tgt = f"addon/{parts[3]}"
                    if ragdb.node_by_key(con, tgt):
                        ragdb.add_edge(con, rkey, tgt, "COMPOSES")
        txt = card_text(rkey)
        if txt:
            nrow = ragdb.node_by_key(con, rkey)
            ragdb.insert_chunk(con, nrow["id"], "card", txt,
                               context_header=f"recipe {niche}", symbol=niche)

    # ---- SUBSTITUTES: operators/recipes covering the same niche are substitutable ----
    for nid, keys in niche_ops.items():
        for i in range(len(keys)):
            for j in range(i + 1, len(keys)):
                try:
                    ragdb.add_edge(con, keys[i], keys[j], "SUBSTITUTES", {"via_niche": nid})
                except KeyError:
                    pass

    # ---- graveyard ingested labeled state=graveyard (findable-as-dead, R53) ----
    gy = 0
    gp = pathlib.Path("graveyard.jsonl")
    if gp.exists():
        for line in gp.read_text().splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                g = json.loads(line)
            except Exception:
                continue
            gid = g.get("canonical_id") or g.get("url") or g.get("id") or f"gy{gy}"
            gkey = f"addon/graveyard::{gid}"[:200]
            reason = g.get("reason") or g.get("why") or g.get("status") or "graveyard"
            try:
                N(gkey, "addon", str(gid)[:80], summary=str(reason)[:200],
                  props={"state": "graveyard", "url": g.get("url"), "reason": reason})
                nrow = ragdb.node_by_key(con, gkey)
                ragdb.insert_chunk(con, nrow["id"], "graveyard",
                                   f"DEAD: {gid} — {reason}. Findable-as-dead (R53); never resolvable.",
                                   context_header="graveyard", symbol=str(gid)[:60])
                gy += 1
            except Exception:
                pass

    con.commit()
    stats = {t: con.execute(f"SELECT COUNT(*) c FROM {t}").fetchone()["c"] for t in ("nodes", "edges", "chunks")}
    by_type = {r["type"]: r["c"] for r in con.execute("SELECT type,COUNT(*) c FROM nodes GROUP BY type")}
    print(json.dumps({"db": os.environ["RAG_DB"], **stats, "graveyard_nodes": gy,
                      "nodes_by_type": by_type, "embed_model": EMBED_MODEL}))


if __name__ == "__main__":
    main()
