# /// script
# requires-python = ">=3.11,<3.12"
# dependencies = ["pyyaml>=6"]
# ///
"""calibration_memo.py — render reports/coverage-calibration.md from the R15 audit data
(D-002 R15). Computes the attainable-base distribution and frames an evidence-based recalibration
PROPOSAL for the owner's D-003 decision. Changes NO target (recalibration-by-fiat is forbidden).
"""
import yaml, pathlib, collections

DATA = pathlib.Path("reports/coverage-calibration-data.yaml")
OUT = pathlib.Path("reports/coverage-calibration.md")
ATTAINABLE = {"verified_free", "free_tool", "free_recipe"}
ORDER = ["verified_free", "free_tool", "free_recipe", "paid_only", "none"]

rows = yaml.safe_load(DATA.read_text())["niches"]
n = len(rows)
by = collections.Counter(r["verdict"] for r in rows)
attain = [r for r in rows if r["verdict"] in ATTAINABLE]
verified = [r for r in rows if r["verdict"] == "verified_free"]
free_tool = [r for r in rows if r["verdict"] == "free_tool"]
free_recipe = [r for r in rows if r["verdict"] == "free_recipe"]
not_attain = [r for r in rows if r["verdict"] in ("paid_only", "none")]

pct = lambda k: f"{len(k)/n*100:.0f}%"
m = ["# Coverage Calibration Memo — Terrain+Vegetation wave-1 (D-002 R15)", ""]
m.append("**Date:** 2026-07-06 · **Method:** cached extensions.blender.org catalog mine + live web "
         "research (2026-07-06). Per-niche market-existence audit of all **%d** wave-1 niches. "
         "Confidence-graded; this is a PROPOSAL for the D-003 decision — **no target is changed here** "
         "(recalibration-by-fiat after a miss is forbidden, R15)." % n)
m.append("")
m.append("## The finding: the 40% target and our metric measure different things\n")
m.append("Our **decision coverage** counts a niche only when a **dedicated free add-on is vaulted AND "
         "survives our headless probe** — currently **7/59 = 11.9%**. But a market-existence audit of "
         "the same 59 niches shows free tooling or a plausible free recipe exists for far more of them; "
         "they simply live on GitHub / free GN packs / Gumroad-\\$0 / built-ins — sources L1 (the tiny "
         "official platform) doesn't reach and that the emulation-capped L2 sample barely touched.\n")
m.append("## Attainable-base distribution (evidence-based)\n")
m.append("| verdict | niches | share | meaning |")
m.append("|---|---:|---:|---|")
labels = {"verified_free": "already probed free tool (decision-grade)",
          "free_tool": "free dedicated add-on exists, not yet vaulted/probed",
          "free_recipe": "no dedicated tool, but a plausible free recipe (built-ins/GN/free packs)",
          "paid_only": "tools exist but only paid (excluded by the free constraint)",
          "none": "no known free tool AND no plausible free recipe"}
for k in ORDER:
    m.append(f"| `{k}` | {by.get(k,0)} | {by.get(k,0)/n*100:.0f}% | {labels[k]} |")
m.append(f"| **ATTAINABLE (free tool or recipe)** | **{len(attain)}** | **{pct(attain)}** | verified_free + free_tool + free_recipe |")
m.append(f"| **NOT attainable (paid/none)** | **{len(not_attain)}** | **{pct(not_attain)}** | the true free-ecosystem ceiling |")
m.append("")
m.append(f"**Read:** ~**{pct(attain)}** of the 59 wave-1 Terrain+Veg niches have SOME free path; only "
         f"**{pct(not_attain)}** ({len(not_attain)} niches) appear genuinely unreachable for free "
         f"(marine flora skews paid: coral/kelp/anemone; plus exotic karst/atoll/meander). So a 40% "
         f"target is **not** obviously unreachable — but our *current metric* (dedicated-add-on-only, "
         f"probe-verified) undercounts the attainable base by design.\n")
m.append("## Not-attainable niches (the real ceiling)\n")
for r in not_attain:
    m.append(f"- `{r['id']}` ({r['verdict']}, {r['confidence']}) — {r['evidence']}")
m.append("")
m.append("## Proposal for D-003 (owner decides; no change made here)\n")
m.append("Three defensible options, in the PRD's own spirit (\"targets are provisional until the thin "
         "slice calibrates them\"):\n")
m.append(f"1. **Keep 40% but measure against the attainable base.** Redefine the coverage denominator "
         f"as attainable niches (~{len(attain)}), not all present niches. Then the target asks \"of the "
         f"niches a free path exists for, how many have we verified\" — a truer feasibility question. "
         f"Requires R14 recipes to be probe-verified and the native L2/L5 harvest to run.")
m.append(f"2. **Keep 40% of all present niches, unchanged**, and treat the gap as a harvest-completeness "
         f"signal: the {len(free_tool)} `free_tool` niches need L2-native + GN-pack/L5 sources, the "
         f"{len(free_recipe)} `free_recipe` niches need R14 recipes machine-checked. Coverage should "
         f"climb toward ~{pct(attain)} as those land — re-evaluate then.")
m.append(f"3. **Engine-core weighting.** Weight the target toward the four engine-core categories "
         f"(Terrain, Vegetation, Simulation-adjacent, Nature/FX) and de-weight exotic niches "
         f"(karst, coral_atoll, gas_giant) the engine may never call. Needs a core/weight pass.\n")
m.append("**Recommendation:** option 1 or 2 (they converge) — the evidence says the ecosystem is richer "
         "than 11.9% implies; the honest next step is to make the metric measure the attainable base and "
         "then complete the harvest (native probe + recipes + GN-pack sources), NOT to lower the bar by "
         "fiat. The decision is the owner's, as D-003.\n")
m.append("## Confidence & honesty notes\n")
lowconf = [r["id"] for r in rows if r["confidence"] == "low"]
m.append(f"- **{len(lowconf)}** verdicts are low-confidence (mostly `free_recipe` claims not yet "
         f"machine-checked): {', '.join('`'+x+'`' for x in lowconf)}. These are audit judgments, not "
         f"probe results — exactly why R14 splits `recipe_verified` from `recipe_unverified`.")
m.append(f"- `free_tool` verdicts ({len(free_tool)}) are add-ons found live but NOT yet vaulted/probed; "
         f"they become decision-grade only after acquisition + a passing probe (native path, R13).")
m.append("- Full per-niche data + evidence URLs: `reports/coverage-calibration-data.yaml`.")
OUT.write_text("\n".join(m) + "\n")
print(f"wrote {OUT}: n={n} attainable={len(attain)} ({pct(attain)}) not_attainable={len(not_attain)} "
      f"[verified={len(verified)} free_tool={len(free_tool)} free_recipe={len(free_recipe)}]")
