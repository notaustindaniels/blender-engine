"""retrieve — the query interface for the hybrid-RAG template.

Hybrid retrieval: FTS5/BM25 keyword leg + vector leg (when embeddings exist),
fused by Reciprocal Rank Fusion (deterministic, no tuning), optionally
re-ranked by a cross-encoder (env RAG_RERANK, see reranker.py; off by
default — output without it is byte-identical), then grouped by owning graph
node so results read as documents/entities, not raw chunks.

Subcommands:
  search "<query>" [--k 8] [--type TYPE] [--near NODE_KEY]... [--near-depth 2]
                   [--rerank|--no-rerank] [--expand] [--json]
      --near KEY keeps only results whose owning node is KEY or within
      --near-depth hops of KEY in the graph (repeatable; all must match).
  show   <node_key> [--json]            # node record + 1-hop neighborhood
  graph  <node_key> [--edge TYPE] [--depth 2] [--dir out|in|both] [--json]

Exit codes: 0 ok, 2 not found, 3 empty index.
"""
from __future__ import annotations

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ragdb  # noqa: E402

RRF_K = 60


def _rrf(rank_lists: list[list[int]]) -> dict[int, float]:
    scores: dict[int, float] = {}
    for ranks in rank_lists:
        for i, cid in enumerate(ranks):
            scores[cid] = scores.get(cid, 0.0) + 1.0 / (RRF_K + i + 1)
    return scores


def _filter_ids_by_graph(con, ids: list[int], near: list[str], depth: int) -> list[int]:
    """Knowledge-graph filter: keep chunks whose owning node is each --near key
    or within `depth` hops of it."""
    if not near:
        return ids
    keep = []
    for cid in ids:
        row = con.execute("SELECT node_id FROM chunks WHERE id=?", (cid,)).fetchone()
        if not row or row["node_id"] is None:
            continue
        node = con.execute("SELECT key FROM nodes WHERE id=?", (row["node_id"],)).fetchone()
        if not node:
            continue
        try:
            nbrs = ragdb.neighbors(con, node["key"], depth=depth)
        except KeyError:
            continue
        keys = {n["key"] for n in nbrs} | {node["key"]}
        if all(t in keys for t in near):
            keep.append(cid)
    return keep


def cmd_search(a) -> int:
    import reranker
    rr_mode = reranker.resolve_mode(force_on=a.rerank, force_off=a.no_rerank)

    con = ragdb.connect()
    total = con.execute("SELECT COUNT(*) c FROM chunks").fetchone()["c"]
    if total == 0:
        print("index is empty — run ragdb.py init and ingest.py first",
              file=sys.stderr)
        return 3

    # -- hybrid legs ---------------------------------------------------------
    fts = ragdb.fts_search(con, a.query, k=max(a.k * 6, 30))
    rank_lists = [[cid for cid, _ in fts]]

    embedded = con.execute(
        "SELECT COUNT(*) c FROM chunks WHERE embedding IS NOT NULL").fetchone()["c"]
    if embedded:
        import embedder
        try:
            vecs, model = embedder.embed_texts([a.query])
        except Exception as e:  # dead backend -> keyword-only, never a hard fail
            print(f"note: embedding backend unavailable ({e}); "
                  "vector leg skipped (FTS only)", file=sys.stderr)
            vecs = None
        if vecs is not None:
            db_model = con.execute(
                "SELECT embed_model FROM chunks WHERE embedding IS NOT NULL LIMIT 1"
            ).fetchone()["embed_model"]
            if db_model == model:
                vs = ragdb.vector_search(con, vecs[0], k=max(a.k * 6, 30))
                rank_lists.append([cid for cid, _ in vs])
            else:
                print(f"note: query backend {model!r} != index {db_model!r}; "
                      "vector leg skipped (FTS only)", file=sys.stderr)

    # -- fusion + graph filter ----------------------------------------------
    fused = _rrf(rank_lists)
    ids = sorted(fused, key=lambda c: -fused[c])
    ids = _filter_ids_by_graph(con, ids, a.near, a.near_depth)

    # -- optional cross-encoder pass over the head of the fused list.
    # Ties keep RRF order (stable sort); backend failure degrades to fusion.
    rr_scores: dict[int, float] = {}
    rr_tag = None
    if rr_mode and ids:
        pool = ids[:reranker.pool_size()]
        docs = []
        for cid in pool:
            ch = con.execute(
                "SELECT context_header, text FROM chunks WHERE id=?", (cid,)).fetchone()
            docs.append(((ch["context_header"] or "") + "\n" + ch["text"]).strip())
        try:
            scores, rr_tag = reranker.rerank(a.query, docs, rr_mode)
            order = sorted(range(len(pool)), key=lambda i: -scores[i])
            ids = [pool[i] for i in order] + ids[len(pool):]
            rr_scores = {pool[i]: scores[i] for i in range(len(pool))}
        except reranker.RerankUnavailable as e:
            print(f"note: rerank backend unavailable ({e}); "
                  "falling back to fusion order", file=sys.stderr)

    # -- group by owning node; best chunk per node ---------------------------
    results, seen_nodes = [], set()
    for cid in ids:
        ch = con.execute("SELECT * FROM chunks WHERE id=?", (cid,)).fetchone()
        node = (con.execute("SELECT * FROM nodes WHERE id=?", (ch["node_id"],)).fetchone()
                if ch["node_id"] else None)
        nkey = node["key"] if node else f"(unowned:{cid})"
        if a.type and (not node or node["type"] != a.type):
            continue
        if nkey in seen_nodes:
            continue
        seen_nodes.add(nkey)
        item = {"node": nkey, "node_type": node["type"] if node else None,
                "label": node["label"] if node else "", "score": round(fused[cid], 5),
                "snippet": ch["text"][:400],
                "where": f"{ch['file_path']}:{ch['start_line']}" if ch["file_path"] else ch["kind"]}
        if cid in rr_scores:
            item["rerank"] = round(rr_scores[cid], 5)
        if a.expand and node:
            item["neighbors"] = ragdb.neighbors(con, nkey, depth=1)[:12]
        results.append(item)
        if len(results) >= a.k:
            break

    if a.json:
        out = {"query": a.query, "results": results}
        if rr_tag:
            out["reranker"] = rr_tag
        print(json.dumps(out, ensure_ascii=False))
    else:
        if rr_tag:
            print(f"# reranked by {rr_tag} (pool {reranker.pool_size()})")
        for i, r in enumerate(results, 1):
            rr = f" · rr {r['rerank']}" if "rerank" in r else ""
            print(f"{i}. [{r['node_type']}] {r['node']}  (score {r['score']}{rr})")
            print(f"   {r['label']} — {r['where']}")
            print(f"   {r['snippet'][:180].replace(chr(10), ' ')}")
            if a.expand and r.get("neighbors"):
                rel = ", ".join(f"{n['via']}->{n['key']}" for n in r["neighbors"][:6])
                print(f"   edges: {rel}")
    return 0 if results else 2


