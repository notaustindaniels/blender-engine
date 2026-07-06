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


---
 
## D-002 · 2026-07-06 · Post-L2 premise checkpoint: stop-line honored — repair the instrument, then re-evaluate
 
**Decision:** The PRD §4 clause is formally crossed (coverage 11.9% < 40%; pass-rate healthy
at 61.9% probed / 50.0% of all acquisitions). Harvest scaling therefore stays **paused** —
no L3/L4/L5. The convened premise decision is: **the coverage instrument is not
decision-grade; repair it cheaply, then re-run the same evaluation.** Neither kill nor
greenlight is decidable on a bounded sample with an incomplete numerator.
 
**Basis:** (1) L2 probing was capped at 15 of 27 candidates by amd64-emulation crashes — a
known instrument defect, not ecosystem signal. (2) Five acquisitions (incl. Sorcar, a
seed-anchor-class procedural node system) sit prescan-blocked awaiting the R6 review
machinery that now exists — recoverable coverage at human-review cost. (3) The numerator
counts only dedicated add-on→niche mappings; the SPEC's registry design always intended
composite **recipes** as first-class coverage and it is unimplemented — the 40% line was
calibrated assuming recipes count. (4) L2's new passes added zero new niches (head
pile-up on already-covered niches), evidence the long tail needs recipes and GN-pack
sources, not more of the same lane.
 
### Binding riders
 
| # | Rider | Durable encoding target(s) |
|---|---|---|
| R12 | **Review the blocked five first** (cheapest coverage recovery): run the R6 batched approval review over the 5 prescan-blocked L2 artifacts. Cleared entries proceed to probing; confirmed-dangerous entries stay quarantined with the finding recorded. Update the prescan-allowlist rules file (dated, justified) for any confirmed false-positive patterns. | one-time via existing R6 workflow + allowlist file update |
| R13 | **Native amd64 probe path — approved in principle, path needs my sign-off:** post a short proposal (progress feed + one file) within a day. Preference order: GitHub Actions on this public repo at $0; else a single cloud VM with a hard cost cap of $25/mo and teardown after use. On approval by my reply, complete the FULL 27-candidate L2 matrix natively, plus the L1 emulation-suspects (bagapie both versions, terrain-mixer@4.5). Never self-provision. | proposal file + workflow encoding + dated SPEC §12 amendment after approval |
| R14 | **Recipe coverage becomes first-class** (SPEC §2.2/§4 intent, currently unbuilt): registry recipe entries mapping niche → composition of vaulted operators and/or built-in Blender features, with verification tiers split in every table exactly like R7 — `recipe_verified` (a probe recipe actually ran) vs `recipe_unverified` (documented composition, not yet machine-checked). Never fabricate a recipe to inflate coverage; an unverified recipe is a claim, and tables must say so. | code: coverage path + registry schema; dated SPEC §12 amendment |
| R15 | **Calibration memo, not a goalpost move:** `reports/coverage-calibration.md` — a per-niche market-existence audit of the 59 (does ANY free tool or plausible recipe exist anywhere, with links/evidence), producing an evidence-based proposal: keep 40%, or redefine the metric (e.g., attainable-niche base, or engine-core weighting). The target does **not** change in this entry; any change is my D-003 call. Recalibration by fiat after a miss is forbidden. | one-time report; proposal consumed by D-003 |
| R16 | **Formal re-evaluation after R12–R14 complete:** re-run the PRD §4 evaluation on decision-grade data (full native matrix + reviewed blocks + recipes counted per R14 tiers; pass-rate reported both as of-probed and of-all-acquisitions). Output `reports/prd4-reeval-2.md` plus the D-003 decision request with options: greenlight L3–L5 / recalibrate per R15 evidence / convene paid-vs-build. | one-time report + D-003 request |
| R17 | **Explicit dispositions of the offered options:** option 3 (paid-vs-build) is deferred to D-003, not rejected; option 4 (proceed to L3/L4 now) is rejected — the stop-line is a contract, and scaling resumes only via D-003. | CLAUDE.md standing rule ("crossed stop-lines pause scaling until a DECISIONS.md entry disposes of them") |
 
### Acknowledgment protocol for D-002
 
Same as D-001: one progress-feed entry mapping R12–R17 to committed encodings (or
one-time actions with evidence links). Sequence after acknowledgment:
R12 review batch → R13 proposal (await my reply) → R14 build → native re-probe →
R15 memo → R16 re-eval → D-003 request. Steps 6–8 remain untouched throughout.