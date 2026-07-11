# /// script
# requires-python = ">=3.11,<3.12"
# dependencies = ["pyyaml>=6"]
# ///
"""discovery_engine.py — the STANDING discovery engine (D-009 R57). Runs unattended (monthly CI wave,
discovery-monthly.yml) OR locally. Reads inputs/discovery-lattice.yaml and consumes ONLY ToS-compatible
machine sources (official APIs, published RSS feeds, public indexes, awesome-list READMEs) — it NEVER
HTML-scrapes a scrape-forbidden marketplace (Gumroad §14, Superhive); those veins are reached via
search-derived URLs in human/assisted rounds, not here. Every find is a click_to_get row (acquisition
stays human-gated, R33). New-unique is deduped against catalog.jsonl + all prior reports/discovery/*.jsonl.

Output: reports/discovery/round-auto-<YYYY-MM>.jsonl (new items only) + a JSON summary to stdout
(new-unique per source — the R56/R47 "documented exhaustion, no single-% threshold" signal for the feed).

Resilient by design: each source is fetched in isolation; a network/parse failure on one source is
recorded and skipped, never fatal. Stdlib-only fetch (urllib) + xml.etree; no third-party HTTP.
"""
import json, re, sys, os, glob, time, socket, signal, pathlib, argparse, datetime, urllib.request, xml.etree.ElementTree as ET
import yaml

ROOT = pathlib.Path(__file__).resolve().parents[2]
socket.setdefaulttimeout(15)          # caps socket ops — but NOT getaddrinfo/DNS (see SIGALRM guard)
MAX_BYTES = 8 * 1024 * 1024           # never read more than 8 MB from a source
DEADLINE = 20                         # wall-clock cap on a whole fetch (bounds trickling streams)
SOURCE_HARD_TIMEOUT = 35              # SIGALRM hard cap per source — interrupts a hung DNS/TLS/read
UA = "blender-vault-discovery/1.0 (+standing R57 engine; RSS/API/index only, no scrape)"


class SourceTimeout(Exception):
    pass


def _on_alarm(signum, frame):
    raise SourceTimeout(f"source exceeded {SOURCE_HARD_TIMEOUT}s hard cap")


if hasattr(signal, "SIGALRM"):        # Unix (CI is Linux; macOS ok) — main-thread only
    signal.signal(signal.SIGALRM, _on_alarm)
GEN_KW = ("generat", "procedural", "geometry node", "geo node", "geonode", "scatter", "kitbash",
          "greeble", "shader", "material", "terrain", "tree", "rock", "cable", "pipe", "rope",
          "building", "city", "cloud", "water", "fur", "hair", "crystal", "fracture", "mograph")
FREE_KW = ("free", "$0", "0+", "cc0", "name your price", "pay what", "download")


def _fetch_once(url, timeout=15):
    """Deadline-bounded chunked read: a server that trickles bytes (keeping the per-recv socket timeout
    from ever firing) still can't stall us past DEADLINE seconds. Returns whatever arrived by then."""
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "*/*",
                                               "Accept-Encoding": "identity"})
    end = time.time() + DEADLINE
    buf = bytearray()
    with urllib.request.urlopen(req, timeout=timeout) as r:
        while time.time() < end and len(buf) < MAX_BYTES:
            chunk = r.read(65536)
            if not chunk:
                break
            buf += chunk
    return bytes(buf)


def fetch(url, timeout=15, retries=1):
    """Retry ONLY on a connection-level exception (transient DNS/reset). NEVER loop on an empty or
    deadline-truncated body — that just passes through fast (a slow/trickling source yields whatever it
    gave and the engine moves on; looping on empty is what stalls the run)."""
    for attempt in range(retries + 1):
        try:
            return _fetch_once(url, timeout)
        except Exception:
            if attempt == retries:
                raise
    return b""


def norm_url(u):
    """Normalize a URL for cross-id-scheme dedup (an extension already enumerated by L1 under a different
    catalog_id shares its extensions.blender.org/add-ons/<slug>/ URL — dedup by URL, not just id)."""
    if not u:
        return ""
    u = u.strip().lower()
    u = re.sub(r"^https?://(www\.)?", "", u)
    return u.rstrip("/")