def cmd_show(a) -> int:
    con = ragdb.connect()
    node = ragdb.node_by_key(con, a.node_key)
    if not node:
        print(f"unknown node: {a.node_key}", file=sys.stderr)
        return 2
    nchunks = con.execute("SELECT COUNT(*) c FROM chunks WHERE node_id=?",
                          (node["id"],)).fetchone()["c"]
    out = {"key": node["key"], "type": node["type"], "label": node["label"],
           "summary": node["summary"], "props": json.loads(node["props"]),
           "chunks": nchunks, "neighbors": ragdb.neighbors(con, a.node_key, depth=1)}
    print(json.dumps(out, indent=None if a.json else 2, ensure_ascii=False))
    return 0


def cmd_graph(a) -> int:
    con = ragdb.connect()
    try:
        nbrs = ragdb.neighbors(con, a.node_key, edge_type=a.edge, depth=a.depth,
                               direction=a.dir)
    except KeyError as e:
        print(str(e), file=sys.stderr)
        return 2
    if a.json:
        print(json.dumps({"node": a.node_key, "neighbors": nbrs}, ensure_ascii=False))
    else:
        for n in nbrs:
            arrow = "->" if n["dir"] == "out" else "<-"
            print(f"d{n['depth']} {arrow} [{n['via']}] {n['key']}  ({n['type']}) {n['label']}")
        if not nbrs:
            print("(no neighbors)")
    return 0


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("search")
    s.add_argument("query")
    s.add_argument("--k", type=int, default=8)
    s.add_argument("--type", default=None)
    s.add_argument("--near", action="append", default=[],
                   help="graph filter: node key (repeatable; all must match)")
    s.add_argument("--near-depth", type=int, default=2)
    s.add_argument("--rerank", action="store_true",
                   help="force re-ranking (requires RAG_RERANK backend)")
    s.add_argument("--no-rerank", action="store_true",
                   help="skip re-ranking even if RAG_RERANK is set")
    s.add_argument("--expand", action="store_true")
    s.add_argument("--json", action="store_true")
    s.set_defaults(fn=cmd_search)

    c = sub.add_parser("show")
    c.add_argument("node_key")
    c.add_argument("--json", action="store_true")
    c.set_defaults(fn=cmd_show)

    g = sub.add_parser("graph")
    g.add_argument("node_key")
    g.add_argument("--edge", default=None)
    g.add_argument("--depth", type=int, default=1)
    g.add_argument("--dir", default="both", choices=["out", "in", "both"])
    g.add_argument("--json", action="store_true")
    g.set_defaults(fn=cmd_graph)

    a = p.parse_args()
    sys.exit(a.fn(a))


if __name__ == "__main__":
    main()
