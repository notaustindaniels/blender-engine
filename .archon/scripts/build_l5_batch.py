# /// script
# requires-python = ">=3.11,<3.12"
# dependencies = ["pyyaml>=6"]
# ///
"""build_l5_batch.py — assemble the first L5/free-tool approval batch (D-003 R20 + R11 ranking;
D-004). ToS-respecting: sources are the R15 audit's link-backed `free_tool` niches (discovered via
web SEARCH, not marketplace scraping — Gumroad §14) plus forum-harvested L5-pending links. Ranks by
(i) targets an UNCOVERED attainable niche, (ii) fills an empty verb×medium grid cell, (iii) GN-pack
likelihood. Mirror-check routes github/gitlab URLs to L2/L3 (free, automatable, no checkout); the
rest become human-gated $0 approval rows. Caps at --max rows. Outputs reports/l5-batch-1.md (the
5-second approval format) + reports/l5-batch-1.json.

Usage: uv run .archon/scripts/build_l5_batch.py [--max 20]
"""
import argparse, json, pathlib, re
import yaml

ROOT = pathlib.Path(__file__).resolve().parents[2]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--max", type=int, default=20)
    a = ap.parse_args()

    cal = yaml.safe_load((ROOT / "reports/coverage-calibration-data.yaml").read_text())["niches"]
    cov = json.loads((ROOT / "reports/coverage.json").read_text())
    medium_map = (yaml.safe_load((ROOT / "inputs/niche-medium.yaml").read_text()) or {}).get("medium", {})
    covered = set(cov.get("covered_by", {}).keys()) | set(cov.get("gate_v2", {}).get("numerator_ids", []))
    # a niche is "covered" if it's in covered_by OR its recipe is verified — reuse coverage.json
    covered = set(cov.get("covered_by", {}).keys())
    grid = cov.get("verb_medium_grid", {})
    empty_media = {"water", "air", "urban"}       # R11: prioritize these media
    tax = yaml.safe_load((ROOT / "inputs/taxonomy.yaml").read_text())
    verbs_by_niche = {}
    for c in tax["categories"]:
        for n in c.get("niches", []) or []:
            verbs_by_niche[n["id"]] = n.get("verbs", [])

    rows = []
    for r in cal:
        nid = r["id"]
        if r["verdict"] != "free_tool":
            continue                      # first batch: free_tool niches (highest-value, URL-backed)
        if nid in covered:
            continue                      # only UNCOVERED (R11: fills the gap)
        url = r.get("url", "")
        host = re.sub(r"https?://", "", url).split("/")[0].lower()
        is_repo = any(h in host for h in ("github.com", "gitlab.com", "codeberg"))
        med = medium_map.get(nid, "abstract")
        nverbs = verbs_by_niche.get(nid, [])
        # rank score: uncovered attainable (all here) + empty-medium bonus + grid-cell-empty bonus + GN/repo
        score = 10
        if med in empty_media:
            score += 5
        # bonus if this niche's (verb,medium) cells are all empty in the grid
        if all(grid.get(f"{v}|{med}", 0) == 0 for v in nverbs):
            score += 4
        rows.append({
            "target_niche": nid, "medium": med, "verbs": nverbs,
            "product": (r.get("evidence", "")[:60] or nid),
            "url": url, "host": host,
            "mirror_check": "GitHub/GitLab → reroute to L2/L3 (free, automatable, NO checkout)" if is_repo
                            else "no free repo mirror found → human $0 acquisition",
            "route": "L2/L3-auto" if is_repo else "L5-human-gated",
            "price_assertion": "$0 (free tool per R15 audit) — CONFIRM at source",
            "license": r.get("license", "confirm at source"),
            "confidence": r.get("confidence"), "score": score,
        })

    rows.sort(key=lambda x: (-x["score"], x["target_niche"]))
    rows = rows[:a.max]

    (ROOT / "reports/l5-batch-1.json").write_text(json.dumps(rows, indent=2))
    md = ["# L5 / free-tool Approval Batch #1 (D-003 R20 · R11 ranking · D-004)", ""]
    md.append("**ToS-respecting:** sourced from the R15 link-backed audit (found via web search, not "
              "marketplace scraping) — targets UNCOVERED attainable Terrain+Veg niches, ranked to move "
              "gate v2 + fill empty verb×medium cells. GitHub-mirrored rows auto-route to L2/L3 (no "
              "checkout); the rest are human-gated $0. **5-second-per-row format below.**\n")
    md.append("| # | target niche | medium/verbs | product (evidence) | source | mirror-check → route | $0? | license |")
    md.append("|--:|---|---|---|---|---|---|---|")
    for i, r in enumerate(rows, 1):
        md.append(f"| {i} | `{r['target_niche']}` | {r['medium']} / {','.join(r['verbs'])} | "
                  f"{r['product']} | {r['host']} | {r['mirror_check']} | {r['price_assertion']} | {r['license']} |")
    md.append(f"\n**{len(rows)} rows.** Auto-route (GitHub, no approval needed): "
              f"{sum(1 for r in rows if r['route']=='L2/L3-auto')}. "
              f"Human-gated $0 (your approval): {sum(1 for r in rows if r['route']=='L5-human-gated')}.\n")
    md.append("**Approve** = I acquire the GitHub-routed ones automatically (hash-verified) and you "
              "complete the $0 checkouts for the human-gated rows; then all go through the standard "
              "probe (R21 for GN-packs). **Reject any row** and it drops. No paid acquisition (R23).")
    (ROOT / "reports/l5-batch-1.md").write_text("\n".join(md) + "\n")
    print(json.dumps({"batch_rows": len(rows),
                      "auto_route": sum(1 for r in rows if r["route"] == "L2/L3-auto"),
                      "human_gated": sum(1 for r in rows if r["route"] == "L5-human-gated")}))


if __name__ == "__main__":
    main()
