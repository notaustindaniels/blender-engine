# /// script
# requires-python = ">=3.11,<3.12"
# ///
"""normalize.py — dedup candidates into one row per real add-on (SPEC §3.3, §2.1 Normalize).

Same add-on iff ANY: identical content hash; identical resolved GitHub repo; OR (fuzzy
name-match >=0.9 AND same author). On match, keep the highest-priority source (§4.2 order
L1>L2>L3>L4>L5a>L5b), union discovery metadata, record all source URLs in sources[].
Deterministic, no AI.

Usage: normalize.py [--candidates candidates] [--out normalized.jsonl] [--existing normalized.jsonl]
"""
import argparse, json, glob, os, re, difflib

PRIORITY = {"L1": 0, "L2": 1, "L3": 2, "L4": 3, "L5a": 4, "L5b": 5}


def norm_name(s):
    return re.sub(r"[^a-z0-9]+", "", (s or "").lower())


def find(parent, x):
    while parent[x] != x:
        parent[x] = parent[parent[x]]; x = parent[x]
    return x


def union(parent, a, b):
    ra, rb = find(parent, a), find(parent, b)
    if ra != rb:
        parent[rb] = ra


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--candidates", default="candidates")
    ap.add_argument("--out", default="normalized.jsonl")
    ap.add_argument("--existing", default="")
    a = ap.parse_args()

    rows = []
    files = sorted(glob.glob(os.path.join(a.candidates, "*.jsonl")))
    if a.existing and os.path.exists(a.existing):
        files.append(a.existing)
    for fp in files:
        for line in open(fp):
            line = line.strip()
            if line:
                rows.append(json.loads(line))

    n = len(rows)
    parent = list(range(n))
    # exact keys: content hash, resolved repo, canonical_id
    by_key = {}
    for i, r in enumerate(rows):
        keys = []
        if r.get("sha256"):
            keys.append("sha:" + r["sha256"])
        if r.get("canonical_id"):
            keys.append("cid:" + r["canonical_id"])
        repo = (r.get("url") or "")
        m = re.search(r"github\.com/([^/]+/[^/#?]+)", repo)
        if m:
            keys.append("repo:" + m.group(1).lower().rstrip(".git"))
        for k in keys:
            if k in by_key:
                union(parent, by_key[k], i)
            else:
                by_key[k] = i
    # fuzzy: same author AND name similarity >= 0.9
    for i in range(n):
        for j in range(i + 1, n):
            if find(parent, i) == find(parent, j):
                continue
            ai, aj = rows[i].get("author", ""), rows[j].get("author", "")
            if ai and ai == aj:
                sim = difflib.SequenceMatcher(None, norm_name(rows[i].get("name")),
                                              norm_name(rows[j].get("name"))).ratio()
                if sim >= 0.9:
                    union(parent, i, j)

    clusters = {}
    for i in range(n):
        clusters.setdefault(find(parent, i), []).append(i)

    out = []
    for members in clusters.values():
        members.sort(key=lambda i: PRIORITY.get(rows[i].get("lane"), 9))
        canon = dict(rows[members[0]])
        sources = []
        seen = set()
        for i in members:
            r = rows[i]
            key = (r.get("lane"), r.get("archive_url") or r.get("url"))
            if key not in seen:
                seen.add(key)
                sources.append({"lane": r.get("lane"), "url": r.get("archive_url") or r.get("url"),
                                "source_id": r.get("source_id"), "fetched_at": r.get("fetched_at")})
        canon["sources"] = sources
        canon["dup_count"] = len(members)
        out.append(canon)

    out.sort(key=lambda r: r.get("canonical_id", ""))
    with open(a.out, "w") as f:
        for r in out:
            f.write(json.dumps(r) + "\n")
    print(json.dumps({"input_rows": n, "normalized_rows": len(out), "out": a.out}))


if __name__ == "__main__":
    main()
