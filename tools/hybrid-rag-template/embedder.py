"""embedder — embed all un-embedded chunks. Pluggable backends.

Backends (env RAG_EMBED, default 'mock'):
  mock    deterministic sha256-seeded vectors (dim 256). PIPELINE TESTING ONLY —
          similarity is meaningless; FTS still carries retrieval quality.
  ollama  POST $OLLAMA_URL/api/embeddings   model=$RAG_EMBED_MODEL (default bge-m3)
  openai  POST $OPENAI_BASE_URL/v1/embeddings with $OPENAI_API_KEY (any compatible server)

The DB stores embed_model per chunk; mixing models is refused at query time.
Usage:
  python3 embedder.py run [--batch 32] [--limit N]
  python3 embedder.py status
  python3 embedder.py query "some text"      # embed one string, print dim (debug)
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import urllib.request

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
import ragdb as dbx  # noqa: E402

MOCK_DIM = 256


def _mock_embed(texts: list[str]) -> list[np.ndarray]:
    out = []
    for t in texts:
        seed = int.from_bytes(hashlib.sha256(t.encode()).digest()[:8], "little")
        rng = np.random.default_rng(seed)
        v = rng.standard_normal(MOCK_DIM).astype(np.float32)
        out.append(v / (np.linalg.norm(v) or 1.0))
    return out


def _http_json(url: str, payload: dict, headers: dict | None = None) -> dict:
    req = urllib.request.Request(
        url, data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json", **(headers or {})})
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read().decode())


def _ollama_embed(texts: list[str]) -> list[np.ndarray]:
    base = os.environ.get("OLLAMA_URL", "http://localhost:11434").rstrip("/")
    model = os.environ.get("RAG_EMBED_MODEL", "bge-m3")
    out = []
    for t in texts:  # ollama embeddings endpoint is single-prompt
        data = _http_json(f"{base}/api/embeddings", {"model": model, "prompt": t})
        out.append(np.asarray(data["embedding"], dtype=np.float32))
    return out


def _openai_embed(texts: list[str]) -> list[np.ndarray]:
    base = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com").rstrip("/")
    model = os.environ.get("RAG_EMBED_MODEL", "text-embedding-3-small")
    key = os.environ.get("OPENAI_API_KEY", "")
    data = _http_json(f"{base}/v1/embeddings", {"model": model, "input": texts},
                      {"Authorization": f"Bearer {key}"})
    return [np.asarray(d["embedding"], dtype=np.float32) for d in data["data"]]


BACKENDS = {"mock": _mock_embed, "ollama": _ollama_embed, "openai": _openai_embed}


def backend_name() -> str:
    name = os.environ.get("RAG_EMBED", "mock")
    if name not in BACKENDS:
        sys.exit(f"unknown RAG_EMBED={name!r}; options: {sorted(BACKENDS)}")
    return name


def embed_texts(texts: list[str]) -> tuple[list[np.ndarray], str]:
    name = backend_name()
    model_tag = {"mock": f"mock-{MOCK_DIM}",
                 "ollama": "ollama:" + os.environ.get("RAG_EMBED_MODEL", "bge-m3"),
                 "openai": "openai:" + os.environ.get("RAG_EMBED_MODEL", "text-embedding-3-small")}[name]
    return BACKENDS[name](texts), model_tag


def cmd_run(args) -> None:
    con = dbx.connect()
    existing = con.execute(
        "SELECT DISTINCT embed_model FROM chunks WHERE embedding IS NOT NULL").fetchall()
    _, model_tag = embed_texts(["probe"])
    for row in existing:
        if row["embed_model"] and row["embed_model"] != model_tag:
            sys.exit(f"DB already contains embeddings from {row['embed_model']!r}; "
                     f"current backend is {model_tag!r}. Re-embed all "
                     f"(UPDATE chunks SET embedding=NULL) or switch backend.")
    q = "SELECT id, context_header, text FROM chunks WHERE embedding IS NULL ORDER BY id"
    if args.limit:
        q += f" LIMIT {int(args.limit)}"
    rows = con.execute(q).fetchall()
    if not rows:
        print("nothing to embed")
        return
    done = 0
    for i in range(0, len(rows), args.batch):
        batch = rows[i:i + args.batch]
        texts = [(r["context_header"] + "\n\n" + r["text"]).strip() for r in batch]
        vecs, model_tag = embed_texts(texts)
        for r, v in zip(batch, vecs):
            con.execute("UPDATE chunks SET embedding=?, embed_model=?, embed_dim=? WHERE id=?",
                        (dbx.vec_to_blob(v), model_tag, int(v.size), r["id"]))
        con.commit()
        done += len(batch)
        print(f"embedded {done}/{len(rows)}", file=sys.stderr)
    print(json.dumps({"embedded": done, "model": model_tag}))


def cmd_status(_args) -> None:
    con = dbx.connect()
    total = con.execute("SELECT COUNT(*) c FROM chunks").fetchone()["c"]
    done = con.execute("SELECT COUNT(*) c FROM chunks WHERE embedding IS NOT NULL").fetchone()["c"]
    models = [r["embed_model"] for r in con.execute(
        "SELECT DISTINCT embed_model FROM chunks WHERE embedding IS NOT NULL")]
    print(json.dumps({"chunks": total, "embedded": done, "models": models,
                      "backend": backend_name()}))


def cmd_query(args) -> None:
    vecs, model = embed_texts([args.text])
    print(json.dumps({"model": model, "dim": int(vecs[0].size)}))


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run"); r.add_argument("--batch", type=int, default=32); r.add_argument("--limit", type=int, default=0); r.set_defaults(fn=cmd_run)
    s = sub.add_parser("status"); s.set_defaults(fn=cmd_status)
    q = sub.add_parser("query"); q.add_argument("text"); q.set_defaults(fn=cmd_query)
    args = p.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
