"""ragdb — the single database access layer for the hybrid-RAG template.

Default engine: stdlib sqlite3 (zero-install). The file format is
libSQL-compatible; to swap engines later, change `connect()` only.

Vectors: float32 BLOBs in chunks.embedding, searched by numpy brute-force
cosine. Up to roughly 100k chunks that is <100 ms and fully deterministic —
no extension loading, no index tuning. If your corpus outgrows it, load
sqlite-vec as a fast path: the schema needs no change, only vector_search().

CLI:
  python3 ragdb.py init      # create/upgrade the DB from schema.sql
  python3 ragdb.py stats     # counts of nodes/edges/chunks/embedded
"""
from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import struct
import sys
from pathlib import Path

import numpy as np

TEMPLATE_DIR = Path(__file__).resolve().parent
DB_PATH = Path(os.environ.get("RAG_DB", "rag.db"))
SCHEMA_PATH = TEMPLATE_DIR / "schema.sql"


def connect(db_path: Path | str | None = None) -> sqlite3.Connection:
    path = Path(db_path) if db_path else DB_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(str(path))
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")
    return con


def init_db(con: sqlite3.Connection) -> None:
    con.executescript(SCHEMA_PATH.read_text())
    con.commit()


# ------------------------------------------------------------------ graph --
def upsert_node(con, key: str, type_: str, label: str, summary: str = "",
                props: dict | None = None) -> int:
    props_json = json.dumps(props or {}, ensure_ascii=False, sort_keys=True)
    con.execute(
        """INSERT INTO nodes(key, type, label, summary, props)
           VALUES(?,?,?,?,?)
           ON CONFLICT(key) DO UPDATE SET
             label=excluded.label,
             summary=CASE WHEN excluded.summary != '' THEN excluded.summary ELSE nodes.summary END,
             props=excluded.props""",
        (key, type_, label, summary, props_json),
    )
    row = con.execute("SELECT id FROM nodes WHERE key=?", (key,)).fetchone()
    return int(row["id"])


def node_by_key(con, key: str):
    return con.execute("SELECT * FROM nodes WHERE key=?", (key,)).fetchone()


def add_edge(con, src_key: str, dst_key: str, type_: str, props: dict | None = None) -> None:
    src = node_by_key(con, src_key)
    dst = node_by_key(con, dst_key)
    if not src or not dst:
        raise KeyError(f"edge {type_}: missing node "
                       f"{src_key if not src else dst_key!r}")
    con.execute(
        """INSERT OR IGNORE INTO edges(src_id, dst_id, type, props)
           VALUES(?,?,?,?)""",
        (src["id"], dst["id"], type_, json.dumps(props or {}, ensure_ascii=False)),
    )


def neighbors(con, key: str, edge_type: str | None = None, depth: int = 1,
              direction: str = "both") -> list[dict]:
    """Breadth-first graph walk. Returns [{key,type,label,summary,via,dir,depth}]."""
    start = node_by_key(con, key)
    if not start:
        raise KeyError(f"unknown node key: {key}")
    seen = {start["id"]}
    frontier = [start["id"]]
    out: list[dict] = []
    for d in range(1, depth + 1):
        if not frontier:
            break
        qmarks = ",".join("?" * len(frontier))
        clauses, params = [], []
        if direction in ("out", "both"):
            clauses.append(
                f"SELECT e.dst_id AS nid, e.type AS via, 'out' AS dir FROM edges e WHERE e.src_id IN ({qmarks})")
            params += frontier
        if direction in ("in", "both"):
            clauses.append(
                f"SELECT e.src_id AS nid, e.type AS via, 'in' AS dir FROM edges e WHERE e.dst_id IN ({qmarks})")
            params += frontier
        sql = " UNION ALL ".join(clauses)
        if edge_type:
            sql = f"SELECT * FROM ({sql}) WHERE via = ?"
            params.append(edge_type)
        rows = con.execute(sql, params).fetchall()
        next_frontier = []
        for r in rows:
            if r["nid"] in seen:
                continue
            seen.add(r["nid"])
            next_frontier.append(r["nid"])
            n = con.execute("SELECT * FROM nodes WHERE id=?", (r["nid"],)).fetchone()
            out.append({"key": n["key"], "type": n["type"], "label": n["label"],
                        "summary": n["summary"], "via": r["via"], "dir": r["dir"], "depth": d})
        frontier = next_frontier
    return out


