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

---

## D-003 · 2026-07-06 · Premise verdict on decision-grade data: ruler redefined (stricter), threshold kept, harvest greenlit to exhaustion

**Decision authority note:** judged by the owner's advisor-agent at explicit owner
delegation ("the agent leveraging the engine will sometimes be you — you should be the
judge"), on the grounds that the corpus's consumer is an LLM agent and the metric must
reflect what an agent can deterministically invoke. The owner retains the wallet (R23),
the commit, and unconditional veto via any subsequent D-entry.

**Decision:** The premise — "the engine is buildable on free tooling" — is **not
falsified**: native pass-rate 15/27 = 55.6% of-probed / 15/37 = 40.5% of-all-acquisitions,
well above the 30% line, with the golden set re-passed natively (instrument sound). The
coverage clause is crossed on decision-grade data (8/59 = 13.6%), so this entry rules on
the ruler itself — and **tightens it** — while moving the final coverage verdict to where
PRD §2 H1 always placed it: after source exhaustion.

**Basis:** (1) The corpus consumer is an agent; `partial` operators and unverified recipes
are runtime landmines an agent cannot improvise around — only the deterministic tier
(full-pass + recipe_verified) is real capability. (2) The R15 audit (link-backed) shows 5
of 59 niches unattainable in the free market anywhere; measuring against them measures the
market, not the harvest. (3) Under the redefined ruler the CURRENT reading is 5/54 =
**9.3%** — lower than the old 13.6% — recorded here so no one can claim the redefinition
flattered the project. (4) L2's head pile-up (new passes, zero new niches) plus R15's
35 recipe-attainable niches say the path to 40% runs through L5 GN packs and recipe
verification, not more of the same lane. (5) PRD structure: §4's early stop-line (premise
health while scaling) fired twice, forced instrument repair, and is satisfied in function;
§2 H1's kill condition ("<40% after exhausting all sources") now governs.

### Binding riders

