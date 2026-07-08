# /// script
# requires-python = ">=3.11,<3.12"
# dependencies = ["httpx>=0.27", "pyyaml>=6"]
# ///
"""L2 enumerator — GitHub (SPEC §2.2 L2, §5.3). Reads GH_TOKEN from env ONLY (never printed).

Stage-1 scope note: the yield spike (spike_l2_yield.py) shows the raw ecosystem is huge; verifying
all of it needs the native-amd64 decision (§12.2#5). So this enumerator produces the BOUNDED
Terrain+Vegetation candidate set the harness will actually acquire+verify: repo-search scoped to
the two probe categories, each repo resolved to an add-on (blender_manifest.toml OR bl_info) with a
download URL, deduped later against L1 by repo (normalize.py §3.3). Hard --ceiling bounds API cost.

Provenance for L2 differs from L1: GitHub has no pre-declared archive hash, so acquire.py computes
and records the SHA-256 at download time (re-downloadable + re-hashable = still zero-fabrication).

Usage: GH_TOKEN in env.  uv run .archon/scripts/enumerate/l2_github.py --out candidates/L2.jsonl \
         [--categories terrain,vegetation] [--ceiling 60]
"""
import argparse, os, sys, json, re, time, datetime, base64, pathlib
import httpx

TOKEN = os.environ.get("GH_TOKEN", "")
if not TOKEN:
    print(json.dumps({"lane": "L2", "status": "error", "note": "GH_TOKEN not in env"}))
    print("[L2] ERROR: GH_TOKEN not in env", file=sys.stderr); sys.exit(2)
H = {"Authorization": f"Bearer {TOKEN}", "Accept": "application/vnd.github+json",
     "X-GitHub-Api-Version": "2022-11-28", "User-Agent": "blender-vault-harvester/0.1"}

# Terrain/Vegetation-scoped repo-search queries (recall-biased; precision at enrich+coverage).
# Curated, high-precision queries for the two probe categories; all OTHER categories are
# auto-derived from the taxonomy below (D-008 R46: full per-category sweep, all 26 categories).
_CURATED = {
    "terrain": ["blender terrain generator in:name,description,readme",
                "blender landscape addon in:name,description,readme",
                "topic:blender-addon terrain", "blender erosion addon in:name,description,readme",
                "blender heightmap addon in:name,description,readme",
                "blender addon rocks mountain in:name,description"],
    "vegetation": ["blender tree generator addon in:name,description,readme",
                   "blender addon vegetation scatter in:name,description,readme",
                   "topic:blender-addon foliage", "blender plant generator addon in:name,description,readme",
                   "blender addon grass forest in:name,description,readme",
                   "blender addon flower leaf generator in:name,description"],
}


def _build_queries():
    """Derive per-category GitHub search queries for ALL 26 taxonomy categories (R46). Each category
    gets a topic query + keyword queries from its name and its niches' distinctive tokens/aliases.
    R11: this ORDERS the sweep by category; it excludes nothing — the ceiling caps probe order only."""
    import yaml as _yaml
    tax = _yaml.safe_load(open(pathlib.Path(__file__).resolve().parents[3] / "inputs/taxonomy.yaml"))
    STOP = {"generator", "system", "tools", "tool", "addon", "the", "and", "for", "pro", "gen"}
    out = {}
    for c in tax["categories"]:
        key = re.sub(r"[^a-z0-9]+", "_", c["name"].lower()).strip("_").split("_")[0]
        if key in _CURATED:
            out[key] = _CURATED[key]; continue
        kws = []
        for n in (c.get("niches") or [])[:6]:
            for t in re.split(r"[_\s\-]+", n["id"]):
                if t and t not in STOP and len(t) > 3 and t not in kws:
                    kws.append(t)
        catword = re.sub(r"[^a-z ]", "", c["name"].lower()).split(" ")[0]
        q = [f"topic:blender-addon {catword}"]
        for kw in kws[:5]:
            q.append(f"blender {kw} addon in:name,description,readme")
        out[key] = q
    return out


