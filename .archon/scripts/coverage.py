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

    # R14 (D-002): recipe registry — composite coverage. recipe_unverified NEVER counts toward the
    # gate; only DIRECT add-on coverage + recipe_verified do. verified beats unverified per niche.
    recipe_tier = {}
    rpath = pathlib.Path("inputs/recipes.yaml")
    if rpath.exists():
        for r in (yaml.safe_load(rpath.read_text()) or {}).get("recipes", []):
            n, t = r.get("niche"), r.get("tier")
            if n and t in ("recipe_verified", "recipe_unverified") and recipe_tier.get(n) != "recipe_verified":
                recipe_tier[n] = t

    # R18 (D-003): gate metric v2 — denominator = ATTAINABLE niches (R15 link-backed audit), the
    # unattainable (paid_only/none) are excluded so we measure the HARVEST not the market. Loaded
    # from the audit data; falls back to all-present if the audit is absent.
    ATTAINABLE_VERDICTS = {"verified_free", "free_tool", "free_recipe"}
    attainable = None  # set of niche ids; None => not available (use all-present)
    unattainable = {}
    cal = pathlib.Path("reports/coverage-calibration-data.yaml")
    if cal.exists():
        attainable = set()
        for r in (yaml.safe_load(cal.read_text()) or {}).get("niches", []):
            if r.get("verdict") in ATTAINABLE_VERDICTS:
                attainable.add(r["id"])
            else:
                unattainable[r["id"]] = r.get("verdict")

    con = sqlite3.connect(a.db)

    covered_by, niche_pass, niche_ops = {}, {}, {}
    for niche, cid, opid, state in con.execute(
            "SELECT DISTINCT niche_id, canonical_id, operator_id, state FROM coverage"):
        covered_by.setdefault(niche, set()).add(cid)
        niche_pass[niche] = niche_pass.get(niche, False) or (state == "pass")
        niche_ops.setdefault(niche, []).append((cid, opid, state))

    # pass-rate: surviving / verified, where verified EXCLUDES skipped_incompatible cells (rider 4)
    verified_ids, surviving_ids, all_ids = set(), set(), set()
    for cid, state in con.execute("SELECT canonical_id, state FROM verify"):
        all_ids.add(cid)                                            # every vaulted artifact
        if state not in ("skipped_incompatible", "needs_review"):   # neither ran a probe
            verified_ids.add(cid)
        if state in SURVIVE:
            surviving_ids.add(cid)
    pass_rate = (len(surviving_ids) / len(verified_ids)) if verified_ids else 0.0
    pass_rate_all = (len(surviving_ids) / len(all_ids)) if all_ids else 0.0   # R16/D-002: of-all

    def cat_cov(cat_id, wave):
        present = cats[cat_id][f"wave{wave}"]
        dpass = [n for n in present if covered_by.get(n) and niche_pass.get(n)]
        dpart = [n for n in present if covered_by.get(n) and not niche_pass.get(n)]
        # recipes apply ONLY to niches with no direct add-on coverage
        rver = [n for n in present if not covered_by.get(n) and recipe_tier.get(n) == "recipe_verified"]
        runver = [n for n in present if not covered_by.get(n) and recipe_tier.get(n) == "recipe_unverified"]
        return present, dpass, dpart, rver, runver

    probe_cats = [c.strip() for c in a.probe_categories.split(",")]
    gate_present, g_dpass, g_dpart, g_rver, g_runver = [], [], [], [], []
    for c in probe_cats:
        p, dp, da, rv, ru = cat_cov(c, 1)
        gate_present += p; g_dpass += dp; g_dpart += da; g_rver += rv; g_runver += ru
    gate_decision = len(g_dpass) + len(g_dpart) + len(g_rver)   # direct + recipe_verified (R14)
    gate_pct = (gate_decision / len(gate_present) * 100) if gate_present else 0.0

    # ── R18 (D-003): GATE v2 — STRICTER. numerator = full_pass + recipe_verified ONLY (partial does
    # NOT count; a partial op is a runtime landmine an agent can't improvise around). denominator =
    # ATTAINABLE probe-category wave-1 niches (excludes the paid_only/none). threshold unchanged 40%.
    gate_present_ids = set(gate_present)
    # R32(3)/D-005: a niche with a verified path (full_pass or recipe_verified) is attainable BY
    # DEFINITION — grow the R15 attainable set with them, so converting a paid_only/none niche via an
    # asset-fed recipe adds it to BOTH numerator and denominator, honestly.
    if attainable is not None:
        verified_path = set(g_dpass) | {n for n in gate_present if recipe_tier.get(n) == "recipe_verified"}
        attainable = attainable | verified_path
    attain_denom = ([n for n in gate_present if n in attainable] if attainable is not None else gate_present)
    v2_num = [n for n in (g_dpass + g_rver) if (attainable is None or n in attainable)]  # full_pass + recipe_verified, attainable
    v2_pct = (len(v2_num) / len(attain_denom) * 100) if attain_denom else 0.0
    v2_excluded = sorted(n for n in gate_present_ids if attainable is not None and n not in attainable)

    reports = pathlib.Path(a.reports); reports.mkdir(exist_ok=True)

    def table(wave):
        lines = ["| category | present | full-pass | partial | recipe✓ | recipe? (claim) | decision % |",
                 "|---|---:|---:|---:|---:|---:|---:|"]
        tp = tdp = tda = trv = tru = 0
        for cid in cats:
            p, dp, da, rv, ru = cat_cov(cid, wave)
            if not p:
                continue
            tp += len(p); tdp += len(dp); tda += len(da); trv += len(rv); tru += len(ru)
            dec = len(dp) + len(da) + len(rv)
            pct = (dec / len(p) * 100) if p else 0
            lines.append(f"| {cats[cid]['name']} | {len(p)} | {len(dp)} | {len(da)} | {len(rv)} | {len(ru)} | {pct:.0f}% |")
        dec = tdp + tda + trv
        pct = (dec / tp * 100) if tp else 0
        lines.append(f"| **TOTAL (wave {wave})** | **{tp}** | **{tdp}** | **{tda}** | **{trv}** | **{tru}** | **{pct:.0f}%** |")
        return "\n".join(lines), tp, dec, tru

    w1_table, w1p, w1dec, w1runver = table(1)
    w2_table, w2p, w2dec, w2runver = table(2)

    detail = ["| niche | category | best | covered by |", "|---|---|---|---|"]
    for c in probe_cats:
        for n in cats[c]["wave1"]:
            if covered_by.get(n):
                best = "pass" if niche_pass.get(n) else "partial"
                detail.append(f"| `{n}` | {c} | {best} | {', '.join(sorted(covered_by[n]))} |")

    gaps = [f"# Coverage Gaps — {', '.join(probe_cats)} (wave-1)\n",
            "Zero-operator niches (targets for L2+ harvest or Stage-2 recipe planning):\n"]
    for c in probe_cats:
        miss = [n for n in cats[c]["wave1"] if not covered_by.get(n) and n not in recipe_tier]
        gaps.append(f"## {cats[c]['name']} — {len(miss)}/{len(cats[c]['wave1'])} with neither add-on nor recipe\n")
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

    # ── R19 (D-003): pass-rate tripwire — of-all-acquisitions <30% at ANY lane gate => pause+escalate.
    tripwire = {"pass_rate_of_all_pct": round(pass_rate_all * 100, 1), "threshold": 30.0,
                "tripped": (pass_rate_all * 100) < 30.0}

    # ── R22 (D-003): verb × medium grid — VERIFIED operators per physical verb × medium. This is what
    # the Stage-2 metaphor resolver consumes (niches are substitutable, verbs are not). Medium per niche
    # from inputs/niche-medium.yaml; an operator counts if its niche survived (pass/partial) on >=1 ver.
    MEDIA = ["ground", "water", "air", "urban", "organic", "abstract"]
    medium_map = {}
    mp = pathlib.Path("inputs/niche-medium.yaml")
    if mp.exists():
        medium_map = (yaml.safe_load(mp.read_text()) or {}).get("medium", {})
    verb_medium = {}   # (verb, medium) -> set(operator_id)
    for niche, ops in niche_ops.items():
        med = medium_map.get(niche, "abstract")
        nverbs = niches.get(niche, {}).get("verbs", []) if False else None
        # verbs live on operators (from enrich); pull from DB
        for cid, opid, state in ops:
            if state not in SURVIVE:
                continue
            row = con.execute("SELECT verbs_json FROM operators WHERE id=?", (opid,)).fetchone()
            vs = json.loads(row[0]) if row and row[0] else []
            for v in vs:
                verb_medium.setdefault((v, med), set()).add(opid)
    verb_medium_counts = {f"{v}|{m}": len(s) for (v, m), s in sorted(verb_medium.items())}

    out = {
        "probe_categories": probe_cats,
        "gate": {"denominator_present_wave1": len(gate_present), "decision_covered": gate_decision,
                 "full_pass": len(g_dpass), "partial": len(g_dpart), "recipe_verified": len(g_rver),
                 "recipe_unverified_claims": len(g_runver), "coverage_pct": round(gate_pct, 1)},
        "gate_v2": {"metric": "(full_pass + recipe_verified) / attainable wave-1 T+V",
                    "numerator": len(v2_num), "denominator_attainable": len(attain_denom),
                    "coverage_pct": round(v2_pct, 1), "threshold": 40.0,
                    "excluded_unattainable": v2_excluded},
        "tripwire": tripwire,
        "verb_medium_grid": verb_medium_counts,
        "pass_rate": {"verified_probed": len(verified_ids), "acquisitions": len(all_ids),
                      "surviving": len(surviving_ids), "pct_of_probed": round(pass_rate * 100, 1),
                      "pct_of_all_acquisitions": round(pass_rate_all * 100, 1)},
        "wave1_total": {"present": w1p, "decision_covered": w1dec, "recipe_unverified_claims": w1runver},
        "wave2_total": {"present": w2p, "decision_covered": w2dec, "recipe_unverified_claims": w2runver},
        "covered_by": {k: sorted(v) for k, v in covered_by.items()},
        "probe_recipe_backlog": sorted(partial_only),
    }
    (reports / "coverage.json").write_text(json.dumps(out, indent=2))

    md = [f"# Coverage Report — L1+L2 ({', '.join(probe_cats)})", ""]
    md.append("Deterministic (`coverage.py` over `corpus.db`). Wave-1 drives the gate (§12.1(4)); "
              "denominators are PRESENT niches (§12.1(5)); every table splits full-pass vs partial "
              "(§12.2).\n")
    md.append("## Gate metrics (PRD §4 wrong-condition)\n")
    md.append(f"- **GATE v2 (R18/D-003 — the governing metric): {len(v2_num)}/{len(attain_denom)} = "
              f"{v2_pct:.1f}%** = (full_pass + recipe_verified) / {len(attain_denom)} ATTAINABLE "
              f"Terrain+Veg wave-1 niches. Threshold **40%** (final verdict after L5b, R19). "
              f"`partial` and `recipe_unverified` do NOT count in v2.")
    md.append(f"  - excluded as unattainable (paid_only/none, R15): {', '.join('`'+n+'`' for n in v2_excluded) or 'none'}")
    md.append(f"- **Tripwire (R19): pass-rate of-all-acquisitions {tripwire['pass_rate_of_all_pct']}%** "
              f"vs 30% floor → {'⚠ TRIPPED — pause + owner escalation' if tripwire['tripped'] else 'OK'}.")
    md.append(f"- _v1 (legacy, all-present denom): {gate_decision}/{len(gate_present)} = {gate_pct:.1f}% "
              f"({len(g_dpass)} full-pass + {len(g_dpart)} partial + {len(g_rver)} recipe✓; "
              f"{len(g_runver)} recipe claims not counted)._")
    md.append(f"- **Acquisition pass-rate (both framings, R16/D-002):** of-probed "
              f"{len(surviving_ids)}/{len(verified_ids)} = {pass_rate*100:.1f}%; of-all-acquisitions "
              f"{len(surviving_ids)}/{len(all_ids)} = {pass_rate_all*100:.1f}% — PRD stop-line <30%.")
    md.append(f"- **Probe-recipe backlog:** {len(partial_only)} niche(s) partial-only "
              f"(see `reports/probe-recipes.md`).\n")
    md.append("## Covered niches (Terrain + Vegetation, wave-1)\n")
    md.append("\n".join(detail) if len(detail) > 2 else "_(none yet)_")
    md.append("\n## Coverage by category (wave-1)\n")
    md.append(w1_table)
    md.append("\n## Wave-2 coverage (separate; does NOT move the gate)\n")
    md.append(w2_table)
    # R22: verb × medium grid (Stage-2 metaphor-resolver entry metric — informational now)
    md.append("\n## Verb × medium grid (R22 — verified operators; Stage-2 consumer metric)\n")
    md.append("Count of VERIFIED (pass/partial) operators by physical verb × medium. Niches are "
              "substitutable; verbs are not — this is what the metaphor resolver queries.\n")
    hdr = "| verb | " + " | ".join(MEDIA) + " |"
    md.append(hdr); md.append("|" + "---|" * (len(MEDIA) + 1))
    verbs_seen = sorted({v for (v, m) in verb_medium})
    for v in verbs_seen:
        cells = [str(len(verb_medium.get((v, m), set()))) for m in MEDIA]
        md.append(f"| {v} | " + " | ".join(cells) + " |")
    if not verbs_seen:
        md.append("| _(no verified operators yet)_ | " + " | ".join(["0"] * len(MEDIA)) + " |")
    (reports / "coverage-report.md").write_text("\n".join(md) + "\n")
    (reports / "gaps.md").write_text("\n".join(gaps) + "\n")
    (reports / "taxonomy-proposals.md").write_text("\n".join(proposals) + "\n")
    (reports / "probe-recipes.md").write_text("\n".join(recipes) + "\n")

    con.close()
    print(json.dumps(out))


if __name__ == "__main__":
    main()
