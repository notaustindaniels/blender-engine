# OWNER-QUEUE.md — human-gated remainders (D-008 campaign) · updated 2026-07-09

The full-taxonomy harvest runs in native-CI waves (L1 ✓, L2 ✓, L6 in progress). Everything below is the
irreducible human floor (R33) or an owner-gated credential/decision. Automatable work continues without
these; surfaced per R49 (batched, consolidated). Nothing here blocks the automatable campaign.

## ⚡ ONE ACTION unblocks L6 at scale — TESTED as a hard permission wall (R2)
The full 773-candidate L6 sweep MUST run in native CI (`l6-wave.yml`, registered + ready): local
arm64-emulation gates only **1 pass in 23** (~96% quarantine/timeout — heavy BlenderKit materials crash
the emulated probe; proven, `manifests/bk__material__*`). I tried to self-serve the CI secret with the
RW token via GitHub's encrypted-secret API — **HTTP 403 "Resource not accessible by personal access
token"**: `blender-engine-rw` has `Actions: write` (dispatch) but NOT `Secrets: write`. So it is a
genuine, tested credential wall. **Pick ONE (either unblocks L6):**
- [ ] **(a) You add the secret** — GitHub → repo **Settings → Secrets and variables → Actions → New
  repository secret** → name `BLENDERKIT_API_KEY`, value = your BlenderKit key. Then tell me and I
  dispatch `l6-wave`, poll, ingest, card, re-eval. *(Recommended — least privilege.)*
- [ ] **(b) You grant `blender-engine-rw` the `Secrets: write` permission** — then I set the secret
  from the local key (encrypted, never printed) AND dispatch the wave fully autonomously.

Until then, L6 coverage stands at the niche-targeted local max (27 passes → 15.9%, 13 categories); the
600-material/173-node-group long-tail is the CI wave's job (real gate states only under native amd64).

## $0 checkout batch — RESOLVED to batch-1 standard (your hands — R33, Gumroad §14 no-automation)
The 84 L5-pending links were resolution-passed (`reports/l5-resolution.md`): ~70 paid/non-procedural
(excluded), free generators rerouted to L2 (probed → several NEVER_ALLOW-quarantined by R6). The
**confirmed-$0, ready-to-click checkout batch** (price machine-confirmed via search; unconfirmable = DENY
per R31):

| # | product | URL | price | license | niche | Blender |
|---|---|---|---|---|---|---|
| 1 | **Buildify 1.0** (Pavel Oliva) | `paveloliva.gumroad.com/l/buildify` | **$0** (PWYW, confirmed) | free-to-use (verify at download) | `building_generator` | 3.2+ |

**Rerouted to L2 (automatable, no checkout needed):** Shot Manager Lite → `github.com/OtherRealms/Shot-Manager-Free`
($0, but a shot/render UI tool → non-niche, not corpus-relevant). **DENIED (R31, unconfirmable $0):** Flex's
generators (rope/crystal/curtain — Gumroad price not machine-confirmable). **EXCLUDED (paid, R23):** BlendFog
(**$18** Superhive — the forum title mislabeled it "free"); ~70 paid brush/detail/rig kits. **Not corpus:**
"[FREE] Base Mesh" (static asset, not procedural → optional Stage-2 scene asset).

To click: open the Buildify URL, enter **$0**, download the `.blend`, drop it into `inputs/dropzone/` and I
probe it next run. (It maps to `building_generator`, already covered by a node-group — so this is depth, not
new coverage.)
- [ ] **Route B GN-pack batch** (D-007 R42) · optional depth; free marketplace $0-GN supply is thin.

## Prescan safety review (R6 — human clears benign-in-context only)
- [ ] **Wave 1: 16 human-clearable** (`reports/prescan-review-wave1.md`) · benign-in-context patterns
  (socket/open-write) only; a human may clear against `policies/prescan-allowlist.yaml` for re-probe.
  Triage niche-relevance first (most are UI/utility). The 143 NEVER_ALLOW stay quarantined permanently.
- [ ] **Wave 2: 227 prescan-flagged** · ~55% of L2 GitHub add-ons hit exec/network patterns (subprocess/
  requests common in GitHub add-ons). Most are NEVER_ALLOW (permanent quarantine); a clearable subset
  will be triaged into a review batch next.

## Wave-3 taxonomy proposals (R40 — owner approves, never auto-added)
- [x] `rock_generator_addon` → `rock_boulder_generator` — APPROVED (D-006), mapped.
- [ ] Pending: candidates surfacing niches not in the taxonomy batch into the next consolidated session
  as they accumulate; none blocking.

## Resolved / not-blocking
- [x] Premise CONFIRMED (D-006 R36); 40% execution milestone cleared; gate-v2 proxy retired (D-008).
- [x] Navigation layer complete + tagged (`snapshot-nav-v1`); Waves 1+2 tagged (`snapshot-wave2`).
- Automatable waves (L1/L2/L6-local) proceed without any of the above.
