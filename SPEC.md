# SPEC — Harvest Harness for the Free Procedural Blender Add-on Corpus (Stage 1)

**Implements:** `PRD.md` H1 (coverage & trust) and H2 (machine usability).
**Audience:** an engineer **and** a zero-context agent building this via an `/archon` (Archon CLI) harness. Every decision is made here; anything left blank, the agent will invent — so nothing is left blank on purpose. Where a decision genuinely can't be made yet, it is listed in §12 as an explicit open decision, not left silent.

> **Reader orientation (Archon).** Archon runs AI workflows in isolated git worktrees. A **workflow** is a YAML DAG of **nodes**; each node is exactly one of `command` (loads `.archon/commands/*.md`), `prompt` (inline AI), `bash`, `script` (`bun` for `.ts`/`.js`, `uv` for `.py`), `loop`, `approval`, or `cancel`. Data flows via `$nodeId.output`. Nodes with satisfied `depends_on` run in parallel. Full authoring guide referenced in §3.4.

---

## 0. Scope Recap & Kickoff Inputs

Build the pipeline that turns "the internet's free procedural Blender add-ons" into a **local, hash-verified, capability-tagged corpus** with a **niche→operator coverage matrix**. Five stages: **Enumerate → Normalize → Acquire → Gate (sandboxed verify) → Map.** Stop at the corpus. No Stage-2 engine code (see PRD §5).

**Kickoff inputs the orchestrating agent must obtain before Node 0 (do not proceed without them):**

1. **`taxonomy.yaml`** — the niche list (~215 static + 72 animation niches across 12 categories). The builder supplies this from the two source documents. If absent, the first command node parses the two provided taxonomy text files into `taxonomy.yaml` matching the §4.1 schema.
2. **`seed-anchors.yaml`** — a hand-verified starter set the agent must NOT trust from memory but re-verify live. Includes at minimum: Sverchok, Tissue, Archipack, Botaniq/Scatter, BagaPie, Modular Tree, JewelCraft, BookGen, Buildify, blender-osm, BlenderGIS, CrowdMaster, Rigacar, Wiggle 2, Camera Shakify, plus Blender's bundled A.N.T. Landscape, Sapling, IvyGen, Cell Fracture, Ocean/Mantaflow, Dynamic Paint. These calibrate the Gate's golden set (§8) and seed GitHub star-graph expansion.

**Definitions locked for this project:**

- **"Free"** = obtainable at $0 through a legitimate path. Includes fully-free, PWYW-with-$0, and free tiers. **Excludes** anything requiring payment, and anything obtained illegitimately (nulled/pirated = hard fail).
- **"Add-on"** = any of: (a) a Python add-on with `bl_info` (pre-4.2 style) in `__init__.py`; (b) a `blender_manifest.toml` extension (4.2+); (c) a Geometry-Nodes **asset pack** distributed as `.blend` node groups. All three are first-class. Excluding (c) would gut the corpus and is prohibited.
- **"Procedural"** = generates or transforms geometry/material via parameters, nodes, or simulation. Static asset dumps with no generative control are recorded but flagged `procedural: false` and excluded from coverage counts.
- **"Operator"** = a callable unit the corpus exposes: a Python `bpy.ops`/panel action, or a named GN node group. One add-on yields many operators.

---

## 1. Technology Stack (versions pinned)

| Layer | Choice | Version / pin | Why |
|---|---|---|---|
| Orchestration | Archon CLI | latest installed; workflows target the DAG schema in §3.4 | Required by the builder; worktree isolation matches per-source parallelism |
| Verification runtime | Blender headless (`blender -b -P`) | **3.6 LTS, 4.2 LTS, 4.5 LTS** (three-version matrix) | Spans the 2.8x→4.x API era and the 4.2 extensions migration named in the PRD |
| Sandbox | Docker + `linuxserver/blender` images (one tag per Blender version) | pinned by digest, not `latest` | Reproducible; per-version isolation |
| Crawlers / glue (Python) | `uv`-run scripts | Python **3.11**; `httpx>=0.27`, `beautifulsoup4>=4.12`, `pyyaml>=6`, `tomli>=2` (stdlib `tomllib` on 3.11 for reads) | Archon `script` nodes run `.py` via `uv`; deps declared per-node |
| Crawlers / glue (TS) | `bun`-run scripts | Bun latest; no extra deps where avoidable | Archon `script` nodes run `.ts`/`.js` via `bun` |
| Browser automation | **Playwright MCP** | current | The builder has it; used for the **two** marketplace lanes only (§6.4) |
| GitHub access | `gh` CLI + REST/code-search API | current; **`GH_TOKEN` via env, never in YAML** | Authenticated pagination; the one lane runnable on a locked-down egress allowlist |
| Corpus store | Filesystem vault + SQLite index (`corpus.db`) | SQLite 3 (stdlib) | Zero-infra, queryable, diffable; JSON manifests are source of truth, DB is the read index |
| Hashing | SHA-256 (stdlib `hashlib`) | — | Content-addressing + rot detection |

No network service, no server, no cloud DB. The corpus is files on the builder's disk.

> **Amendment 2026-07-05 (sandbox base image — reality reconciled with §1, per the working rule).** `linuxserver/blender` publishes **only the current Blender release** (verified live on Docker Hub: every tag is `5.1.x` / `latest`, multi-arch amd64+arm64). It therefore cannot supply the 3.6 / 4.2 / 4.5 matrix. The three probe images are instead built from **official `download.blender.org` release tarballs, each pinned by SHA-256**, on a **digest-pinned** base image (`linux/amd64`, run under emulation on this arm64 host). This is strictly more reproducible than a rolling image. See §12.1(1). Owner-endorsed 2026-07-05.

---

## 2. Architecture & Patterns

### 2.1 The five-stage loop

