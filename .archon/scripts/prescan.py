# /// script
# requires-python = ">=3.11,<3.12"
# ///
"""prescan.py — static danger scan; GATE PRECONDITION before ANY container run (SPEC §3.4, §7,
PRD guardrail #1). Greps each artifact's Python for dangerous APIs. ANY hit => status
`needs_review`; the artifact must NOT enter the sandbox until a human clears it. GN-only .blend
packs get a driver-expression scan (drivers can execute Python).

Deterministic, no AI. Emits a JSON list to stdout: [{artifact, status, hits:[{pattern,sample}]}].
Exit code 0 always (status is in the payload); the orchestrator decides gating.

Usage: prescan.py <artifact> [<artifact> ...]
"""
import sys, os, re, json, zipfile

# Dangerous-API patterns (SPEC §3.4). Conservative: false positives cost a human glance;
# false negatives are a sandbox-escape exposure, so we err toward flagging.
PATTERNS = {
    "subprocess": r"\bsubprocess\b",
    "os.system": r"\bos\.system\b",
    "os.popen": r"\bos\.popen\b",
    "urllib": r"\burllib\b",
    "requests": r"\brequests\b",
    "httpx": r"\bhttpx\b",
    "socket": r"\bsocket\b",
    "eval(": r"\beval\s*\(",
    "exec(": r"\bexec\s*\(",
    "__import__": r"__import__\s*\(",
    "ctypes": r"\bctypes\b",
    "base64-decode": r"base64\b[\s\S]{0,40}?(b64decode|decodebytes|\.decode)",
    "open-write": r"open\s*\([^)]*,\s*['\"][wax]b?\+?['\"]",
    "driver-expression": r"driver\.expression|\bFModifier\b",   # .blend GN packs (SPEC §3.4)
}
# Aligned to the SPEC §3.4 enumerated list. `importlib`/`pickle`/`marshal` were dropped as
# they are not in that list and produced benign false positives; the exec-capable and network
# APIs that ARE listed remain gating. `open-write` stays conservative (the "outside temp"
# qualifier can't be resolved statically), so preset-writing add-ons will land in needs_review
# and get a human glance — the intended §3.4 friction, not a bug.
COMPILED = {k: re.compile(v) for k, v in PATTERNS.items()}


def scan_text(text):
    hits = []
    for name, rx in COMPILED.items():
        m = rx.search(text)
        if m:
            s = m.start()
            hits.append({"pattern": name, "sample": text[max(0, s - 20):s + 40].replace("\n", " ")})
    return hits


def scan_artifact(path):
    low = path.lower()
    texts = []
    if low.endswith(".py"):
        texts.append(open(path, "r", errors="ignore").read())
    elif low.endswith(".zip"):
        try:
            z = zipfile.ZipFile(path)
            for n in z.namelist():
                if n.endswith(".py") or n.endswith(".toml"):
                    texts.append(z.read(n).decode("utf-8", "ignore"))
        except Exception as e:
            return {"artifact": path, "status": "error", "hits": [], "error": f"bad zip: {e}"}
    elif low.endswith(".blend"):
        # GN pack: binary .blend — scan as latin-1 text for driver-expression / dangerous tokens
        data = open(path, "rb").read().decode("latin-1", "ignore")
        texts.append(data)
    else:
        return {"artifact": path, "status": "error", "hits": [], "error": "unknown artifact type"}

    all_hits = []
    for t in texts:
        all_hits.extend(scan_text(t))
    # dedupe by pattern
    seen, deduped = set(), []
    for h in all_hits:
        if h["pattern"] not in seen:
            seen.add(h["pattern"]); deduped.append(h)
    status = "needs_review" if deduped else "clean"
    return {"artifact": path, "status": status, "hits": deduped}


def main():
    if len(sys.argv) < 2:
        print("usage: prescan.py <artifact> [<artifact> ...]", file=sys.stderr)
        sys.exit(2)
    results = [scan_artifact(p) for p in sys.argv[1:]]
    print(json.dumps(results, indent=2))
    flagged = [r["artifact"] for r in results if r["status"] == "needs_review"]
    if flagged:
        print(f"[prescan] {len(flagged)} artifact(s) NEED REVIEW (blocked from sandbox): "
              + ", ".join(os.path.basename(f) for f in flagged), file=sys.stderr)


if __name__ == "__main__":
    main()
