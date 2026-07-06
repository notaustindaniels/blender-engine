# /// script
# requires-python = ">=3.11,<3.12"
# dependencies = ["httpx>=0.27"]
# ///
"""L3 enumerator — BlenderArtists forum link-router (SPEC §2.2 L3, §5.3; D-003 R20 greenlit).

Discourse exposes `.json` on any category/topic URL (no browser). This crawls the "Released Scripts
and Themes" category (coding/50, discovered live 2026-07-06), reads each topic's first post, extracts
outbound links, and ROUTES them:
  - github.com / gitlab.com / codeberg  -> candidates/L3.jsonl as lane L3 (an L2-style repo candidate)
  - extensions.blender.org               -> L3 candidate (already-L1, dedup collapses it)
  - gumroad / superhive / blendermarket / fab  -> L5-pending (marketplace; human-gated acquisition)
  - dead / unreachable (HEAD != 2xx/3xx) -> graveyard.jsonl (reason=dead-link), never a silent skip

Deterministic, no AI. Respects a page-depth cap. Read-only outward (HEAD probes only).

Usage: uv run .archon/scripts/enumerate/l3_forum.py --out candidates/L3.jsonl \
         [--graveyard graveyard.jsonl] [--l5-pending candidates/L5_pending.jsonl] \
         [--max-pages 6] [--category coding/released-scripts-and-themes/50]
"""
import argparse, json, re, sys, time, datetime, pathlib, urllib.parse
import httpx

BASE = "https://blenderartists.org"
UA = "blender-vault-harvester/0.1 (Stage-1 research; contact: local)"
REPO_HOSTS = ("github.com", "gitlab.com", "codeberg.org")
L5_HOSTS = ("gumroad.com", "superhivemarket.com", "blendermarket.com", "fab.com", "cubebrush.co")
SKIP_HOSTS = ("blenderartists.org", "youtube.com", "youtu.be", "twitter.com", "x.com",
              "patreon.com", "discord.", "imgur.com", "artstation.com")


def slug(s): return re.sub(r"[^a-z0-9]+", "-", (s or "").lower()).strip("-")


def get_json(client, url):
    try:
        r = client.get(url, headers={"User-Agent": UA}, timeout=30, follow_redirects=True)
        if r.status_code == 200 and r.headers.get("content-type", "").startswith("application/json"):
            return r.json()
    except Exception:
        pass
    return None


def link_alive(client, url):
    try:
        r = client.head(url, headers={"User-Agent": UA}, timeout=15, follow_redirects=True)
        if r.status_code < 400:
            return True
        # some hosts reject HEAD; try a light GET
        r = client.get(url, headers={"User-Agent": UA}, timeout=20, follow_redirects=True)
        return r.status_code < 400
    except Exception:
        return False


def canon_repo(url):
    m = re.search(r"(https?://(?:github|gitlab|codeberg)[^/]+/[^/#?]+/[^/#?]+)", url)
    if not m:
        return None
    base = m.group(1).rstrip("/").removesuffix(".git")
    parts = urllib.parse.urlparse(base)
    owner_repo = parts.path.strip("/").split("/")[:2]
    if len(owner_repo) < 2:
        return None
    return base, owner_repo[0], owner_repo[1]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="candidates/L3.jsonl")
    ap.add_argument("--graveyard", default="graveyard.jsonl")
    ap.add_argument("--l5-pending", default="candidates/L5_pending.jsonl")
    ap.add_argument("--category", default="c/coding/released-scripts-and-themes/50")
    ap.add_argument("--max-pages", type=int, default=6)
    ap.add_argument("--max-topics", type=int, default=120)
    a = ap.parse_args()

    now = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")
    client = httpx.Client()
    topics = []
    for page in range(a.max_pages):
        data = get_json(client, f"{BASE}/{a.category}.json?page={page}")
        if not data:
            break
        page_topics = data.get("topic_list", {}).get("topics", [])
        if not page_topics:
            break
        topics += page_topics
        if len(topics) >= a.max_topics:
            break
        time.sleep(1.0)
    topics = topics[:a.max_topics]

    seen_repo, repo_rows, l5_rows, grave = set(), [], [], []
    routed_dead = 0
    for t in topics:
        tid = t.get("id")
        if t.get("title", "").lower().startswith("about the "):
            continue
        td = get_json(client, f"{BASE}/t/{tid}.json")
        if not td:
            continue
        posts = td.get("post_stream", {}).get("posts", [])
        if not posts:
            continue
        html = posts[0].get("cooked", "")
        links = re.findall(r'href=["\']([^"\'>]+)["\']', html)
        title = td.get("title", "")
        for url in links:
            if not url.startswith("http"):
                continue
            host = urllib.parse.urlparse(url).netloc.lower()
            if any(h in host for h in SKIP_HOSTS):
                continue
            if any(h in host for h in REPO_HOSTS):
                cr = canon_repo(url)
                if not cr:
                    continue
                base, owner, repo = cr
                if base in seen_repo:
                    continue
                seen_repo.add(base)
                if not link_alive(client, base):
                    grave.append({"url": base, "reason": "dead-link (L3 forum)", "seen_at": now, "lane": "L3"}); routed_dead += 1
                    continue
                repo_rows.append({
                    "canonical_id": f"{slug(owner)}__{slug(repo)}", "source_id": f"{owner}/{repo}",
                    "name": repo, "author": owner, "lane": "L3", "url": base, "archive_url": "",
                    "sha256": "", "route": "L2-style repo", "forum_topic": f"{BASE}/t/{tid}",
                    "forum_title": title[:120], "fetched_at": now,
                })
            elif any(h in host for h in L5_HOSTS):
                l5_rows.append({"url": url, "lane": "L5-pending", "route": host,
                                "forum_topic": f"{BASE}/t/{tid}", "forum_title": title[:120], "seen_at": now})
        time.sleep(0.5)

    def write_jsonl(path, rows, append=False):
        p = pathlib.Path(path); p.parent.mkdir(parents=True, exist_ok=True)
        mode = "a" if append else "w"
        with open(p, mode) as f:
            for r in rows:
                f.write(json.dumps(r) + "\n")

    write_jsonl(a.out, sorted(repo_rows, key=lambda r: r["canonical_id"]))
    write_jsonl(a.l5_pending, l5_rows)
    # dedup-append graveyard
    seen_g = set()
    gp = pathlib.Path(a.graveyard)
    if gp.exists():
        for line in gp.read_text().splitlines():
            if line.strip():
                try:
                    seen_g.add(json.loads(line).get("url"))
                except Exception:
                    pass
    write_jsonl(a.graveyard, [g for g in grave if g["url"] not in seen_g], append=True)

    print(json.dumps({"lane": "L3", "topics_scanned": len(topics), "repo_candidates": len(repo_rows),
                      "l5_pending": len(l5_rows), "dead_links_graveyarded": routed_dead}))
    print(f"[L3] {len(topics)} topics -> {len(repo_rows)} repo candidates, {len(l5_rows)} L5-pending, "
          f"{routed_dead} dead-links graveyarded", file=sys.stderr)


if __name__ == "__main__":
    main()