| # | Rider | Durable encoding target(s) |
|---|---|---|
| R18 | **Gate metric v2:** coverage = (full_pass + recipe_verified) / attainable wave-1 Terrain+Veg niches (54, per the R15 link-backed audit; the 5 unattainable are listed, excluded, and revisited if evidence changes). Threshold **unchanged at 40%**. Current v2 reading 5/54 = 9.3% is recorded in the coverage report as the starting point. | code: `coverage.py`; dated SPEC §12 amendment; dated PRD §3 footnote (this IS the calibration §3 declared provisional targets awaited) |
| R19 | **Verdict venue + tripwire:** the final 40% (v2) evaluation occurs after L5b completes (source exhaustion per H1). The §4 early stop-line is retired as satisfied-in-function. Pass-rate (of-all-acquisitions) remains a live tripwire at EVERY lane gate: <30% at any lane → pause + owner escalation. | dated SPEC §12 amendment; lane-gate check in coverage/report path |
| R20 | **GREENLIGHT steps 6–8:** L3 → L4 → L5a → L5b per SPEC order, all guardrails intact — L5 acquisition stays human-gated (ToS read first, approval-node checkout batches, GitHub-mirror rerouting before any checkout, receipts acknowledged as creator-visible). Owner is hereby warned: L5 will require approval batches from them. | existing workflows; no loosening permitted |
| R21 | **Recipe-probe mode gets built** (the machinery R16 identified): drive newly full-passed generative operators / EXEC_DEFAULT with explicit params inside the same sandbox. Recipes count toward the gate ONLY when probe-verified; verify the 5 seeded during the L3/L4 window; enrich recipe candidates from every new full-pass operator. | code: probe recipe mode + `recipes.yaml` growth; dated SPEC §12 amendment |
| R22 | **Verb×medium grid report:** coverage outputs gain the engine-consumer metric — verified operators per physical verb × medium (ground/water/air/urban/organic) — informational now, the intended Stage-2 entry gate later. This is what the metaphor resolver actually consumes; niches are substitutable, verbs are not. | code: `coverage.py` new table; dated SPEC §12 amendment |
| R23 | **Paid-vs-build trigger (owner's wallet, reserved):** after L5b + the recipe drive, produce the still-uncovered-attainable list with per-niche priced paid options and recipe-feasibility notes → owner decision D-00x. The 2 "none" niches (karst, coral_atoll) go to the Stage-2 recipe/from-scratch backlog now. No paid acquisition, ever, without that owner entry. | report template + CLAUDE.md standing rule |
| R24 | **Delegation accountability:** this entry's reasoning is auditable above; any party (owner, builder, reviewer) may challenge it via a new D-entry. The owner's veto is unconditional and requires no justification. | CLAUDE.md standing rule |

### Acknowledgment protocol for D-003

Same as D-001/D-002: one progress-feed entry mapping R18–R24 to committed encodings, then
proceed in order: R18/R19/R22 encodings → R21 recipe-probe build → L3 → L4 → (owner
approval batches) L5a → L5b → recipe drive completion → final v2 evaluation →
reports/prd4-final.md + the D-00x request per R23.

---

## D-004 · 2026-07-07 · Asset lanes added (Sketchfab, ArtStation, Fab) as a new lane class — off the gate, on the map

**Decision (owner-initiated, advisor-shaped):** ArtStation, Fab.com, and Sketchfab join
the harvest as a NEW lane class — **A-lanes (asset lanes): A1 Sketchfab, A2 ArtStation,
A3 Fab** — serving Stage-2 scene-asset needs. They are explicitly **excluded from gate v2
and the verb×medium grid** (they host assets, not procedural operators), and they must
not delay L5a/L5b, which remain the gate-v2 critical path. This entry supersedes the
earlier "Fab needs an L5c note" instruction: Fab is A3.

**Basis:** (1) These marketplaces overwhelmingly host static assets our rubric marks
`procedural: false`; counting them toward the tool gate would corrupt the metric.
(2) The engine's Stage-2 scenes need exactly this content (props, scans, creatures), so
harvesting it is real value on a different ledger. (3) Strategic exception: asset + GN
composition = legitimate recipe. The three "paid-only" R15 niches are marine flora —
CC0 kelp/coral models plus procedural scatter/growth compositions may convert them to
free-recipe-attainable, feeding gate v2 through R21's front door. (4) Sketchfab exposes
an official API for CC-licensed downloads — automatable without browser or checkout.

### Binding riders

| # | Rider | Durable encoding target(s) |
|---|---|---|
| R25 | **A-lane semantics:** entries carry `entry_type: asset_pack`, `procedural: false` expected and fine; never counted in gate v2 or the grid; a separate asset-inventory report tracks them by scene-asset category. Asset-fed recipes (asset + procedural composition) ARE legitimate gate contributors — but only as `recipe_verified` through the standard R21 probe, never by assertion. | registry schema note; `coverage.py` exclusion + new asset report; dated SPEC §12 amendment |
| R26 | **License becomes load-bearing:** every A-lane item records `usage_license` (cc0 / cc-by / cc-by-nc / cc-by-nd / standard / engine-locked) and format. Engine-locked licenses and `.uasset`-only downloads are useless to us → graveyard with reason recorded. NC/ND items are acquired but SEGREGATED pending a future owner call on engine-output commerciality (parked question — flagged, not decided here). Attribution requirements (cc-by) are recorded per item so Stage-2 can emit credits. | meta schema extension; dated SPEC §12 amendment |
| R27 | **Asset probe variant:** import-and-render gate — headless import (gltf/fbx/blend) → non-empty geometry → workbench render thumbnail → license + attribution captured. Pure mesh formats skip the code prescan; `.blend` assets still get the driver/embedded-script scan (blend files can carry Python). | code: probe asset mode; dated SPEC §12 amendment |
| R28 | **Automation posture per source, ToS first:** A1 Sketchfab — official API, automatable for CC-filtered content, token via `.archon/.env` (`SKETCHFAB_TOKEN`), never in chat or YAML. A2 ArtStation / A3 Fab — ToS-check pass with findings posted BEFORE any discovery automation; anything checkout-shaped stays human-gated exactly like L5. All three accounts use the project identity, owner-created. | dated SPEC §12 notes per source; policies file entries |
| R29 | **Priority protection:** A1 discovery may run in parallel (cheap, API-based); A2/A3 begin only after the first L5a approval batch ships. Any conflict for attention resolves in favor of L5a/L5b. The marine-flora recipe experiment (R25 exception) is authorized as soon as suitable CC0/CC-BY specimens land. | CLAUDE.md standing rule |

### Acknowledgment protocol for D-004

Standard: one feed entry mapping R25–R29 to committed encodings. Sequencing folds into
the D-003 plan: L5 ToS pass → L5a batches (owner) → A1 in parallel → A2/A3 after batch 1
→ L5b → recipe drive (including asset-fed marine trio) → final v2 evaluation.