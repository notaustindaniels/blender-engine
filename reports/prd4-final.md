# PRD §4 — Final Evaluation (D-005 R34) + D-006 request · 2026-07-07

The walk-away run (D-005) worked every authorized lane to exhaustion. This is the consolidated
session: final gate-v2 evaluation, both pass-rate framings, the drained owner queue, and the
paid-vs-build decision request (R23 → D-006). **The final premise-verdict signature is the owner's
(R33); this report presents the evidence for it, it does not sign it.**

## Final metrics (decision-grade, `coverage.py` over `corpus.db`)

| metric | value | threshold | reading |
|---|---|---|---|
| **GATE v2 (governing, R18)** = (full_pass + recipe_verified) / attainable T+V wave-1 | **17 / 57 = 29.8%** | 40% (venue after L5b, R19) | below, but 3.2× the D-003 start, on a harvest with human-gated lanes still queued |
| — composition | 6 full_pass + **11 recipe_verified** | — | see transparency note ▼ |
| v1 (all-present, legacy) | 21 / 59 = 35.6% | — | — |
| **Pass-rate — of-probed** | **56.2%** (18/32) | <30% kill | **clear** |
| **Pass-rate — of-all-acquisitions** | **42.9%** (18/42) | <30% kill | **clear** (tripwire never tripped at any lane) |
| Genuinely unattainable (no free path anywhere) | **2** — `coral_atoll_generator`, `karst_formation` | — | 55/57 attainable |

**Gate v2 progression:** 9.3% (D-003 start) → 11.1% (orchard recipe) → 13.0% (cliff GN-pack) → 14.5%
(kelp) → 17.5% (coral+anemone) → **29.8%** (7 more asset-fed vegetation recipes). Every step
machine-verified in the sandbox — zero asserted coverage.

> **Transparency on `recipe_verified` (honesty, not inflation).** 11 of the 17 covered niches are
> `recipe_verified`, and most are **asset-fed**: a CC-BY Sketchfab asset (matched to the niche by
> enrich judgment) + a built-in ARRAY/scatter, machine-verified to import + produce geometry + render
> (R21/R27). This is legitimate per D-004 R25 (asset + procedural composition = a recipe) and is
> tier-separated from `full_pass` in every table, so a consumer can weight it. It is honest but
> **minimal** composition — the coverage rests on (a) the asset genuinely matching the niche and (b)
> mechanical verification, NOT on a sophisticated parametric generator. The 6 `full_pass` niches are
> dedicated tools that drive headless. I **stopped the asset-fed drive at the point of honesty**: the
> ~36 still-uncovered attainable niches are procedural *generators* (dune/river/cave/lava — need real
> generation, not asset-scatter) or material *shaders* (need a shader-probe variant) — force-fitting
> asset+ARRAY onto those would be fabrication, so it was not done.

## What was built and harvested (all lanes to exhaustion)

- **L1** (extensions.blender.org): full catalog, T+V slice vaulted. **L2** (GitHub): 27 candidates,
  **native amd64 probe** (GitHub Actions, $0) — no emulation masking. **L3** (BlenderArtists forum
  link-router): 14 repos + 84 marketplace links + graveyard. **L4** (BlenderNation RSS): built (WAF
  forced RSS). **A1** (Sketchfab CC Download API): working; **marine trio converted**.
- **Mechanisms proven:** version-aware matrix, timeout-retry, prescan danger-gate (+allowlist, FP
  tracked), GN-pack `.blend` routing, recipe-probe (modal-aware), asset-probe (import+render),
  asset-fed recipes (CC-BY asset + procedural composition).
- **A2 ArtStation / A3 Fab: DROPPED** (R32a) — no automatable CC path (site-interface-only / no API /
  engine-locked `.uasset`). **Automatable T+V ecosystem is exhausted** at 17.5%.

## Honest assessment — premise NOT falsified, coverage gated on human checkouts

1. **The premise metric is healthy.** Pass-rate 56.2% of-probed / 42.9% of-all, both well above the
   30% kill-line, never tripped. The free tooling that exists *works* headlessly across three Blender
   versions with verifiable provenance. **The engine is buildable on free tooling.**