# ---------------------------------------------------------------- vectors --
def vec_to_blob(v: np.ndarray) -> bytes:
    v = np.asarray(v, dtype=np.float32).ravel()
    return struct.pack(f"<{v.size}f", *v.tolist())


def blob_to_vec(b: bytes) -> np.ndarray:
    return np.frombuffer(b, dtype="<f4")


def content_hash(context_header: str, text: str) -> str:
    return hashlib.sha256((context_header + "\x00" + text).encode("utf-8")).hexdigest()


def insert_chunk(con, node_id: int | None, kind: str, text: str, *,
                 file_path: str = "", symbol: str = "", start_line: int = 0,
                 end_line: int = 0, context_header: str = "") -> int:
    h = content_hash(context_header, text)
    cur = con.execute(
        """INSERT INTO chunks(node_id, kind, file_path, symbol, start_line, end_line,
                              context_header, text, content_hash)
           VALUES(?,?,?,?,?,?,?,?,?)""",
        (node_id, kind, file_path, symbol, start_line, end_line, context_header, text, h),
    )
    return int(cur.lastrowid)


def vector_search(con, query_vec: np.ndarray, k: int = 8,
                  node_type: str | None = None) -> list[tuple[int, float]]:
    """Brute-force cosine over all embedded chunks. Deterministic."""
    sql = """SELECT c.id, c.embedding FROM chunks c
             LEFT JOIN nodes n ON n.id = c.node_id
             WHERE c.embedding IS NOT NULL"""
    params: list = []
    if node_type:
        sql += " AND n.type = ?"
        params.append(node_type)
    rows = con.execute(sql, params).fetchall()
    if not rows:
        return []
    ids = np.array([r["id"] for r in rows], dtype=np.int64)
    mat = np.vstack([blob_to_vec(r["embedding"]) for r in rows])
    q = np.asarray(query_vec, dtype=np.float32).ravel()
    denom = (np.linalg.norm(mat, axis=1) * (np.linalg.norm(q) or 1e-9))
    denom[denom == 0] = 1e-9
    sims = mat @ q / denom
    order = np.argsort(-sims, kind="stable")[:k]
    return [(int(ids[i]), float(sims[i])) for i in order]


def fts_search(con, query: str, k: int = 8) -> list[tuple[int, float]]:
    """BM25 keyword search. Sanitizes the query into FTS-safe OR-of-terms."""
    terms = ["".join(ch for ch in t if ch.isalnum() or ch == "_")
             for t in query.split()]
    terms = [t for t in terms if t]
    if not terms:
        return []
    match = " OR ".join(f'"{t}"' for t in terms)
    try:
        rows = con.execute(
            """SELECT rowid, bm25(chunks_fts) AS score FROM chunks_fts
               WHERE chunks_fts MATCH ? ORDER BY score LIMIT ?""",
            (match, k),
        ).fetchall()
    except sqlite3.OperationalError:
        return []
    # bm25: lower is better -> convert to descending positive score
    return [(int(r["rowid"]), -float(r["score"])) for r in rows]


# --------------------------------------------------------------------- cli --
def main() -> None:
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    con = connect()
    if cmd == "init":
        init_db(con)
        print(json.dumps({"db": str(DB_PATH), "initialized": True}))
    elif cmd == "stats":
        out = {t: con.execute(f"SELECT COUNT(*) c FROM {t}").fetchone()["c"]
               for t in ("nodes", "edges", "chunks")}
        out["embedded"] = con.execute(
            "SELECT COUNT(*) c FROM chunks WHERE embedding IS NOT NULL").fetchone()["c"]
        out["db"] = str(DB_PATH)
        print(json.dumps(out))
    else:
        sys.exit("usage: ragdb.py init|stats   (env RAG_DB overrides ./rag.db)")


if __name__ == "__main__":
    main()
