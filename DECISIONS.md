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

---

## D-005 · 2026-07-07 · The walk-away contract: batch-driven autonomy replaces interrupt-driven asks

**Decision:** The owner's involvement converts from interrupt-driven to batch-driven. The
agent works every authorized lane to exhaustion without stopping for owner input, queues
anything owner-gated, and surfaces exactly one consolidated session at the end. Rationale:
all identity provisioning is now complete (GH read/write, Actions, Sketchfab, marketplace
accounts); the remaining interrupt classes are checkouts and final decisions, both
batchable by design.

### Binding riders

| # | Rider | Durable encoding target(s) |
|---|---|---|
| R30 | **Owner-queue discipline:** never stop for an owner ask while ANY non-blocked authorized work remains. Owner-gated items accumulate in `OWNER-QUEUE.md` (one line each: item, why gated, exact action needed, evidence link). Surface to the owner only when (a) all remaining work is owner-blocked, or (b) the final v2 evaluation is ready — whichever comes first. Interim milestones go to the progress feed, not to the owner. | CLAUDE.md standing rule + `OWNER-QUEUE.md` |
| R31 | **Immediate dispositions of the three open asks:** fern checkout APPROVED (owner executing at the committed resolved URL); river DENIED under the new default rule — an unconfirmable price is a no; it may re-enter the queue only with a machine-confirmed $0; marine-flora asset-fed recipe experiment APPROVED under existing R21 sandbox + R25–R29 license rules (CC-BY assets only; by-nc stays segregated and out of recipes). | one-time + feed evidence; the price-default rule → CLAUDE.md |
| R32 | **Pre-authorizations (all under existing guardrails, zero new permissions):** (a) A2 ArtStation and A3 Fab activate after batch #1 ships, each gated on its own ToS read — a ToS that forbids the plan DROPS the lane with a recorded finding, no escalation; (b) L5b Superhive discovery + batch prep proceed under the recorded conservative posture; (c) the recipe drive and further asset-fed recipe experiments continue for any attainable niche; (d) taxonomy-proposal and re-verification workflows run on schedule. | dated SPEC §12 note listing (a)–(d) |
| R33 | **Non-delegations — the irreducible human floor, stated as contract:** $0 checkouts remain the owner's hands, batched (D-001 guardrail #2 stands; Gumroad §14 makes automated checkout ToS-hostile, and this entry explicitly declines to amend that); the wallet (R23 paid-vs-build) and the final premise verdict signature remain the owner's; credentials remain the owner's to mint. No autonomy argument overrides these. | CLAUDE.md standing rule |
| R34 | **Definition of walk-away done:** when work exhausts or blocks entirely on the owner, present ONE consolidated session: the drained `OWNER-QUEUE.md` (checkout links, each with confirmed price + license), `reports/prd4-final.md` (final v2 evaluation, full tier splits, both pass-rate framings), and the R23 D-00x decision request with priced options. Nothing else interrupts before that. | report contract + CLAUDE.md |

### Acknowledgment protocol for D-005

One feed entry mapping R30–R34 to encodings, then resume: fern probe on receipt → marine
recipe experiment → batch #1 close-out → A2/A3 ToS reads → L5b → recipe drive → final
evaluation → the consolidated owner session.

---

## D-006 · 2026-07-07 · The premise signature — contingent on adversarial review of the walk-away run

**Decision:** The owner signs the premise verdict below, **contingent on R35 passing**. The
walk-away run (D-005) produced the largest gate movement in project history (9.3% → 29.8%,
11 recipe_verified conversions) without the adversarial review every prior milestone
received — a gap in D-005's own drafting, closed here before anything is signed on it.

### Binding riders

