# /// script
# requires-python = ">=3.11,<3.12"
# dependencies = ["pyyaml>=6"]
# ///
"""prescan.py — static danger scan; GATE PRECONDITION before ANY container run (SPEC §3.4, §7,
PRD guardrail #1). Greps each artifact's Python for dangerous APIs. A GATING hit => status
`needs_review`; the artifact must NOT enter the sandbox until a human clears it. GN-only .blend
packs get a driver-expression scan.

Owner rider 6 (§12.2): a dated allowlist (reviews/prescan-allowlist.yaml) DOWNGRADES
almost-always-benign patterns (Blender node 'socket', preset open-writes, driver-expression) from
gating to informational — never the exec/network-capable patterns. Allowlisted hits are still
recorded. The human gate stays exactly as-is for the dangerous patterns.

Deterministic, no AI. Emits a JSON list: [{artifact, status, gating:[...], allowlisted:[...]}].

Usage: prescan.py [--allowlist reviews/prescan-allowlist.yaml] <artifact> [<artifact> ...]
"""
import sys, os, re, json, zipfile, argparse, pathlib
import yaml

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
    "driver-expression": r"driver\.expression|\bFModifier\b",
}
COMPILED = {k: re.compile(v) for k, v in PATTERNS.items()}
# Patterns that may NEVER be allowlisted (exec/network-capable), enforced regardless of the file.
NEVER_ALLOW = {"subprocess", "os.system", "os.popen", "urllib", "requests", "httpx",
               "eval(", "exec(", "__import__", "ctypes", "base64-decode"}


def scan_text(text):
    hits = []
    for name, rx in COMPILED.items():
        m = rx.search(text)
        if m:
            s = m.start()
            hits.append({"pattern": name, "sample": text[max(0, s - 20):s + 40].replace("\n", " ")})
    return hits


def scan_artifact(path, allow):
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
            return {"artifact": path, "status": "error", "gating": [], "allowlisted": [], "error": f"bad zip: {e}"}
    elif low.endswith(".blend"):
        texts.append(open(path, "rb").read().decode("latin-1", "ignore"))
    else:
        return {"artifact": path, "status": "error", "gating": [], "allowlisted": [], "error": "unknown artifact type"}

    seen, hits = set(), []
    for t in texts:
        for h in scan_text(t):
            if h["pattern"] not in seen:
                seen.add(h["pattern"]); hits.append(h)
    gating = [h for h in hits if h["pattern"] not in allow]
    allowlisted = [h for h in hits if h["pattern"] in allow]
    status = "needs_review" if gating else "clean"
    return {"artifact": path, "status": status,
            "gating": [h["pattern"] for h in gating],
            "allowlisted": [h["pattern"] for h in allowlisted],
            "hits": hits}


def load_allow(path):
    p = pathlib.Path(path)
    if not p.exists():
        return set()
    doc = yaml.safe_load(p.read_text()) or {}
    allow = {a["pattern"] for a in doc.get("allow", []) if "pattern" in a}
    return allow - NEVER_ALLOW   # exec/network patterns can never be allowlisted


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--allowlist", default="policies/prescan-allowlist.yaml")
    ap.add_argument("artifacts", nargs="+")
    a = ap.parse_args()
    allow = load_allow(a.allowlist)
    results = [scan_artifact(p, allow) for p in a.artifacts]
    print(json.dumps(results, indent=2))
    flagged = [r["artifact"] for r in results if r["status"] == "needs_review"]
    if flagged:
        print(f"[prescan] {len(flagged)} artifact(s) NEED REVIEW (blocked from sandbox): "
              + ", ".join(os.path.basename(f) for f in flagged), file=sys.stderr)


if __name__ == "__main__":
    main()
