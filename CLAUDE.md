# CLAUDE.md — standing rules for this repo (Blender Vault, Stage 1 → 2)

## Session start / after any context compaction (D-001 obligation)
Before acting, **RE-READ**: `KICKOFF.md` (the Stage-1 acceptance contract), `SPEC.md §12`
(all dated amendments), and `DECISIONS.md` (the append-only owner decision log, D-001…).
Context is designed to be lost; these files are the memory. A rider counts as *received* only
when its durable encoding is committed — code, workflow YAML, a dated SPEC §12 amendment, or a
rule in this file. Remembering it in context does not count.

## Standing rules
- **SINGLE-WRITER — exactly one session owns the main working tree (D-006 addendum, 2026-07-07).**
  A session writes `.agent-lock` (session id + timestamp) on start and respects an existing FRESH lock
  (do not write the main tree if another session holds it). Any parallel work runs in an **archon
  worktree** and merges deliberately — never two agents editing `repo/` at once. Rationale: parallel
  edits silently reverted committed work (the D-006 collision). If you find a lock you don't own and it
  is fresh, stop and coordinate.
- **Token hygiene (R2).** `GH_TOKEN` lives in `.archon/.env` (git-ignored). Read it from env
  only — never echo, print, log, or commit it. Validate auth before use; on an auth failure,
  report it **plainly and stop** — NEVER work around an auth failure silently (fallback is an
  owner-supplied classic `public_repo` token).
- **The human prescan gate never loosens (R6).** `policies/prescan-allowlist.yaml` may downgrade
  benign-in-context patterns (node `socket`, preset `open`-writes, driver-expression), but the
  exec/network-capable patterns (`subprocess`, `os.system`, `os.popen`, `eval(`, `exec(`,
  `__import__`, `urllib`, `requests`, `httpx`, `ctypes`, `base64-decode`) can **never** be
  allowlisted (enforced in `prescan.py` via `NEVER_ALLOW`). Every artifact runs sandboxed
  (`--network none`, read-only, non-root) regardless of prescan.
- **Scope discipline (R9).** SPEC §9 steps 5–8 are sequential and gated. L2 ends with the updated
  coverage report + a formal PRD §4 re-evaluation before anything else starts. Do not begin
  steps 6–8 without an owner GO (a new DECISIONS.md entry).
- **L2 enumeration orders, never filters (R11).** Stars/recency may prioritize probe order; they
  never exclude candidates from enumeration — the long tail is the point. Legacy / archived /
  no-signature repos become `graveyard.jsonl` records, never silent skips.
- **Crossed stop-lines pause scaling until disposed (R17, D-002).** When a PRD §4 stop-line is
  crossed, harvest scaling (new lanes / steps 6–8) STAYS PAUSED until a DECISIONS.md entry
  explicitly disposes of it. A crossed stop-line is a contract — never worked around, never
  recalibrated by fiat after a miss, never resumed on agent initiative.
- **Recipes are claims until machine-checked (R14, D-002).** A registry recipe (niche → composition
  of vaulted operators / built-in features) counts as `recipe_verified` ONLY if a probe recipe
  actually ran; otherwise it is `recipe_unverified` — a documented claim, labelled as such in every
  table. Never fabricate a recipe to inflate coverage.
- **Awaiting-owner is a valid terminal state; never loop against it (D-002 follow-up).** When
  progress is blocked on an owner-gated action (a permission, a sign-off, a push, a D-00x
  decision), stopping and reporting the precise blocker IS the correct behavior — not a goal
  failure. Do not re-run verification, re-argue, or take initiative to route around the gate;
  state the one action the owner must take and stop. (If a Stop-hook loops against a
  legitimately-superseded goal, the resolution is the owner clearing/patching the goal, never the
  agent undoing committed owner-authorized work.)
- **No paid acquisition, ever, without an owner D-entry (R23, D-003).** The corpus is free-only.
  After L5b + the recipe drive, the still-uncovered-attainable niches get a priced-options +
  recipe-feasibility report → owner decision. Never buy, even a $0-illegitimate ("nulled") source
  is a hard fail. The 2 `none` niches (karst_formation, coral_atoll_generator) are Stage-2
  recipe/from-scratch backlog, not purchases.
- **Decisions are auditable and vetoable (R24, D-003).** DECISIONS.md reasoning may be challenged by
  any party via a new D-entry; the owner's veto is unconditional and needs no justification. A
  decision judged by a delegated advisor-agent still carries owner authority until the owner vetoes.
- **A-lanes are off the gate; L5a/L5b have priority (R25/R29, D-004).** Asset lanes (A1 Sketchfab,
  A2 ArtStation, A3 Fab) serve Stage-2 scene assets — `entry_type: asset_pack`, never counted in gate
  v2 or the verb×medium grid. Asset-fed recipes reach the gate ONLY as `recipe_verified` via the R21
  probe, never by assertion. A1 may run in parallel (API); A2/A3 begin only after the first L5a
  approval batch; attention conflicts resolve for L5a/L5b. Never start A-lane acquisition before the
  owner confirms the account and delivers the token (e.g. `SKETCHFAB_TOKEN`).
- **Batch-driven, not interrupt-driven (R30, D-005).** Never stop for an owner ask while ANY
  non-blocked authorized work remains. Owner-gated items accumulate in `OWNER-QUEUE.md` (one line:
  item, why gated, exact action, evidence link). Surface to the owner ONLY when (a) all remaining
  work is owner-blocked, or (b) the final v2 evaluation is ready. Interim milestones go to the
  progress feed, never to the owner.
- **Unconfirmable price is a NO (R31, D-005).** A candidate whose $0 price cannot be machine-confirmed
  is denied — it may re-enter the queue only with a machine-confirmed $0. Never assume a price through.
- **The irreducible human floor (R33, D-005).** These never delegate, no autonomy argument overrides:
  $0 checkouts are the owner's hands (batched); the wallet (paid acquisition, R23) and the final
  premise-verdict signature are the owner's; credentials are the owner's to mint. Queue them, never
  self-perform.
- **The two unattainables are Stage-2 backlog, never purchases (R38, D-006).** `karst_formation` and
  `coral_atoll_generator` have no free tool or plausible free recipe (R15 audit) and are the ONLY two
  niches excluded from the gate-v2 attainable denominator. They go to from-scratch/recipe research in
  Stage 2 (`reports/stage2-backlog.md`) — no paid acquisition without an explicit owner D-entry (R23).
  Revisit only if new evidence (a free tool or viable composition) surfaces.
- **Premise CONFIRMED; 40% is an execution milestone, not a kill-line (R36, D-006).** The R35 review
  passed; the premise is signed CONFIRMED (SPEC §12.8, `reports/prd4-final.md` §D-006 R36). The 40%
  gate-v2 line is now an execution milestone. The <30% pass-rate tripwire (R19) stays live at every
  lane. If the no-spend path completes still <40%, the R23 priced-options request fires automatically.
- **Never diverge from the SPEC silently.** If reality contradicts it, add a dated SPEC §12
  amendment in the same change.
- **Two niches are Stage-2 build-from-scratch, never purchased (R38, D-006).** `karst_formation` and
  `coral_atoll_generator` have no free path anywhere → `reports/stage2-backlog.md` for Stage-2 node
  authoring. No paid acquisition for them without an owner D-entry.
- **Quality tiers ride into Stage-2 (R39, D-006).** The handoff exposes per operator/recipe a quality
  field (full generator vs `quality: minimal` asset-fed composition) so the Stage-2 resolver prefers
  depth. Asset-fed coverage answered the premise; it must never masquerade as generator sophistication.