```
                 ┌────────────────────────────────────────────────┐
                 │  taxonomy.yaml  +  seed-anchors.yaml (inputs)   │
                 └───────────────────────┬────────────────────────┘
                                         │
   [ENUMERATE]  per-source discovery ────┤  → candidates/*.jsonl  (URL, source, license?, ver?)
   [NORMALIZE]  dedup + canonical id ────┤  → normalized.jsonl    (one row per real add-on)
   [ACQUIRE]    fetch to vault ──────────┤  → vault/<id>/<ver>/… + meta.json (hash, provenance)
   [GATE]       sandboxed verify (Docker)┤  → manifests/<id>.json (pass/fail, operators, tags)
   [MAP]        enrich + coverage ───────┘  → corpus.db + coverage-report.md + gaps.md
```

Each stage's output file **is** the next stage's input contract (Archon artifact-chain discipline). A downstream node must be executable from its input artifact alone — no reliance on prior-node memory (all cross-stage nodes run `context: fresh`).

### 2.2 Source lanes (each independently runnable, each its own worktree)

| Lane | Source | Access method | Automation posture |
|---|---|---|---|
| **L1** | Official extensions platform | **JSON API** (`/api/v1/extensions/…`) + direct download URLs | Fully automated. Runs first (cheapest, cleanest, all-free by policy). |
| **L2** | GitHub | Code-search for `bl_info` / `blender_manifest.toml` signatures + `topic:` filters + awesome-list expansion + seed star-graph | Fully automated. Heavy cull expected; runs second. Only lane runnable under a strict egress allowlist. |
| **L3** | BlenderArtists forum (Discourse) | **`.json` on any thread/category URL** — no browser | Automated link-router: extract outbound links, route to L2 or L5, dead links → `graveyard.jsonl`. |
| **L4** | BlenderNation archives | RSS/archive scrape | Automated link-router (same as L3). |
| **L5a** | Marketplace A (Gumroad-class) | **Playwright MCP** for **discovery only**; acquisition human-gated | Discovery automated; $0 checkout requires human approval (ToS + CAPTCHA). Check for a GitHub mirror first (route to L2). |
| **L5b** | Marketplace B (Blender Market / Superhive-class) | Playwright MCP discovery; acquisition human-gated | Same as L5a. Runs last (highest friction; benefits from a mature dedup layer). |

**Lane ordering is deliberate:** L1 → L2 → {L3, L4 in parallel} → L5a → L5b. Rationale in PRD §7 / this section.

### 2.3 Directory structure

```
repo/
├── .archon/
│   ├── config.yaml                 # env injection (GH_TOKEN), worktree base branch
│   ├── workflows/
│   │   ├── harvest-source.yaml      # parameterized single-lane pipeline (the workhorse)
│   │   ├── verify-batch.yaml        # gate-only rerun over an existing vault subset
│   │   └── coverage-report.yaml     # read-only: rebuild matrix + gaps from corpus.db
│   ├── commands/
│   │   ├── parse-taxonomy.md
│   │   ├── enrich-manifest.md       # AI: read README+source → verbs, niche tags
│   │   └── write-coverage.md        # AI: narrative gap analysis on top of computed matrix
│   └── scripts/
│       ├── enumerate/{l1_extensions.py, l2_github.py, l3_forum.py, l4_bnation.py}
│       ├── l5_discover.ts           # Playwright MCP driver (discovery only)
│       ├── normalize.py             # dedup + canonical id
│       ├── acquire.py               # fetch → vault + meta.json (+ prescan hook)
│       ├── prescan.py               # static danger scan (subprocess/urllib/eval/…)
│       ├── build_index.py           # manifests/*.json → corpus.db
│       └── coverage.py              # corpus.db → coverage matrix (deterministic)
├── sandbox/
│   ├── Dockerfile.probe             # base image per Blender version (digest-pinned)
│   └── probe.py                     # runs INSIDE container: install→enable→introspect→render
├── inputs/{taxonomy.yaml, seed-anchors.yaml}
├── vault/<canonical-id>/<version>/  # the artifacts + meta.json   (git-ignored; large, private)
├── candidates/  normalized.jsonl  manifests/  graveyard.jsonl
├── corpus.db
└── reports/{coverage-report.md, gaps.md}
```

### 2.4 Naming conventions

- **Canonical add-on id:** `slugify(author + "__" + name)`; lowercase, `[a-z0-9_-]`. Collisions resolved by source priority (§4.2), hash tiebreak.
- **Vault path:** `vault/<canonical-id>/<version>/`; original filename preserved inside.
- **Scripts:** verb-first snake_case (`enumerate_l1`, `acquire`, `build_index`).
- **Archon nodes:** `stage-lane` (`enumerate-l1`, `acquire-fetch`, `gate-verify-42`).
- **Manifests:** `manifests/<canonical-id>.json`.

---

## 3. Behavior Specifications (the fuzzy words, pinned)

### 3.1 What "verification-passing" means (the core definition)

An operator **passes** for a given Blender version iff, inside the sandbox, ALL hold:

1. **Installs** — `bpy.ops.preferences.addon_install` (or `bpy.ops.extensions.*` for 4.2+ extensions, or `.blend` asset-link for packs) raises no exception.
2. **Enables** — `bpy.ops.preferences.addon_enable` succeeds with no traceback captured on stderr.
3. **Registers ≥1 introspectable operator** — post-enable diff of `dir(bpy.ops.<module>)` / registered node groups is non-empty.
4. **Smoke-runs** — at least one detected operator/node group executes on an empty scene (or its documented minimal input) without exception, producing a non-empty mesh/curve/material delta.
5. **Renders a thumbnail** — a single EEVEE frame renders to PNG without crashing Blender.

