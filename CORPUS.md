# CORPUS.md — Blender Vault: the Tier-0 skill card (always load this first)

You are navigating a **local, hash-verified corpus of free procedural Blender tooling** (add-ons,
GN-packs, materials, assets) tagged by capability. This card is all you need loaded; everything else
is fetched on demand. **Budget: ≤2k tokens — do not inline cards or manifests here.**

## The one doctrine: RETRIEVAL PROPOSES, THE REGISTRY DISPOSES
1. **Propose** with `search_capabilities(nl)` — hybrid semantic+keyword search returns candidate
   **cards** (Tier-1, ~120 words each). These are suggestions, not answers.
2. **Dispose** with `query_registry(verb, medium, niche, quality_min, license_class, blender_ver)` —
   a deterministic facet query over the authoritative registry. **Selection MUST terminate here.** It
   returns only **verified, license-tagged, resolvable** entries. Never invoke a tool you reached by
   retrieval alone.
3. **Read** the chosen entry with `get_card(id)` (Tier-1) then `get_usage(id)` (Tier-2 full manifest:
   verify states, operators, params).
4. **Compose** when no single tool fits: `plan_recipe(niche)` returns a verified composition (or a
   labeled unverified claim). `find_substitutes(id|niche)` widens the option set.

**recipe_unverified and graveyard results are returned LABELED and are NEVER resolvable at render
time.** Dead tools are findable-as-dead so you don't re-propose them.

## Interface (MCP server `blender-vault-corpus`, or CLI twin `.archon/scripts/corpus_cli.py`)
`search_capabilities(nl, medium?, verb?, near?)` · `query_registry(verb?, medium?, niche?, quality_min?,
license_class?, blender_ver?)` · `get_card(id)` · `get_usage(id)` · `find_substitutes(id|niche)` ·
`plan_recipe(niche)`. All return JSON.

## Facets (the vocabulary you query with)
- **verbs** (physical action): generate, scatter, trace, stack, accumulate, branch, simulate, deplete,
  carve, fracture, fill, reveal, aggregate. *Verbs are not substitutable.*
- **media**: ground, water, air, organic. *Niches ARE substitutable within a medium.*
- **quality tiers** (resolver MUST prefer depth): `full_generator` > `composed` > `asset_fed_minimal`.
- **license classes** (obligations bind every render): `cc-by` (visible attribution in credits),
  `cc0` (none), `royalty_free` (BlenderKit — **rendered-video only, no 3D-export**, incorporation-only),
  `gpl` (code only, not output), `unrecorded` (verify first).
- **blender_ver**: 3.6, 4.2, 4.5 (a tool is resolvable only for versions it passed).

## THE CATALOG — the whole library, three faces (D-008 catalog campaign)
Headline metric is **TOTAL CATALOG ENTRIES** (coverage % is secondary). One database, three faces:
1. **`corpus_kb.db`** (this KB) holds **everything** — verified add-ons, Sketchfab CC assets, and
   external-discovery items — as hybrid-searchable cards. Discovery/asset nodes are **findable but
   `props.verified=False`**: retrieval proposes them LABELED; only `query_registry` (corpus.db)
   resolves the verified ones. Registry still disposes.
2. **THE LIST** — `reports/catalog/index.html` (+ `CATALOG.md`): the full filterable/sortable page,
   grouped, live URLs, verified / click-to-get / excluded badges. Regenerated on every ingest; served
   by `progress/serve.sh`. This is the human browse face.
3. **`corpus.db`** — the authoritative registry of gate-verified entries only (what `query_registry`
   returns).

Entry **status**: `auto_acquired_verified` (API/GitHub → acquired, prescanned, native-CI gated, real
verify states) · `click_to_get` (checkout/free-download-gated: resolved URL + machine-confirmed or
confirm-at-source price; the owner clicks — never auto-checked-out) · `excluded` (dead / actually-paid /
NC-ND-segregated, reason recorded). See `reports/discovery-saturation.md` for per-marketplace exhaustion.

## Coverage at a glance (this snapshot)
Deep: **Terrain** and **Vegetation/organic** (first harvest) + **hard-surface/materials** (L6 BlenderKit).
The full 328-niche taxonomy across 26 categories is the campaign target — `reports/gaps/` names market
absences per category. **Provisional** niches (auto-added from discovery) are marked and **never counted
as verified coverage** (R14). Two niches are unbuildable from free tooling (`karst_formation`,
`coral_atoll_generator`) — Stage-2 from-scratch backlog, never resolvable here.

## Rules that never bend
- The registry (`corpus.db`) is authoritative; the KB (`corpus_kb.db`) only routes. Both are DERIVED —
  rebuilt from JSON manifests, never hand-edited.
- Every invocation carries its license obligation into the render (see `get_card`'s License line).
- If `query_registry` returns nothing resolvable for a need, that's a **documented gap**, not a
  license to invoke an unverified or graveyard entry. Report the gap.