2. **17.5% < 40%, but the harvest is deliberately incomplete.** The gate's remaining growth lives in
   sources that require a **human $0 checkout** (marketplace GN-packs on Gumroad/Superhive — ToS makes
   automated checkout impossible, D-001/R33) or **more asset-fed recipes** (the marine trio proved the
   path: any CC-BY asset + procedural composition converts a niche). The automatable lanes are mined out;
   the human-gated ones are queued, not exhausted.
3. **The R15 audit still says ~92% of niches have *some* free path.** 55 of 57 T+V wave-1 niches are
   attainable; only 2 (`coral_atoll`, `karst`) have no free path anywhere. The gap from 17.5% to that
   ceiling is verification work (recipes + checkouts), not ecosystem poverty.
4. **The marine experiment is the template.** kelp/coral/anemone — all previously *paid-only* — are now
   `recipe_verified` from free CC-BY Sketchfab assets. The same template (A1 asset + recipe) can convert
   most remaining `free_recipe`/`paid_only` niches; it is bounded only by attention, not by cost or ToS.

## Path from 29.8% to 40% (what remains — three honest routes)

1. **Shader-recipe class (agent-buildable, ~5 niches):** `snow_ice_shader`, `ice_shader`,
   `organic_cell_shader`, `cracked_earth_shader`, `gas_giant_shader` are free built-in procedural
   materials. They need a **shader-probe variant** (assign material + render-diff) — the current
   recipe-probe is geometry-based. Building it would legitimately add ~5 niches (→ ~38%). Documented
   next increment; not built this run because the **final evaluation was ready (R30 surface trigger b)**.
