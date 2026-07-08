# Hybrid-RAG Template

A minimal, dependency-light (numpy only), single-SQLite-file RAG stack that
combines **five retrieval methods**. Extracted and generalized from the
Diegesis knowledge base; drop the folder into any project and adapt.

| # | Method | Where it lives |
|---|--------|----------------|
| 1 | **Hybrid retrieval** (BM25 + vectors, RRF fusion) | `schema.sql` (`chunks`, `chunks_fts` + sync triggers, `embedding` BLOBs) · `ragdb.py` (`fts_search`, `vector_search`) · `retrieve.py` (`_rrf`) |
| 2 | **Knowledge graph** | `schema.sql` (`nodes`, `edges`) · `ragdb.py` (`upsert_node`, `add_edge`, `neighbors` BFS) · `retrieve.py` (`--near` filter, `--expand`, `graph`) |
| 3 | **Context-aware chunking** | `chunker.py` — Python split at AST boundaries (functions/classes/methods), text split at headings, overlap-windowed |
| 4 | **Contextual retrieval** | `chunker.py` builds a `context_header` ("source X > file > symbol") per chunk; `embedder.py` embeds header+text together; FTS indexes the header too |
| 5 | **Re-ranking** | `reranker.py` — cross-encoder pass over the fused head, wired into `retrieve.py` after fusion + graph filter, before node-grouping |

## Quickstart

```bash
pip install numpy

python3 ragdb.py init                      # create rag.db (env RAG_DB overrides path)
python3 ingest.py ./docs --key doc/handbook --type document --label "Handbook"
python3 ingest.py ./src  --key code/backend --type codebase \
        --link "DOCUMENTS:doc/handbook"    # optional graph edge (target must exist)
python3 embedder.py run                    # fill the vector leg (mock by default!)
python3 retrieve.py search "how does auth refresh work" --k 5
```

Everything is deterministic out of the box: the `mock` embedding backend is
for **pipeline testing only** (vectors are hash-seeded noise; BM25 carries all
quality until you switch to a real backend).

## Going real

```bash
# Embeddings — Ollama:
ollama pull bge-m3
export RAG_EMBED=ollama                    # or: openai (any OpenAI-compatible server)
python3 embedder.py run                    # embeds only chunks with embedding IS NULL
# If you previously embedded with mock: clear first —
#   sqlite3 rag.db "UPDATE chunks SET embedding=NULL"
# (mixing models is refused at query time by design)

# Re-ranking — serve a cross-encoder over a /rerank HTTP endpoint.
# NOTE: Ollama cannot serve cross-encoders natively (ollama/ollama#7219);
# use llama.cpp or TEI instead:
#   llama-server -m bge-reranker-v2-m3-Q8_0.gguf --rerank --port 8080
export RAG_RERANK=http                     # default 'off'; 'mock' for CI
python3 retrieve.py search "..." --k 5     # now reranked; --no-rerank to compare
```

## The retrieval pipeline (`retrieve.py search`)

```
BM25 leg (FTS5) ─┐
                 ├─ Reciprocal Rank Fusion ─ graph filter (--near) ─ rerank pool ─ group by node ─ top-k
vector leg ──────┘        (RRF_K=60)           (BFS ≤ --near-depth)   (top 32)     (best chunk/node)
```

Properties worth keeping when you adapt it:
- **Off-by-default rerank**: with `RAG_RERANK` unset, output is byte-identical
  to fusion-only. A dead rerank backend degrades to fusion order (stderr note,
  exit 0) — retrieval never hard-fails because a model server is down.
- **Stable ties**: reranked ties keep RRF order; RRF ties keep leg order.
- **Model guard**: the vector leg is skipped (with a note) if the query
  backend differs from the model the index was embedded with.
- **Idempotent ingest**: chunks are diffed by `content_hash(header+text)`, so
  re-ingesting keeps unchanged chunks *and their embeddings*.

## Environment variables

| Var | Default | Meaning |
|---|---|---|
| `RAG_DB` | `./rag.db` | SQLite file path |
| `RAG_EMBED` | `mock` | `mock` \| `ollama` \| `openai` |
| `RAG_EMBED_MODEL` | `bge-m3` / `text-embedding-3-small` | per backend |
| `RAG_RERANK` | `off` | `off` \| `mock` \| `http` \| `ollama-llm` |
| `RAG_RERANK_URL` | `http://localhost:8080/v1/rerank` | for `http` (llama.cpp/TEI/Infinity/vLLM shapes all parsed) |
| `RAG_RERANK_MODEL` | `bge-reranker-v2-m3` / `llama3.2` | per backend |
| `RAG_RERANK_POOL` | `32` | fused candidates re-scored per query |
| `OLLAMA_URL` | `http://localhost:11434` | ollama backends |
| `OPENAI_BASE_URL`, `OPENAI_API_KEY` | — | openai backend |

## Adapting to your domain

- **Node/edge vocabulary**: `nodes.type` and `edges.type` are free-form TEXT.
  Add `CHECK (type IN (...))` constraints in `schema.sql` once your ontology
  settles (that's how the source project used it).
- **Graph as filter vs. context**: `--near key` constrains results to a
  subgraph; `--expand` attaches 1-hop neighbors to each hit for the LLM to
  follow. Both come free from `ragdb.neighbors`.
- **Other languages**: `chunker.py` uses stdlib `ast` for Python and heading
  splits for everything else. Swap in tree-sitter inside `chunk_file` if you
  ingest C++/JS/etc. and want symbol-boundary chunks there too.
- **Scale**: vector search is numpy brute-force — deterministic and <100 ms up
  to ~100k chunks. Past that, load sqlite-vec and rewrite only
  `ragdb.vector_search`; the schema already fits.
- **Agentic RAG** is a usage pattern, not a schema: point your agent loop at
  `retrieve.py search/show/graph --json` and let it iterate (search → walk
  edges → filtered re-search). All output is JSON-able and exit-coded
  (0 ok, 2 not found, 3 empty index).

## Smoke test

```bash
bash test_smoke.sh    # ~5s, self-ingests this folder, must print ALL PASS
```
