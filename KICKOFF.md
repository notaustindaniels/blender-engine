Read PRD.md and SPEC.md in this repo top to bottom before doing anything — they are the complete "why" and "how." Nothing else exists yet. Your job is Stage 1, scoped exactly as below.

**0. Contract first.** Save this entire message verbatim to KICKOFF.md and commit it. It is the acceptance contract; a fresh-context reviewer will later judge the work against it, so it must live in the repo, not in your memory.

**1. /archon.** Load the archon skill before touching anything else. If the archon CLI isn't installed, follow the skill's setup guide. Initialize `.archon/` here, author the workflows, commands, and scripts exactly per SPEC §2.3 and §6, and run `archon validate workflows` until clean.

**2. Kickoff inputs.** Ask me for anything SPEC §0 requires that isn't in the repo — at minimum the taxonomy source document. Do not invent a taxonomy. Draft `inputs/seed-anchors.yaml` from the list in SPEC §0, but live-verify every entry before recording it; never trust an add-on name from memory (the PRD's fabrication-rate-zero metric applies to you too). GH_TOKEN is not needed yet — the thin slice is L1 only.

**3. Scope.** Execute SPEC §9 steps 1–3 only: (1) repo + Archon init, (2) sandbox + probe.py + golden set, (3) the L1 thin slice over Terrain + Vegetation. Then STOP at the mandatory decision gate. Do not start steps 4–8. Write `reports/gate-decision.md` — the coverage numbers against PRD §4's wrong-condition thresholds, plus your recommendation — and hand the go/no-go to me.

**4. Follow-along page.** Spin up a persistent HTML page (`progress/index.html`, auto-refreshing, served by a background local server; media in `progress/media/`). As you work, append clear, timestamped updates with screenshots/media — golden-set results, probe render thumbnails, the coverage matrix, key terminal output — so I can follow along. Newest first. Every SPEC §9 done-signal gets an entry with evidence, not narration. Log open questions there instead of guessing.

**5. Working rules.** Deterministic work in bash/script nodes; AI only where SPEC §6 says so. PRD §4 guardrails are non-negotiable: every probe runs with `--network none`, no secrets ever committed, prescan before any container execution. If reality contradicts the SPEC, update the SPEC with a dated note — never silently diverge.

**6. The bar (definition of done).**
a. `archon validate workflows` clean for all three workflows.
b. Golden set: correct state for every golden artifact on Blender 3.6, 4.2, and 4.5 (SPEC §8).
c. L1 thin slice end-to-end: every vault entry has meta.json + SHA-256, manifests written, corpus.db rebuilt idempotently, `reports/coverage-report.md` with real Terrain + Vegetation numbers.
d. `reports/gate-decision.md` exists; steps 4–8 untouched.
e. Security spot-checks: no secrets in git history, sandbox flags present in the actual run commands, prescan wired ahead of every container run.
f. Progress page live, timestamped, with media per milestone.
g. Zero fabrication: every vault entry traces to a live URL and a matching hash.

**7. Review gate.** When you believe a–g are met, spin up a fresh-context subagent on Claude Fable (pin model `claude-fable-5`; define `.claude/agents/reviewer.md` if needed) as an adversarial reviewer. Give it ONLY KICKOFF.md, PRD.md, SPEC.md, and the repo — not your conversation, not your summary of what you did. It must independently re-verify each bar item: re-run the validator and the golden set, spot-check 5 random vault entries' URLs and hashes, grep for sandbox flags and leaked secrets — and return per-item PASS/FAIL with evidence. On any FAIL: fix, log it to the progress page, re-review. Maximum 3 cycles; if still failing, stop and present the failures to me honestly rather than looping. Only after a full PASS: post the verdict and gate decision to the progress page and notify me. The decision to proceed past the gate is mine, not yours.