**Result states:** `pass` (all 5), `partial` (1–3 pass, 4 or 5 fail — records what worked), `fail` (install/enable fails), `quarantine` (crashed the container or timed out), `legacy` (declares only pre-2.8 API and never enables). Only `pass` and `partial` count toward PRD coverage; `partial` is flagged in reports.

### 3.2 Per-version behavior

Every artifact is verified against **all three** Blender versions. The manifest records a per-version result vector. An operator "covers" a niche if it passes on **≥1** version. `compat: [3.6?, 4.2?, 4.5?]` booleans are stored so Stage 2 can later demand a specific version.

### 3.3 Dedup / "same add-on" rule (Normalize)

Two candidate rows are the **same add-on** if any: identical content hash; identical resolved GitHub repo; OR (fuzzy name-match ≥0.9 AND same author). On match, keep the highest-priority source (§4.2), union the discovery metadata, and record all source URLs in `meta.json.sources[]`. This is why the same tool surfacing on L1+L2+L5 collapses to one row.

### 3.4 Danger prescan (gate precondition — must pass before any container run)

`prescan.py` statically greps each artifact's Python for: `subprocess`, `os.system`, `urllib`, `requests`, `httpx`, `socket`, `eval(`, `exec(`, `__import__`, `ctypes`, `open(` with write modes outside temp, and any base64-decode-then-exec pattern. **Any hit → status `needs_review`; the artifact does NOT enter the container until a human clears it.** GN-only `.blend` packs with no Python skip most of this but still get a driver-expression scan (drivers can run Python). Rationale: PRD guardrail #1.

Authoritative Archon references the agent should read before writing workflows: the workflow-authoring DAG guide, the parameter matrix (which field is valid on which node type), and the good-practices/anti-patterns guide. These define valid node fields, `trigger_rule` semantics, `context: fresh` state-passing, and the `interactive: true` requirement for approval gates.

---

## 4. Data Model (decisions made, not deferred)

### 4.1 `taxonomy.yaml`

```yaml
categories:
  - id: terrain
    name: "Terrain & landscape"
    niches:
      - id: terrain_generator
        aliases: ["heightmap", "A.N.T. landscape"]
        verbs: [generate]          # physical-verb tags (see §4.4)
        core: true                 # engine-core category?
```

### 4.2 `meta.json` (one per vaulted artifact — source of truth for provenance)

```json
{
  "canonical_id": "aaron__antlandscape",
  "name": "A.N.T. Landscape",
  "author": "Aaron",
  "version": "0.1.9",
  "sources": [
    {"lane": "L1", "url": "https://…", "fetched_at": "2026-07-05T…Z"}
  ],
  "license": "GPL-2.0-or-later",
  "license_source": "manifest|readme|assumed",
  "addon_type": "python_bl_info | extension_manifest | gn_pack",
  "file": "antlandscape.zip",
  "sha256": "…",
  "declared_blender_min": "3.0.0",
  "procedural": true
}
```

