"""reranker — optional cross-encoder re-ranking stage for retrieve.py.

Runs AFTER hybrid RRF fusion and the graph filter,
re-scoring the top RAG_RERANK_POOL (default 32) candidates against the
query; retrieve.py falls back to fusion order if the backend is unreachable.
With RAG_RERANK unset, retrieve.py output is byte-identical to the
pre-rerank behavior (so it can be layered onto any pipeline without changing baseline behavior).

Backends (env RAG_RERANK, default 'off'):
  off         no reranking. The default.
  mock        deterministic lexical-overlap scorer. PIPELINE TESTING ONLY —
              real relevance quality comes from a cross-encoder.
  http        any Jina/Cohere-shaped rerank endpoint. THIS is the
              bge-reranker-v2-m3 path; serve it locally with either:
                llama.cpp:  llama-server -m bge-reranker-v2-m3-Q8_0.gguf --rerank
                            -> POST http://localhost:8080/v1/rerank
                TEI:        text-embeddings-router --model-id BAAI/bge-reranker-v2-m3
                            -> POST http://localhost:8080/rerank
              env: RAG_RERANK_URL   (default http://localhost:8080/v1/rerank)
                   RAG_RERANK_MODEL (default bge-reranker-v2-m3)
  ollama-llm  pointwise LLM-judge scoring (0-100, temperature 0) via Ollama
              /api/generate. Weaker than a true cross-encoder; use it when
              installing llama.cpp/TEI is unwanted. NOTE: Ollama has NO native
              rerank endpoint for cross-encoders (ollama/ollama#7219 unmerged
              as of 2026-07); /api/embed-based reranker "hacks" bypass the
              model's classification head and score garbage — refused here.
              env: OLLAMA_URL            (default http://localhost:11434)
                   RAG_RERANK_MODEL (default llama3.2)

Tuning:
  RAG_RERANK_POOL  candidates re-scored per query (default 32)

Usage (debug CLI):
  python3 reranker.py status
  python3 reranker.py score "query" "doc one" "doc two" [--json]
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request

MAX_DOC_CHARS = 1600   # bge-reranker-v2-m3 default serving window is 512 tokens
DEFAULT_POOL = 32


class RerankUnavailable(Exception):
    """Backend unreachable/misbehaving — caller degrades to fusion order."""


# ------------------------------------------------------------------ common --
def _http_json(url: str, payload: dict, timeout: int = 120) -> dict | list:
    req = urllib.request.Request(
        url, data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode())
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError) as e:
        raise RerankUnavailable(f"{url}: {e}") from e


def _tok(s: str) -> list[str]:
    return re.findall(r"[a-z0-9_]+", s.lower())


# ---------------------------------------------------------------- backends --
def _mock_scores(query: str, docs: list[str]) -> list[float]:
    """Deterministic lexical overlap: |q ∩ d| / |q|, +0.25 exact-phrase bonus."""
    q = _tok(query)
    qset = set(q)
    qphrase = " ".join(q)
    out: list[float] = []
    for d in docs:
        toks = _tok(d)
        if not qset or not toks:
            out.append(0.0)
            continue
        score = len(qset & set(toks)) / len(qset)
        if qphrase and qphrase in " ".join(toks):
            score += 0.25
        out.append(round(min(score, 1.0), 6))
    return out


def _parse_rerank_response(resp: dict | list, n: int) -> list[float]:
    items = resp.get("results") if isinstance(resp, dict) else resp
    if not isinstance(items, list):
        raise RerankUnavailable(f"unrecognized rerank response shape: {str(resp)[:200]}")
    scores = [0.0] * n
    for it in items:
        try:
            i = int(it["index"])
            s = float(it.get("relevance_score", it.get("score")))
        except (KeyError, TypeError, ValueError) as e:
            raise RerankUnavailable(f"bad rerank result item: {it!r}") from e
        if 0 <= i < n:
            scores[i] = s
    return scores


def _http_scores(query: str, docs: list[str]) -> list[float]:
    """Generic /rerank endpoint. Sends both Jina/Cohere ('documents') and TEI
    ('texts') field names; parses 'results'-wrapped or bare-list responses and
    'relevance_score' or 'score' keys. Covers llama.cpp --rerank, TEI,
    Infinity, vLLM, LocalAI."""
    url = os.environ.get("RAG_RERANK_URL", "http://localhost:8080/v1/rerank")
    model = os.environ.get("RAG_RERANK_MODEL", "bge-reranker-v2-m3")
    resp = _http_json(url, {"model": model, "query": query,
                            "documents": docs, "texts": docs,
                            "top_n": len(docs)})
    return _parse_rerank_response(resp, len(docs))


_JUDGE_PROMPT = (
    "You are a search relevance judge. Score how relevant the DOCUMENT is to "
    "the QUERY on an integer scale of 0 (irrelevant) to 100 (perfectly "
    "relevant). Reply with ONLY the integer.\n\nQUERY: {q}\n\nDOCUMENT:\n{d}\n\nSCORE:"
)


def _ollama_llm_scores(query: str, docs: list[str]) -> list[float]:
    base = os.environ.get("OLLAMA_URL", "http://localhost:11434").rstrip("/")
    model = os.environ.get("RAG_RERANK_MODEL", "llama3.2")
    out: list[float] = []
    for d in docs:
        resp = _http_json(f"{base}/api/generate",
                          {"model": model,
                           "prompt": _JUDGE_PROMPT.format(q=query, d=d),
                           "stream": False,
                           "options": {"temperature": 0, "seed": 0,
                                       "num_predict": 8}})
        if isinstance(resp, dict) and "error" in resp:
            raise RerankUnavailable(f"ollama: {resp['error']}")
        m = re.search(r"\d+", str(resp.get("response", "")) if isinstance(resp, dict) else "")
        out.append(min(int(m.group()), 100) / 100.0 if m else 0.0)
    return out


BACKENDS = {"mock": _mock_scores, "http": _http_scores, "ollama-llm": _ollama_llm_scores}


# --------------------------------------------------------------------- api --
def resolve_mode(force_on: bool = False, force_off: bool = False) -> str | None:
    """Backend name to use, or None for no reranking. Exit 2 on bad config."""
    if force_off:
        return None
    name = os.environ.get("RAG_RERANK", "off")
    if name in ("", "off"):
        if force_on:
            print("--rerank requested but RAG_RERANK is unset/off; set "
                  "RAG_RERANK=mock|http|ollama-llm (see reranker.py)",
                  file=sys.stderr)
            raise SystemExit(2)
        return None
    if name not in BACKENDS:
        print(f"unknown RAG_RERANK={name!r}; options: off, "
              f"{', '.join(sorted(BACKENDS))}", file=sys.stderr)
        raise SystemExit(2)
    return name


def pool_size() -> int:
    try:
        return max(1, int(os.environ.get("RAG_RERANK_POOL", DEFAULT_POOL)))
    except ValueError:
        return DEFAULT_POOL


def model_tag(name: str) -> str:
    return {"mock": "mock-lex",
            "http": "http:" + os.environ.get("RAG_RERANK_MODEL", "bge-reranker-v2-m3"),
            "ollama-llm": "ollama-llm:" + os.environ.get("RAG_RERANK_MODEL", "llama3.2"),
            }[name]


def rerank(query: str, docs: list[str], name: str) -> tuple[list[float], str]:
    """Score each doc against the query. Returns (scores, model_tag).
    Raises RerankUnavailable when the backend can't be reached."""
    clipped = [d[:MAX_DOC_CHARS] for d in docs]
    return BACKENDS[name](query, clipped), model_tag(name)


# --------------------------------------------------------------------- cli --
def cmd_status(_a) -> None:
    name = os.environ.get("RAG_RERANK", "off")
    print(json.dumps({"backend": name,
                      "valid": name in ("off", "") or name in BACKENDS,
                      "pool": pool_size(),
                      "tag": model_tag(name) if name in BACKENDS else None}))


def cmd_score(a) -> None:
    mode = resolve_mode(force_on=True)  # explicit scoring implies a backend
    scores, tag = rerank(a.query, a.docs, mode)
    if a.json:
        print(json.dumps({"reranker": tag, "scores": scores}))
    else:
        for s, d in sorted(zip(scores, a.docs), key=lambda x: -x[0]):
            print(f"{s:8.4f}  {d[:90]}")


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("status"); s.set_defaults(fn=cmd_status)
    c = sub.add_parser("score")
    c.add_argument("query")
    c.add_argument("docs", nargs="+")
    c.add_argument("--json", action="store_true")
    c.set_defaults(fn=cmd_score)
    a = p.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
