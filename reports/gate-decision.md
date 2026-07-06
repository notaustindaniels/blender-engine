# Stage-1 Decision Gate — L1 Thin Slice (mandatory gate after SPEC §9 step 3)

**Date:** 2026-07-05 · **Scope run:** SPEC §9 steps 1–3 (L1 extensions lane, Terrain + Vegetation).
**This is a recommendation. The go/no-go is the owner's, not the harness's.**

---

## The numbers (deterministic, from `corpus.db` via `coverage.py`)

| PRD §4 metric | Result | Stop-line | Triggered? |
|---|---|---|---|
| **Coverage — Terrain + Vegetation, wave-1** | **7 / 59 = 11.9%** | `< 40%` | see note ▼ |
| **Acquisition pass-rate** (survive verification on ≥1 of 3.6/4.2/4.5) | **10 / 11 = 90.9%** | `< 30%` | **No — 3× above the line** |

Covered wave-1 niches (7): `terrain_generator`, `heightmap_stack_tools`, `erosion_sim`,
`snow_accumulation` (Terrain 4/36) · `tree_generator`, `space_colonization_growth`, `ivy_generator`
(Vegetation 3/23). Wave-2: `biome_scatter_system` (1). Full matrix in `reports/coverage-report.md`.

▼ **The <40% coverage line is NOT yet in force.** PRD §4 evaluates it *"after the thin slice **plus
the first mass source-lane**"* (L1 **+ L2**). L1 is deliberately the *cleanest and smallest* lane —
the curated official extensions platform (998 add-ons total, ~11 relevant to the two probe
categories). 11.9% is the expected **floor from one narrow lane**, not a kill signal. L2 (GitHub
code-search over thousands of `bl_info`/`blender_manifest.toml` repos + the seed star-graph) is the
lane designed to supply the bulk of coverage.

---

## Reading the signal

**The decisive L1 result is the pass-rate, and it is strongly positive.** The PRD's dominant
*feasibility* risk was that heterogeneous free add-ons could not be machine-verified at scale, or
that the ecosystem is "too rotten to build on" (pass-rate < 30%). Instead **10 of 11 obtainable
free add-ons survived headless verification** across a real 3-version Blender matrix, with fully
verifiable provenance (every vault entry has a live URL + a SHA-256 that matched the platform's
declared hash — zero fabrication). The one non-survivor (`bagapie`) *quarantined* (timed out), it
did not fail — see caveats.

The whole loop ran end-to-end and produced trustworthy artifacts: enumerate → normalize → acquire
(+hash) → prescan (+human clearance) → verify (sandboxed, `--network none`) → enrich → index →
coverage. The Gate is calibrated (golden set 100% correct across all three Blender versions).

## Recommendation: **PROCEED to L2** (premise survives)

Nothing in the L1 slice trips a PRD §4 stop condition. The pipeline works, provenance is trustworthy,
and the ecosystem's survival rate is excellent. Build the L2 GitHub lane next (SPEC §9 step 5), then
re-evaluate the <40% coverage line on the L1+L2 union — that is the point at which the coverage
metric becomes decision-grade.

---

## Caveats & honest findings (things to weigh before proceeding)

1. **`bagapie` quarantined under emulation.** This host is arm64; Blender runs as `linux/amd64`
   under emulation, so a large GN toolkit can exceed the 120 s per-artifact cap. On native amd64 it
   would likely pass. **Action:** re-verify large add-ons natively, or raise the cap for them, before
   trusting quarantine counts at scale. (Does not change the recommendation — quarantine ≠ fail.)
2. **Prescan friction: 4/11 flagged `needs_review`.** All were cleared after *source-level*
   inspection (`reviews/prescan_clearances.yaml`); one (`modular-tree`) was a pure false positive
   (Blender node "socket" ≠ network socket). At L2 scale this human-review step is real throughput
   friction and the `socket`/`open-write` patterns likely need tightening. **Action:** measure the
   false-positive rate on the first L2 batch.
3. **Version reality (the 4.2 migration is real).** Every 4.2+ extension is `fail` on 3.6 (no
   extension system pre-4.2); several are min-4.4/4.5 (`pass` on 4.5 only). Coverage is a ≥1-version
   metric so this is fine, but Stage-2's minimum-Blender choice (PRD open question) materially
   affects how much tooling is admissible.
4. **Coverage denominators are wide by design.** The gate divides by all 59 *present* wave-1
   Terrain+Vegetation niches, many of which are exotic (`karst_formation`, `coral_atoll_generator`,
   `gas_giant_shader`). The PRD notes its targets are *provisional until the thin slice calibrates
   them* — expect to revisit the 40% figure once L2 yields land.

## What was NOT done (scope discipline)

SPEC §9 steps 4–8 are **untouched**: no dedup/idempotency hardening beyond what step 3 required
(idempotency IS demonstrated), no L2 GitHub harvest, no L3/L4 link-routers, no L5 marketplace
discovery, no full coverage report across all PRD §3 targets. Those begin only if the owner says go.

---

## Owner decision — 2026-07-06: **GO to L2** (recorded per owner rider 1)

The owner reviewed this gate and authorized proceeding to the L2 GitHub lane (SPEC §9 step 5),
spike-first (SPEC §10). **The PRD §4 <40% coverage line is formally evaluated after L2, on wave-1
Terrain+Vegetation.** For information, the two framings of the L1-only baseline:

| framing | L1 coverage | note |
|---|---|---|
| **Gate metric** — Terrain+Vegetation, wave-1 | **7 / 59 = 11.9%** | the number the <40% line is judged on |
| Whole-taxonomy, wave-1 (informational) | **7 / 269 = 2.6%** | all 12 static + 10 animation categories |

L2 concludes with an updated coverage report (full-pass vs partial split) and a formal PRD §4
re-evaluation on the L1+L2 union before any of steps 6–8 begin. Owner riders 4–8 (version-aware
matrix, timeout-retry state, prescan-throughput allowlist, honest pass/partial split, non-event
server restarts) are being implemented as part of this phase.
