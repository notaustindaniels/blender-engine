# /// script
# requires-python = ">=3.11,<3.12"
# dependencies = ["pyyaml>=6"]
# ///
"""coverage.py — corpus.db -> coverage matrix (SPEC §4.5, §2.1 Map). DETERMINISTIC; the AI
`write-coverage` node narrates on TOP of these computed numbers, never replaces them.

WAVE ISOLATION (§12.1(4)): PRD §3/§4 targets + the step-3 gate compute on WAVE-1 niches only.
Denominators are PRESENT niches per the taxonomy (§12.1(5)). Wave-2 gets a separate table.
Emits reports/coverage-report.md, reports/coverage.json, reports/gaps.md, and
reports/taxonomy-proposals.md (§12.1(6)).

Usage: coverage.py [--db corpus.db] [--taxonomy inputs/taxonomy.yaml] [--reports reports]
"""
import argparse, json, sqlite3, pathlib
import yaml

SURVIVE = {"pass", "partial"}


def load_taxonomy(path):
    doc = yaml.safe_load(open(path).read())
    niches = {}   # niche_id -> {cat, cat_name, wave, core}
    cats = {}     # cat_id -> {name, wave1:[...], wave2:[...], core}
    for cat in doc.get("categories", []):
        cid = cat["id"]
        cats[cid] = {"name": cat.get("name", cid), "wave1": [], "wave2": []}
        for n in cat.get("niches", []) or []:
            w = int(n.get("wave", 1))
            niches[n["id"]] = {"cat": cid, "cat_name": cat.get("name", cid), "wave": w,
                               "core": bool(n.get("core")), "aliases": n.get("aliases", [])}
            cats[cid][f"wave{w}"].append(n["id"])
    return doc, niches, cats


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="corpus.db")
    ap.add_argument("--taxonomy", default="inputs/taxonomy.yaml")
    ap.add_argument("--reports", default="reports")
    ap.add_argument("--probe-categories", default="terrain,vegetation")
    a = ap.parse_args()

    doc, niches, cats = load_taxonomy(a.taxonomy)
    con = sqlite3.connect(a.db)

    covered_by = {}   # niche_id -> set(canonical_id)
    for niche, cid in con.execute("SELECT DISTINCT niche_id, canonical_id FROM coverage"):
        covered_by.setdefault(niche, set()).add(cid)

    # acquisition pass-rate = addons surviving (pass/partial) on >=1 version / addons verified
    verified_ids, surviving_ids = set(), set()
    for cid, ver, state, rok in con.execute("SELECT canonical_id, blender_ver, state, render_ok FROM verify"):
        verified_ids.add(cid)
        if state in SURVIVE:
            surviving_ids.add(cid)
    pass_rate = (len(surviving_ids) / len(verified_ids)) if verified_ids else 0.0

    def cat_cov(cat_id, wave):
        present = cats[cat_id][f"wave{wave}"]
        covered = [n for n in present if covered_by.get(n)]
        return present, covered

    probe_cats = [c.strip() for c in a.probe_categories.split(",")]
    # ---- gate: probe categories, wave-1 only ----
    gate_present, gate_covered = [], []
    for c in probe_cats:
        p, cv = cat_cov(c, 1)
        gate_present += p; gate_covered += cv
    gate_pct = (len(gate_covered) / len(gate_present) * 100) if gate_present else 0.0

    reports = pathlib.Path(a.reports); reports.mkdir(exist_ok=True)

    # ---- full wave-1 category table ----
    def table(wave):
        lines = ["| category | present | covered | % |", "|---|---:|---:|---:|"]
        tot_p = tot_c = 0
        for cid in cats:
            p, cv = cat_cov(cid, wave)
            if not p:
                continue
            tot_p += len(p); tot_c += len(cv)
            pct = (len(cv) / len(p) * 100) if p else 0
            lines.append(f"| {cats[cid]['name']} | {len(p)} | {len(cv)} | {pct:.0f}% |")
        pct = (tot_c / tot_p * 100) if tot_p else 0
        lines.append(f"| **TOTAL (wave {wave})** | **{tot_p}** | **{tot_c}** | **{pct:.0f}%** |")
        return "\n".join(lines), tot_p, tot_c

    w1_table, w1_p, w1_c = table(1)
    w2_table, w2_p, w2_c = table(2)

    # ---- covered-niche detail for the probe categories ----
    detail = ["| niche | category | covered by |", "|---|---|---|"]
    for c in probe_cats:
        for n in cats[c]["wave1"]:
            if covered_by.get(n):
                detail.append(f"| `{n}` | {c} | {', '.join(sorted(covered_by[n]))} |")

    # ---- gaps (zero-operator wave-1 niches in probe categories) ----
    gaps = [f"# Coverage Gaps — {', '.join(probe_cats)} (wave-1)\n",
            "Zero-operator niches (targets for L2+ harvest or Stage-2 recipe planning):\n"]
    for c in probe_cats:
        miss = [n for n in cats[c]["wave1"] if not covered_by.get(n)]
        gaps.append(f"## {cats[c]['name']} — {len(miss)}/{len(cats[c]['wave1'])} uncovered\n")
        for n in miss:
            al = niches[n].get("aliases") or []
            gaps.append(f"- `{n}`" + (f"  ({', '.join(al)})" if al else ""))
        gaps.append("")

    # ---- taxonomy proposals: surviving add-ons whose niches were unmapped ----
    all_niche_ids = set(niches)
    proposals = ["# Taxonomy Proposals (§12.1(6))\n",
                 "Harvested add-ons that survived verification but map to NO taxonomy niche — "
                 "candidate wave-3 niches. Owner-approved only; never auto-added.\n"]
    mapped_addons = {cid for s in covered_by.values() for cid in s}
    prop_rows = []
    for cid in sorted(surviving_ids - mapped_addons):
        name, tags = con.execute(
            "SELECT name, addon_type FROM addons WHERE canonical_id=?", (cid,)).fetchone() or (cid, "")
        prop_rows.append(f"- `{cid}` ({name}) — survived verification, no niche mapped yet")
    proposals += (prop_rows or ["_(none — every surviving add-on mapped to a niche)_"])

    out = {
        "probe_categories": probe_cats,
        "gate": {"denominator_present_wave1": len(gate_present), "covered": len(gate_covered),
                 "coverage_pct": round(gate_pct, 1),
                 "terrain_veg_niches": len(gate_present)},
        "pass_rate": {"verified": len(verified_ids), "surviving": len(surviving_ids),
                      "pct": round(pass_rate * 100, 1)},
        "wave1_total": {"present": w1_p, "covered": w1_c},
        "wave2_total": {"present": w2_p, "covered": w2_c},
        "covered_by": {k: sorted(v) for k, v in covered_by.items()},
    }
    (reports / "coverage.json").write_text(json.dumps(out, indent=2))

    md = [f"# Coverage Report — L1 Thin Slice ({', '.join(probe_cats)})", ""]
    md.append("Computed deterministically by `coverage.py` from `corpus.db`. Wave-1 drives the "
              "gate (§12.1(4)); denominators are PRESENT niches (§12.1(5)).\n")
    md.append("## Gate metrics (PRD §4 wrong-condition)\n")
    md.append(f"- **Terrain + Vegetation coverage (wave-1): {len(gate_covered)}/{len(gate_present)} "
              f"= {gate_pct:.1f}%**  — PRD stop-line is <40% (evaluated after L1+L2).")
    md.append(f"- **Acquisition pass-rate: {len(surviving_ids)}/{len(verified_ids)} = "
              f"{pass_rate*100:.1f}%** (pass/partial on ≥1 version) — PRD stop-line is <30%.\n")
    md.append("## Covered niches (Terrain + Vegetation, wave-1)\n")
    md.append("\n".join(detail) if len(detail) > 2 else "_(none yet)_")
    md.append("\n## Coverage by category (wave-1)\n")
    md.append(w1_table)
    md.append("\n## Wave-2 coverage (separate; does NOT move the gate)\n")
    md.append(w2_table)
    (reports / "coverage-report.md").write_text("\n".join(md) + "\n")
    (reports / "gaps.md").write_text("\n".join(gaps) + "\n")
    (reports / "taxonomy-proposals.md").write_text("\n".join(proposals) + "\n")

    con.close()
    print(json.dumps(out))


if __name__ == "__main__":
    main()
