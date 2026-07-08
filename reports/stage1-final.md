# Stage 1 — Final Report (D-007 R44) · CLOSED 2026-07-08

Stage 1 asked one question: **can a trusted corpus of *real*, free, procedural Blender tooling be
acquired and machine-verified — enough to build the engine on?** The answer, verified and signed:
**yes.** This report closes Stage 1.

## The verdict
- **Premise CONFIRMED (D-006 R36, independently re-reviewed R35 + R41):** the engine is buildable on
  free tooling. Acquisition pass-rate **63.2% of-probed / 50.0% of-all** — both far above the 30%
  kill-line, never tripped at any lane gate.
- **Execution milestone met, zero spend:** gate v2 **23/57 = 40.4%** on the two probe categories
  (Terrain + Vegetation, wave-1) = `(full_pass + recipe_verified) / attainable`, 12 full_pass + 11
  recipe_verified. Reached without a single purchase.
- **Zero fabrication:** every one of 58 vault entries traces to a live source URL + a matching SHA-256;
  three independent adversarial reviews re-downloaded and re-hashed random samples — no mismatch.

## Gate-v2 progression (every step machine-verified)
9.3% (D-003 ruler set) → 11.9% (L1) → 13.6% (native L2) → 29.8% (D-005 asset-fed recipe drive) →
31.6% (fern) → **40.4%** (L6 BlenderKit procedural shader materials). The ruler was tightened once
(v2, stricter than v1) and the threshold never moved — the number rose to meet it.

## Whole-taxonomy coverage (one-time, informational — the gate was always a T+V proxy)
The corpus harvested the two probe categories deeply; the full 328-niche taxonomy is Stage-2's map.
- **Wave-1: 27/269 = 10.0%** — concentrated in the two probed categories: **Terrain 12/36**,
  **Vegetation 15/23**. The other 24 categories (cities, buildings, characters, hard-surface, materials,
  simulation, all 8 animation tiers, and the wave-2 emergent/diegetic tiers) are **0%, untouched** —
  they were out of Stage-1 scope by design.
- **Wave-2: 1/59 = 1.7%** (`biome_scatter_system`). The emergent_formation / diegetic_dataviz tiers —
  the engine's actual heart — are unharvested; Stage 2 plans and harvests against them.
- **Read for Stage-2:** the *method* is proven on T+V; extending to the other 24 categories is
  execution, not research. The 2 genuinely-unattainable niches (`karst_formation`,
  `coral_atoll_generator`) are `reports/stage2-backlog.md` build-from-scratch, no purchase.

## What was built (the harness, all lanes to exhaustion)
- **Lanes:** L1 (extensions.blender.org API), L2 (GitHub + native amd64 probe via GitHub Actions, $0),
  L3 (BlenderArtists Discourse link-router), L4 (BlenderNation RSS), **L6 (BlenderKit API, HYBRID:
  materials/node-groups → Gate, models → A-lane)**, A1 (Sketchfab CC Download API). Dropped with
  recorded findings: L5 automated scraping (Gumroad §14), A2 ArtStation, A3 Fab (no automatable CC path).
- **The Gate:** digest+SHA-pinned Blender 3.6/4.2/4.5 sandbox (`--network none`, read-only, non-root,
  cap-drop), five probe variants — add-on, GN-pack, asset (import+render), recipe (composition), shader
  (pixel-delta). Golden set 100% correct across all three versions. Danger prescan + human clearance
  gate (never loosened). Version-aware skipping, timeout-retry, native-vs-emulation reconciliation.
- **Honesty machinery:** gate-v2 ruler with tier split (full_pass vs partial vs recipe_verified vs
  recipe_unverified), attainable-denominator calibration (link-backed market audit), verb×medium grid,
  probe-recipe backlog, per-asset license capture, `procedural`-vs-image-texture verification.

## The decision arc (DECISIONS.md, owner-signed)
D-001 GO to L2 · D-002 repair the instrument · D-003 ruler v2 + greenlight 6–8 · D-004 asset lanes ·
D-005 walk-away autonomy · D-006 review-gated premise signature (CONFIRMED) · D-007 close-out. Four
independent fresh-context adversarial reviews (Fable) gated the milestones; all passed. One parallel-
work collision was found, repaired, and prevented from recurring (SINGLE-WRITER rule).

## Stage 1 is CLOSED
The corpus is frozen as a **read-only dependency**. Consumption interface: `HANDOFF.md` (schemas,
quality tiers the resolver must prefer, verb×medium grid, and the **load-bearing license obligations**
every render inherits — CC-BY attribution, BlenderKit rendered-video-only/no-3D-export, RF
incorporation-only). Freshness: the 90-day re-verification workflow is armed (`.github/workflows/
reverify-90d.yml`). This repo is not developed further except via `verify-batch` re-verification.

## Stage 2 opens by its own PRD + SPEC (R45)
Author Stage 2 fresh — the create-prd / create-spec discipline that opened Stage 1 — against
`HANDOFF.md`. Thin slice: the **fish-form-an-equation** vertical (emergent_formation × diegetic_dataviz)
from the original engine plan. Owner + advisor convene on the Stage-2 PRD as the next act.

**Stage 1: done — verified, signed, and handed off.**
