-- Hybrid-RAG knowledge base schema (template, extracted from Diegesis)
-- One SQLite/libSQL file carries all five methods:
--   knowledge graph        -> nodes + edges (generic, typed, BFS-walkable)
--   context-aware chunking -> chunker.py fills `chunks` at semantic boundaries
--   contextual retrieval   -> chunks.context_header, embedded WITH the text
--   hybrid retrieval       -> chunks_fts (BM25) + chunks.embedding (vector),
--                             fused by Reciprocal Rank Fusion in retrieve.py
--   re-ranking             -> reranker.py re-scores the fused head (no schema needed)
PRAGMA journal_mode = WAL;
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS meta (
  k TEXT PRIMARY KEY,
  v TEXT NOT NULL
);

-- ---------------------------------------------------------------- graph ----
-- `type` is free-form here. To enforce a domain vocabulary, add a CHECK, e.g.:
--   CHECK (type IN ('person','project','document','concept'))
CREATE TABLE IF NOT EXISTS nodes (
  id      INTEGER PRIMARY KEY,
  key     TEXT NOT NULL UNIQUE,           -- e.g. 'doc/design_notes', 'concept/rrf'
  type    TEXT NOT NULL,
  label   TEXT NOT NULL,
  summary TEXT DEFAULT '',
  props   TEXT DEFAULT '{}',              -- JSON
  created_at TEXT DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_nodes_type ON nodes(type);

CREATE TABLE IF NOT EXISTS edges (
  id       INTEGER PRIMARY KEY,
  src_id   INTEGER NOT NULL REFERENCES nodes(id) ON DELETE CASCADE,
  dst_id   INTEGER NOT NULL REFERENCES nodes(id) ON DELETE CASCADE,
  type     TEXT NOT NULL,                 -- e.g. 'PART_OF','REFERENCES','AUTHORED_BY'
  props    TEXT DEFAULT '{}',
  UNIQUE (src_id, dst_id, type)
);
CREATE INDEX IF NOT EXISTS idx_edges_src ON edges(src_id, type);
CREATE INDEX IF NOT EXISTS idx_edges_dst ON edges(dst_id, type);

-- --------------------------------------------------------------- corpus ----
CREATE TABLE IF NOT EXISTS chunks (
  id             INTEGER PRIMARY KEY,
  node_id        INTEGER REFERENCES nodes(id) ON DELETE CASCADE,  -- owning graph node
  kind           TEXT NOT NULL DEFAULT 'doc',    -- e.g. 'code','doc','summary'
  file_path      TEXT DEFAULT '',
  symbol         TEXT DEFAULT '',          -- function/class/heading name
  start_line     INTEGER DEFAULT 0,
  end_line       INTEGER DEFAULT 0,
  context_header TEXT DEFAULT '',          -- contextual-retrieval prefix (source > file > symbol)
  text           TEXT NOT NULL,
  embedding      BLOB,                     -- float32[dim] little-endian; NULL until embedded
  embed_model    TEXT DEFAULT '',
  embed_dim      INTEGER DEFAULT 0,
  content_hash   TEXT NOT NULL,            -- sha256(context_header + text); enables re-ingest
                                           -- without re-embedding unchanged chunks
  created_at     TEXT DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_chunks_node ON chunks(node_id);
CREATE INDEX IF NOT EXISTS idx_chunks_hash ON chunks(content_hash);

-- Keyword leg of hybrid retrieval (BM25 via FTS5), kept in sync by triggers.
CREATE VIRTUAL TABLE IF NOT EXISTS chunks_fts USING fts5(
  text, context_header, symbol,
  content='chunks', content_rowid='id', tokenize='porter unicode61'
);
CREATE TRIGGER IF NOT EXISTS chunks_ai AFTER INSERT ON chunks BEGIN
  INSERT INTO chunks_fts(rowid, text, context_header, symbol)
  VALUES (new.id, new.text, new.context_header, new.symbol);
END;
CREATE TRIGGER IF NOT EXISTS chunks_ad AFTER DELETE ON chunks BEGIN
  INSERT INTO chunks_fts(chunks_fts, rowid, text, context_header, symbol)
  VALUES ('delete', old.id, old.text, old.context_header, old.symbol);
END;
CREATE TRIGGER IF NOT EXISTS chunks_au AFTER UPDATE OF text, context_header, symbol ON chunks BEGIN
  INSERT INTO chunks_fts(chunks_fts, rowid, text, context_header, symbol)
  VALUES ('delete', old.id, old.text, old.context_header, old.symbol);
  INSERT INTO chunks_fts(rowid, text, context_header, symbol)
  VALUES (new.id, new.text, new.context_header, new.symbol);
END;

-- ------------------------------------------------------------- ingestion ----
CREATE TABLE IF NOT EXISTS ingest_log (
  id         INTEGER PRIMARY KEY,
  source_key TEXT NOT NULL,
  src_path   TEXT NOT NULL,
  status     TEXT NOT NULL CHECK (status IN ('ok','partial','failed')),
  detail     TEXT DEFAULT '',
  at         TEXT DEFAULT (datetime('now'))
);