QUERIES = _build_queries()


def slug(s): return re.sub(r"[^a-z0-9]+", "-", (s or "").lower()).strip("-")


def gh(url, params=None):
    r = httpx.get(url, headers=H, params=params or {}, timeout=30, follow_redirects=True)
    return r


def get_file(owner, repo, path):
    r = gh(f"https://api.github.com/repos/{owner}/{repo}/contents/{path}")
    if r.status_code == 200:
        try:
            return base64.b64decode(r.json()["content"]).decode("utf-8", "ignore")
        except Exception:
            return None
    return None


def find_addon_file(owner, repo, branch):
    """Find the add-on signature at root OR nested. Returns (addon_type, path, content) or (None,)*3."""
    manifest = get_file(owner, repo, "blender_manifest.toml")
    if manifest:
        return "extension_manifest", "blender_manifest.toml", manifest
    init = get_file(owner, repo, "__init__.py")
    if init and "bl_info" in init:
        return "python_bl_info", "__init__.py", init
    r = gh(f"https://api.github.com/repos/{owner}/{repo}/git/trees/{branch}", {"recursive": "1"})
    if r.status_code != 200:
        return None, None, None
    tree = r.json().get("tree", [])
    mans = sorted([t["path"] for t in tree if t["path"].endswith("blender_manifest.toml")],
                  key=lambda p: p.count("/"))
    if mans:
        c = get_file(owner, repo, mans[0])
        if c:
            return "extension_manifest", mans[0], c
    inits = sorted([t["path"] for t in tree if t["path"].endswith("__init__.py")], key=lambda p: p.count("/"))
    for path in inits[:6]:
        c = get_file(owner, repo, path)
        if c and "bl_info" in c:
            return "python_bl_info", path, c
    return None, None, None


