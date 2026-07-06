# PRD §4 Re-evaluation #2 — decision-grade (native amd64) + D-003 request (D-002 R16)

**Date:** 2026-07-06 · **Scope:** L1 + full L2 (all 27 candidates) verified **natively on amd64**
(GitHub Actions run `28825791382`, no emulation), version-aware, prescan-gated. Golden set re-passed
under native (bar b holds). **This is the decision-grade re-evaluation D-002 called for. The premise
decision below (D-003) is the owner's.**

---

## The numbers (native, deterministic — `coverage.py` over `corpus.db`)

| PRD §4 metric | emulated (bounded 15) | **native (all 27)** | stop-line | reading |
|---|---|---|---|---|
| **Coverage — Terrain+Veg, wave-1** | 7/59 = 11.9% | **8/59 = 13.6%** (5 full-pass + 3 partial + 0 recipe✓) | `< 40%` | below the line |
| **Pass-rate — of-probed** | 13/22 = 59.1% | **15/27 = 55.6%** | `< 30%` | well above |
| **Pass-rate — of-all-acquisitions** | 13/26 = 50.0% | **15/37 = 40.5%** | `< 30%` | above (R16: reported both ways) |
| Whole-taxonomy wave-1 (info) | 7/269 = 2.6% | **8/269 = 3.0%** | — | — |
| Recipe claims shown, NOT counted | 5 | **5** (`recipe_unverified`) | — | R14/rider-4: 0 verified → 0 gate movement |

Covered wave-1 niches (8): `terrain_generator` (now **full-pass** via beneking102), `heightmap_stack_tools`,
`erosion_sim` (petak5/bp now **full-pass on all 3 versions**), `snow_accumulation`, `alien_biome_generator`
(**new**, via ra100/planet-gen), `tree_generator`, `space_colonization_growth`, `ivy_generator`.

## What the native run changed (decision-grade findings)

1. **The native path worked — no emulation masking.** All 27 L2 candidates were acquired and probed
   natively (vs the bounded 15 under emulation). Golden set re-passed natively → the instrument is sound.
2. **Two new survivors the emulated sample never reached:** `beneking102__bene-proggen-maps`
   ("procedural city, terrain & dungeon", `generate_city`) → **full pass** 4.2/4.5, upgrading
   `terrain_generator` to full-pass; and `ra100__planet-gen` (`create_planet`) → partial, covering the
   previously-empty `alien_biome_generator`. Net gate: **+1 niche, +1 full-pass.**
3. **`bagapie` quarantines even natively** (4.2/4.5) — so its failure was a **real crash**, not
   emulation. Honest correction to the earlier "likely a native pass" caveat. `zets__terrain-mixer`
   also crashes on 4.5 natively.
4. **The L2 tail is genuinely rotten.** Of 27 probed: 15 survive, 12 do not — 5 fail, 2 legacy, and
   **8 stay prescan-blocked** (dangerous APIs) including several new ones (`cradoux__project-r`,
   `openresearchtools__video-toolkit`, `dimateos__upc-miri-tfm-erosion`, `shifty81`, `yazington`).
   The of-all-acquisitions pass-rate (40.5%) is the honest ecosystem-health number and still clears 30%.
5. **Recipes remain claims (rider 4, honestly).** The 5 seeded recipes compose **dialog-gated**
   operators (A.N.T. `landscape_add`, scatter — `PASS_THROUGH` even natively), so no cheap probe-recipe
   succeeded this run. Zero `recipe_verified`; they do not move the gate. A recipe-probe mode (drive
   the newly full-pass generative operators, or invoke via `EXEC_DEFAULT` with explicit params) is the
   clear next increment — see D-003 option 1.

## Formal PRD §4 reading

- **Coverage 13.6% < 40% — the clause is crossed**, on decision-grade data this time (full native L2).
- **BUT the R15 calibration memo (evidence-backed, now URL-sourced) shows 54/59 = 92% of these niches
  have SOME free path** — the gap is not ecosystem poverty, it is that (a) most free tooling is GN-packs
  / Gumroad-\$0 / recipes that L1+L2-GitHub don't reach, and (b) recipe coverage is built but unverified.
- **The premise metric (pass-rate) is healthy** — 55.6% of-probed / 40.5% of-all, both well above the
  30% kill-line. The tooling that exists works; the ecosystem is not "too rotten to build on."

**So the premise is not falsified.** The coverage number is now decision-grade *for L1+L2-GitHub*, but
that is not the whole free ecosystem, and the metric still counts only probe-verified dedicated add-ons.

---

## D-003 decision request (owner decides; nothing changed here)

Per D-002 R16, the options — with the R15 evidence attached (`reports/coverage-calibration.md`,
`reports/coverage-calibration-data.yaml`, now URL-sourced on every load-bearing verdict):

1. **Build recipe-verification + measure against the attainable base (recommended).** Implement the
   recipe-probe (compose vaulted operators / built-ins in the sandbox), machine-check the 5 seeded
   recipes + expand them, and redefine the coverage denominator as the **~54 attainable** niches
   (R15). This makes the 40% line answer the real feasibility question ("of niches a free path exists
   for, how many are verified") and is the highest-information next step. Recipes only move the gate
   once `recipe_verified` (R14). No new lane needed yet.
2. **Harvest the sources L1+L2-GitHub miss:** GN-pack / marketplace-\$0 lanes (L5) + BlenderKit backlog
   (L6, R10) — where the `free_tool` niches (fern, grass, flower, coral-adjacent, planet packs) actually
   live. This resumes scaling (steps 6–8) and needs a D-003 GO to unfreeze the stop-line (R17).
3. **Convene paid-vs-build** (the PRD's original fork) — only if 1 and 2 are declined. The kill-condition
   assumes source exhaustion, which we have **not** reached (L3/L4/L5/L6 untouched; recipes unbuilt).

**Recommendation: option 1, then option 2.** Verify recipes + fix the metric first (cheap, no ToS risk,
makes the number trustworthy); then open the GN-pack/marketplace lanes where the missing free tools live.
Do **not** kill on 13.6% — it measures a deliberately narrow slice of a 92%-attainable space.

## Scope discipline (R17)

Steps 6–8 (L3/L4 link-routers, L5 marketplace, L6 BlenderKit, full multi-category coverage) remain
**frozen**. The crossed stop-line stays paused until this D-003 request is answered with a DECISIONS.md
entry. Nothing past the gate resumes on agent initiative.
