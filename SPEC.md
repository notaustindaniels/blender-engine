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

Keep this spec in sync as implementation reveals reality — the code is a lossy projection of it, not the other way around.