def load_seen():
    seen_ids, seen_urls = set(), set()
    files = [ROOT / "catalog.jsonl"] + [pathlib.Path(p) for p in glob.glob(str(ROOT / "reports/discovery/*.jsonl"))]
    for fp in files:
        if not fp.exists():
            continue
        for l in fp.read_text().splitlines():
            l = l.strip()
            if not l:
                continue
            try:
                d = json.loads(l)
            except Exception:
                continue
            seen_ids.add(d.get("catalog_id"))
            if d.get("url"):
                seen_urls.add(norm_url(d["url"]))
    seen_ids.discard(None)
    seen_urls.discard("")
    return seen_ids, seen_urls


def guess_category(text, cats):
    t = text.lower()
    for cat, nouns in cats.items():
        for n in nouns:
            if n in t:
                return n.replace(" ", "_")
    return None


def slugify(s):
    return re.sub(r"[^a-z0-9]+", "-", (s or "").lower()).strip("-")[:60]


def src_markdown_index(src, cats):
    """awesome-list README → markdown links to gumroad/github/kofi/etc. generator tools."""
    out = []
    body = fetch(src["url"]).decode("utf-8", "replace")
    for m in re.finditer(r"\[([^\]]+)\]\((https?://[^)\s]+)\)", body):
        name, url = m.group(1).strip(), m.group(2).strip()
        low = (name + " " + url).lower()
        if not any(k in low for k in GEN_KW):
            continue
        if not re.search(r"gumroad\.com|github\.com|ko-fi\.com|kofi|itch\.io|blendernation|3d-wolf", url):
            continue
        market = ("gumroad" if "gumroad" in url else "github" if "github" in url else
                  "kofi" if "ko-fi" in url or "kofi" in url else "itch" if "itch.io" in url else "web")
        out.append({"name": name, "url": url, "marketplace": market,
                    "category": guess_category(low, cats), "license": "confirm-at-source"})
    return out


def src_rss(src, cats):
    """RSS feed (BlenderNation, itch.io official tag feeds) → items matching generator + free keywords."""
    out = []
    raw = fetch(src["url"])
    root = ET.fromstring(raw)
    for item in root.iter("item"):
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        desc = (item.findtext("description") or "")
        blob = f"{title} {desc}".lower()
        if not link or not any(k in blob for k in GEN_KW):
            continue
        # itch tag feeds are all-blender already; blendernation needs a free+generator gate
        if src["marketplace_hint"] == "blendernation" and not any(k in blob for k in FREE_KW):
            continue
        out.append({"name": title[:120], "url": link, "marketplace": src["marketplace_hint"],
                    "category": guess_category(blob, cats), "license": "confirm-at-source"})
    return out


def src_index_extensions(src, cats):
    """extensions.blender.org official index API → add-ons (route to L1 gate)."""
    out = []
    data = json.loads(fetch(src["url"]).decode("utf-8", "replace"))
    items = data if isinstance(data, list) else (data.get("data") or data.get("results") or [])
    for e in items:
        name = e.get("name") or e.get("slug") or ""
        slug = e.get("slug") or slugify(name)
        blob = f"{name} {e.get('tagline','')} {' '.join(e.get('tags',[]) if isinstance(e.get('tags'),list) else [])}".lower()
        if not any(k in blob for k in GEN_KW):
            continue
        out.append({"name": name[:120], "url": f"https://extensions.blender.org/add-ons/{slug}/",
                    "marketplace": "extensions.blender.org", "category": guess_category(blob, cats),
                    "license": e.get("license") or "GPL"})
    return out


