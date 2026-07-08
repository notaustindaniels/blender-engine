# NEXT-SESSION.md — full-taxonomy harvest campaign (D-008 R46–R55)

**One-paragraph status (2026-07-08):** The navigation layer is complete and tagged (`snapshot-nav-v1`,
golden eval hit@5=1.0). The full-taxonomy harvest is now RUNNING as sharded CI waves. Wave 1 (L1 full
catalog — 904 extensions across all 26 categories, stripped of the T+V thin-slice filter) is being
dispatched to `wave-probe.yml` (8 parallel native-amd64 shards). The supervisor session dispatches →
polls → ingests manifests → mints cards → rebuilds the KB → dispatches the next wave. Guardrails
unchanged: prescan NEVER_ALLOW holds, sandbox `--network none`, single-writer, secrets never printed,
retrieval-proposes/registry-disposes, R11 (order-not-exclude).

## Wave chain (supervisor state)
| wave | scope | candidates | status |
|---|---|---|---|
| 0 | thin slice (T+V, 11 cats) | 57 acquired | DONE — gate-v2 40.4%, nav layer tagged |
| **1** | **L1 full catalog (all 26 cats)** | **904** | **DISPATCHING → wave-probe.yml (8 shards)** |
| 2 | L2 full per-category signature sweep | 29 + ceiling | queued |
| 3 | L6 BlenderKit full free-tier sweep | tbd | queued |
| 4 | Route B + L5 pending resolution | 84 pending | queued (human-gated checkouts → OWNER-QUEUE) |

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
