# Coverage Calibration Memo — Terrain+Vegetation wave-1 (D-002 R15)

**Date:** 2026-07-06 · **Method:** cached extensions.blender.org catalog mine + live web research (2026-07-06). Per-niche market-existence audit of all **59** wave-1 niches. Confidence-graded; this is a PROPOSAL for the D-003 decision — **no target is changed here** (recalibration-by-fiat after a miss is forbidden, R15).

## The finding: the 40% target and our metric measure different things

Our **decision coverage** counts a niche only when a **dedicated free add-on is vaulted AND survives our headless probe** — currently **7/59 = 11.9%**. But a market-existence audit of the same 59 niches shows free tooling or a plausible free recipe exists for far more of them; they simply live on GitHub / free GN packs / Gumroad-\$0 / built-ins — sources L1 (the tiny official platform) doesn't reach and that the emulation-capped L2 sample barely touched.

## Attainable-base distribution (evidence-based)

| verdict | niches | share | meaning |
|---|---:|---:|---|
| `verified_free` | 8 | 14% | already probed free tool (decision-grade) |
| `free_tool` | 10 | 17% | free dedicated add-on exists, not yet vaulted/probed |
| `free_recipe` | 36 | 61% | no dedicated tool, but a plausible free recipe (built-ins/GN/free packs) |
| `paid_only` | 3 | 5% | tools exist but only paid (excluded by the free constraint) |
| `none` | 2 | 3% | no known free tool AND no plausible free recipe |
| **ATTAINABLE (free tool or recipe)** | **54** | **92%** | verified_free + free_tool + free_recipe |
| **NOT attainable (paid/none)** | **5** | **8%** | the true free-ecosystem ceiling |

**Read:** ~**92%** of the 59 wave-1 Terrain+Veg niches have SOME free path; only **8%** (5 niches) appear genuinely unreachable for free (marine flora skews paid: coral/kelp/anemone; plus exotic karst/atoll/meander). So a 40% target is **not** obviously unreachable — but our *current metric* (dedicated-add-on-only, probe-verified) undercounts the attainable base by design.

## Not-attainable niches (the real ceiling)

- `karst_formation` (none, medium) — searched karst/sinkhole/sea-stack Blender addon: no free tool, no obvious recipe; only generic boolean/erosion tutorials
- `coral_atoll_generator` (none, medium) — no free ring-atoll generator found; coral/reef tools are paid (Superhive) or manual
- `kelp_forest_generator` (paid_only, medium) — 3DT Coral Reef Gen / Procedural Coral include kelp — paid (Superhive/Fab); free = tutorials only
- `coral_generator` (paid_only, high) — Procedural Coral, 3DT Coral Reef Generator — all paid (Superhive/Fab/Cubebrush)
- `anemone_generator` (paid_only, medium) — bundled in paid Procedural Coral (animated anemones); no standalone free anemone tool

## Proposal for D-003 (owner decides; no change made here)

Three defensible options, in the PRD's own spirit ("targets are provisional until the thin slice calibrates them"):

1. **Keep 40% but measure against the attainable base.** Redefine the coverage denominator as attainable niches (~54), not all present niches. Then the target asks "of the niches a free path exists for, how many have we verified" — a truer feasibility question. Requires R14 recipes to be probe-verified and the native L2/L5 harvest to run.
2. **Keep 40% of all present niches, unchanged**, and treat the gap as a harvest-completeness signal: the 10 `free_tool` niches need L2-native + GN-pack/L5 sources, the 36 `free_recipe` niches need R14 recipes machine-checked. Coverage should climb toward ~92% as those land — re-evaluate then.
3. **Engine-core weighting.** Weight the target toward the four engine-core categories (Terrain, Vegetation, Simulation-adjacent, Nature/FX) and de-weight exotic niches (karst, coral_atoll, gas_giant) the engine may never call. Needs a core/weight pass.

**Recommendation:** option 1 or 2 (they converge) — the evidence says the ecosystem is richer than 11.9% implies; the honest next step is to make the metric measure the attainable base and then complete the harvest (native probe + recipes + GN-pack sources), NOT to lower the bar by fiat. The decision is the owner's, as D-003.

## Confidence & honesty notes

- **13** verdicts are low-confidence (mostly `free_recipe` claims not yet machine-checked): `sediment_deposition`, `stalactite_generator`, `sand_sim`, `glacier_flow_generator`, `icicle_generator`, `volcanic_caldera_generator`, `fissure_generator`, `rice_terrace_generator`, `alien_biome_generator`, `meander_braid_tools`, `coastline_generator`, `succulent_generator`, `mushroom_generator`. These are audit judgments, not probe results — exactly why R14 splits `recipe_verified` from `recipe_unverified`.
- `free_tool` verdicts (10) are add-ons found live but NOT yet vaulted/probed; they become decision-grade only after acquisition + a passing probe (native path, R13).
- Full per-niche data + evidence URLs: `reports/coverage-calibration-data.yaml`.
