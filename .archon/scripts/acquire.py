# /// script
# requires-python = ">=3.11,<3.12"
# dependencies = ["httpx>=0.27"]
# ///
"""acquire.py — fetch to vault + meta.json with SHA-256 provenance (SPEC §2.1, §4.2, §5, §7).

For each normalized row (L1/L2/L3/L4 auto; L5 is post-approval — out of Stage-1 scope):
  * validate URL (https only; host allowlist), size-cap the download (§7.4),
  * hash the bytes and VERIFY against the API-declared sha256 (provenance integrity, §7.6 /
    PRD zero-fabrication — a mismatch is a hard fail, artifact rejected),
  * store at vault/<canonical_id>/<version>/<original-filename>,
  * write meta.json (§4.2). vault/ is git-ignored (large, private, redistribution-guarded).
Deterministic, no AI. Emits acquired.jsonl (canonical_id, path) for the verify step.

Usage: acquire.py [--normalized normalized.jsonl] [--vault vault] [--limit N] [--out acquired.jsonl]
"""
import argparse, json, os, hashlib, re, datetime, pathlib
import httpx

ALLOW_HOSTS = {"extensions.blender.org", "github.com", "codeload.github.com",
               "objects.githubusercontent.com", "raw.githubusercontent.com"}
MAX_BYTES = 250 * 1024 * 1024  # 250 MB size cap (§7.4)
UA = "blender-vault-harvester/0.1 (Stage-1 research; contact: local)"


def host_of(url):
    m = re.match(r"https://([^/]+)/", url)
    return m.group(1) if m else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--normalized", default="normalized.jsonl")
    ap.add_argument("--vault", default="vault")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--out", default="acquired.jsonl")
    a = ap.parse_args()

    rows = [json.loads(l) for l in open(a.normalized) if l.strip()]
    if a.limit:
        rows = rows[:a.limit]

    acquired, skipped = [], []
    for r in rows:
        cid = r["canonical_id"]
        url = r.get("archive_url") or ""
        rec = {"canonical_id": cid, "name": r.get("name"), "lane": r.get("lane")}
        if not url.startswith("https://") or host_of(url) not in ALLOW_HOSTS:
            rec["status"] = "skip"; rec["reason"] = f"url not allowed: {url[:60]}"
            skipped.append(rec); continue
        try:
            with httpx.stream("GET", url, headers={"User-Agent": UA}, timeout=120,
                              follow_redirects=True) as resp:
                resp.raise_for_status()
                buf = bytearray()
                for chunk in resp.iter_bytes():
                    buf += chunk
                    if len(buf) > MAX_BYTES:
                        raise ValueError("exceeds size cap")
        except Exception as e:
            rec["status"] = "error"; rec["reason"] = str(e)[:120]
            skipped.append(rec); continue

        sha = hashlib.sha256(buf).hexdigest()
        declared = r.get("sha256")
        if declared and sha != declared:
            rec["status"] = "hash_mismatch"; rec["reason"] = f"got {sha[:12]} want {declared[:12]}"
            skipped.append(rec); continue  # PROVENANCE FAIL -> reject (never vault a tampered artifact)

        fname = os.path.basename(url.split("?")[0]) or f"{cid}.zip"
        ver = str(r.get("version") or "0")
        dest = pathlib.Path(a.vault) / cid / ver
        dest.mkdir(parents=True, exist_ok=True)
        fpath = dest / fname
        fpath.write_bytes(bytes(buf))

        lic = r.get("license") or []
        lic_str = lic[0].replace("SPDX:", "") if lic else "assumed"
        meta = {
            "canonical_id": cid, "name": r.get("name"), "author": r.get("author"),
            "version": ver,
            "sources": r.get("sources") or [{"lane": r.get("lane"), "url": r.get("url"),
                                             "fetched_at": r.get("fetched_at")}],
            "license": lic_str, "license_source": "manifest" if lic else "assumed",
            "addon_type": r.get("addon_type", "extension_manifest"),
            "file": fname, "sha256": sha,
            "declared_blender_min": r.get("blender_version_min"),
            "procedural": r.get("procedural"),
            "tags": r.get("tags", []), "niche_hint": r.get("niche_hint", []),
            "acquired_at": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
        }
        (dest / "meta.json").write_text(json.dumps(meta, indent=2))
        rec.update(status="ok", path=str(fpath), sha256=sha, version=ver, bytes=len(buf))
        acquired.append(rec)

    with open(a.out, "w") as f:
        for r in acquired:
            f.write(json.dumps(r) + "\n")
    print(json.dumps({"acquired": len(acquired), "skipped": len(skipped),
                      "skips": skipped[:8], "out": a.out}))


if __name__ == "__main__":
    main()