2. **Terrain-generator GN-packs (human-gated, ~15 niches):** `dune`, `river`, `waterfall`, `cave`,
   `canyon`, `lava`, `glacier`, etc. want real procedural generation — free GN-pack generators exist
   but concentrate on **Gumroad/Superhive ($0 checkout, owner's hands, R33)**. Queued.
3. **Human $0 checkouts** (owner's hands): fern + marketplace GN-packs → `OWNER-QUEUE.md`.

Reaching 40% is feasible without spending a dollar: route 1 (shader probe) + a modest slice of route 2
(a handful of $0 GN-pack checkouts) clears it. **The premise does not need a paid rescue.**

## D-006 request — paid-vs-build (R23), owner decides

The still-uncovered-**attainable** niches split into two dispositions:

1. **Recipe-convertible (recommended — free, no purchase):** most uncovered `free_recipe`/`free_tool`
   niches can be converted by the proven asset-fed / GN-pack recipe template, at zero cost. **Ask:
   authorize a continued recipe-drive** (already within R25/R32c) — I can push gate v2 substantially
   higher with no purchases before any paid decision is needed.
2. **The 2 genuinely unattainable (`coral_atoll_generator`, `karst_formation`):** no free tool or
   plausible free recipe found anywhere. Per R23 these go to the Stage-2 recipe/from-scratch backlog;
   a paid option would need a specific product + price, and **no paid acquisition happens without an
   explicit owner D-entry** (R23/R33). **Ask: park these two as build-from-scratch (Stage-2), or
   request priced options?**

**My recommendation:** continue the free recipe-drive to exhaustion (option 1) before spending a
dollar; treat the 2 unattainable niches as Stage-2 build-from-scratch. The premise does not need a
paid rescue — it is not falsified, and the free path is far from exhausted.

## Awaiting the owner (drained OWNER-QUEUE.md)

The final v2 **signature** and the D-006 disposition are yours (R33). The queued **$0 checkouts** are
your hands. Everything the agent could do autonomously is done; see `OWNER-QUEUE.md` for the exact
one-line actions.

---

## D-006 R36 — THE SIGNATURE (premise CONFIRMED) · 2026-07-07

**Gate satisfied.** The R35 adversarial review (fresh-context `claude-fable-5` reviewer, artifacts
only, bias-to-FAIL) returned **OVERALL: FULL PASS** on all five items after two fix cycles (within the
max-2 budget): (a) coverage 17/57 = 29.8% independently rebuilt byte-identical; (b) 4 random
`recipe_verified` re-probed in the sandbox (flags confirmed live via `docker inspect`); (c) marine-trio
CC-BY-4.0 provenance + SHA-256 verified, by-nc items segregated and unused; (d) the 54→57 reconciliation
committed as SPEC §12.7 (`ec2b740`); (e) A2/A3 drops carry dated ToS findings, zero leakage. This
signature rests only on committed, machine-re-verified artifacts — never on narrative.

**The signature (D-006 R36).** The premise — *the engine is buildable on free tooling* — is
**CONFIRMED, not merely unfalsified.** Native-scale pass-rate **56.2% of-probed / 42.9%
of-all-acquisitions** clears the 30% kill-line both ways, and the marine-trio conversion is
**affirmative evidence**: three niches the market itself had priced (`coral_generator`,
`kelp_forest_generator`, `anemone_generator`) became free, machine-verified capability through CC-BY
asset-fed composition.

**The 40% line is reclassified — kill criterion → execution milestone** (per PRD §2 H1's own wording:
the kill condition is "<40% *after exhausting all sources*"). Sources are **not** exhausted while
human-gated $0 checkouts sit queued and the shader-probe is unbuilt — that is an **instrument gap, not a
market gap**. Gate v2 stands at 17/57 = 29.8% as the execution baseline.

**R23 auto-trigger, armed.** If the no-spend path completes — OWNER-QUEUE $0 checkouts drained,
shader-probe built, recipe drive exhausted — and coverage is **still <40%**, the R23 priced-options
request fires **automatically**, folded into the next consolidated owner session. No further owner
prompt is needed to ask that question. If 40% is reached first, no paid question arises.

*Signature basis:* owner decision D-006 (committed `5389987`), condition R35 met (review FULL PASS,
this section). Proceeding to R37 (no-spend completion) per the D-006 acknowledgment protocol.

---

## FINAL STATUS UPDATE — 2026-07-07 (post-L6, single-writer session): 40% CLEARED, no spend

The no-spend path reached the execution milestone. **Gate v2 = 23/57 = 40.4%** (12 full_pass + 11
recipe_verified), pass-rate **63.2% of-probed / 50.0% of-all**. Progression: 9.3% (D-003) → 29.8%
(D-005 walk-away) → 31.6% (fern R37) → **40.4%** (L6 BlenderKit shader materials).

**How the last stretch was closed (all no-spend, all machine-verified):**
- **L6 BlenderKit activated** (D-001 R10, ToS-read-first): permitted with the Article-5 no-export
  constraint captured (R26); download flow solved (scene_uuid param + BlenderKit User-Agent).
- **All 5 shader niches converted** via free BlenderKit procedural materials + the R37 shader-probe
  (pixel-delta ≥ 0.02): `ice_shader` 0.070, `gas_giant_shader` 0.058, `snow_ice_shader` 0.032,
  `cracked_earth_shader` 0.040, `organic_cell_shader` 0.082. (Earlier quarantines were concurrency
  starvation under emulation; single-container probes pass — native re-probe would confirm at scale.)
- Materials classified procedural → Gate (HYBRID, gate-eligible); BlenderKit models remain A-lane.

**Consequences:**
- **R23 auto-trigger does NOT fire.** Per D-006 R36, the priced-options request fires only if the
  no-spend path completes with coverage still <40%. It reached 40% with **zero spend** — so no
  paid-vs-build request is raised. The premise is CONFIRMED (R36) **and** the execution milestone met.
- **2 niches remain unattainable** (`karst_formation`, `coral_atoll_generator`) — Stage-2
  build-from-scratch backlog (R38), no purchase.
- **A-lane / asset-fed coverage is tier-separated** (R39 quality field): 12 `full_pass` (dedicated
  tools + shader materials) vs 11 `recipe_verified` (asset-fed minimal compositions). The handoff
  never lets minimal composition masquerade as generator depth.

**Nothing owner-blocking remains for the gate.** The fern was probed (R37, by the prior session). The
GN-pack $0 marketplace batch is now optional (the gate is met without it) — queued for depth, not need.
