# Consolidated Owner Session — 2026-07-07 (D-006 R34/R30 surface)

The R35 review gate passed and the premise is signed **CONFIRMED** (R36). This is the single
consolidated surface per R30: the state, the two no-spend routes to 40%, the checkout batch (owner's
hands), the wave-3 proposal, and the R23 auto-trigger status. Nothing here spent a dollar.

## 1. Where the gate stands

| metric | value | note |
|---|---|---|
| **Gate v2** | **18 / 57 = 31.6%** | up from 29.8% at signature — `fern_generator` verified full_pass (your $0 PWYW checkout) |
| Premise | **CONFIRMED (R36)** | pass-rate 56.2% of-probed / 44.2% of-all — clears the 30% kill-line both ways |
| Tripwire (R19) | 44.2% vs 30% | not tripped |
| Quality tiers (R39) | 7 full_generator · 1 composed_procedural · 10 asset_fed_minimal | asset-fed answered the premise; flagged so it never reads as generator depth in Stage-2 |

**40% needs 5 more verified niches (23/57).** Both routes below are no-spend.

## 2. Two no-spend routes to 40% (need 5)

**Route A — free shader niches (agent-doable, likely no checkout).** The shader-probe variant is
built and self-validated in-sandbox (R37a; `sandbox/probe_shader.py`, delta 0.137 ≥ 0.02 on the
self-test). Five uncovered **`free_recipe` shader** niches are now verifiable that the geometry/asset
probes read as empty: `cracked_earth_shader`, `gas_giant_shader`, `ice_shader`, `organic_cell_shader`,
`snow_ice_shader`. Acquiring free shader node-setups (GitHub / free GN packs) + probing them = a
path to **~40% with zero checkout**. **This is agent-doable on your go** — it is the natural next increment.

**Route B — $0 GN-pack checkout batch (your hands, R33).** Terrain GN generators among the 30
uncovered `free_recipe` niches — strongest candidates: `dune_generator`, `canyon_mesa_generator`,
`cave_network_generator`, `lava_field_generator`, `volcanic_caldera_generator`, `glacier_flow_generator`.
**Honest status:** these are grounded *targets* (R15 audit `free_recipe`); a batch-1-standard
resolution (final product URL + machine-confirmed $0 + captured license per R31) has **not** been run
for them yet — I did not fabricate URLs/prices. Say the word and I'll produce the resolution-passed
batch for one checkout session (Gumroad §14 keeps the checkout your hands).

## 3. Wave-3 proposal (R40 — you decide, never auto-added)

`tu2463__rock_generator_addon` (`mesh.primitive_rock_add`) **passes on 3.6/4.2/4.5** and matches the
existing **wave-2** niche `rock_boulder_generator` ("procedural individual rocks"). Off the wave-1 gate,
so it doesn't move gate-v2. **Ask:** approve the mapping (records real Stage-2 capability) or keep as a
wave-3 candidate? Default = no change until you rule. (`reports/taxonomy-proposals.md`)

## 4. R23 auto-trigger — armed, NOT fired

The priced-options request fires automatically **only if** the no-spend path completes (Route A + B
exhausted) with coverage still <40%. It is **31.6% with two clear no-spend routes open**, so no priced
question arises now. The two genuinely unattainable niches (`karst_formation`, `coral_atoll_generator`)
are parked as Stage-2 build-from-scratch (R38, `reports/stage2-backlog.md`) — no purchase.

## 5. What I need from you (one of)

1. **"Run Route A"** → I acquire + probe free shader niches toward 40%, no checkout. *(recommended)*
2. **"Prep the GN-pack batch"** → I produce the resolution-passed $0 checkout batch for your hands.
3. **Rule on the wave-3 rock mapping** (§3) — optional, anytime.

Everything else (review, signature, fern, shader-probe, backlog, quality tiers, wave-3 proposal) is
done and committed.
