# /// script
# requires-python = ">=3.11,<3.12"
# dependencies = ["pyyaml>=6", "numpy>=1.26"]
# ///
"""eval_golden.py — the R55 acceptance gate (D-008). Runs the golden-query set through the KB's
hybrid retrieval and measures hit@5: a query HITS if any expected substring appears in the top-5
returned cards (key/symbol/label/text). hit@5 >= threshold (0.90) or exit 1 → BLOCKS snapshot tagging.

Run: RAG_DB=corpus_kb.db RAG_EMBED=ollama RAG_EMBED_MODEL=bge-m3 uv run --with numpy .archon/eval/eval_golden.py
"""
import json, os, sys, pathlib, subprocess, sqlite3
import yaml

TEMPLATE = pathlib.Path("tools/hybrid-rag-template").resolve()
GOLDEN = yaml.safe_load(open(".archon/eval/golden_queries.yaml"))
DB = str(pathlib.Path(os.environ.get("RAG_DB", "corpus_kb.db")).resolve())


def covered_niches(node_key):
    """Resolve a returned node to the niches it COVERS via the KB graph — the honest 'right card'
    signal (retrieve returns canonical/operator keys; the niche lives on the COVERS edge)."""
    try:
        con = sqlite3.connect(DB); con.row_factory = sqlite3.Row
        rows = con.execute(
            """SELECT n2.key FROM nodes n1 JOIN edges e ON e.src_id=n1.id
               JOIN nodes n2 ON n2.id=e.dst_id
               WHERE n1.key=? AND e.type='COVERS'""", (node_key,)).fetchall()
        return [r["key"] for r in rows]
    except Exception:
        return []


def top_k(query, k=5):
    env = dict(os.environ, RAG_DB=DB,
               RAG_EMBED=os.environ.get("RAG_EMBED", "ollama"),
               RAG_EMBED_MODEL=os.environ.get("RAG_EMBED_MODEL", "bge-m3"))
    r = subprocess.run([sys.executable, "retrieve.py", "search", query, "--k", str(k), "--json"],
                       cwd=TEMPLATE, env=env, capture_output=True, text=True)
    try:
        d = json.loads(r.stdout)
    except Exception:
        return []
    res = d.get("results") or d.get("hits") or (d if isinstance(d, list) else [])
    blobs = []
    for h in res[:k]:
        node = h.get("node") or h.get("node_key") or h.get("key") or ""
        parts = [str(h.get(f, "")) for f in ("node", "label", "snippet", "symbol", "text", "context_header")]
        parts += covered_niches(node)              # resolve niche via the graph
        blobs.append(" ".join(parts).lower())
    return blobs


def main():
    qs = GOLDEN["queries"]
    thr = float(GOLDEN.get("threshold_hit_at_5", 0.90))
    hits = 0
    misses = []
    for item in qs:
        q = item["q"]
        expect = [e.lower() for e in item["expect"]]
        blobs = top_k(q, 5)
        hit = any(any(e in b for b in blobs) for e in expect)
        if hit:
            hits += 1
        else:
            misses.append(q)
    rate = hits / len(qs) if qs else 0.0
    print(json.dumps({"queries": len(qs), "hits": hits, "hit_at_5": round(rate, 3),
                      "threshold": thr, "pass": rate >= thr, "misses": misses}, indent=1))
    sys.exit(0 if rate >= thr else 1)


if __name__ == "__main__":
    main()
