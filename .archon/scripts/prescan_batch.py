# /// script
# requires-python = ">=3.11,<3.12"
# dependencies = ["pyyaml>=6"]
# ///
"""prescan_batch.py — batch the prescan gate into ONE findings report for the human approval node
(SPEC §12.2, owner rider 6). Runs prescan.py over the whole vault, applies the dated allowlist,
cross-references reviews/prescan_clearances.yaml, and tracks the FALSE-POSITIVE RATE as a metric.

Writes reports/prescan-findings.{md,json}. Deterministic, no AI. The human gate is unchanged in
strength — this only makes review cheap (one batch, one report, allowlist-downgraded noise removed).

Usage: prescan_batch.py [--vault vault] [--allowlist ...] [--clearances ...] [--reports reports]
"""
import argparse, json, subprocess, glob, os, pathlib
import yaml

ROOT = pathlib.Path(__file__).resolve().parents[2]
PRESCAN = ROOT / ".archon" / "scripts" / "prescan.py"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--vault", default="vault")
    ap.add_argument("--allowlist", default="policies/prescan-allowlist.yaml")
    ap.add_argument("--clearances", default="reviews/prescan_clearances.yaml")
    ap.add_argument("--reports", default="reports")
    a = ap.parse_args()

    files = sorted(glob.glob(os.path.join(a.vault, "*", "*", "*.zip")) +
                   glob.glob(os.path.join(a.vault, "*", "*", "*.py")) +
                   glob.glob(os.path.join(a.vault, "*", "*", "*.blend")))
    if not files:
        pathlib.Path(a.reports).mkdir(exist_ok=True)
        (pathlib.Path(a.reports) / "prescan-findings.md").write_text("# Prescan Findings\n\n_(no vault artifacts)_\n")
        print(json.dumps({"artifacts": 0, "flagged": 0}))
        return

    res = subprocess.run(["uv", "run", str(PRESCAN), "--allowlist", a.allowlist, *files],
                         capture_output=True, text=True)
    results = json.loads(res.stdout)

    cleared = set()
    cp = pathlib.Path(a.clearances)
    if cp.exists():
        doc = yaml.safe_load(cp.read_text()) or {}
        cleared = {c["artifact"] for c in doc.get("cleared", [])}

    flagged, downgraded, cleared_hits = [], [], []
    for r in results:
        base = os.path.basename(r["artifact"])
        if r["status"] == "needs_review":
            flagged.append(base)
            if base in cleared:
                cleared_hits.append(base)
        elif r.get("allowlisted"):   # clean only because of the allowlist
            downgraded.append(base)

    # false-positive rate: of everything the scanner flagged for review, how much was benign
    reviewed = len(flagged)
    fp = (len(cleared_hits) / reviewed * 100) if reviewed else 0.0

    reports = pathlib.Path(a.reports); reports.mkdir(exist_ok=True)
    out = {"artifacts": len(results), "flagged": len(flagged), "allowlist_downgraded": len(downgraded),
           "cleared": len(cleared_hits), "false_positive_rate_pct": round(fp, 1),
           "still_blocked": [f for f in flagged if f not in cleared]}
    (reports / "prescan-findings.json").write_text(json.dumps(out, indent=2))

    md = ["# Prescan Findings — batched review (SPEC §12.2)", ""]
    md.append(f"- artifacts scanned: **{len(results)}**")
    md.append(f"- flagged `needs_review` (gating hit): **{len(flagged)}**")
    md.append(f"- allowlist-downgraded to clean (benign patterns only): **{len(downgraded)}**")
    md.append(f"- human-cleared (with cited rationale): **{len(cleared_hits)}**")
    md.append(f"- **false-positive rate: {fp:.1f}%** (flagged-then-cleared / flagged) — high FP means "
              f"the scanner is over-aggressive and the allowlist should grow")
    md.append(f"- **still blocked (awaiting review): {len(out['still_blocked'])}** {out['still_blocked'] or ''}\n")
    md.append("| artifact | status | gating patterns | allowlisted (informational) |")
    md.append("|---|---|---|---|")
    for r in results:
        base = os.path.basename(r["artifact"])
        st = "cleared" if (r["status"] == "needs_review" and base in cleared) else r["status"]
        md.append(f"| `{base}` | {st} | {', '.join(r.get('gating', [])) or '—'} | {', '.join(r.get('allowlisted', [])) or '—'} |")
    (reports / "prescan-findings.md").write_text("\n".join(md) + "\n")
    print(json.dumps(out))


if __name__ == "__main__":
    main()
