# OWNER-QUEUE.md — human-gated remainders (D-008 campaign) · updated 2026-07-09

The full-taxonomy harvest runs in native-CI waves (L1 ✓, L2 ✓, L6 in progress). Everything below is the
irreducible human floor (R33) or an owner-gated credential/decision. Automatable work continues without
these; surfaced per R49 (batched, consolidated). Nothing here blocks the automatable campaign.

## Owner-gated credential (blocks the FULL L6 sweep only)
- [ ] **BlenderKit key in CI for the 773-candidate L6 sweep** · the full sweep needs `BLENDERKIT_API_KEY`
  as a GitHub Actions secret (a wave probing 600 materials + 173 node-groups); the key is yours to place
  (R33). Local batches proceed now with the local key (no CI secret) — a representative material batch is
  running. Say the word to add the CI secret for the full sweep, or I continue in local batches.

## $0 checkout batches (your hands — R33, Gumroad §14 no-automation)
- [ ] **L5 pending resolution** · `candidates/L5_pending.jsonl` holds **84** marketplace links (Gumroad/
  Superhive) from L3/L4 routing. Each needs resolution to the batch-1 standard (GitHub-mirror check →
  confirmed $0 → captured license) before a checkout batch. **Next agent step (automatable):** run the
  mirror-check + price-confirm pass, producing a resolution-passed batch (~15–25 rows) for one checkout
  session. Flagged/unconfirmable prices default to DENY (R31).
- [ ] **Route B GN-pack batch** (D-007 R42) · optional depth; the free marketplace $0-GN supply is thin
  (mostly paid/unconfirmable). Re-open only if you want depth beyond the free-API lanes.

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
