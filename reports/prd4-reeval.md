# PRD §4 Re-evaluation — after L1 + L2 (owner riders R1, R9)

**Date:** 2026-07-06 · **Scope:** SPEC §9 steps 1–3 (L1) + step 5 (L2 GitHub, spike-first, bounded).
**This is the L2-gate the owner asked for. The premise decision below is the owner's, not mine.**

---

## The numbers (deterministic, `coverage.py` over `corpus.db`)

| PRD §4 metric | L1 only | **L1 + L2** | Stop-line | Reading |
|---|---|---|---|---|
| **Coverage — Terrain+Veg, wave-1** | 7/59 = 11.9% | **7/59 = 11.9%** (4 full-pass + 3 partial-only) | `< 40%` | **below the line** |
| **Acquisition pass-rate** | 10/11 = 90.9% | **13/21 = 61.9%** | `< 30%` | **well above** |
| Whole-taxonomy wave-1 (informational) | 7/269 = 2.6% | **7/269 = 2.6%** | — | — |

L2 **upgraded `erosion_sim` to full-pass** (via `petak5__bp`, which drives headless) but added **no
new niche** — its survivors (`bp`, `varkenvarken__erosion`, `bsc-thesis`/ZagrebGIS) all map to niches
L1 already covered (erosion_sim, terrain_generator). Probe-recipe backlog: 4 partial-only niches
(`reports/probe-recipes.md`).

## What L2 actually showed (the honest findings)

1. **GitHub is markedly rottener than the curated platform.** L1 (extensions.blender.org) pass-rate
   was **91%**; the L2 GitHub sample was **~30%** (3 of 10 non-gated survived; 7 fail/legacy — dead
   deps, pip-install-at-enable that fails under `--network none`, 2.7x-era code, or GitHub-archive
   structure). This is the PRD's "ecosystem is structurally hard to inventory" thesis, quantified.
2. **The danger gate bites hard on GitHub code.** Of 15 acquired, **5 stayed blocked** (`sorcar`,
   `blender-python-nodes` [a code-executor by design], `witcher3-tools`, `trailprint3d`, `fastpbr`)
   on `eval`/`exec`/`os.system`/`ctypes`/`base64`/`subprocess`. Correct behavior — recorded, not
   verified. Prescan false-positive rate is tracked in `reports/prescan-findings.md`.
3. **Enumeration ≠ verification bottleneck.** The yield spike found tens of thousands of `bl_info`
   hits; the R11 enumerator recorded **27 active T+V candidates + 136 graveyard records** from 160
   repos. But verification is the wall — see the native-probe decision.

## Formal PRD §4 reading — and why it is NOT yet decision-grade

PRD §4: *"After the thin slice plus the first mass source-lane: if coverage for Terrain+Vegetation is
**<40%** … stop scaling the harvest. Convene a premise decision."*

- **Coverage 11.9% < 40% → the clause is literally crossed.**
- **BUT L2 here was NOT a mass harvest.** It was a **bounded 15-of-27 sample**, capped because
  large add-ons crash under amd64 emulation on this arm64 host (the native-probe decision, SPEC
  §12.2#5, is unresolved). And the 59-niche denominator is dominated by **exotic niches**
  (`karst_formation`, `coral_atoll_generator`, `gas_giant_shader`, `planetary_ring_generator`) with
  little-to-no free tooling anywhere, while common niches that DO have free add-ons (dune, river,
  waterfall, flower, grass, mushroom, moss…) were simply outside the bounded harvest, not absent.
- So **11.9% is a lower bound from a deliberately narrow harvest**, not the ecosystem's true T+V
  coverage. The pass-rate (61.9%) — the *premise* metric — remains healthy.

## Recommendation — this IS the premise decision the PRD designed the gate for

Do **not** auto-proceed to steps 6–8 (R9). The evidence now justifies the cheap, owner-level
premise decision the PRD calls for. Concretely, the owner's choices (a future D-002):

1. **Approve the native amd64 probe path** (cloud/CI runner) so the FULL L2 long tail can be
   verified — the current coverage is not decision-grade until L2 is actually mass-harvested. This
   is the highest-information next step and the cleanest way to make the <40% line meaningful.
2. **Recalibrate the 40% target** (PRD §3 says targets are "provisional until the thin slice
   calibrates them"). The thin slice now suggests 40% of these specific 59 wave-1 niches from free
   tooling may be structurally unreachable; a niche-weighted or engine-core-only target may be truer.
3. **Only if both above are declined:** convene the paid-add-on-budget vs. build-from-scratch
   premise decision, cheaply, before sinking months into L3–L5 crawling.

My read: the premise is **not** falsified — the tooling that exists works (61.9% pass-rate) — but
the coverage number is not yet trustworthy enough to kill or greenlight on. **Recommend option 1**
(native-probe path) to make the L2 coverage real, then re-evaluate.

## Scope discipline (R9)

Steps 6–8 (L3/L4 link-routers, L5 marketplace, full multi-category coverage) are **untouched**.
BlenderKit (R10) is a dated SPEC §12.2 backlog note only — no build. The decision to proceed is the
owner's, recorded as the next `DECISIONS.md` entry.
