# /// script
# requires-python = ">=3.11,<3.12"
# dependencies = ["httpx>=0.27"]
# ///
"""L4 enumerator — BlenderNation archives link-router (SPEC §2.2 L4, §5.3; D-003 R20 greenlit).

BlenderNation's wp-json REST API is WAF-blocked (403), but its RSS feeds work — and SPEC §2.2
specifies "RSS/archive scrape" for L4. This reads the main + tag feeds (each `<item>` carries
`content:encoded` full HTML), extracts outbound links, and ROUTES them exactly like L3:
github/gitlab -> L4 repo candidate; marketplace -> L5-pending; dead -> graveyard.jsonl.
Same automated link-router (SPEC §2.2 says L4 mirrors L3). Deterministic. (Amendment 2026-07-06:
RSS not wp-json — reality reconciled, see SPEC §12.4.)

Usage: uv run .archon/scripts/enumerate/l4_bnation.py --out candidates/L4.jsonl \
         [--graveyard graveyard.jsonl] [--l5-pending candidates/L5_pending.jsonl] [--max-posts 80]
"""
import argparse, json, re, sys, time, datetime, pathlib, urllib.parse
import xml.etree.ElementTree as ET
import httpx

BASE = "https://www.blendernation.com"
UA = "blender-vault-harvester/0.1 (Stage-1 research; contact: local)"
REPO_HOSTS = ("github.com", "gitlab.com", "codeberg.org")
L5_HOSTS = ("gumroad.com", "superhivemarket.com", "blendermarket.com", "fab.com", "cubebrush.co")
SKIP_HOSTS = ("blendernation.com", "youtube.com", "youtu.be", "twitter.com", "x.com",
              "patreon.com", "facebook.com", "imgur.com")


def slug(s): return re.sub(r"[^a-z0-9]+", "-", (s or "").lower()).strip("-")


def canon_repo(url):
    m = re.search(r"(https?://(?:github|gitlab|codeberg)[^/]+/[^/#?]+/[^/#?]+)", url)
    if not m:
        return None
    base = m.group(1).rstrip("/").removesuffix(".git")
    parts = urllib.parse.urlparse(base).path.strip("/").split("/")[:2]
    return (base, parts[0], parts[1]) if len(parts) == 2 else None


def link_alive(client, url):
    for meth in ("HEAD", "GET"):
        try:
            r = client.request(meth, url, headers={"User-Agent": UA}, timeout=15, follow_redirects=True)
            if r.status_code < 400:
                return True
        except Exception:
            pass
    return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="candidates/L4.jsonl")
    ap.add_argument("--graveyard", default="graveyard.jsonl")
    ap.add_argument("--l5-pending", default="candidates/L5_pending.jsonl")
    ap.add_argument("--max-posts", type=int, default=80)
    ap.add_argument("--search", default="addon")
    a = ap.parse_args()

    now = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")
    client = httpx.Client()
    # RSS feeds: main + add-on/script tag feeds + paged main, for depth (WordPress supports ?paged=)
    feeds = [f"{BASE}/feed/", f"{BASE}/tag/add-on/feed/", f"{BASE}/tag/addon/feed/",
             f"{BASE}/tag/script/feed/", f"{BASE}/category/blender/blender-add-ons/feed/",
             f"{BASE}/feed/?paged=2", f"{BASE}/feed/?paged=3"]
    NS = {"content": "http://purl.org/rss/1.0/modules/content/"}
    posts, seen_links = [], set()
    for feed in feeds:
        if len(posts) >= a.max_posts:
            break
        try:
            r = client.get(feed, headers={"User-Agent": UA}, timeout=30, follow_redirects=True)
            if r.status_code != 200 or "xml" not in r.headers.get("content-type", "") and "<rss" not in r.text[:200]:
                continue
            root = ET.fromstring(r.content)
        except Exception as e:
            print(f"[L4] feed parse failed {feed}: {e}", file=sys.stderr)
            continue
        for item in root.iter("item"):
            link = (item.findtext("link") or "").strip()
            if link in seen_links:
                continue
            seen_links.add(link)
            enc = item.find("content:encoded", NS)
            html = (enc.text if enc is not None else "") or (item.findtext("description") or "")
            posts.append({"link": link, "title": item.findtext("title") or "", "html": html})
        time.sleep(1.0)
    posts = posts[:a.max_posts]

    seen_repo, repo_rows, l5_rows, grave = set(), [], [], []
    routed_dead = 0
    for p in posts:
        html = p.get("html", "")
        title = p.get("title", "")
        for url in re.findall(r'href=["\']([^"\'>]+)["\']', html):
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
                    grave.append({"url": base, "reason": "dead-link (L4 bnation)", "seen_at": now, "lane": "L4"}); routed_dead += 1
                    continue
                repo_rows.append({
                    "canonical_id": f"{slug(owner)}__{slug(repo)}", "source_id": f"{owner}/{repo}",
                    "name": repo, "author": owner, "lane": "L4", "url": base, "archive_url": "",
                    "sha256": "", "route": "L2-style repo", "bnation_post": p.get("link"),
                    "bnation_title": re.sub(r"<[^>]+>", "", title)[:120], "fetched_at": now,
                })
            elif any(h in host for h in L5_HOSTS):
                l5_rows.append({"url": url, "lane": "L5-pending", "route": host,
                                "bnation_post": p.get("link"), "seen_at": now})
        time.sleep(0.3)

    def write_jsonl(path, rows, append=False):
        pp = pathlib.Path(path); pp.parent.mkdir(parents=True, exist_ok=True)
        with open(pp, "a" if append else "w") as f:
            for r in rows:
                f.write(json.dumps(r) + "\n")

    write_jsonl(a.out, sorted(repo_rows, key=lambda r: r["canonical_id"]))
    write_jsonl(a.l5_pending, l5_rows, append=True)
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

    print(json.dumps({"lane": "L4", "posts_scanned": len(posts), "repo_candidates": len(repo_rows),
                      "l5_pending": len(l5_rows), "dead_links_graveyarded": routed_dead}))
    print(f"[L4] {len(posts)} posts -> {len(repo_rows)} repo candidates, {len(l5_rows)} L5-pending, "
          f"{routed_dead} dead-links graveyarded", file=sys.stderr)


if __name__ == "__main__":
    main()
