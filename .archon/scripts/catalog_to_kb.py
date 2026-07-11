# /// script
# requires-python = ">=3.11,<3.12"
# dependencies = ["numpy>=1.26"]
# ///
"""catalog_to_kb.py — grow corpus_kb.db to hold THE WHOLE CATALOG (D-008 catalog campaign, face 1).
After kb_build (which adds gated add-ons + taxonomy + graveyard), this adds the remaining catalog
entries (Sketchfab CC assets, external-discovery click_to_get items) as findable nodes + FTS/vector
chunks, LABELED by status in props. Retrieval-proposes / registry-disposes intact: click_to_get and
excluded entries are findable but their props mark them non-verified (never resolvable as verified).

Node types (schema CHECK): sketchfab CC -> 'asset'; discovery add-ons -> 'addon'. A card chunk per
entry makes it BM25-findable immediately (FTS triggers) + vector-embeddable by embedder.py.
Usage: RAG_DB=corpus_kb.db uv run .archon/scripts/catalog_to_kb.py
"""
import json, os, sys, pathlib
sys.path.insert(0, str(pathlib.Path("tools/hybrid-rag-template").resolve()))
import ragdb
os.environ.setdefault("RAG_DB", "corpus_kb.db")
ROOT = pathlib.Path(__file__).resolve().parents[2]


def main():
    con = ragdb.connect()
    existing = {r["key"] for r in con.execute("SELECT key FROM nodes")}
    added = chunks = 0
    for line in open(ROOT / "catalog.jsonl"):
        line = line.strip()
        if not line:
            continue
        e = json.loads(line)
        market = e.get("marketplace") or "?"
        # node key + type
        if market == "sketchfab":
            key, ntype = f"asset/{e['catalog_id']}", "asset"
        elif e["status"] == "excluded":
            key, ntype = f"addon/cat::{e['catalog_id']}", "addon"
        else:
            key, ntype = f"addon/cat::{e['catalog_id']}", "addon"
        if key in existing:
            continue
        props = {"status": e["status"], "marketplace": market, "url": e.get("url"),
                 "license": e.get("license"), "price_class": e.get("price_class"),
                 "provisional": e.get("provisional"), "gate_state": e.get("gate_state"),
                 "reason": e.get("reason"), "verified": e["status"] == "auto_acquired_verified" and e.get("gate_state") in ("pass", "partial")}
        nid = ragdb.upsert_node(con, key, ntype, (e.get("name") or e["catalog_id"])[:120],
                                summary=(e.get("card") or "")[:200], props=props)
        # card chunk (FTS-findable; embeddable). Include status so retrieval can surface labeled.
        card = (e.get("card") or "") + f"\n[{e['status']}] {market} · {e.get('price_class') or ''} · " \
               f"{e.get('license') or ''} · {e.get('category') or ''}"
        ragdb.insert_chunk(con, nid, "catalog_card", card,
                           context_header=f"{market} {e['status']} > {e.get('name','')}",
                           symbol=(e.get("category") or e.get("name") or "")[:60])
        added += 1; chunks += 1
    con.commit()
    from collections import Counter
    by_type = {r["type"]: r["c"] for r in con.execute("SELECT type,COUNT(*) c FROM nodes GROUP BY type")}
    print(json.dumps({"catalog_nodes_added": added, "chunks_added": chunks,
                      "total_nodes": con.execute("SELECT COUNT(*) c FROM nodes").fetchone()["c"],
                      "nodes_by_type": by_type,
                      "total_chunks": con.execute("SELECT COUNT(*) c FROM chunks").fetchone()["c"]}))


if __name__ == "__main__":
    main()