def resolve_addon(owner, repo, meta):
    """Detect add-on type + min version + download URL. Returns dict or None if not an add-on."""
    branch = meta.get("default_branch", "main")
    addon_type, _path, content = find_addon_file(owner, repo, branch)
    if not addon_type:
        return None   # no add-on signature found -> skip
    bmin = version = None
    if addon_type == "extension_manifest":
        m = re.search(r'blender_version_min\s*=\s*"([^"]+)"', content); bmin = m.group(1) if m else None
        m = re.search(r'^\s*version\s*=\s*"([^"]+)"', content, re.M); version = m.group(1) if m else None
    else:
        m = re.search(r'"blender"\s*:\s*\(\s*(\d+)\s*,\s*(\d+)\s*,?\s*(\d+)?', content)
        if m:
            bmin = ".".join(x for x in m.groups() if x)
        m = re.search(r'"version"\s*:\s*\(\s*(\d+)\s*,\s*(\d+)\s*,?\s*(\d+)?', content)
        if m:
            version = ".".join(x for x in m.groups() if x)
    # prefer a tagged release archive; else the default-branch archive (both via github.com/codeload)
    rel = gh(f"https://api.github.com/repos/{owner}/{repo}/releases/latest")
    if rel.status_code == 200 and rel.json().get("tag_name"):
        tag = rel.json()["tag_name"]
        archive_url = f"https://github.com/{owner}/{repo}/archive/refs/tags/{tag}.zip"
        version = version or tag.lstrip("v")
    else:
        archive_url = f"https://github.com/{owner}/{repo}/archive/refs/heads/{branch}.zip"
    return {"addon_type": addon_type, "blender_version_min": bmin, "version": version or "0",
            "archive_url": archive_url}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="candidates/L2.jsonl")
    ap.add_argument("--categories", default="terrain,vegetation")
    ap.add_argument("--graveyard", default="graveyard.jsonl")
    a = ap.parse_args()
    cats = [c.strip() for c in a.categories.split(",") if c.strip()]

    # 1) collect unique repos from scoped repo-search
    seen, repos = set(), []
    for c in cats:
        for q in QUERIES.get(c, []):
            r = gh("https://api.github.com/search/repositories", {"q": q, "per_page": 30, "sort": "stars"})
            if r.status_code != 200:
                print(f"[L2] search failed ({r.status_code}) for: {q}", file=sys.stderr); time.sleep(3); continue
            for it in r.json().get("items", []):
                full = it["full_name"]
                if full not in seen:
                    seen.add(full)
                    repos.append((it, c))
            time.sleep(2.5)
    print(f"[L2] {len(repos)} unique candidate repos from {sum(len(QUERIES[c]) for c in cats)} queries", file=sys.stderr)

    # 2) classify + resolve EVERY repo — R11: order, never exclude. Archived / no-add-on-signature /
    #    legacy-2.7x candidates land in graveyard.jsonl as RECORDS (never silent skips). Stars only
    #    order probe priority (probe_rank); the whole enumerated set is written to candidates.
    now = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")
    rows, grave = [], []
    for it, cat in repos:
        owner, repo = it["owner"]["login"], it["name"]
        url = it["html_url"]
        if it.get("archived"):
            grave.append({"url": url, "reason": "archived-repo", "seen_at": now, "lane": "L2"})
            continue
        info = resolve_addon(owner, repo, it)
        if not info:
            grave.append({"url": url, "reason": "no-addon-signature", "seen_at": now, "lane": "L2"})
            continue
        mn = str(info.get("blender_version_min") or "")
        m = re.match(r"(\d+)\.(\d+)", mn)
        is_legacy = bool(m and (int(m.group(1)), int(m.group(2))) < (2, 80))
        if is_legacy:   # still a candidate (enumerate + gate) AND a graveyard record (R11)
            grave.append({"url": url, "reason": f"legacy-pre-2.8 (min {mn})", "seen_at": now, "lane": "L2"})
        lic = it.get("license") or {}
        rows.append({
            "canonical_id": f"{slug(owner)}__{slug(repo)}",
            "source_id": it["full_name"], "name": repo, "author": owner,
            "version": info["version"], "addon_type": info["addon_type"], "lane": "L2",
            "url": url, "archive_url": info["archive_url"], "sha256": "",
            "blender_version_min": info["blender_version_min"], "legacy": is_legacy,
            "license": [f"SPDX:{lic.get('spdx_id')}"] if lic.get("spdx_id") and lic.get("spdx_id") != "NOASSERTION" else [],
            "tags": it.get("topics", []), "tagline": (it.get("description") or "")[:200],
            "stars": it.get("stargazers_count", 0), "procedural": None, "probe_category_hint": cat,
            "fetched_at": now,
        })
        time.sleep(0.3)

    rows.sort(key=lambda r: (-r.get("stars", 0), r["canonical_id"]))   # stars ORDER probe priority
    for i, r in enumerate(rows):
        r["probe_rank"] = i

    pathlib.Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    with open(a.out, "w") as f:
        for row in rows:
            f.write(json.dumps(row) + "\n")
    gpath = pathlib.Path(a.graveyard)
    seen_g = set()
    if gpath.exists():
        for line in gpath.read_text().splitlines():
            if line.strip():
                try:
                    seen_g.add(json.loads(line).get("url"))
                except Exception:
                    pass
    with open(gpath, "a") as f:
        for g in grave:
            if g["url"] not in seen_g:
                f.write(json.dumps(g) + "\n")
                seen_g.add(g["url"])
    print(json.dumps({"lane": "L2", "repos_found": len(repos), "addons_enumerated": len(rows),
                      "graveyard_records": len(grave), "out": a.out}))
    print(f"[L2] enumerated {len(rows)} add-ons (star-ordered) + {len(grave)} graveyard records", file=sys.stderr)


if __name__ == "__main__":
    main()
