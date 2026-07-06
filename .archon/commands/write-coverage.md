---
description: "AI narrative gap analysis ON TOP of the deterministic coverage matrix (SPEC §6.3). Runs coverage.py first, then interprets — never invents numbers."
argument-hint: (no arguments — reads corpus.db via coverage.py)
---

# Write Coverage — narrative on computed matrix

**Workflow ID**: $WORKFLOW_ID · **Artifacts**: $ARTIFACTS_DIR
**Context is fresh.**

The NUMBERS are computed deterministically — you narrate, you do not recompute. First run:

```bash
uv run .archon/scripts/coverage.py --db corpus.db --taxonomy inputs/taxonomy.yaml --reports reports
```

This writes `reports/coverage-report.md`, `reports/coverage.json`, `reports/gaps.md`, and
`reports/taxonomy-proposals.md`. Treat `reports/coverage.json` as ground truth.

## Phase 1: LOAD
Read `reports/coverage.json` (gate %, pass-rate, per-category present/covered) and
`reports/gaps.md` (zero-operator niches) and `reports/taxonomy-proposals.md`.

## Phase 2: NARRATE (append, don't overwrite the tables)
Append an "## Analysis" section to `reports/coverage-report.md`:
- State the Terrain+Vegetation wave-1 coverage % and pass-rate verbatim from coverage.json, and
  compare to PRD §4 stop-lines (<40% coverage, <30% pass-rate). Be explicit that the <40% line is
  formally evaluated after L1+L2, so an L1-only slice below target is expected, not a kill signal.
- Name the highest-value uncovered niches (from gaps.md) and which future lane (L2 GitHub, L5
  marketplace) is most likely to fill each.
- Review `reports/taxonomy-proposals.md`: for each unmapped surviving add-on, say whether it
  suggests a genuine missing niche (wave-3 candidate) or is out-of-scope. Never auto-add.

## Phase 3: REPORT
Keep it honest and short. Do not restate PRD intent. Do not touch the computed tables above your
Analysis section. Write a one-paragraph `$ARTIFACTS_DIR/coverage-narrative.md` summary for the gate.