**Decision — license capture:** read from `blender_manifest.toml` (authoritative) → SPDX in README → else `assumed` with a flag. Never guess a specific license silently; `assumed` blocks nothing at Stage 1 but is surfaced, because redistribution posture (PRD guardrail #3) depends on it later.

### 4.3 `manifests/<id>.json` (verification result + capability — Gate + Map write this)

```json
{
  "canonical_id": "aaron__antlandscape",
  "verify": {
    "3.6":  {"state": "pass", "operators": ["mesh.landscape_add"], "render_ok": true},
    "4.2":  {"state": "pass", "operators": ["mesh.landscape_add"], "render_ok": true},
    "4.5":  {"state": "pass", "operators": ["mesh.landscape_add"], "render_ok": true}
  },
  "operators": [
    {"kind": "bpy_op", "id": "mesh.landscape_add",
     "params": [{"name": "subdivision_x", "type": "int"}],
     "verbs": ["generate"], "niches": ["terrain_generator", "dune_generator"]}
  ],
  "prescan": "clean",
  "enriched_by": "ai|manual",
  "notes": "…"
}
```

**Decision — two files, not one.** `meta.json` (provenance, immutable after acquire) vs. `manifests/*.json` (verification+capability, rewritten on re-verify). Keeps a corrupt re-verify from destroying provenance. Rejected alternative: single blob — loses that safety and makes re-verification destructive.

### 4.4 Physical-verb vocabulary (fixed enum — the bridge to Stage 2)

`generate, scatter, trace, stack, accumulate, branch, fill, deplete, reveal, illuminate, simulate, deform`. Chart primitives map to verbs downstream; storing verbs now means Stage 2's metaphor mapper is a query, not a rewrite. This enum is frozen for Stage 1; extensions require an explicit decision.

> **Amendment 2026-07-05 (kickoff decision, per the §12 freeze rule):** the enum is extended by exactly **one** verb — **`aggregate`** (many small units self-organize into a target shape; required by the wave-2 emergent-formation tier). Full v2 enum: `generate, scatter, trace, stack, accumulate, branch, fill, deplete, reveal, illuminate, simulate, deform, aggregate`. Additionally, **pure-utility niches may carry `verbs: []`** (no physical verb applies — e.g. `sound_drive`, `sim_bake`, camera utilities). No other extension.

### 4.5 `corpus.db` (SQLite — the read index, rebuilt from JSON, never hand-edited)

Tables: `addons(canonical_id PK, name, author, license, addon_type, procedural)`; `operators(id, canonical_id FK, kind, op_id, verbs_json)`; `verify(canonical_id FK, blender_ver, state, render_ok)`; `coverage(niche_id, canonical_id FK, operator_id, blender_ver)`; `graveyard(url, reason, seen_at)`. **Decision:** JSON manifests are canonical; `build_index.py` regenerates the DB idempotently, so the DB is disposable and always reproducible.

---

## 5. Component Specifications

### 5.1 `probe.py` (runs inside the container — the heart of the Gate)

Contract: argv = artifact path + Blender version tag. Steps: prescan-already-clean assertion → install → enable (capture stderr) → introspect registered ops/node groups → for each, attempt a guarded smoke-run on an empty scene → render one EEVEE frame → emit a JSON result to stdout matching §4.3's `verify` shape. **Every bpy call wrapped in try/except; a crash is a `quarantine` result, never a harness abort.** Hard per-artifact wall-clock cap: **120 s** (SIGKILL the container past it → `quarantine`).

### 5.2 Sandbox (`Dockerfile.probe`) — non-negotiable settings

- **`--network none`** on every probe run (PRD guardrail #1).
- Read-only mounts except one scratch tmpfs; artifact mounted read-only.
- Non-root user; dropped capabilities; memory + pid limits.
- One container invocation per artifact per version (no state bleed between add-ons).
- Base image pinned by **digest**.

### 5.3 Enumerators — per-lane stop conditions (so lanes terminate)

- **L1:** paginate the full API; done when `next` is null.
- **L2:** code-search is capped by the API — partition queries by signature × language × star-bucket to stay under result limits; expand seed star-graph to **depth 2**; hard stop at a configurable candidate ceiling (default 5,000) to bound cost.
- **L3/L4:** crawl the target category to a configurable page depth (default: full Released-Scripts category / 24 months of archives).
- **L5:** discovery walks $0-filtered listing pages until pagination ends or a ceiling (default 1,000/marketplace) is hit.

### 5.4 Playwright MCP usage (L5) — strict boundaries

Discovery only: navigate $0-filtered listings, extract {product URL, creator, title, description, price==0 assertion}. **No automated purchase/checkout.** Acquisition is a **separate human-gated Archon `approval` node**: the workflow pauses, the human completes $0 checkouts in batch, then a follow-up node sweeps the buyer's library page for durable re-download links. Before queueing any checkout, `l5_discover.ts` checks the product page for a GitHub link and, if present, reroutes to L2 (free, automatable, no checkout).

---

## 6. Archon Harness Specification

### 6.1 `harvest-source.yaml` (the parameterized workhorse — one run per lane)

Node chain (all cross-stage nodes `context: fresh`, reading their upstream artifact):

| Node | Type | Reads → Writes | Notes |
|---|---|---|---|
| `enumerate` | `script` (uv/bun per lane) | source → `candidates/<lane>.jsonl` | Lane selected by `$ARGUMENTS`; L5 uses the Playwright driver |
| `normalize` | `script` (uv) | `candidates/*` + existing `normalized.jsonl` → updated `normalized.jsonl` | Dedup rule §3.3 |
| `prescan` | `script` (uv) | vault-pending artifacts → sets `needs_review` flags | Gate precondition |
| `acquire-gate` | `approval` | — | **Only present for L5**; batches $0 checkouts. Requires workflow-level `interactive: true` |
| `acquire` | `script` (uv) | `normalized.jsonl` → `vault/…` + `meta.json` | L1–L4 auto; L5 post-approval |
| `verify` | `bash` | vault artifacts → `manifests/*.json` | Loops the 3-version Docker matrix via `probe.py`; deterministic, no AI |
| `enrich` | `command` (`enrich-manifest`) | `manifests/*` + README/source → verbs+niches | AI where judgment is real; `model: sonnet` |
| `index` | `script` (uv) | `manifests/*` → `corpus.db` | Idempotent rebuild |
| `report` | `command` (`write-coverage`) | `corpus.db` → `reports/*` | Narrative on top of computed matrix |

**Determinism split (Archon good-practice #1):** enumerate/normalize/prescan/acquire/verify/index are `bash`/`script` (right answers a computer produces). Only `enrich` and `report` are AI nodes — the two steps needing genuine judgment. Never ask an AI node to "run the verifier and tell me if it passed."

**`interactive: true`** is set at workflow level (required for the L5 `approval` gate to reach the web UI). **`worktree.enabled: true`** — the harvest writes files; force isolation. Cheap models for any glue; `sonnet` for enrich/report.

### 6.2 `verify-batch.yaml`

Gate-only rerun over a vault subset (e.g., after adding a 4th Blender version or fixing `probe.py`). `worktree.enabled: false` acceptable if it only writes manifests/DB and touches no tracked source. Nodes: `verify → index → report`.

### 6.3 `coverage-report.yaml`

Read-only. `worktree.enabled: false`. `coverage.py` (deterministic matrix) → `write-coverage` (AI narrative + `gaps.md`). This is the command run to answer "where are we against PRD §3 targets."

### 6.4 Parallelism

Each lane is `archon workflow run harvest-source --branch harvest/l1 "L1"` in its own worktree, so L1 and L2 progress simultaneously without collision. Normalize/index are last-write-wins per lane; a final `coverage-report` run reconciles. **Never** combine lanes in one invocation.

### 6.5 Secrets

`GH_TOKEN` and any marketplace session creds come from `.archon/config.yaml`'s `env:` block or Web UI project env — **never in workflow YAML, never committed.** MCP configs use `$ENV_VAR` expansion.

---

## 7. Security (mandatory baseline)

1. **Never commit secrets.** `GH_TOKEN`, marketplace cookies → env injection only. `.gitignore` covers `vault/`, `*.db`, any `*session*`, `.env`.
2. **Sandbox all harvested-code execution.** `--network none`, read-only mounts, non-root, capability drops, resource limits, per-artifact container. No exceptions — this is the project's single largest risk surface (mass-running unvetted internet Python).
3. **Static prescan before dynamic run** (§3.4). Dangerous-API hits gate on human review.
4. **Input validation on all crawled data.** URLs validated before fetch; downloads size-capped; archives zip-slip-checked before extraction; never `eval` crawled content.
5. **ToS & legal.** Per-lane automation policy switch; marketplace acquisition human-gated by default; no redistribution of vaulted artifacts; hard-fail on any illegitimately-$0 (nulled/pirated) source.
6. **Provenance integrity.** Every artifact SHA-256'd at acquire; re-hash on demand detects tampering/rot. An operator with no live-verifiable provenance is inadmissible downstream (directly enforces PRD's zero-fabrication metric).

Row-level security / webhook verification: **N/A** — single-user, local, no server, no inbound webhooks. Stated explicitly so the agent doesn't invent an auth layer.

---

## 8. Testing (what, and why)

- **Golden set (gates the whole Gate).** ~10 known-good seed anchors + ~5 known-bad (a deliberately broken zip, a 2.7x-only legacy add-on, a non-procedural asript dump, a GN pack, a driver-Python pack). `probe.py` MUST return the correct state for every one before the Gate is trusted at scale. *Why:* the PRD's feasibility risk lives here; a miscalibrated verifier corrupts every coverage number.
- **Dedup unit tests.** Same add-on via three synthetic source rows → one normalized row. *Why:* dedup is the difference between a real coverage count and an inflated one.
- **Prescan tests.** Craft artifacts hitting each dangerous pattern → each flags `needs_review`; a clean one passes. *Why:* a false-negative here is a sandbox-escape exposure.
- **Idempotency test.** Run `index` twice → identical `corpus.db` content. *Why:* the DB must be disposable/reproducible.
- **Resolver mock (H2 acceptance).** Fresh agent, registry-only, 10 sampled niches → ≥8 resolved to a passing operator in <1 min each. *Why:* this is literally PRD H2.
- **Thin-slice acceptance (H1 gate).** L1 lane end-to-end over Terrain + Vegetation → coverage report → compare to PRD §4 wrong-condition thresholds.

Test structure: `pytest` for Python units; golden-set + thin-slice are integration runs invoked by `verify-batch` against a fixtures vault.

---

## 9. Build Sequencing (in order, each with a done-signal)

1. **Repo + Archon init + inputs.** `.archon/` scaffold, `taxonomy.yaml` + `seed-anchors.yaml` present. **Done:** `archon validate workflows harvest-source` runs clean (even against stubs).
2. **Sandbox + `probe.py` + golden set.** **Done:** golden set returns 100% correct pass/fail/legacy/quarantine states across all three Blender versions. *(This is a spike — see §10.)*
3. **L1 thin slice (PRD's thinnest slice).** Full loop, extensions lane, Terrain+Vegetation only. **Done:** `reports/coverage-report.md` exists with real numbers; decision-gate against PRD §4.
4. **Normalize/index/coverage hardening.** Dedup + idempotency tests green. **Done:** re-running L1 adds nothing new.
5. **L2 (GitHub) at scale.** **Done:** candidate ceiling respected; legacy cull rate measured (feeds PRD pass-rate metric).
6. **L3 + L4 link-routers.** **Done:** outbound links routed; `graveyard.jsonl` populating.
7. **L5a then L5b (Playwright).** **Done:** discovery populated; human-gated acquisition loop exercised once end-to-end.
8. **Full coverage report + gap analysis.** **Done:** matrix vs. all PRD §3 targets; `gaps.md` lists zero-operator niches for Stage-2 recipe planning.

Gate after step 3 is mandatory (PRD wrong-condition). Steps 5–7 proceed only if the premise survives.

---

## 10. Spike-vs-Build Decisions

- **SPIKE first — headless verification of heterogeneous add-ons** (esp. GN packs and the smoke-run heuristic). Highest feasibility unknown; prove on the golden set before scaling. (Step 2.)
- **SPIKE first — each enumerator's real yield** (GitHub code-search caps; marketplace anti-bot). One-day yield probe per lane before building the full lane.
- **SPIKE first — Playwright $0 discovery** against one marketplace; confirm extractability and ToS posture before building L5b.
- **BUILD directly — L1 lane, normalize, index, coverage.** Cheap, reversible, well-understood; just build and roll back via worktree if wrong.

---

## 11. Quality Checks (run before calling the spec done)

- ✅ Versions pinned (Blender 3.6/4.2/4.5; Python 3.11; image digests) — not just named.
- ✅ Every fuzzy word defined: "verification-passing" (§3.1), "same add-on" (§3.3), "free/procedural/operator" (§0), "dangerous API" (§3.4).
- ✅ Security baseline present: no-commit-secrets, sandbox specifics, prescan, input validation, ToS/no-redistribution.
- ✅ Data-model "two valid options" resolved: two-file split (§4.3), JSON-canonical/DB-derived (§4.5), license-capture precedence (§4.2).
- ✅ Test plan covers what **and** why, tied to PRD guardrails and hypotheses.
- ✅ No PRD/intent restated — coverage *targets* are referenced, not re-argued.
- ✅ No silent agent-discretion gaps: open decisions named in §12; verb enum + result states frozen.

---

## 12. Open Engineering Decisions (named, not silently left blank)

1. **Exact marketplace domains** for L5a/L5b and each one's API existence — pending the ToS read (§10 spike). Until resolved, L5 stays discovery-only.
2. **GN-pack smoke-run heuristic** — how to auto-invoke a node group with no documented inputs (best-effort: instance on default geometry and check for a mesh delta). Finalize during the Step-2 spike; record the chosen heuristic in `probe.py` comments.
3. **Candidate/graveyard ceilings** (defaults 5,000 / 1,000) — tune after Step-5 yield data.
4. **Fourth Blender version?** If Stage 2 pins a newer/older release, add it via `verify-batch` — schema already supports N versions.
5. **`enrich` model tier** — `sonnet` assumed; drop to a cheaper tier if README-reading proves shallow enough, or raise if verb/niche tagging is unreliable.

### 12.1 Dated amendments — 2026-07-05 kickoff (reality reconciled with SPEC)

Logged per the working rule: *if reality contradicts the SPEC, update the SPEC with a dated note — never silently diverge.*

1. **Sandbox images (amends §1).** `linuxserver/blender` ships only the current release (all tags `5.1.x`/`latest`), so "one tag per Blender version" cannot yield 3.6/4.2/4.5. The three-version matrix is built from **official `download.blender.org` tarballs pinned by SHA-256** on a **digest-pinned** base image. Strictly more reproducible. Owner-endorsed. (See the §1 note.)
2. **Verb enum (amends §4.4).** Extended by exactly one verb, **`aggregate`**; `verbs: []` permitted for pure-utility niches. (See the §4.4 note.)
3. **Taxonomy delivered, not parsed (amends §0).** `inputs/taxonomy.yaml` (v2) is supplied by the owner as a finished file in the §4.1 schema + additive keys. The `parse-taxonomy` step is therefore a **validator** (schema + meta-count checks, tolerant of unknown keys), not a parser. Parse-from-source stays the documented fallback if the file is ever absent.
4. **Wave isolation (amends §3, §4.1).** Niches carry an additive `wave` key (absent ⇒ 1). **PRD §3/§4 targets and the step-3 gate compute on wave-1 niches ONLY** — denominators from `meta` (`wave1_present=269`; Terrain+Vegetation wave-1 = 36+23 = **59**). Wave-2 (59 niches across 4 new categories: `emergent_formation`, `diegetic_dataviz`, `physical_process_media`, `light_shadow_data`) gets a **separate** coverage table and never moves the gate.
5. **Corrupted-but-counted niches (amends §4.1).** 16 wave-1 niches were unrecoverable from the owner's source and are recorded as per-category `unrecovered_count` + `unrecovered_hints` — deliberately NOT placeholder entries. Coverage denominators use **present** niches (`meta.present_total=328`). `reconstructed: true` entries are usable now; the owner will confirm them against the pristine original; ids **freeze at the first coverage run**.
6. **New report artifact (amends §2.3, §6.3).** `coverage-report` also emits `reports/taxonomy-proposals.md` — niches implied by harvested add-on tags that map to no existing niche. Owner-approved proposals become wave 3; nothing is auto-added.

### 12.2 Dated amendments — 2026-07-06 (owner GO to L2; riders folded in)

The owner reviewed the step-3 gate and authorized L2 (SPEC §9 step 5), spike-first. These implement the owner's riders and keep the SPEC in sync with the code.

1. **Version-aware verify matrix (amends §3.2, §6.1).** The Gate no longer probes Blender versions an artifact declares impossible: a `blender_manifest.toml` extension skips 3.6 (no extension system pre-4.2), and any artifact skips versions below its `blender_version_min`. Skipped cells are a new result state **`skipped_incompatible`** — NOT `fail` — so arithmetic and reports distinguish "can't run here" from "ran and failed." (Excluded from the pass-rate denominator.)
2. **Timeout is its own state with one retry (amends §3.1, §5.1).** A wall-clock timeout is now **`quarantine_timeout`** (distinct from a crash `quarantine`), retried ONCE at 2× the cap (both the outer subprocess timeout and the probe's internal SIGALRM scale via an argv cap). Persistent timeouts under emulation feed the native-probe decision (#5). *Observed:* large add-ons (`bagapie`, `terrain-mixer`@4.5) actually **crash** (`quarantine`, no result emitted — likely OOM/segfault under emulation), which the timeout-retry correctly does not mask.
3. **Prescan throughput (amends §3.4).** The human gate is unchanged in strength. A dated `policies/prescan-allowlist.yaml` downgrades almost-always-benign patterns (Blender node `socket`, preset `open`-writes, driver-expression) from gating to informational — the exec/network-capable patterns (`subprocess`, `eval(`, `exec(`, `__import__`, `urllib`, …) can **never** be allowlisted. Review is batched into one `reports/prescan-findings.md`, and the **false-positive rate** is tracked as a metric.
4. **Honest coverage composition — probe-recipe backlog (rider 7).** Coverage tables split **full-pass vs partial-only**. A niche covered only by `partial` operators (registered + rendered, but not auto-drivable to a geometry delta headless — typically a dialog/modal generator) is logged to `reports/probe-recipes.md` as a **probe-recipe TODO** (a per-operator hint to upgrade partial→pass), never silently counted identical to a pass. Partials still count toward coverage (SPEC §3.1) but are never conflated with full passes.
5. **Native amd64 probe path — OWNER DECISION (not self-approved).** The L2 yield spike shows the GitHub ecosystem is large (tens of thousands of `bl_info` hits; ~1,800 topic-tagged repos), and large add-ons crash under amd64 emulation on this arm64 host. Verifying L2 at scale needs a native amd64 sandbox host (cloud/CI). This is surfaced to the owner as a decision; no infrastructure is provisioned without approval. Until then, L2 verification is a bounded, honestly-capped emulated sample.
6. **PRD §4 re-evaluation point (R1).** L2 concludes with an updated coverage report and a formal PRD §4 re-evaluation on the L1+L2 union (Terrain+Vegetation wave-1), with the whole-taxonomy wave-1 number alongside for information. Steps 6–8 begin only after that, on owner say-so.
7. **L2 enumeration orders, never excludes (R11).** Stars / last-commit may PRIORITIZE probe order (so coverage climbs fastest) but NEVER filter enumeration — the long tail is the point. Legacy 2.7x-era candidates still enumerate, still pass the prescan gate, and are recorded in `graveyard.jsonl` (with a reason); archived and no-add-on-signature repos are likewise graveyard **records**, never silent skips. The probe *bound* (native-probe decision, #5) applies to how many are verified now, ordered by stars — not to what is enumerated.
8. **BlenderKit = backlog lane L6 (R10), NOT now.** Candidate lane **L6**: public API with a free-account key, likely richer in assets than tools, ToS on bulk download unverified. Spike its ToS + yield ONLY after L2's gate evaluation. No build in this phase — this note is the only artifact.

### 12.3 Dated amendments — 2026-07-06 (D-002: repair the instrument, then re-evaluate)

Owner decision D-002: the PRD §4 coverage line is crossed but the instrument is not decision-grade; scaling stays PAUSED (no L3/L4/L5) until a D-003 entry disposes of it (R17). Riders R12–R17.

1. **R12 prescan repair + blocked-five review (amends §3.4).** The danger prescan now **skips test files** (`tests/`, `test_*.py`, `*_test.py`) and **full-line comments**, removing context false-positives (a commented-out `# exec(` or a test-harness `exec(compile(...))` no longer gate). Exec/network patterns remain un-allowlistable. The 5 prescan-blocked L2 artifacts were source-reviewed: 2 cleared (`sorcar`, `trailprint3d`), 3 stay recorded-blocked (`reports/prescan-blocked-findings.md`) — `blender-python-nodes` is a **confirmed arbitrary-Python executor** whose operators are inadmissible for the corpus.
2. **R14 recipes are first-class but claims-until-checked (amends §2.2, §4).** Registry **recipe** entries map a niche → a composition of vaulted operators / built-in Blender features. Coverage tables split `recipe_verified` (a probe recipe actually ran) vs `recipe_unverified` (documented composition, not machine-checked) — never conflated, never fabricated. Encoded in the coverage path + CLAUDE.md.
3. **R16 pass-rate reported two ways (amends §3, §4.5).** The acquisition pass-rate is reported both **of-probed** (excludes `skipped_incompatible` + `needs_review`) and **of-all-acquisitions** (every vaulted artifact is a denominator), so a bounded/blocked sample cannot flatter the number.
4. **R13 native amd64 probe path — Option A APPROVED 2026-07-06 (amends §1, §5.2).** Owner approved GitHub Actions at \$0. Workflow `.github/workflows/native-probe.yml` built: native amd64 `ubuntu-latest`, re-acquires archives from public URLs (vault stays git-ignored / off GitHub), probes in the unchanged `--network none` sandbox, uploads manifests+coverage. Runs the full L1+L2 matrix + emulation-suspects. Running it requires the workflow pushed to the public `blender-engine` remote (see §12.3 note on push mechanics).

### 12.4 Dated amendments — 2026-07-06 (D-003: ruler redefined stricter, threshold kept, harvest greenlit)

Owner decision D-003 (judged by the owner's advisor-agent at delegation; owner retains veto). Premise NOT falsified (native pass-rate clears 30% both ways). Riders R18–R24.

1. **Gate metric v2 (R18, amends §3, §4.5; PRD §3 footnote).** The governing coverage metric is now **`(full_pass + recipe_verified) / attainable wave-1 Terrain+Veg niches`** — STRICTER than v1: `partial` and `recipe_unverified` do NOT count (a partial operator is a runtime landmine an agent cannot improvise around). Denominator = **54 attainable** niches (the R15 link-backed audit; the **5 unattainable** — `karst_formation`, `coral_atoll_generator`, `coral_generator`, `kelp_forest_generator`, `anemone_generator` — are listed, excluded, revisited only if evidence changes). Threshold **unchanged at 40%**. Current v2 reading **5/54 = 9.3%** is recorded as the starting point (lower than the old 13.6% — the redefinition did not flatter). v1 stays reported as legacy. Encoded in `coverage.py` (`gate_v2`).
2. **Verdict venue + tripwire (R19, amends §3, §9).** The final 40%-v2 evaluation occurs **after L5b** (source exhaustion, per PRD §2 H1's own wording). The §4 early stop-line is **retired as satisfied-in-function** (it fired twice, forced instrument repair, did its job). Pass-rate **of-all-acquisitions** is a **live tripwire at every lane gate**: `<30%` at any lane → pause + owner escalation. Encoded in `coverage.py` (`tripwire`).
3. **Steps 6–8 GREENLIT (R20, amends §9).** L3 → L4 → L5a → L5b per SPEC order, **zero guardrail loosening**: L5 acquisition stays human-gated (ToS read first, approval-node checkout batches, GitHub-mirror rerouting before any checkout, receipts creator-visible). No SPEC change to the guardrails — they hold exactly as written (§5.4, §7).
4. **Recipe-probe mode (R21, amends §5.1, §12).** `probe.py` gains a recipe mode: compose vaulted operators / built-ins in the same sandbox (drive newly full-passed generative operators, or `EXEC_DEFAULT` with explicit params). Recipes count toward the gate ONLY when `recipe_verified`. Verify the 5 seeded during the L3/L4 window; enrich recipe candidates from every new full-pass operator.
5. **Verb×medium grid (R22, amends §4.5).** `coverage.py` emits verified-operators-per (physical verb × medium: ground/water/air/urban/organic/abstract) — informational now, the intended Stage-2 metaphor-resolver entry gate later. Niche→medium map in `inputs/niche-medium.yaml`.
6. **Paid-vs-build trigger (R23) + delegation accountability (R24)** → CLAUDE.md standing rules. No paid acquisition ever without an owner D-entry; the 2 `none` niches (karst, coral_atoll) go to the Stage-2 recipe/from-scratch backlog now.
7. **L3/L4 built (R20, amends §2.2, §5.3).** L3 = BlenderArtists Discourse link-router — `.json` on the "Released Scripts and Themes" category (`coding/released-scripts-and-themes/50`, discovered live); extracts OP outbound links, routes github/gitlab→L3 repo candidates, marketplace→`candidates/L5_pending.jsonl` (owner-gated), dead→`graveyard.jsonl`. L4 = BlenderNation — its wp-json REST API is **WAF-blocked (403)**, so L4 uses the **RSS feeds** (`/feed/`, tag/category feeds), exactly the "RSS/archive scrape" §2.2 specifies; same routing. Both are automated link-routers, no browser. L5-pending links accumulate for the human-gated L5 lane (R20).
8. **Gumroad anti-scraping (amends §5.4).** Gumroad ToS §14 forbids automated "spiders, robots, scrapers, crawlers … to scrape or download data from any web pages." Therefore **L5a discovery is NOT automated Playwright scraping** (stricter than §5.4 assumed): discovery+acquisition is fully human-gated; mirror-checking is via web search, not page scraping. Superhive ToS is WAF-unreadable → default human-gated, owner manual-read flagged. Full findings: `policies/marketplace-tos.md`.

### 12.5 Dated amendments — 2026-07-07 (D-004: asset lanes A1/A2/A3, off the gate)

Owner decision D-004: ArtStation/Fab/Sketchfab join as **A-lanes** (asset lanes) — Stage-2 scene assets, NOT tool coverage. Riders R25–R29.

1. **A-lane semantics (R25, amends §4, §4.5).** A-lane entries carry `entry_type: asset_pack`, `procedural: false` (expected, fine). They are **excluded from gate v2 and the verb×medium grid** (they host assets, not operators) — enforced in `coverage.py` (only operator-bearing manifests reach coverage) and tracked in a separate **asset-inventory report** by scene-asset category. **Asset-fed recipes** (asset + procedural composition) ARE legitimate gate contributors — but ONLY as `recipe_verified` through the standard R21 probe, never by assertion.
2. **License load-bearing (R26, amends §4.2).** Every A-lane item records `usage_license` (cc0 / cc-by / cc-by-nc / cc-by-nd / standard / engine-locked) + format + attribution string. **Engine-locked licenses and `.uasset`-only downloads → graveyard** (useless to us, reason recorded). **NC/ND → acquired but SEGREGATED** pending an owner call on engine-output commerciality (parked question). cc-by attribution recorded per item for Stage-2 credits.
3. **Asset probe variant (R27, amends §5.1).** `probe_asset.py`: headless import (gltf/glb/fbx/blend) → non-empty geometry → workbench render thumbnail → license+attribution captured. Pure mesh formats **skip the code prescan**; `.blend` assets still get the driver/embedded-script scan (blend can carry Python).
4. **Automation posture per source (R28).** A1 Sketchfab — official Download API, automatable for CC content, `SKETCHFAB_TOKEN` via `.archon/.env` (never chat/YAML). A2 ArtStation / A3 Fab — ToS-check pass posted BEFORE any discovery automation; checkout-shaped steps human-gated like L5. See `policies/marketplace-tos.md`.
5. **Priority protection (R29).** A1 discovery may run in parallel (cheap, API-based); A2/A3 begin only after the first L5a approval batch ships. Any attention conflict resolves for L5a/L5b (the gate-v2 critical path). The marine-flora recipe experiment (R25 exception) is authorized as soon as suitable CC0/CC-BY specimens land.

### 12.6 Dated amendments — 2026-07-07 (D-005: the walk-away contract; batch-driven autonomy)

Owner decision D-005: involvement converts interrupt-driven → batch-driven. Agent works every authorized lane to exhaustion, queues owner-gated items in `OWNER-QUEUE.md`, surfaces ONE consolidated R34 session. Riders R30–R34.

1. **Pre-authorizations under existing guardrails, zero new permissions (R32).** (a) **A2 ArtStation + A3 Fab** activate after batch #1 ships, EACH gated on its own ToS read — a ToS that forbids the plan **DROPS the lane with a recorded finding, no escalation**. (b) **L5b Superhive** discovery + batch prep proceed under the recorded conservative posture (search-derived URLs, human checkout queued). (c) The **recipe drive** + further **asset-fed recipe experiments** continue for any attainable niche. (d) **taxonomy-proposal** + **re-verification** workflows run on schedule.
2. **Owner-queue discipline (R30) + walk-away done (R34)** → CLAUDE.md + `OWNER-QUEUE.md` + the `reports/prd4-final.md` report contract. Dispositions (R31): fern approved+executed by owner; **river DENIED** (unconfirmable price = no); marine-flora asset-fed recipe experiment **APPROVED** (CC-BY only; by-nc segregated, out of recipes).
3. **Attainable set grows with verified paths.** A niche that earns a `full_pass` or `recipe_verified` is attainable BY DEFINITION — coverage v2's denominator = the R15 attainable set ∪ any niche with a verified path. So converting a paid_only/none niche via an asset-fed recipe (R25) both adds it to the numerator and the denominator, honestly.

### 12.7 Dated amendments — 2026-07-07 (D-006 R35(d): marine-trio conversion recorded; amends §12.4(1))

`coral_generator`, `kelp_forest_generator`, `anemone_generator` — listed `paid_only`/unattainable in the §12.4(1) R15 audit — earned `recipe_verified` via CC-BY asset-fed recipes (R25/R21; artifacts `marine__{coral,seaweed,anemone}-ccby`, each CC-BY-4.0 commercial with attribution + SHA-256 captured, machine-checked in `reports/recipe-verify.json` and independently re-verified by the D-006 R35 review). Per §12.6(3) the general rule now has its concrete instance: these 3 enter the attainable base. **Gate-v2 denominator 54 → 57**; the §12.4(1) unattainable list shrinks **5 → 2** — only `karst_formation` and `coral_atoll_generator` remain unattainable (Stage-2 build-from-scratch backlog per D-006 R38). Both numerator and denominator grew; current reading **17/57 = 29.8%**.

Keep this spec in sync as implementation reveals reality — the code is a lossy projection of it, not the other way around.
