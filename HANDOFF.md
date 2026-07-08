# HANDOFF.md — the Stage-1 → Stage-2 consumption contract (D-007 R43)

Stage 1 built a **local, hash-verified, capability-tagged corpus** of free procedural Blender tooling.
This file is the interface Stage-2 (the engine) consumes it through. **This repo becomes a read-only
dependency (registry + vault) — not a workspace (R45).** Everything below is machine-readable and
re-derivable from committed artifacts.

## 1. What the corpus is (final numbers)
- **Gate v2 (Terrain+Veg wave-1): 23/57 = 40.4%** — `(full_pass + recipe_verified) / attainable`.
  12 `full_pass` + 11 `recipe_verified`. Reproduce: `uv run .archon/scripts/build_index.py && uv run .archon/scripts/coverage.py`.
- **Pass-rate** (premise health): 63.2% of-probed / 50.0% of-all-acquisitions — both clear the 30% floor.
- **58 vault entries** (add-ons, GN-packs, materials, assets), **48 manifests**, **11 verified recipes**.
- **Whole-taxonomy coverage:** see `reports/stage1-final.md` (the gate was always a T+V proxy; Stage-2
  plans against the whole map).

## 2. The read interface (consume these, do not re-run the harness)
| artifact | schema | what Stage-2 does with it |
|---|---|---|
| `corpus.db` (SQLite) | tables `addons, operators, verify, coverage(niche,cid,op,ver,state), graveyard` | **rebuilt, never hand-edited** — `build_index.py` regenerates it from JSON. Query for niche→operator resolution. |
| `manifests/<id>.json` | §4.3: `verify{ver:{state,operators,render_ok}}`, `operators_enriched[{kind,id,verbs,niches,quality}]` | per-artifact capability + verification result |
| `vault/<id>/<ver>/meta.json` | §4.2 + `usage_license, attribution, entry_type, procedural` | provenance (source URL + SHA-256) + **license obligation** |
| `inputs/recipes.yaml` | `{niche, tier, steps[], note}` | composite coverage; `tier ∈ {recipe_verified, recipe_unverified}` |
| `reports/coverage.json` | `gate_v2, pass_rate, verb_medium_grid, covered_by` | the coverage matrix + the resolver's grid |

## 3. Quality tiers — the resolver MUST prefer depth (R39)
Every operator/recipe carries a **quality** signal. When multiple entries serve a niche, the Stage-2
metaphor resolver **MUST** prefer higher depth:
1. `full_generator` — a dedicated procedural tool/GN-pack/material that drives headless (deepest).
2. `composed` — a multi-operator recipe of real generators (`recipe_verified`, non-asset).
3. `asset_fed_minimal` — a CC asset + a scatter/array composition (`recipe_verified`, minimal). **Real
   coverage, but shallow** — answered the premise question; must **never** be treated as generator depth.

`recipe_unverified` entries are CLAIMS — never resolve to them at render time.

## 4. The verb×medium grid (the resolver's primary index)
`reports/coverage.json.verb_medium_grid` = verified operators per (physical verb × medium:
ground/water/air/urban/organic/abstract). **Niches are substitutable within a medium; verbs are not.**
The resolver queries by (verb, medium), not by niche id. 14 cells currently populated. Empty cells
(aggregate/fill/reveal × water/air/urban) are Stage-2 authoring targets.

## 5. LICENSE OBLIGATIONS every Stage-2 render inherits (LOAD-BEARING — R43)
Each vault entry's `meta.json.usage_license` binds the engine's output. **The renderer MUST enforce:**
- **CC-BY / CC Attribution assets** → **visible attribution required** in the render's credits or video
  description. Each entry's `meta.json.attribution` string is the exact credit to emit (it ends
  "provided by Sketchfab" for A1 assets). Rendering a scene using a CC-BY asset **without** emitting its
  attribution is a license breach.
- **BlenderKit assets (CC0 or Royalty-Free)** → **rendered-video output ONLY**. Per BlenderKit Article-5,
  the engine **MUST NOT** offer any functionality that exports a 3D model / scene containing a BlenderKit
  asset, and the asset must not be openable/separable by an end-user. Video frames are compliant; a
  "download .blend / export FBX" feature is a breach. (`policies/marketplace-tos.md` L6.)
- **Royalty-Free assets (any source)** → **incorporation-only**: usable inside a project/render, but
  **never redistributed standalone** and a project may not consist only of the asset.
- **by-nc / by-nd assets** → **segregated** (`meta.json.segregated: true`); **do not use** in commercial
  engine output until the owner resolves the parked NC/ND commerciality question (R26). None are in the
  current gate.
- **GPL add-ons** → the add-on's GPL applies to the add-on code, not to rendered output; safe to invoke.

Stage-2 SHOULD carry a per-render license manifest (which vaulted entries a frame used + their required
credits) so obligations are auditable.

## 6. Re-verification API (freshness — R43)
- `archon workflow run verify-batch` re-probes the vault against the 3-version Blender matrix and
  rewrites manifests + `corpus.db`. `coverage-report` recomputes the matrix read-only.
- **90-day re-verification is armed** (`.github/workflows/reverify-90d.yml`, scheduled): re-acquires
  from source URLs, re-hashes (detects rot/tampering), re-probes natively (amd64). An entry whose source
  URL is dead or whose hash drifts is flagged for Stage-2 (provenance integrity, PRD zero-fabrication).
- **Native probe:** `.github/workflows/native-probe.yml` (amd64, no emulation) is the authoritative Gate
  at scale; the local emulated probe is a dev convenience (large add-ons quarantine under emulation).

## 7. What is NOT in scope (do not expect it here)
No Stage-2 engine code, no scene compiler, no metaphor mapper. 2 niches are unattainable
(`karst_formation`, `coral_atoll_generator`) → `reports/stage2-backlog.md` for build-from-scratch. The
marketplace $0 GN-pack depth (Route B) is queued, not harvested (gate met without it).

## 8. Stage-2 opens by its own PRD + SPEC (R45)
Author Stage-2 fresh (the create-prd / create-spec discipline that opened Stage 1) against THIS file.
Thin slice = the "fish-form-an-equation" vertical (emergent_formation × diegetic_dataviz). This repo is a
consumed dependency; do not develop it further except via `verify-batch` re-verification.