def src_api_sketchfab(src, cats):
    """official Sketchfab CC Download API via a1_sketchfab.py (needs SKETCHFAB_TOKEN). Opt-in + slow —
    only runs when DISCOVERY_SKETCHFAB=1 (the CI wave sets it; local/default runs skip it for speed)."""
    if os.environ.get("DISCOVERY_SKETCHFAB") != "1":
        return []
    if not (os.environ.get("SKETCHFAB_TOKEN") or (ROOT / ".archon/.env").exists()):
        return []
    # a1_sketchfab.py writes reports/sketchfab-sweep.json; the engine just re-runs a light sweep if present.
    script = ROOT / ".archon/scripts/a1_sketchfab.py"
    if not script.exists():
        return []
    import subprocess
    try:
        subprocess.run(["uv", "run", str(script), "--per", "24", "--queries",
                        "procedural,generator,kitbash,greeble"], cwd=ROOT, timeout=600,
                       capture_output=True, text=True)
    except Exception:
        return []
    return []  # sketchfab items are folded by catalog_build from the sweep json, not emitted here


HANDLERS = {"markdown_index": src_markdown_index, "rss": src_rss,
            "index_extensions": src_index_extensions, "api_sketchfab": src_api_sketchfab}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stamp", default=datetime.date.today().strftime("%Y-%m"))
    ap.add_argument("--config", default=str(ROOT / "inputs/discovery-lattice.yaml"))
    a = ap.parse_args()
    cfg = yaml.safe_load(open(a.config))
    cats = cfg.get("categories", {})
    seen, seen_urls = load_seen()
    new_rows, per_source, errors = [], {}, {}
    for src in cfg.get("sources", []):
        h = HANDLERS.get(src["kind"])
        if not h:
            continue
        print(f"  fetching {src['key']} ({src['kind']}) …", file=sys.stderr, flush=True)
        if hasattr(signal, "SIGALRM"):
            signal.alarm(SOURCE_HARD_TIMEOUT)     # hard interrupt a hung DNS/TLS/read for THIS source
        try:
            cands = h(src, cats)
        except Exception as e:
            errors[src["key"]] = f"{type(e).__name__}: {e}"
            per_source[src["key"]] = 0
            print(f"    ! {src['key']}: {type(e).__name__}: {e}", file=sys.stderr, flush=True)
            continue
        finally:
            if hasattr(signal, "SIGALRM"):
                signal.alarm(0)                   # clear the alarm whether the source succeeded or not
        print(f"    {src['key']}: {len(cands)} raw candidates", file=sys.stderr, flush=True)
        n = 0
        for c in cands:
            cid = f"{c['marketplace']}::{slugify(c['name']) or slugify(c['url'])}"
            nu = norm_url(c.get("url"))
            if not cid or cid in seen or (nu and nu in seen_urls):   # dedup by id AND normalized URL
                continue
            seen.add(cid)
            if nu:
                seen_urls.add(nu)
            new_rows.append({
                "catalog_id": cid, "name": c["name"], "creator": None,
                "marketplace": c["marketplace"], "url": c["url"],
                "price_class": "unconfirmed", "license": c.get("license") or "confirm-at-source",
                "status": "click_to_get", "category": c.get("category"), "verbs": [],
                "provisional": True, "discovered_by": f"R57-engine:{src['key']}",
                "card": f"Auto-discovered ({src['key']}, {a.stamp}). Free procedural Blender item — "
                        f"price/license confirm-at-source (R31). Human checkout (R33). click-to-get."})
            n += 1
        per_source[src["key"]] = n
    # write the auto round (append-safe: unique filename per month)
    if new_rows:
        outp = ROOT / "reports/discovery" / f"round-auto-{a.stamp}.jsonl"
        existing = ""
        if outp.exists():
            existing = outp.read_text()
            have = {json.loads(l)["catalog_id"] for l in existing.splitlines() if l.strip()}
            new_rows = [r for r in new_rows if r["catalog_id"] not in have]
        with open(outp, "a") as f:
            for r in new_rows:
                f.write(json.dumps(r) + "\n")
    print(json.dumps({"stamp": a.stamp, "new_unique_total": len(new_rows),
                      "per_source": per_source, "errors": errors}, indent=1))


if __name__ == "__main__":
    main()
