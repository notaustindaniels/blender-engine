"""ingest — turn a file or directory into a graph node + context-aware chunks.

One node per ingested source; every chunk is owned by that node and carries a
contextual-retrieval header. Re-ingesting is cheap and idempotent: chunks are
matched by content_hash, so unchanged chunks (and their embeddings) survive,
new ones are inserted, stale ones are deleted.

Usage:
  python3 ingest.py PATH [--key doc/my_notes] [--type document] [--label "My notes"]
                    [--summary "..."] [--link "EDGE_TYPE:other/node/key"]...
                    [--include-ext .py,.md,...]

Then:  python3 embedder.py run     # fill the vector leg
       python3 retrieve.py search "..."
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import chunker  # noqa: E402
import ragdb    # noqa: E402

SKIP_DIRS = {".git", "__pycache__", "node_modules", ".venv", "venv"}
DEFAULT_EXTS = {".py", ".md", ".rst", ".txt", ".sql", ".json", ".yaml", ".yml",
                ".toml", ".cfg", ".ini", ".sh", ".js", ".ts", ".html", ".css"}


def _slug(s: str) -> str:
    return re.sub(r"[^a-z0-9_]+", "_", s.lower()).strip("_") or "source"


def iter_files(root: Path, exts: set[str]):
    if root.is_file():
        yield root
        return
    for p in sorted(root.rglob("*")):
        if p.is_file() and p.suffix.lower() in exts \
                and not any(part in SKIP_DIRS for part in p.parts):
            yield p


def ingest(path: Path, key: str, type_: str, label: str, summary: str,
           links: list[str], exts: set[str]) -> dict:
    con = ragdb.connect()
    node_id = ragdb.upsert_node(con, key, type_, label, summary)

    # gather new chunk set
    root = path if path.is_dir() else path.parent
    new: dict[str, chunker.Chunk] = {}
    files = 0
    for f in iter_files(path, exts):
        files += 1
        for ch in chunker.chunk_file(f, key, root):
            new[ragdb.content_hash(ch.context_header, ch.text)] = ch

    # diff against what the node already owns (embeddings on unchanged rows survive)
    existing = {r["content_hash"]: r["id"] for r in con.execute(
        "SELECT id, content_hash FROM chunks WHERE node_id=?", (node_id,))}
    stale = [cid for h, cid in existing.items() if h not in new]
    added = 0
    for h, ch in new.items():
        if h in existing:
            continue
        ragdb.insert_chunk(con, node_id, ch.kind, ch.text, file_path=ch.file_path,
                           symbol=ch.symbol, start_line=ch.start_line,
                           end_line=ch.end_line, context_header=ch.context_header)
        added += 1
    if stale:
        qmarks = ",".join("?" * len(stale))
        con.execute(f"DELETE FROM chunks WHERE id IN ({qmarks})", stale)

    # optional graph edges: "EDGE_TYPE:target/node/key" (target must exist)
    for spec in links:
        etype, _, target = spec.partition(":")
        if not etype or not target:
            raise SystemExit(f"bad --link {spec!r}; expected EDGE_TYPE:node/key")
        ragdb.add_edge(con, key, target, etype)

    status = "ok" if files else "failed"
    con.execute("INSERT INTO ingest_log(source_key, src_path, status, detail) VALUES(?,?,?,?)",
                (key, str(path), status,
                 f"files={files} added={added} kept={len(existing) - len(stale)} removed={len(stale)}"))
    con.commit()
    return {"key": key, "files": files, "chunks_added": added,
            "chunks_kept": len(existing) - len(stale), "chunks_removed": len(stale),
            "edges": len(links), "status": status}


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("path", type=Path)
    p.add_argument("--key", default=None, help="node key (default: source/<name>)")
    p.add_argument("--type", default="source", help="node type (default: source)")
    p.add_argument("--label", default=None)
    p.add_argument("--summary", default="")
    p.add_argument("--link", action="append", default=[],
                   metavar="EDGE_TYPE:node/key",
                   help="add a graph edge from this node (repeatable)")
    p.add_argument("--include-ext", default=None,
                   help="comma-separated extension whitelist (default: common text/code)")
    a = p.parse_args()
    if not a.path.exists():
        sys.exit(f"no such path: {a.path}")
    key = a.key or f"source/{_slug(a.path.stem if a.path.is_file() else a.path.name)}"
    label = a.label or a.path.name
    exts = ({e.strip().lower() if e.strip().startswith(".") else "." + e.strip().lower()
             for e in a.include_ext.split(",")} if a.include_ext else DEFAULT_EXTS)
    print(json.dumps(ingest(a.path, key, a.type, label, a.summary, a.link, exts)))


if __name__ == "__main__":
    main()
