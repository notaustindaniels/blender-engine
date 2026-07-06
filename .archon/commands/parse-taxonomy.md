---
description: Validate inputs/taxonomy.yaml against the SPEC §4.1 schema + meta counts (repurposed from "parse" per §12.1(3)); parse-from-source is the documented fallback.
argument-hint: (no arguments — reads inputs/taxonomy.yaml)
---

# Validate Taxonomy

**Workflow ID**: $WORKFLOW_ID · **Artifacts**: $ARTIFACTS_DIR

The owner delivers `inputs/taxonomy.yaml` as a finished file (SPEC §0 + §12.1(3)), so this step
**validates** rather than parses. The authoritative check is the DETERMINISTIC script — run it,
do not re-derive counts by eye:

```bash
uv run .archon/scripts/validate_taxonomy.py inputs/taxonomy.yaml
```

## Phase 1: VALIDATE
- Run the script above. It tolerates the additive keys (`meta`, `wave`, `origin`,
  `reconstructed`, `declared_count`, `unrecovered_count/hints`, `note`) and checks: verb enum ==
  the frozen v2 set (incl. `aggregate`); every niche's verbs ⊆ enum (`[]` allowed); unique ids;
  and the meta identity `declared_total − unrecovered_total − crossref_dedup_total == wave1_present`.
- **Exit non-zero ⇒ STOP** and report the errors. Do not proceed to harvest on an invalid taxonomy.

## Phase 2: FALLBACK (only if inputs/taxonomy.yaml is ABSENT)
If and only if the file does not exist, parse the two owner-provided taxonomy source documents
into `inputs/taxonomy.yaml` matching the §4.1 schema + additive keys, then re-run Phase 1.
Never invent niches; unrecoverable source fragments are recorded as `unrecovered_count`/hints,
not as placeholder entries (§12.1(5)).

## Phase 3: REPORT
Write `$ARTIFACTS_DIR/taxonomy-validation.md` with the script's JSON summary and PASS/FAIL, and
echo the wave-1 gate denominator (Terrain+Vegetation = 59) for the downstream coverage step.
