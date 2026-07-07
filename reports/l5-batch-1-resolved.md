# L5 Approval Batch #1 — RESOLVED (D-003 R20 · resolution pass per owner condition) — 2026-07-07

Batch #1 was APPROVED with a binding **resolution pass** on the non-GitHub rows: resolve each to the
final product page, confirm $0, capture license; **flag/drop anything login-walled, subscription-only,
or paid — never assume through.** Done below. Gumroad prices are JS-rendered, so per Gumroad §14
(no scraping) confirmation is via **search retrieval**, not live page scraping.

## Rows 1,2,5,6 — GitHub reroutes (proceeded immediately, hash-verified) ✅ DONE

| # | niche | repo | result |
|--:|---|---|---|
| 5 | `cliff_rockface_generator` | marcueberall/blender.cliffgenerator (GN-pack, GPL-3.0) | **PASS all 3 versions** — GN node group produces cliff geometry. Gate v2 +1 → **7/54**. |
| 1 | `asteroid_generator` | Donitzo/procedural-asteroid-generator (.blend, MIT) | **PARTIAL** — renders, no auto-delta. v1 covered. |
| 2 | `planetary_ring_generator` | MarekHlavka/Planet-and-space-objects-generator (GPL-3.0) | **FAIL** — project scripts, no add-on/.blend. Not covered. |
| 6 | `crater_field_generator` | (same MarekHlavka repo) | **FAIL** — same. Not covered. |

All 4 acquired + SHA-256-verified regardless (provenance holds). 2 of 4 niches now covered.

## Rows 3,4,7,8,9,10 — resolution pass on human-gated rows

| # | niche | resolved to | $0? | license | **verdict** |
|--:|---|---|---|---|---|
| **7** | `fern_generator` | **sagado.gumroad.com/l/ozxrlu** (Alex Martinelli, procedural GN .blend, Blender 4.3+) | **YES — PWYW, $0 min (search-confirmed)** | "no usage restrictions" (stated) | ✅ **CHECKOUT — the one clean $0 procedural tool** |
| 3 | `river_generator` | cgmatter.gumroad.com/l/river | **UNCONFIRMED** — CGMatter mixes free + paid + "name a fair price"; the river's price could not be confirmed $0 (a full YouTube course exists, suggesting a paid product) | unknown | ⚠️ **FLAG — do not check out until you confirm $0** |
| 4 | `waterfall_generator` | studio.blender.org | **NO — $17/mo subscription** (Blender Studio / Cloud) | subscription | ❌ **DROP** (owner's flag confirmed) |
| 8 | `flower_generator` | bd3d.gumroad.com/l/plant-library | **YES — "100% free, no catch"** (search-confirmed) | **commercial-use OK** | ↪️ **REROUTE → A-lane** — it is a 170+ **asset pack** (`procedural:false`), not a procedural tool; feeds a `flower_generator` recipe via R21 (asset + scatter). |
| 9 | `grass_meadow_scatter` | Graswald free (graswald.gumroad.com / store) | free assets, but **store login** | **NC (non-commercial EULA)** | ↪️ **REROUTE → A-lane, SEGREGATED (R26 NC)** — assets not a tool; free scatter is Biome-Reader (off-L1). |
| 10 | `ground_cover` | Graswald free (same) | same | **NC** | ↪️ **REROUTE → A-lane, SEGREGATED (R26 NC)** — same as row 9. |

## The checkout list (ready to click — one line, $0-confirmed)

1. **`fern_generator`** → https://sagado.gumroad.com/l/ozxrlu — $0 (name-your-price), no usage
   restrictions, procedural GN .blend. Complete the $0 checkout; I then probe it (R21) to try for
   `recipe_verified`/pass on `fern_generator`.

## Not on the checkout list (honest dispositions)
- **FLAGGED (needs your eyeball):** row 3 river — price unconfirmable without visiting; I won't assume $0.
- **DROPPED:** row 4 waterfall (subscription).
- **REROUTED → A-lane:** rows 8/9/10 — free/near-free **asset packs**, not procedural tools. Plant-Library
  (commercial-OK) and Graswald (NC → segregated) become asset inventory; they can feed grass/flower/
  ground_cover **recipes** (asset + free scatter) verified via the R21 probe — the D-004 asset-fed path.

**Net from batch #1:** gate v2 **9.3% → 13.0%** (cliff GN-pack full-pass); 1 confirmed $0 checkout for
you (fern); the vegetation-scatter niches route through the A-lane/recipe path, not $0 marketplace tools.
