# DECISIONS.md — Append-Only Owner Decision Log

**Role:** the canonical record of owner decisions, with the same standing as KICKOFF.md.
Chat messages are ephemeral pointers to this file; this file is the memory. Entries are
append-only — corrections are new entries, never edits.

**Agent obligations:**
1. Re-read KICKOFF.md, SPEC §12, and this file at session start and after any context
   compaction, before acting. Encode that instruction in CLAUDE.md (see D-001 R2/R9).
2. A rider below counts as **received only when its durable encoding is committed**
   (code, workflow YAML, dated SPEC §12 amendment, or CLAUDE.md standing rule).
   Remembering it in context does not count — context is designed to be lost.
3. Precedence: KICKOFF.md and this file express owner intent; the SPEC encodes it.
   Conflicts get a dated SPEC §12 amendment, never silent reconciliation.

---

## D-001 · 2026-07-06 · Stage-1 decision gate: **GO to L2**

**Decision:** Proceed past the PRD §4 gate to the L2 (GitHub) lane.
**Basis:** acquisition pass-rate 10/11 = 90.9% vs. the <30% stop-line (the premise
metric, decisively cleared; independently recomputed by the owner's advisor from raw
manifests). Coverage 7/59 = 11.9% is the designed floor of the smallest lane; the <40%
line is formally evaluated after L2, per the PRD's own schedule.

### Binding riders

| # | Rider | Durable encoding target(s) |
|---|---|---|
| R1 | Record this owner decision (dated) in `reports/gate-decision.md`. The <40% line is evaluated after L2 on **wave-1 Terrain+Veg**; report the whole-taxonomy wave-1 number alongside for information. | one-time edit to `reports/gate-decision.md`; evaluation rule → dated SPEC §12 note |
| R2 | `GH_TOKEN` is in `.archon/.env`. Read from env only — never echo, log, or commit. Validate with a rate-limit call (`gh api rate_limit`) before anything else; report auth failure plainly (fallback: owner supplies a classic public_repo token). Never work around auth failures silently. | CLAUDE.md standing rule (token hygiene + no-silent-workaround); validation = one-time action with feed evidence |
| R3 | **Spike first** (SPEC §10): GitHub yield spike — candidates per signature query (`bl_info` / `blender_manifest.toml` / topics) under authenticated limits — with the yield table posted to the progress page **before** building the full L2 lane. | one-time action + feed evidence |
| R4 | **Version-aware matrix:** never probe versions the artifact declares impossible (extension-manifest artifacts skip 3.6; respect `blender_version_min` generally). Skipped cells recorded as `skipped_incompatible`, not `fail`. | code: `verify_matrix.py` / probe path; dated SPEC §12 amendment |
| R5 | **Timeout policy:** quarantine-by-timeout becomes a distinct state (`quarantine_timeout`) with one automatic retry at 2× timeout. Re-probe `bagapie` (both versions) and `terrain-mixer@4.5` under it. If the spike suggests L2 volume in the hundreds, **propose** a native amd64 probe path as an owner decision (future D-00x) — never self-approve infrastructure. | code: probe runner; dated SPEC §12 amendment; re-probes = one-time with feed evidence |
| R6 | **Prescan throughput:** the human gate stays exactly as-is. Make review cheap: a dated prescan-allowlist rules file (pattern + justification per entry), batched review via an approval node with per-batch findings report, false-positive rate tracked as a reported metric. | new `policies/prescan-allowlist.yaml` + workflow approval node; dated SPEC §12 amendment; CLAUDE.md standing rule ("the human gate never loosens") |
| R7 | **Honest coverage composition:** all coverage tables split full-pass vs. partial; partials accumulate a `probe_recipe` backlog (SPEC §12.2) rather than silently counting the same as passes. | code: `coverage.py` + report templates; dated SPEC §12 amendment |
| R8 | **Progress server:** restart it now; make restarts a non-event — `progress/serve.sh` (one command, prints URL), noted in the feed, and workflows check/relaunch the server at run start so the owner never has to. | code: `progress/serve.sh` + workflow preflight node |
| R9 | **Scope discipline:** steps 5–8 remain untouched. L2 ends with the updated coverage report and the formal PRD §4 re-evaluation before anything else starts. | CLAUDE.md standing rule |
| R10 | **BlenderKit = backlog lane, not now:** log as candidate L6 in a dated SPEC §12 note — public API with free-account key, likely richer in assets than tools, ToS on bulk download unverified. Spike its ToS + yield only after L2's gate evaluation. | dated SPEC §12 note only; **no build** |
| R11 | **Ordering, not exclusion (L2):** stars/last-commit may prioritize probe order so coverage climbs fastest, but never filter enumeration — the long tail is the point. Legacy 2.7x-era candidates still enumerate, still gate, and land in the graveyard as records, not silent skips. | code: L2 enumerator config/comments; CLAUDE.md standing rule |

### Acknowledgment protocol for D-001

Post **one** progress-feed entry listing R1–R11, each with the commit hash of its durable
encoding (or "one-time action: done + evidence link"). Only then proceed:
token validation → server restart → yield spike → L2 build.

---

*(Future decisions append below as D-002, D-003, … — same structure: decision, basis,
riders with encoding targets, acknowledgment protocol.)*
