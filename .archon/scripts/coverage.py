# /// script
# requires-python = ">=3.11,<3.12"
# dependencies = ["pyyaml>=6"]
# ///
"""coverage.py — corpus.db -> coverage matrix (SPEC §4.5, §2.1 Map). DETERMINISTIC; the AI
`write-coverage` node narrates on TOP of these numbers, never replaces them.

WAVE ISOLATION (§12.1(4)): PRD §3/§4 targets + the step-3 gate compute on WAVE-1 niches only;
denominators are PRESENT niches (§12.1(5)); wave-2 gets a separate table.
HONEST COMPOSITION (§12.2, owner rider 7): every coverage table splits FULL-PASS vs PARTIAL-only,
and partial-only niches accumulate a probe-recipe backlog (reports/probe-recipes.md) instead of
being silently counted the same as passes.

Emits reports/{coverage-report.md, coverage.json, gaps.md, taxonomy-proposals.md, probe-recipes.md}.

Usage: coverage.py [--db corpus.db] [--taxonomy inputs/taxonomy.yaml] [--reports reports]
                   [--probe-categories terrain,vegetation]
"""
import argparse, json, sqlite3, pathlib
import yaml

SURVIVE = {"pass", "partial"}


def load_taxonomy(path):
    doc = yaml.safe_load(open(path).read())
    niches, cats = {}, {}
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

    covered_by, niche_pass, niche_ops = {}, {}, {}
    for niche, cid, opid, state in con.execute(
            "SELECT DISTINCT niche_id, canonical_id, operator_id, state FROM coverage"):
        covered_by.setdefault(niche, set()).add(cid)
        niche_pass[niche] = niche_pass.get(niche, False) or (state == "pass")
        niche_ops.setdefault(niche, []).append((cid, opid, state))

    # pass-rate: surviving / verified, where verified EXCLUDES skipped_incompatible cells (rider 4)
    verified_ids, surviving_ids = set(), set()
    for cid, state in con.execute("SELECT canonical_id, state FROM verify"):
        if state != "skipped_incompatible":
            verified_ids.add(cid)
        if state in SURVIVE:
            surviving_ids.add(cid)
    pass_rate = (len(surviving_ids) / len(verified_ids)) if verified_ids else 0.0

    def cat_cov(cat_id, wave):
        present = cats[cat_id][f"wave{wave}"]
        covered = [n for n in present if covered_by.get(n)]
        cpass = [n for n in covered if niche_pass.get(n)]
        cpart = [n for n in covered if not niche_pass.get(n)]
        return present, covered, cpass, cpart

    probe_cats = [c.strip() for c in a.probe_categories.split(",")]
    gate_present, gate_cov, gate_pass, gate_part = [], [], [], []
    for c in probe_cats:
        p, cv, cp, cpa = cat_cov(c, 1)
        gate_present += p; gate_cov += cv; gate_pass += cp; gate_part += cpa
    gate_pct = (len(gate_cov) / len(gate_present) * 100) if gate_present else 0.0

    reports = pathlib.Path(a.reports); reports.mkdir(exist_ok=True)

    def table(wave):
        lines = ["| category | present | covered | full-pass | partial-only | % |",
                 "|---|---:|---:|---:|---:|---:|"]
        tp = tc = tpass = tpart = 0
        for cid in cats:
            p, cv, cp, cpa = cat_cov(cid, wave)
            if not p:
                continue
            tp += len(p); tc += len(cv); tpass += len(cp); tpart += len(cpa)
            pct = (len(cv) / len(p) * 100) if p else 0
            lines.append(f"| {cats[cid]['name']} | {len(p)} | {len(cv)} | {len(cp)} | {len(cpa)} | {pct:.0f}% |")
        pct = (tc / tp * 100) if tp else 0
        lines.append(f"| **TOTAL (wave {wave})** | **{tp}** | **{tc}** | **{tpass}** | **{tpart}** | **{pct:.0f}%** |")
        return "\n".join(lines), tp, tc, tpass, tpart

    w1_table, w1p, w1c, w1pass, w1part = table(1)
    w2_table, w2p, w2c, w2pass, w2part = table(2)

    detail = ["| niche | category | best | covered by |", "|---|---|---|---|"]
    for c in probe_cats:
        for n in cats[c]["wave1"]:
            if covered_by.get(n):
                best = "pass" if niche_pass.get(n) else "partial"
                detail.append(f"| `{n}` | {c} | {best} | {', '.join(sorted(covered_by[n]))} |")

    gaps = [f"# Coverage Gaps — {', '.join(probe_cats)} (wave-1)\n",
            "Zero-operator niches (targets for L2+ harvest or Stage-2 recipe planning):\n"]
    for c in probe_cats:
        miss = [n for n in cats[c]["wave1"] if not covered_by.get(n)]
        gaps.append(f"## {cats[c]['name']} — {len(miss)}/{len(cats[c]['wave1'])} uncovered\n")
        for n in miss:
            al = niches[n].get("aliases") or []
            gaps.append(f"- `{n}`" + (f"  ({', '.join(al)})" if al else ""))
        gaps.append("")

    # probe-recipe backlog (§12.2): niches covered ONLY by partial -> need a smoke-run recipe
    recipes = ["# Probe-Recipe Backlog (SPEC §12.2)\n",
               "Niches whose only covering operators reached `partial` (registered + rendered, but "
               "the operator could not be auto-driven to a geometry delta headless — typically a "
               "dialog/modal generator). Each needs a per-operator probe recipe (params/context to "
               "make it emit geometry) to upgrade `partial -> pass`. These COUNT toward coverage but "
               "are tracked here so partials never silently masquerade as full passes.\n"]
    partial_only = [n for n in covered_by if not niche_pass.get(n)]
    if not partial_only:
        recipes.append("_(none — every covered niche has at least one full-pass operator)_")
    for n in sorted(partial_only):
        cat = niches.get(n, {}).get("cat", "?")
        for cid, opid, state in sorted(niche_ops.get(n, [])):
            if state == "partial":
                recipes.append(f"- `{n}` ({cat}) ← `{opid}`  — recipe TODO")

    all_niche_ids = set(niches)
    proposals = ["# Taxonomy Proposals (§12.1(6))\n",
                 "Harvested add-ons that survived verification but map to NO taxonomy niche — "
                 "candidate wave-3 niches. Owner-approved only; never auto-added.\n"]
    mapped = {cid for s in covered_by.values() for cid in s}
    prop_rows = []
    for cid in sorted(surviving_ids - mapped):
        row = con.execute("SELECT name FROM addons WHERE canonical_id=?", (cid,)).fetchone()
        prop_rows.append(f"- `{cid}` ({row[0] if row else cid}) — survived, no niche mapped")
    proposals += (prop_rows or ["_(none — every surviving add-on mapped to a niche)_"])

    out = {
        "probe_categories": probe_cats,
        "gate": {"denominator_present_wave1": len(gate_present), "covered": len(gate_cov),
                 "full_pass": len(gate_pass), "partial_only": len(gate_part),
                 "coverage_pct": round(gate_pct, 1)},
        "pass_rate": {"verified": len(verified_ids), "surviving": len(surviving_ids),
                      "pct": round(pass_rate * 100, 1)},
        "wave1_total": {"present": w1p, "covered": w1c, "full_pass": w1pass, "partial_only": w1part},
        "wave2_total": {"present": w2p, "covered": w2c, "full_pass": w2pass, "partial_only": w2part},
        "covered_by": {k: sorted(v) for k, v in covered_by.items()},
        "probe_recipe_backlog": sorted(partial_only),
    }
    (reports / "coverage.json").write_text(json.dumps(out, indent=2))

    md = [f"# Coverage Report — L1+L2 ({', '.join(probe_cats)})", ""]
    md.append("Deterministic (`coverage.py` over `corpus.db`). Wave-1 drives the gate (§12.1(4)); "
              "denominators are PRESENT niches (§12.1(5)); every table splits full-pass vs partial "
              "(§12.2).\n")
    md.append("## Gate metrics (PRD §4 wrong-condition)\n")
    md.append(f"- **Terrain + Vegetation coverage (wave-1): {len(gate_cov)}/{len(gate_present)} = "
              f"{gate_pct:.1f}%**  ({len(gate_pass)} full-pass + {len(gate_part)} partial-only) — "
              f"PRD stop-line <40%.")
    md.append(f"- **Acquisition pass-rate: {len(surviving_ids)}/{len(verified_ids)} = "
              f"{pass_rate*100:.1f}%** (pass/partial on ≥1 compatible version; skipped-incompatible "
              f"cells excluded) — PRD stop-line <30%.")
    md.append(f"- **Probe-recipe backlog:** {len(partial_only)} niche(s) partial-only "
              f"(see `reports/probe-recipes.md`).\n")
    md.append("## Covered niches (Terrain + Vegetation, wave-1)\n")
    md.append("\n".join(detail) if len(detail) > 2 else "_(none yet)_")
    md.append("\n## Coverage by category (wave-1)\n")
    md.append(w1_table)
    md.append("\n## Wave-2 coverage (separate; does NOT move the gate)\n")
    md.append(w2_table)
    (reports / "coverage-report.md").write_text("\n".join(md) + "\n")
    (reports / "gaps.md").write_text("\n".join(gaps) + "\n")
    (reports / "taxonomy-proposals.md").write_text("\n".join(proposals) + "\n")
    (reports / "probe-recipes.md").write_text("\n".join(recipes) + "\n")

    con.close()
    print(json.dumps(out))


if __name__ == "__main__":
    main()
