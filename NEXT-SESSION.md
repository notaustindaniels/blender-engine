# NEXT-SESSION.md — full-taxonomy harvest campaign (D-008 R46–R55)

**One-paragraph status (2026-07-09):** Navigation layer complete + tagged (`snapshot-nav-v1`). Waves 1
(L1 full catalog, 904) and 2 (L2 full sweep, 412 new across 26 categories) are PROBED + INGESTED in
native CI and tagged (`snapshot-wave2`): whole-taxonomy coverage **7.0% → 9.1%, 9 categories** (full_pass
+ recipe_verified), pass-rate tripwire clear both waves (64.4%/52.9% of-all), golden eval **hit@5 = 1.0**.
An L6 BlenderKit material batch (uncovered Materials-category niches) is probing locally now. Remaining
automatable: finish L6 (materials + node-groups), L5-pending resolution pass (→ OWNER-QUEUE checkout
batch). Owner-gated: BlenderKit key in CI for the full 773 L6 sweep; L5/Route B checkouts; prescan
clearances. Guardrails unchanged throughout.

## ⚑ EFFICIENT-PATH BOTTLENECK (surface to owner): the full L6 sweep needs the BlenderKit key in CI
Local emulated shader-probing does **~1–2 materials per 9 min** — the L6 free-tier is **600 materials +
173 node-groups**, so a local sweep is ~30 h (impractical). The efficient path is a **native-CI L6 wave**
(fast, like L1/L2) which needs `BLENDERKIT_API_KEY` as a GitHub Actions **secret** — an owner-gated
credential (R33). READY-TO-BUILD once the secret exists: an `l6-wave.yml` sharding `candidates/L6.jsonl`,
each shard running a bk-aware acquire (scene_uuid+UA) → shader-probe (materials) / gate (node-groups) →
manifests artifact, then `wave_ingest`. Until then, local material batches continue slowly (7 done).

## Wave chain (supervisor state)
| wave | scope | candidates | status |
|---|---|---|---|
| 0 | thin slice (T+V, 11 cats) | 57 acquired | DONE — gate-v2 40.4%, nav layer tagged |
| **1** | **L1 full catalog (all 26 cats)** | **904** | **DONE — 612 working (137 pass + 475 partial), tripwire clear (64.4% of-all); 159 prescan-flagged (R6); 36 niche-mapped; whole-tax 7.0%→8.2%, 6 cats** |
| 2 | L2 full per-category signature sweep (26 cats) | 29 + ceiling | queued (l2_github.py ready) |
| 3 | L6 BlenderKit full free-tier sweep | 773 enum | queued (candidates/L6.jsonl ready; needs bk download+probe wave) |
| 4 | Route B + L5 pending resolution | 84 pending | queued (human-gated → OWNER-QUEUE) |

**Wave 1 notes:** enrich recall is CONSERVATIVE (36/612 working add-ons niche-mapped) — most catalog
add-ons are UI/utility/exporter tools, correctly unmatched, BUT some real generators miss (Archimesh→
building_generator, ClothDrop→cloth) because taxonomy niche aliases don't cover common add-on vocabulary
(room/window/wall/cloth). NEXT: a synonym map (`inputs/enrich-synonyms.yaml`, doesn't touch the owner's
taxonomy) to lift recall, then re-run enrich (deterministic, cheap). 159 prescan needs_review/quarantine
accumulate for a human-review batch (R6). Fixed this wave: reviewed-enrich clobbering (CI re-probe
overwrote enrichments → wave_ingest now re-runs enrich_thinslice first); R26 license backfill from
candidate metadata (ephemeral CI vault).

## Method (survives session death)
Waves run in CI (`wave-probe.yml`, 8 shards of ~119 each, `normalized_full.jsonl`). Each shard:
re-acquire (hash-verified) → prescan → native sandbox gate → manifests artifact. Supervisor merges
artifacts → enrich → mint_cards → kb_build → coverage/gap reports → next wave. Between polls: card QA,
recipe drive, gap analysis, per-category coverage tables.

## Ingest procedure (per wave, after CI completes)
1. `gh run download <id>` the 8 `wave-manifests-shard-*` artifacts → merge into `manifests/`.
2. `enrich_thinslice.py` (or enrich at scale) → `mint_cards.py` → `build_index.py` → `kb_build.py` + embed.
3. `coverage.py` per-category + gap reports (R47). Check the <30%-of-all pass-rate tripwire (R19).
4. Run golden eval; grow the golden set; tag a snapshot if green (R55).
5. Update this file + the progress feed.

## ⚠ Tripwire-at-scale consideration (Wave 1 gate — decide honestly, do NOT recalibrate by fiat)
The R19 tripwire (<30% of-all pass → pause+report) was calibrated for the TARGETED T+V harvest, where
acquisitions were expected to be procedural generators. At FULL-CATALOG scale (R46), we acquire the
whole catalog incl. UI/exporter/rigging add-ons that were never meant to pass a generation probe — so
"of-all pass-rate" will be low by construction (wrong denominator), NOT a premise failure. Per R17 I
must NOT recalibrate the tripwire by fiat after a miss. If it fires on Wave 1: PAUSE, compute both the
naive of-all rate AND the procedural-subset rate (procedural:true), and REPORT to the owner for a
D-entry disposing of it (confirm the procedural-subset denominator, or treat as a real signal). Pausing
is the correct behavior, not a failure.

## Ingest tooling built (ready for Wave 1 completion)
`enrich_scale.py` (keyword-heuristic niche mapping, labeled, non-clobbering) · `mint_cards.py` ·
`build_index.py` · `kb_build.py` + embed · `gap_report.py` (R47 per-category) · `eval_golden.py` (R55).

## Guardrail reminders (never loosen for throughput)
Prescan human gate (R6) — NEVER_ALLOW exec/network patterns quarantine, never cleared for throughput.
Awaiting-owner is a valid terminal state. Tripwire (<30% of-all pass) → pause + report (see ⚠ above).
Auth/ToS wall → report plainly (R2), never work around. Single-writer lock held. Secrets env-only.
