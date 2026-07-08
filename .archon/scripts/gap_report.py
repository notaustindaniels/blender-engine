# /// script
# requires-python = ">=3.11,<3.12"
# dependencies = ["pyyaml>=6"]
# ///
"""gap_report.py — per-category coverage + first-class gap reports for ALL 26 categories (D-008 R47).

The campaign metric that replaces the retired T+V proxy: per-category quality-tiered coverage, plus a
gap report naming what the free ecosystem genuinely lacks per category. A gap is an uncovered niche;
where the R15 calibration audit classified it, we say WHY (no free tool found / paid-only / unattainable).

Reads corpus.db (coverage), taxonomy.yaml (all categories/niches/waves), recipes.yaml (recipe tiers),
coverage-calibration-data.yaml (attainability). Emits reports/gap-report.md + reports/gaps/<cat>.md +
reports/per-category-coverage.json. Rebuild anytime; grows as waves ingest.
"""
import json, sqlite3, pathlib, sys
import yaml

ROOT = pathlib.Path(__file__).resolve().parents[2]
TAX = yaml.safe_load(open(ROOT / "inputs/taxonomy.yaml"))
RECIPES = yaml.safe_load(open(ROOT / "inputs/recipes.yaml"))["recipes"]
CAL = {}
calp = ROOT / "reports/coverage-calibration-data.yaml"
if calp.exists():
    cd = yaml.safe_load(open(calp)) or {}
    # niches: list of {id, cat, verdict, confidence, evidence} (R15 audit)
    for item in (cd.get("niches") or []):
        if isinstance(item, dict) and item.get("id"):
            CAL[item["id"]] = item.get("verdict") or item.get("class") or "unclassified"


def slug(name):
    return "".join(c if c.isalnum() else "-" for c in name.lower()).strip("-")


def main():
    con = sqlite3.connect(ROOT / "corpus.db"); con.row_factory = sqlite3.Row
    # niche -> best state (pass > partial), and recipe tier
    covered = {}
    for r in con.execute("SELECT niche_id, state FROM coverage"):
        cur = covered.get(r["niche_id"])
        rank = {"pass": 3, "partial": 2}.get(r["state"], 1)
        if not cur or rank > cur[1]:
            covered[r["niche_id"]] = (r["state"], rank)
    rv = {r["niche"] for r in RECIPES if r.get("tier") == "recipe_verified"}
    ru = {r["niche"] for r in RECIPES if r.get("tier") == "recipe_unverified"}

    def niche_status(nid):
        if nid in covered and covered[nid][1] == 3:
            return "full_pass"
        if nid in rv:
            return "recipe_verified"
        if nid in covered and covered[nid][1] == 2:
            return "partial"
        if nid in ru:
            return "recipe_unverified"
        return "GAP"

    gapdir = ROOT / "reports/gaps"; gapdir.mkdir(parents=True, exist_ok=True)
    percat = {}
    summary_rows = []
    total_niches = total_covered = 0
    for cat in TAX["categories"]:
        niches = cat.get("niches") or []
        rows = []
        cov = 0
        for n in niches:
            nid = n["id"]; st = niche_status(nid)
            if st in ("full_pass", "recipe_verified"):
                cov += 1
            rows.append({"niche": nid, "wave": int(n.get("wave", 1)), "status": st,
                         "attainability": CAL.get(nid, "unclassified")})
        total_niches += len(niches); total_covered += cov
        percat[cat["name"]] = {"present": len(niches), "covered": cov,
                               "pct": round(100 * cov / len(niches), 1) if niches else 0.0, "niches": rows}
        summary_rows.append((cat["name"], len(niches), cov, percat[cat["name"]]["pct"]))
        # per-category gap file
        gaps = [r for r in rows if r["status"] == "GAP"]
        lines = [f"# Gap report — {cat['name']} (D-008 R47)\n",
                 f"Coverage: **{cov}/{len(niches)} = {percat[cat['name']]['pct']}%** "
                 f"(full_pass + recipe_verified). {len(gaps)} gaps.\n",
                 "| niche | wave | status | attainability (R15) |", "|---|---|---|---|"]
        for r in rows:
            lines.append(f"| {r['niche']} | {r['wave']} | {r['status']} | {r['attainability']} |")
        if gaps:
            lines.append(f"\n**Gaps ({len(gaps)}):** what the free ecosystem lacks here — "
                         + ", ".join(f"`{g['niche']}`({g['attainability']})" for g in gaps))
        (gapdir / f"{slug(cat['name'])}.md").write_text("\n".join(lines) + "\n")

    # summary
    summary_rows.sort(key=lambda x: -x[3])
    out = [f"# Per-category coverage + gap summary (D-008 R47) — all {len(TAX['categories'])} categories\n",
           f"**Whole-taxonomy coverage: {total_covered}/{total_niches} = "
           f"{round(100*total_covered/total_niches,1)}%** (full_pass + recipe_verified). Per-category detail "
           f"in `reports/gaps/<category>.md`. A gap is an uncovered niche; attainability from the R15 audit.\n",
           "| category | covered | present | % | gaps |", "|---|---|---|---|---|"]
    for name, present, cov, pct in summary_rows:
        out.append(f"| {name} | {cov} | {present} | {pct}% | {present-cov} |")
    (ROOT / "reports/gap-report.md").write_text("\n".join(out) + "\n")
    (ROOT / "reports/per-category-coverage.json").write_text(json.dumps(
        {"total_niches": total_niches, "total_covered": total_covered,
         "pct": round(100*total_covered/total_niches, 1), "categories": percat}, indent=1))
    print(json.dumps({"categories": len(TAX["categories"]), "total_niches": total_niches,
                      "total_covered": total_covered,
                      "pct": round(100*total_covered/total_niches, 1),
                      "covered_categories": sum(1 for _, _, c, _ in summary_rows if c > 0)}))


if __name__ == "__main__":
    main()
