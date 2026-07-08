"""chunker — context-aware chunking (method: split at semantic boundaries).

Python files: stdlib `ast` splits at top-level functions/classes (methods split
out of large classes) — exact spans, zero install risk. Swap in tree-sitter
here only if you ingest other languages.

Everything else that decodes as UTF-8 text: split on markdown-style headings,
then hard-wrap oversized sections into MAX_LINES windows with OVERLAP.

Every chunk gets a context_header — the Contextual Retrieval prefix:
  "source <key> > <file> > class Foo > def bar(...)  [kind]"
Header + text are embedded together (see embedder.py) and hashed together
(see ragdb.content_hash), so re-locating a chunk changes its identity.
"""
from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path

MAX_LINES = 120
OVERLAP = 8


@dataclass
class Chunk:
    text: str
    kind: str
    file_path: str
    symbol: str
    start_line: int
    end_line: int
    context_header: str


def _header(source_key: str, rel_path: str, symbol: str, kind: str) -> str:
    parts = [f"source {source_key}", rel_path]
    if symbol:
        parts.append(symbol)
    return " > ".join(parts) + f"  [{kind}]"


def _window(lines: list[str], lo: int, hi: int) -> list[tuple[int, int]]:
    """Split [lo,hi] (1-based inclusive) into <=MAX_LINES windows with overlap."""
    spans = []
    start = lo
    while start <= hi:
        end = min(start + MAX_LINES - 1, hi)
        spans.append((start, end))
        if end == hi:
            break
        start = end - OVERLAP + 1
    return spans


def chunk_python(source: str, source_key: str, rel_path: str) -> list[Chunk]:
    lines = source.splitlines()
    chunks: list[Chunk] = []
    try:
        tree = ast.parse(source)
    except SyntaxError:
        for lo, hi in _window(lines, 1, len(lines)):
            chunks.append(Chunk("\n".join(lines[lo - 1:hi]), "code", rel_path, "",
                                lo, hi, _header(source_key, rel_path, "(unparsed)", "code")))
        return chunks

    covered: set[int] = set()

    def emit(node: ast.AST, symbol: str) -> None:
        lo, hi = node.lineno, getattr(node, "end_lineno", node.lineno)
        covered.update(range(lo, hi + 1))
        for wlo, whi in _window(lines, lo, hi):
            chunks.append(Chunk("\n".join(lines[wlo - 1:whi]), "code", rel_path,
                                symbol, wlo, whi,
                                _header(source_key, rel_path, symbol, "code")))

    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            emit(node, f"def {node.name}")
        elif isinstance(node, ast.ClassDef):
            size = (getattr(node, "end_lineno", node.lineno) - node.lineno) + 1
            bases = ", ".join(ast.unparse(b) for b in node.bases) if node.bases else ""
            cls_sym = f"class {node.name}({bases})"
            if size <= MAX_LINES:
                emit(node, cls_sym)
            else:
                # header (decorators/docstring/attrs) then each method separately
                first_method = None
                for item in node.body:
                    if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        first_method = item.lineno
                        break
                head_end = (first_method - 1) if first_method else getattr(node, "end_lineno", node.lineno)
                if head_end >= node.lineno:
                    covered.update(range(node.lineno, head_end + 1))
                    for wlo, whi in _window(lines, node.lineno, head_end):
                        chunks.append(Chunk("\n".join(lines[wlo - 1:whi]), "code",
                                            rel_path, cls_sym, wlo, whi,
                                            _header(source_key, rel_path, cls_sym, "code")))
                for item in node.body:
                    if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        emit(item, f"{cls_sym} > def {item.name}")

    # module-level residue (imports, constants, registration) grouped into windows
    residue: list[int] = [i for i in range(1, len(lines) + 1)
                          if i not in covered and lines[i - 1].strip()]
    if residue:
        run_start = residue[0]
        prev = residue[0]
        runs: list[tuple[int, int]] = []
        for i in residue[1:]:
            if i > prev + 2:
                runs.append((run_start, prev))
                run_start = i
            prev = i
        runs.append((run_start, prev))
        for lo, hi in runs:
            for wlo, whi in _window(lines, lo, hi):
                chunks.append(Chunk("\n".join(lines[wlo - 1:whi]), "code", rel_path,
                                    "(module)", wlo, whi,
                                    _header(source_key, rel_path, "(module)", "code")))
    return chunks


def chunk_text(source: str, source_key: str, rel_path: str, kind: str = "doc") -> list[Chunk]:
    lines = source.splitlines()
    sections: list[tuple[str, int]] = [("(top)", 1)]
    for i, ln in enumerate(lines, 1):
        if ln.startswith("#"):
            sections.append((ln.lstrip("# ").strip()[:80] or "(section)", i))
    sections.append(("(end)", len(lines) + 1))
    chunks: list[Chunk] = []
    for (title, lo), (_t2, nxt) in zip(sections, sections[1:]):
        hi = nxt - 1
        if hi < lo:
            continue
        body = "\n".join(lines[lo - 1:hi]).strip()
        if not body:
            continue
        for wlo, whi in _window(lines, lo, hi):
            chunks.append(Chunk("\n".join(lines[wlo - 1:whi]), kind, rel_path, title,
                                wlo, whi, _header(source_key, rel_path, title, kind)))
    return chunks


def chunk_file(path: Path, source_key: str, root: Path) -> list[Chunk]:
    rel = str(path.relative_to(root)) if path != root else path.name
    try:
        src = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []
    if "\x00" in src:          # binary — skip
        return []
    if path.suffix == ".py":
        return chunk_python(src, source_key, rel)
    return chunk_text(src, source_key, rel, "doc")
