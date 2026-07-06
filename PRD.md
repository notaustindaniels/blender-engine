# PRD — A Trusted Corpus of Free Procedural Blender Add-ons ("Stage 1: the Vault")

**Status:** Draft v1 · **Owner:** the builder (solo) · **Date:** 2026-07-05
**Companion:** `SPEC.md` (the *how* — all solution and tech decisions live there, not here)

**Program context (for a zero-context reader, two sentences):** A larger program aims to build a Blender-powered, agent-directed video engine — a drop-in alternative to HyperFrames/Remotion that renders *diegetic* data visualization (charts and math as physical, in-world objects and emergent formations). That engine's premise is that free procedural Blender tooling can supply most of its operator library; **this PRD covers Stage 1 only: whether that library can actually be acquired and trusted.**

---

## 1. Problem

The engine design depends on a capability inventory that does not exist. Across an internal taxonomy of procedural niches (~215 static-generation niches in 12 categories plus 72 animation niches; supplied as a kickoff input — see SPEC §0), **it is unknown which niches are served by real, working, free Blender add-ons.** The whole program's viability hangs on that number, and today there is no way to learn it except slowly and unreliably.

What people (the builder, and later, agents) do today to cope:

- **Ad-hoc hunting per need.** Search, download, test by hand, ~10–30 minutes per add-on (builder's estimate, unmeasured), with no durable record — the same add-on gets re-found and re-tested across sessions.
- **Trusting LLM-recalled add-on names without verification.** Demonstrated unreliable inside this program's own working sessions: several project-critical tools (HyperFrames, Pixal3D, SkinTokens) postdated model knowledge entirely and required live verification, and plausible-sounding-but-nonexistent add-on names are a known LLM failure mode. The builder's requirement, stated verbatim, is a library "consisting of real, free blender add on procedural generators" — *real* is the operative word.
- **Buying commercial packs.** Violates the free constraint and still doesn't answer the coverage question.

The ecosystem is structurally hard to inventory, which is why no one has: free procedural tooling is fragmented across at least six source classes (an official extensions platform, GitHub, two marketplaces' $0 tiers, forum threads, blog archives); a 2019 API break (Blender 2.79→2.8x) silently killed a large share of legacy add-ons; a 2024 packaging migration split "bundled" from "platform-hosted"; and marketplace links rot (a repeatedly observed pattern whose actual rate is unquantified — measuring it is itself an output of this work).

The downstream stake is what makes this urgent rather than nice-to-have: Stage 2's director agent will **select operators automatically**. If it selects from unverified names, fabrication stops being an authoring annoyance and becomes a runtime failure mode of the entire engine.

**Switching bar.** Replacing "hunt and hope" is only worth building if niche→operator resolution becomes near-instant and trust becomes machine-checkable. Anything less, and manual hunting remains the rational choice.

**Evidence quality note (honesty over polish):** this is an internal, solo-builder tool. The evidence base is the builder's own research sessions and assistant-verified spot checks — not external user data. Estimates are labeled as estimates throughout.

---

## 2. Hypotheses

**H1 — Coverage & trust.**
We believe that **systematically acquiring and machine-verifying every obtainable free procedural Blender add-on into a local, capability-tagged corpus** will cause **the builder and downstream director agents** to **select only real, working operators instead of recalled or hoped-for ones**, which results in **the engine being buildable on free tooling — or a fast, evidence-based kill of that premise**. We'll know we're right if, within roughly 6 weeks of part-time effort *(time budget is an assumption — confirm with owner)*, a coverage matrix shows **≥60% of taxonomy niches with at least one verification-passing operator** and Stage-2 dry runs surface **zero fabricated dependencies**. We'll know we're wrong if coverage lands **below 40% after exhausting all sources**, or if **fewer than 30% of acquisitions survive verification** (an ecosystem too rotten to build on).

**H2 — Machine usability.**
We believe that **capability metadata generated at verification time** will cause **a zero-context agent** to **resolve a niche to a working operator without human help**, which results in **the corpus being consumable by Stage 2 as designed**. We'll know we're right if a fresh agent resolves **≥8 of 10 sampled niches** to a working operator in **under a minute each** using only the registry. We'll know we're wrong if resolution still requires human search, or if the metadata proves too lossy to choose between candidates.

---

## 3. Success Metrics (outcomes, not activity)

- **Coverage:** % of taxonomy niches with ≥1 verification-passing operator. Provisional targets: ≥60% overall; ≥80% for the four engine-core categories (Terrain, Vegetation, Simulation-adjacent, Nature/FX). *(Targets are provisional until the thin slice calibrates them.)*
  > **Calibration footnote — 2026-07-06 (D-003 R18; this IS the calibration §3 awaited).** The thin slice + native L2 calibrated the coverage metric to **v2**: `(full_pass + recipe_verified) / attainable wave-1 niches`, per-probe-category. Rationale: the corpus consumer is an LLM agent, and only the deterministic tier (full-pass or probe-verified recipe) is capability it can invoke without improvising; `partial`/`recipe_unverified` are runtime landmines. The denominator excludes market-unattainable niches (R15 link-backed audit). The 40% threshold is **unchanged**; the venue moves to after source exhaustion (L5b), per §2 H1. See SPEC §12.4.
- **Fabrication rate:** 0 — every operator invoked downstream traces to a vaulted artifact with a hash and live-verified provenance.
- **Resolution speed:** niche→operator lookup by an agent in <1 minute median (vs. today's ~10–30 min manual hunt, builder's estimate).
- **Freshness:** 100% of corpus entries carry re-verifiable provenance (source URL + content hash), so rot is detectable on demand rather than discovered at render time.

Explicitly **not** metrics: entries downloaded, lines of code, "pipeline shipped."

---

## 4. Wrong Condition & Guardrails

**Wrong / rollback line.** After the thin slice plus the first mass source-lane: if coverage for the two probe categories (Terrain + Vegetation) is **<40%**, or the verification pass-rate of acquisitions is **<30%**, **stop scaling the harvest.** Convene a premise decision instead — paid add-on budget vs. build-from-scratch node tooling — cheaply, before months of crawling get sunk into a dead premise.

**Guardrails (hold even if the metrics look great):**

1. **No execution of harvested code outside a sandbox, ever.** This project mass-runs unvetted internet Python inside an application with full disk access; containment is non-negotiable.
2. **No ToS-violating automation.** Acquisition steps that would require it stay human-gated or fully manual, even at the cost of throughput.
3. **No redistribution.** The corpus is local/private; "free to download" is not "free to republish." No pirated or "nulled" content under any circumstance — a $0 price obtained illegitimately is a hard fail, not a bargain.

A guardrail breach means stop and revisit constraints — never trade a guardrail for coverage.

---

## 5. Non-Goals (deliberate, not deferred)

- Building any Stage-2+ component (scene compiler, metaphor mapper, director agent, render contract).
- Porting, fixing, or maintaining broken/legacy add-ons — record them; don't rescue them.
- Acquiring paid add-ons, even cheap ones.
- Any public mirror, marketplace, or redistribution of the corpus.
- Verification on Windows/macOS (one OS is enough to establish "works headlessly").
- Ranking add-on *quality* beyond pass/fail plus basic signals — deep quality review happens later, driven by actual Stage-2 need.

---

## 6. Open Questions

- The true coverage percentage — the central unknown the thin slice exists to estimate.
- What share of modern procedural tooling ships as node-group asset packs rather than Python add-ons, and how reliably packs can be machine-verified.
- The marketplaces' terms-of-service posture on assisted $0 checkout; whether the second marketplace exposes any API.
- Final taxonomy size (expansion toward 400–600 niches is planned later — does the corpus schema hold up under it?).
- The engine's eventual minimum Blender version, which determines how much legacy-era tooling matters at all.
- The owner's actual disk and time budget (assumed ~100 GB and ~6 weeks part-time; unconfirmed).

---

## 7. Riskiest Assumptions & De-risking Plan

| Assumption | Dominant risk | De-risk before committing |
|---|---|---|
| The free ecosystem covers enough niches to matter | **Value** | Run the thin slice (below) on two taxonomy categories in week 1, *before* any mass crawling |
| Heterogeneous headless verification is automatable at scale — especially node-group packs | **Feasibility** | Spike a golden set: ~10 known-good + ~5 known-bad artifacts; require correct pass/fail on all before scaling the gate |
| Enumeration is tractable (code-search caps, marketplace anti-bot) | **Feasibility** | A one-day yield spike per source lane; measure before building the full lane |
| Assisted $0 checkout is acceptable to marketplaces | **Viability** | Read the ToS first; default to human-gated acquisition; keep a per-source policy switch |
| Verification-time metadata is agent-usable (H2) | **Usability** | Mock resolver test: a fresh agent, 10 sampled niches, registry-only |

**Thinnest end-to-end slice (the actual next step — not "build it all"):** one source lane (the official extensions platform, the cleanest and cheapest) → acquire → verify in a single Blender version → tag → coverage report for Terrain + Vegetation, then a decision gate against §4. This is a full pass through every stage of the loop at minimum width, not a feature-reduced v1.

**Spike-vs-build calls:** the extensions-platform lane is cheap and reversible — build it directly. Node-group-pack verification and marketplace automation carry real unknowns — spike both first.

---

*Solution and technology material discussed during discovery (source lanes, sandbox design, orchestration approach) was deliberately kept out of this document; it lives in `SPEC.md`.*
