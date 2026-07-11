# /// script
# requires-python = ">=3.11,<3.12"
# dependencies = ["numpy>=1.26"]
# ///
"""embed_discovery.py — vector-embed ONLY the click_to_get discovery add-on chunks so the grown KB
surfaces external-discovery generators on semantic capability queries (not just BM25). Scoped on
purpose: the 4460 Sketchfab CC *asset* chunks stay FTS-only (scene props, browsed via THE LIST, not
semantically routed — and embedding them risks diluting the R55 capability eval). Registry-disposes is
untouched (props.verified already False on these). Idempotent: only embeds NULL-embedding discovery
add-on chunks. Re-run the R55 eval after; if it regresses, this is safe to revert (embeddings only).
"""
import os, sys, pathlib
sys.path.insert(0, str(pathlib.Path("tools/hybrid-rag-template").resolve()))
os.environ.setdefault("RAG_DB", "corpus_kb.db")
os.environ.setdefault("RAG_EMBED", "ollama")
os.environ.setdefault("RAG_EMBED_MODEL", "bge-m3")
import ragdb, embedder

BATCH = 64


def main():
    con = ragdb.connect()
    rows = con.execute(
        """SELECT ch.id, ch.context_header, ch.text
           FROM chunks ch JOIN nodes n ON n.id = ch.node_id
           WHERE ch.embedding IS NULL AND n.key LIKE 'addon/cat::%'
             AND json_extract(n.props,'$.status') = 'click_to_get'
           ORDER BY ch.id""").fetchall()
    print(f"discovery add-on chunks to embed: {len(rows)}", file=sys.stderr)
    done = 0
    for i in range(0, len(rows), BATCH):
        batch = rows[i:i + BATCH]
        texts = [f"{r['context_header']}\n{r['text']}" for r in batch]
        vecs, model = embedder.embed_texts(texts)
        for r, v in zip(batch, vecs):
            con.execute("UPDATE chunks SET embedding=?, embed_model=?, embed_dim=? WHERE id=?",
                        (ragdb.vec_to_blob(v), model, len(v), r["id"]))
        con.commit()
        done += len(batch)
        print(f"  embedded {done}/{len(rows)}", file=sys.stderr)
    total = con.execute("SELECT COUNT(*) c FROM chunks WHERE embedding IS NOT NULL").fetchone()["c"]
    print(f"done. discovery embedded={done}; total embedded chunks={total}")


if __name__ == "__main__":
    main()
