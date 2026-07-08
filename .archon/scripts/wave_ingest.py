# /// script
# requires-python = ">=3.11,<3.12"
# dependencies = ["pyyaml>=6"]
# ///
"""wave_ingest.py — the supervisor ingest orchestrator (D-008 R46/R47/R52). Run once a CI wave
completes: downloads the shard manifest artifacts, merges them, then runs the full ingest chain and
reports the pass-rate + the R19 tripwire status.

Chain: download+merge manifests -> enrich_scale -> mint_cards -> build_index (corpus.db) ->
kb_build + embed (corpus_kb.db) -> gap_report (R47) -> coverage tripwire check.

Reads GH_TOKEN_RW from .archon/.env (env-only, never printed, R2). Does NOT auto-tag a snapshot — that
is gated on the golden eval (run separately, R55). Reports the tripwire; if it fires, the SUPERVISOR
pauses + reports (R17 — never recalibrate by fiat).

Usage: uv run .archon/scripts/wave_ingest.py --run <run_id> [--no-download]  (--no-download to re-run the
chain on already-merged manifests)
"""
import json, os, sys, subprocess, pathlib, urllib.request, io, zipfile, argparse

ROOT = pathlib.Path(__file__).resolve().parents[2]
REPO = "notaustindaniels/blender-engine"


def token():
    for line in open(ROOT / ".archon/.env"):
        if line.startswith("GH_TOKEN_RW="):
            return line.split("=", 1)[1].strip()
    return os.environ.get("GH_TOKEN_RW", "")


class _StripAuthOnRedirect(urllib.request.HTTPRedirectHandler):
    """GitHub artifact downloads 302 to signed Azure blob URLs that REJECT the GitHub token.
    Strip Authorization when the redirect crosses hosts (R2: token only to api.github.com)."""
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        nr = super().redirect_request(req, fp, code, msg, headers, newurl)
        if nr is not None:
            nr.headers.pop("Authorization", None)
            nr.headers = {k: v for k, v in nr.headers.items() if k.lower() != "authorization"}
        return nr


_OPENER = urllib.request.build_opener(_StripAuthOnRedirect)


def api(url, tok, raw=False):
    req = urllib.request.Request(url, headers={"Authorization": f"token {tok}",
                                               "Accept": "application/vnd.github+json"})
    r = (_OPENER.open(req, timeout=120) if raw else urllib.request.urlopen(req, timeout=60))
    return r.read() if raw else json.load(r)


def download_merge(run_id, tok):
    arts = api(f"https://api.github.com/repos/{REPO}/actions/runs/{run_id}/artifacts", tok)
    merged = 0
    mdir = ROOT / "manifests"; mdir.mkdir(exist_ok=True)
    for a in arts.get("artifacts", []):
        if not a["name"].startswith("wave-manifests-shard-"):
            continue
        blob = api(a["archive_download_url"], tok, raw=True)
        z = zipfile.ZipFile(io.BytesIO(blob))
        for name in z.namelist():
            if name.startswith("manifests/") and name.endswith(".json"):
                data = z.read(name)
                (mdir / pathlib.Path(name).name).write_bytes(data)
                merged += 1
            elif name.startswith("reports/wave-shard-"):
                (ROOT / "reports" / pathlib.Path(name).name).write_bytes(z.read(name))
    return merged, len(arts.get("artifacts", []))


def run(cmd, **kw):
    print(f"  $ {' '.join(cmd[:4])} ...", file=sys.stderr)
    return subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, **kw)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", default="")
    ap.add_argument("--no-download", action="store_true")
    a = ap.parse_args()
    report = {}
    if not a.no_download:
        if not a.run:
            sys.exit("need --run <id> (or --no-download)")
        merged, nart = download_merge(a.run, token())
        report["merged_manifests"] = merged
        report["artifacts"] = nart
    # ingest chain — re-apply the operator-reviewed map FIRST (CI re-probe writes fresh un-enriched
    # manifests that overwrite the reviewed enrichments on merge), THEN the heuristic pass fills the rest.
    run(["uv", "run", ".archon/scripts/enrich_thinslice.py"])
    run(["uv", "run", ".archon/scripts/enrich_scale.py"])
    run(["uv", "run", ".archon/scripts/mint_cards.py"])
    run(["uv", "run", ".archon/scripts/build_index.py", "--db", "corpus.db"])
    kb = run(["uv", "run", ".archon/scripts/kb_build.py"], env=dict(os.environ, RAG_DB="corpus_kb.db"))
    report["kb"] = kb.stdout.strip().splitlines()[-1] if kb.stdout.strip() else kb.stderr[-200:]
    run(["uv", "run", ".archon/scripts/gap_report.py"])
    cov = run(["uv", "run", ".archon/scripts/coverage.py", "--db", "corpus.db"])
    try:
        cj = json.loads([l for l in cov.stdout.splitlines() if l.strip().startswith("{")][-1])
        pr = cj.get("pass_rate", {})
        report["pass_rate_of_all"] = pr.get("pct_of_all_acquisitions")
        report["pass_rate_of_probed"] = pr.get("pct_of_probed")
        report["tripwire_fires"] = (pr.get("pct_of_all_acquisitions") or 100) < 30
    except Exception as e:
        report["coverage_parse_error"] = str(e)
    # per-category summary
    pcp = ROOT / "reports/per-category-coverage.json"
    if pcp.exists():
        pc = json.loads(pcp.read_text())
        report["whole_taxonomy_pct"] = pc.get("pct")
        report["covered_categories"] = sum(1 for v in pc["categories"].values() if v["covered"] > 0)
    print(json.dumps(report, indent=1))
    if report.get("tripwire_fires"):
        print("\n⚠ TRIPWIRE FIRES (<30% of-all). SUPERVISOR PAUSES — report to owner (R17: do NOT "
              "recalibrate by fiat). Include naive vs procedural-subset denominator analysis.", file=sys.stderr)


if __name__ == "__main__":
    main()