| # | Rider | Durable encoding target(s) |
|---|---|---|
| R35 | **Adversarial review first (KICKOFF item 7 pattern):** fresh-context reviewer, artifacts only. Must independently: (a) rebuild coverage and reproduce 17/57 = 29.8%; (b) re-probe a random 4 of the 11 recipe_verified entries — each must reproduce its geometry delta in the sandbox; (c) verify marine-trio provenance — CC-BY license + attribution captured, by-nc assets excluded from recipes; (d) **reconcile the 54→57 denominator**: the coverage code moved but SPEC §12's R18 amendment still reads 54/5-unattainable — add the dated amendment recording the marine conversions (or revert if unjustified); (e) verify the A2/A3 drop findings. Per-item PASS/FAIL, max 2 fix cycles. **The R36 signature takes effect only on full PASS.** | one-time review + fixes; dated SPEC §12 amendment for (d) |
| R36 | **The signature (contingent on R35):** the premise — *the engine is buildable on free tooling* — is **CONFIRMED, not merely unfalsified**: pass-rate 56.2%/42.9% clears the 30% kill-line both ways at full native scale, and the marine-trio conversion is affirmative evidence (three niches the market itself had priced became free, machine-verified capability through composition). The 40% line is **reclassified from kill criterion to execution milestone**, per H1's own wording — sources are not exhausted while human-gated $0 checkouts sit queued and the shader-probe is unbuilt (an instrument gap, not a market gap). **Auto-trigger:** if the no-spend path completes (queue drained, shader-probe built, recipe drive exhausted) with coverage still <40%, the R23 priced-options request fires automatically — no further owner prompt needed to ask the question. | signed block appended to `reports/prd4-final.md` on R35 PASS; dated SPEC §12 note |
| R37 | **No-spend completion authorized:** (a) build the shader-probe variant (several remaining niches are shaders the Gate currently cannot verify at all); (b) prepare the terrain GN-pack $0 batch to the batch-1 resolution standard — final product URLs, confirmed prices, captured licenses — for one owner checkout session; (c) continue the recipe drive, including the asteroid partial→recipe TODO. All under existing guardrails; nothing new is permitted. | probe code + batch report + recipe registry |
| R38 | **The two unattainables parked:** `karst_formation` and `coral_atoll_generator` go to the Stage-2 build-from-scratch backlog (adopting prd4-final's recommendation). No purchase is authorized for them. | backlog file + CLAUDE.md note |
| R39 | **Quality tiers ride into Stage-2:** the handoff contract exposes, per operator and per recipe, a quality field (full generator vs. `quality: minimal` asset-fed composition) alongside the verb×medium grid, so the Stage-2 resolver prefers depth where it exists. Asset-fed coverage answered the premise question; it must never masquerade as generator sophistication downstream. | manifest/recipe schema + handoff doc |
| R40 | **Wave-3 intake:** `rock_generator_addon` (the unmapped taxonomy candidate from verification bookkeeping) enters the taxonomy-proposal flow; proposals batch into the next consolidated owner session per R30 — never auto-added. | taxonomy-proposals report |

### Acknowledgment protocol for D-006

One feed entry mapping R35–R40, then: R35 review → on PASS, post the signed block and
proceed R37 → next consolidated owner session = the GN-pack checkout batch + any
auto-triggered R23 request + wave-3 proposals. The fern `.blend` will be waiting in
`inputs/dropzone/` — probe it first.

---

## D-007 · 2026-07-07 · Stage-1 close-out: 40% verified-then-declared, depth batch, handoff contract, stage transition

**Decision:** Gate v2 at 23/57 = 40.4% (zero spend) is accepted as the execution-milestone
reading, **contingent on R41** — the 31.6%→40.4% delta postdates the last adversarial
review and gets one before "done" is declared. Route B is authorized for depth, the
Stage-2 handoff contract is commissioned, and Stage 1 formally closes on completion.

### Binding riders

| # | Rider | Durable encoding target(s) |
|---|---|---|
| R41 | **Delta review (fresh-context, scoped to post-R35 work):** reproduce 23/57 = 40.4%; re-probe 2 of the 5 BlenderKit shader conversions AND confirm each is a genuinely procedural node material (not an image-texture pack wearing the label); verify every concurrency-starvation re-pass has its single-container state individually recorded; verify L6 per-asset license capture (CC0 vs RF flagged per item). One fix cycle. Declaring Stage 1 done is blocked on PASS. | one-time review + feed evidence |
| R42 | **Route B authorized — depth, not number:** prepare the $0 GN-pack batch to the batch-1 resolution standard (final URLs, confirmed $0, captured licenses), cap ~15 rows, ranked by (i) upgrading `asset_fed_minimal` niches to `full_generator` and (ii) filling empty verb×medium cells (water/air/urban; aggregate/fill/reveal). One owner checkout session; flagged prices default to deny. | batch report per existing standard |
| R43 | **The Stage-2 handoff contract — `HANDOFF.md`:** the consumption interface for the engine: registry + manifest schemas, quality tiers (resolver MUST prefer depth), verb×medium grid, recipes registry, re-verification API — and the **license obligations every Stage-2 render inherits**: CC-BY assets require visible attribution (video credits/description); BlenderKit assets are rendered-video-only — **no 3D-export of scenes containing them**; Royalty-Free means incorporation-only, no standalone redistribution. A registry snapshot is committed and the 90-day re-verification schedule is armed. | `HANDOFF.md` + snapshot + scheduled workflow |
| R44 | **Stage 1 closes** on R41 PASS + Route B probed: post the final consolidated report, including — once, informational — whole-taxonomy coverage (wave-1 + wave-2 + grid) for Stage-2 planning. The gate was always a T+V proxy; Stage 2 plans against the whole map. | `reports/stage1-final.md` |
| R45 | **Stage 2 opens by its own PRD + SPEC** (the create-prd / create-spec discipline that opened Stage 1), authored fresh against `HANDOFF.md`; thin slice = the fish-form-an-equation vertical from the original engine plan. This repo becomes a consumed, read-only dependency (registry + vault) — not a workspace. Owner and advisor convene on the Stage-2 PRD as the next act. | new PRD/SPEC artifacts (Stage-2 repo) |

### Acknowledgment protocol for D-007

One feed entry mapping R41–R45, then: R41 review → Route B batch prep → owner checkout
session → probe → `HANDOFF.md` + snapshot → `stage1-final.md` → Stage 1 CLOSED.

---

## D-008 · 2026-07-08 · The mission is the library — full-taxonomy harvest campaign WITH the navigation layer built in

**Decision:** Stage 1's closure is **reinterpreted, not revoked**: what closed was the
premise test and the factory. The MISSION — the comprehensive library the owner specified
on day one ("the tip of an iceberg... anything and everything conceivable") — stands at
**10.0% whole-taxonomy (27/269 wave-1)** and now becomes the explicit campaign. Because a
library only an expert can navigate is not a library, the campaign includes the
**LLM-navigation layer** (hybrid-RAG knowledge base + progressive-disclosure cards) as a
first-class deliverable — and because cards are cheapest to mint at gate time, it ships
INSIDE the harvest, not after it. R45's "read-only repo" rule is amended: this repo
remains the harvest workspace until campaign completion; `HANDOFF.md` becomes a versioned
snapshot contract (tagged per milestone).

### Binding riders — the harvest at width

| # | Rider | Durable encoding target(s) |
|---|---|---|
| R46 | **Campaign scope = the entire taxonomy**, all 26 categories, waves 1+2 (328 niches) plus wave-3 intake — every lane re-run WITHOUT the T+V filter: L1 full-catalog classification+probe (all ~998 platform extensions); L2 full per-category signature/keyword sweep to the enumeration ceiling; L3/L4 continued; L5a/L5b at scale with batched checkouts; L6 BlenderKit full free-tier sweep; Route B executed. R11 governs: stars/recency ORDER probing, never exclude enumeration. | lane configs stripped of T+V filters; dated SPEC §12 amendment |
| R47 | **Campaign metrics replace the retired proxy:** per-category verified coverage (quality-tiered), the full verb×medium grid, and first-class **gap reports** naming market absences per category. No single %-threshold; the target is DOCUMENTED EXHAUSTION per lane per category. The 30% of-all pass-rate tripwire stays live at every lane gate. | coverage.py per-category tables + reports/gaps/ |
| R48 | **Scale posture:** native CI probing is the authoritative gate at campaign volume; local emulation is dev-only. Throughput + backlog reported on the progress page. Cost stays $0 on public-repo Actions; if limits bite, PROPOSE alternatives as an owner decision — never self-provision. | workflow batching + feed reporting |
| R49 | **Owner cadence (walk-away contract governs):** recurring touchpoints are checkout batches (~15–25 resolution-passed rows per session) and batched wave-3 approvals; consolidated sessions only; the one unscheduled escalation is the pass-rate tripwire. | CLAUDE.md standing rule |
| R50 | **Stage 2 may proceed in parallel** in its own repo against tagged HANDOFF snapshots; single-writer holds per repo; campaign completion = final consolidated report per R47 + a closing D-entry that closes the MISSION, not a proxy. | snapshot tagging convention + CLAUDE.md |

### Binding riders — the navigation layer (how any LLM uses the library)

| # | Rider | Durable encoding target(s) |
|---|---|---|
| R51 | **`corpus_kb.db` on the owner's hybrid-RAG template, adopted as-is** (schema.sql, ragdb.py, chunker.py, embedder.py, ingest.py, retrieve.py, reranker.py from `hybrid-rag-template`): a SECOND derived database, rebuilt deterministically from the same JSON manifests that build `corpus.db` — never hand-edited, always regenerable. Graph vocabulary FIXED via CHECKs: node types `{addon, operator, recipe, asset, niche, verb, medium, category, license}`; edge types `{PROVIDES, COVERS, PERFORMS, IN_MEDIUM, COMPOSES, LICENSED, PART_OF, SUBSTITUTES}`. The graveyard is ingested and labeled `state: graveyard` so dead tools are findable-as-dead. | vendored template + kb_build script; dated SPEC §12 amendment |
| R52 | **Operator cards are GATE ARTIFACTS + three-tier progressive disclosure:** the enrich step, while it already holds the README, mints a ~120-word card per operator and recipe on a fixed template (what it does · verbs · media · niches · quality tier · license obligation · param signature · one example invocation · Blender versions). Tier 0 = `CORPUS.md` (≤2k tokens, committed, versioned with snapshots — the only always-loaded artifact); Tier 1 = cards (what retrieval returns); Tier 2 = full manifests + doc chunks (fetched on selection). Cards for the existing 58 entries are back-filled once. | enrich prompt + card template; CORPUS.md |
| R53 | **Retrieval doctrine — RETRIEVAL PROPOSES, THE REGISTRY DISPOSES:** hybrid search (FTS5+vector, RRF, optional rerank per the template) and graph walks only ever ROUTE to canonical ids; final selection MUST resolve through `corpus.db` verification state + license obligation before any invocation, and tool selection terminates in deterministic facet queries (verb × medium × quality ≥ tier × license class × blender version). Embedding model is pinned in `meta` (local/open, $0); `content_hash` gives incremental re-ingest as the harvest grows; a model change = recorded full re-embed. `recipe_unverified` and `graveyard` results are returned labeled and are NEVER resolvable at render time. | retrieve/resolve wrapper + CLAUDE.md standing rule |
| R54 | **The consumption interface — an MCP server (+CLI twins)** over `corpus_kb.db` + `corpus.db`, exposing: `search_capabilities(nl, filters, near)`, `query_registry(verb, medium, niche, quality_min, license_class, blender_ver)`, `get_card(id)`, `get_usage(id)`, `find_substitutes(id|niche)`, `plan_recipe(niche)`. This becomes the PRIMARY interface any fresh LLM — Stage 2 included — uses; `HANDOFF.md` is amended accordingly. | MCP server + HANDOFF amendment |
| R55 | **The "down pat" bar is falsifiable (H2 redux):** a golden-query eval set (≥30 natural-language needs → expected operator/niche, growing with the corpus) measured in CI — hit@5 ≥ 90% — plus a fresh-context agent resolution test (NL need → verified, license-checked selection, no human help). Regressions BLOCK snapshot tagging. This is the acceptance test for "any LLM can navigate it." | eval harness + CI gate |

### Acknowledgment protocol for D-008

One feed entry mapping R46–R55, then: vendor the template + build `corpus_kb.db` + back-fill
cards for the existing 58 (R51/R52 first — the KB must exist before the flood) → strip lane
filters → L1 full catalog → L2 → L6 → L5 cycles → cards minted at every gate pass → eval
green before every snapshot tag → consolidated owner sessions per R49.