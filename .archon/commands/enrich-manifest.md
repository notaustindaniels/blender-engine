---
description: "AI enrich — read each verified add-on's README/source + operators and assign taxonomy niches + physical verbs (SPEC §4.3, §4.4). Judgment step; deterministic verify already ran."
argument-hint: (no arguments — reads manifests/*.json and vault/*/meta.json)
---

# Enrich Manifests — verbs + niche tags

**Workflow ID**: $WORKFLOW_ID · **Artifacts**: $ARTIFACTS_DIR
**Context is fresh** — rely only on files, not prior-node memory.

This is the one place real judgment happens (SPEC §6 determinism split): map each add-on's
VERIFIED operators to taxonomy niches and physical verbs. Never re-run the verifier or invent
operators — the operators are already introspected in `manifests/<id>.json` (`operators` list)
and provenance is in `vault/<id>/<ver>/meta.json`.

## Phase 1: LOAD
- Read `inputs/taxonomy.yaml` (niche ids, aliases, verbs, categories, `wave`).
- For each `manifests/*.json`: read its `operators`, `verify` states, and `artifact_type`.
- Read the matching `vault/<canonical_id>/<version>/meta.json` (name, tags, `niche_hint`) and,
  if present, the add-on's README/`blender_manifest.toml` inside the vaulted archive for context.

## Phase 2: ENRICH (judgment)
For each add-on, produce an `operators_enriched` array. For each meaningful operator/node group:
- `kind`: `bpy_op` | `gn_node_group`
- `id`: the operator bl_idname or node-group name (verbatim from the manifest — do NOT fabricate)
- `verbs`: subset of the FROZEN enum only — `generate, scatter, trace, stack, accumulate, branch,
  fill, deplete, reveal, illuminate, simulate, deform, aggregate`
- `niches`: taxonomy niche ids this operator genuinely serves (match against ids + aliases). Assign
  a niche ONLY with evidence (operator semantics, name, README). If nothing fits, leave `niches: []`
  — an unmapped-but-working add-on becomes a taxonomy PROPOSAL later (§12.1(6)); never force-fit.
- Prefer wave-1 niches for the probe categories; wave-2 niches are allowed but reported separately.

## Phase 3: WRITE
Rewrite each `manifests/<id>.json` adding `operators_enriched`, `enriched_by: "ai"`, and a short
`notes` justifying non-obvious niche assignments. Preserve the existing `verify` block untouched.

### PHASE_3_CHECKPOINT
- [ ] Every niche id used exists in `inputs/taxonomy.yaml`
- [ ] Every verb used is in the frozen enum
- [ ] No operator id invented — all trace to the manifest's introspected `operators`
- [ ] Zero-fit add-ons left with `niches: []` (not force-fit)

## Phase 4: REPORT
Write `$ARTIFACTS_DIR/enrich-summary.md`: per add-on, its niches + verbs, and any left unmapped.
