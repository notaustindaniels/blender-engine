# /// script
# requires-python = ">=3.11,<3.12"
# dependencies = ["httpx>=0.27"]
# ///
"""spike_l2_yield.py — GitHub yield spike (SPEC §10; owner rider 3). Measures candidate yield per
signature query under AUTHENTICATED rate limits BEFORE building the full L2 lane. Reads GH_TOKEN
from env ONLY; NEVER prints/logs the token. Rate-limit-aware (code search is ~10/min, search 30/min).

Emits reports/l2-yield.json + a markdown table on stdout. No harvesting — counts only.

Usage: GH_TOKEN must be in env.  uv run .archon/scripts/spike_l2_yield.py
"""
import os, sys, json, time, pathlib
import httpx

TOKEN = os.environ.get("GH_TOKEN", "")
if not TOKEN:
    print("ERROR: GH_TOKEN not in env", file=sys.stderr)
    sys.exit(2)
H = {"Authorization": f"Bearer {TOKEN}", "Accept": "application/vnd.github+json",
     "X-GitHub-Api-Version": "2022-11-28", "User-Agent": "blender-vault-harvester/0.1"}

# (kind, label, query, sleep_after) — code=search/code (~10/min), repo=search/repositories (30/min)
QUERIES = [
    ("code", "manifest extensions (4.2+): blender_manifest.toml", "blender_manifest.toml in:path", 7),
    ("code", "legacy add-ons: bl_info in Python", 'bl_info in:file language:Python', 7),
    ("code", "legacy add-ons (tight): \"bl_info = {\"", '"bl_info = {" in:file language:Python', 7),
    ("repo", "topic:blender-addon", "topic:blender-addon", 2.5),
    ("repo", "topic:blender-plugin", "topic:blender-plugin", 2.5),
    ("repo", "topic:blender-extension", "topic:blender-extension", 2.5),
    ("repo", "topic:geometry-nodes", "topic:geometry-nodes", 2.5),
    ("repo", "Terrain-scoped: topic:blender-addon terrain", "topic:blender-addon terrain", 2.5),
    ("repo", "Vegetation-scoped: topic:blender-addon (tree/plant)",
     "topic:blender-addon tree in:name,description,readme", 2.5),
]


def count(kind, q):
    url = "https://api.github.com/search/code" if kind == "code" else "https://api.github.com/search/repositories"
    r = httpx.get(url, headers=H, params={"q": q, "per_page": 1}, timeout=30)
    if r.status_code != 200:
        return None, f"HTTP {r.status_code}: {r.json().get('message','')[:80]}"
    return r.json().get("total_count"), None


def main():
    rows = []
    for kind, label, q, slp in QUERIES:
        n, err = count(kind, q)
        rows.append({"kind": kind, "label": label, "query": q, "total_count": n, "error": err})
        print(f"  [{kind}] {label:52} -> {n if n is not None else err}", file=sys.stderr)
        time.sleep(slp)

    pathlib.Path("reports").mkdir(exist_ok=True)
    pathlib.Path("reports/l2-yield.json").write_text(json.dumps(rows, indent=2))

    md = ["| kind | signature | GitHub total_count |", "|---|---|---:|"]
    for r in rows:
        v = f"{r['total_count']:,}" if r["total_count"] is not None else f"⚠ {r['error']}"
        md.append(f"| {r['kind']} | {r['label']} | {v} |")
    print("\n".join(md))
    print(json.dumps({"queries": len(rows), "out": "reports/l2-yield.json"}))


if __name__ == "__main__":
    main()
