#!/usr/bin/env bash
# Hybrid-RAG template smoke test — proves all five methods end-to-end in ~5s.
# Self-ingests this folder into a scratch DB; leaves nothing behind.
set -euo pipefail
cd "$(dirname "$0")"

SCRATCH="$(mktemp -d)"
export RAG_DB="$SCRATCH/rag.db"
export RAG_EMBED=mock
trap 'rm -rf "$SCRATCH"' EXIT
pass() { echo "PASS  $1"; }

# 1. schema + init
python3 ragdb.py init > /dev/null
python3 ragdb.py stats | python3 -c "import json,sys; d=json.load(sys.stdin); assert d['nodes']==0 and d['chunks']==0, d"
pass "ragdb init: schema loads clean"

# 2. context-aware ingest (this folder: .py via AST, .md/.sql via headings) + graph edge
python3 ingest.py . --key code/template --type codebase --label "Hybrid-RAG template" > "$SCRATCH/i1.json"
python3 - "$SCRATCH/i1.json" <<'PY'
import json, sys
d = json.load(open(sys.argv[1]))
assert d["status"] == "ok" and d["files"] >= 7 and d["chunks_added"] >= 40, d
PY
python3 - <<'PY'
import ragdb
con = ragdb.connect()
ragdb.upsert_node(con, "concept/reranking", "concept", "Cross-encoder re-ranking")
ragdb.add_edge(con, "code/template", "concept/reranking", "COVERS")
con.commit()
# contextual headers present on every chunk
n = con.execute("SELECT COUNT(*) c FROM chunks WHERE context_header=''").fetchone()["c"]
assert n == 0, f"{n} chunks missing context_header"
# AST chunking produced symbol-scoped code chunks
s = con.execute("SELECT COUNT(*) c FROM chunks WHERE kind='code' AND symbol LIKE 'def %'").fetchone()["c"]
assert s >= 10, s
PY
pass "ingest: AST + heading chunks, contextual headers on all, graph edge added"

# 3. idempotent re-ingest (hash diff keeps everything)
python3 ingest.py . --key code/template --type codebase --label "Hybrid-RAG template" > "$SCRATCH/i2.json"
python3 - "$SCRATCH/i2.json" <<'PY'
import json, sys
d = json.load(open(sys.argv[1]))
assert d["chunks_added"] == 0 and d["chunks_removed"] == 0 and d["chunks_kept"] > 40, d
PY
pass "ingest: re-run adds/removes nothing (content_hash diff)"

# 4. hybrid retrieval: embed (mock) then search; both legs fuse
python3 embedder.py run --batch 64 > /dev/null 2>&1
python3 retrieve.py search "reciprocal rank fusion of keyword and vector legs" --k 5 --json > "$SCRATCH/s.json"
python3 - "$SCRATCH/s.json" <<'PY'
import json, sys
d = json.load(open(sys.argv[1]))
assert d["results"] and d["results"][0]["node"] == "code/template", d["results"][:1]
assert "reranker" not in d, "rerank must be off by default"
PY
pass "retrieve: hybrid BM25+vector search returns grouped results, no rerank by default"

# 5. knowledge-graph features: graph walk + --near filter
python3 retrieve.py graph code/template --json | python3 -c "
import json,sys; n=json.load(sys.stdin)['neighbors']
assert any(x['key']=='concept/reranking' and x['via']=='COVERS' for x in n), n"
python3 retrieve.py search "cross encoder" --near concept/reranking --k 3 --json > "$SCRATCH/near.json"
python3 - "$SCRATCH/near.json" <<'PY'
import json, sys
d = json.load(open(sys.argv[1]))
assert d["results"] and all(r["node"] == "code/template" for r in d["results"]), d["results"]
PY
python3 retrieve.py search "cross encoder" --near concept/nonexistent --k 3 --json > /dev/null 2>&1 \
  && { echo "expected exit 2 for unmatched --near"; exit 1; } || true
pass "graph: BFS walk works; --near filters results through the graph"

# 6. re-ranking: on (mock), off-by-default byte-identical, dead-backend degrade
RAG_RERANK=mock python3 retrieve.py search "reciprocal rank fusion of keyword and vector legs" --k 5 --json > "$SCRATCH/s_rr.json"
python3 - "$SCRATCH/s_rr.json" <<'PY'
import json, sys
d = json.load(open(sys.argv[1]))
assert d.get("reranker") == "mock-lex" and "rerank" in d["results"][0], d
PY
python3 retrieve.py search "reciprocal rank fusion of keyword and vector legs" --k 5 --json > "$SCRATCH/s_off.json"
cmp -s "$SCRATCH/s.json" "$SCRATCH/s_off.json" || { echo "rerank-off output changed"; exit 1; }
RAG_RERANK=http RAG_RERANK_URL=http://127.0.0.1:1/v1/rerank \
  python3 retrieve.py search "fusion" --k 3 --json > "$SCRATCH/dead.json" 2> "$SCRATCH/dead.err"
grep -q "falling back to fusion order" "$SCRATCH/dead.err"
python3 -c "import json; d=json.load(open('$SCRATCH/dead.json')); assert d['results'] and 'reranker' not in d"
pass "rerank: mock reorders+tags; off is byte-identical; dead backend degrades gracefully"

# 7. embedding resilience: dead backend degrades; model-mismatch guard skips vector leg
RAG_EMBED=ollama OLLAMA_URL=http://127.0.0.1:1 \
  python3 retrieve.py search "fusion" --k 3 --json > "$SCRATCH/g1.json" 2> "$SCRATCH/g1.err"
grep -q "embedding backend unavailable" "$SCRATCH/g1.err"
python3 -c "import json; assert json.load(open('$SCRATCH/g1.json'))['results']"
python3 -c "
import ragdb
con = ragdb.connect()
con.execute(\"UPDATE chunks SET embed_model='other-model' WHERE embedding IS NOT NULL\")
con.commit()"
python3 retrieve.py search "fusion" --k 3 --json > "$SCRATCH/g2.json" 2> "$SCRATCH/g2.err"
grep -q "vector leg skipped" "$SCRATCH/g2.err"
python3 -c "import json; assert json.load(open('$SCRATCH/g2.json'))['results']"
pass "embedding: dead backend and model mismatch both degrade to FTS-only with a note"

echo
echo "ALL PASS"
