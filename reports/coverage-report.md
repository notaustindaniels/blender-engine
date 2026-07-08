# Coverage Report — L1+L2 (terrain, vegetation)

Deterministic (`coverage.py` over `corpus.db`). Wave-1 drives the gate (§12.1(4)); denominators are PRESENT niches (§12.1(5)); every table splits full-pass vs partial (§12.2).

## Gate metrics (PRD §4 wrong-condition)

- **GATE v2 (R18/D-003 — the governing metric): 23/57 = 40.4%** = (full_pass + recipe_verified) / 57 ATTAINABLE Terrain+Veg wave-1 niches. Threshold **40%** (final verdict after L5b, R19). `partial` and `recipe_unverified` do NOT count in v2.
  - excluded as unattainable (paid_only/none, R15): `coral_atoll_generator`, `karst_formation`
- **Tripwire (R19): pass-rate of-all-acquisitions 64.4%** vs 30% floor → OK.
- _v1 (legacy, all-present denom): 27/59 = 45.8% (12 full-pass + 4 partial + 11 recipe✓; 5 recipe claims not counted)._
- **Acquisition pass-rate (both framings, R16/D-002):** of-probed 612/708 = 86.4%; of-all-acquisitions 612/951 = 64.4% — PRD stop-line <30%.
- **Probe-recipe backlog:** 7 niche(s) partial-only (see `reports/probe-recipes.md`).

## Covered niches (Terrain + Vegetation, wave-1)

| niche | category | best | covered by |
|---|---|---|---|
| `terrain_generator` | terrain | pass | beneking102__bene-proggen-maps, community__a-n-t-landscape, lmesaric__bsc-thesis-fer-2020, nicolaspriniotakis__srtm-terrain-importer, zets__terrain-mixer |
| `heightmap_stack_tools` | terrain | partial | nicolaspriniotakis__srtm-terrain-importer, zets__terrain-mixer |
| `erosion_sim` | terrain | pass | community__a-n-t-landscape, petak5__bp, varkenvarken__erosion |
| `cliff_rockface_generator` | terrain | pass | marcueberall__blender-cliffgenerator |
| `cracked_earth_shader` | terrain | pass | bkmat__cracked_earth_shader |
| `snow_ice_shader` | terrain | pass | bkmat__snow_ice_shader |
| `ice_shader` | terrain | pass | bkmat__ice_shader |
| `snow_accumulation` | terrain | pass | nacioss__real-snow |
| `asteroid_generator` | terrain | partial | donitzo__procedural-asteroid-generator |
| `alien_biome_generator` | terrain | partial | ra100__planet-gen |
| `gas_giant_shader` | terrain | pass | bkmat__gas_giant_shader |
| `tree_generator` | vegetation | pass | brandyn-britton__modular-tree, community__sapling-tree-gen, jacob-johnston__easy-tree, ls__space-colonization-tree-generator |
| `space_colonization_growth` | vegetation | pass | ls__space-colonization-tree-generator |
| `fern_generator` | vegetation | pass | sagado__procedural-fern |
| `ivy_generator` | vegetation | partial | community__ivygen |
| `organic_cell_shader` | vegetation | pass | bkmat__organic_cell_shader |

## Coverage by category (wave-1)

| category | present | full-pass | partial | recipe✓ | recipe? (claim) | decision % |
|---|---:|---:|---:|---:|---:|---:|
| Terrain & landscape | 36 | 8 | 3 | 1 | 4 | 33% |
| Vegetation & organic | 23 | 4 | 1 | 10 | 1 | 65% |
| Cities & urban | 18 | 0 | 0 | 0 | 0 | 0% |
| Buildings & architecture | 17 | 0 | 0 | 0 | 0 | 0% |
| Rooms & interiors | 12 | 0 | 0 | 0 | 0 | 0% |
| Characters & creatures | 8 | 0 | 0 | 0 | 0 | 0% |
| Hard surface & props | 17 | 0 | 0 | 0 | 0 | 0% |
| Fabric & soft goods | 5 | 0 | 0 | 0 | 0 | 0% |
| Nature elements & FX geometry | 20 | 0 | 0 | 0 | 0 | 0% |
| Abstract, mograph & design | 11 | 0 | 0 | 0 | 0 | 0% |
| Materials & texturing | 19 | 0 | 0 | 0 | 0 | 0% |
| Simulation-adjacent | 14 | 0 | 0 | 0 | 0 | 0% |
| Animation: motion fundamentals | 6 | 0 | 0 | 0 | 0 | 0% |
| Animation: character & creature | 12 | 0 | 0 | 0 | 0 | 0% |
| Animation: mechanical | 9 | 0 | 0 | 0 | 0 | 0% |
| Animation: nature & environment | 8 | 0 | 0 | 0 | 0 | 0% |
| Animation: growth, reveal & build | 7 | 0 | 0 | 0 | 0 | 0% |
| Animation: cloth, rope & soft proxies | 5 | 0 | 0 | 0 | 0 | 0% |
| Animation: camera & cinematic | 5 | 1 | 0 | 0 | 0 | 20% |
| Animation: FX & particles | 6 | 0 | 0 | 0 | 0 | 0% |
| Animation: data-driven & utility | 7 | 0 | 1 | 0 | 0 | 14% |
| Animation: stylized / NPR | 4 | 1 | 0 | 0 | 0 | 25% |
| **TOTAL (wave 1)** | **269** | **14** | **5** | **11** | **5** | **11%** |

## Wave-2 coverage (separate; does NOT move the gate)

| category | present | full-pass | partial | recipe✓ | recipe? (claim) | decision % |
|---|---:|---:|---:|---:|---:|---:|
| Terrain & landscape | 3 | 0 | 0 | 0 | 0 | 0% |
| Vegetation & organic | 2 | 0 | 1 | 0 | 0 | 50% |
| Nature elements & FX geometry | 4 | 1 | 0 | 0 | 0 | 25% |
| Abstract, mograph & design | 3 | 1 | 0 | 0 | 0 | 33% |
| Materials & texturing | 3 | 0 | 0 | 0 | 0 | 0% |
| Simulation-adjacent | 1 | 0 | 0 | 0 | 0 | 0% |
| Emergent formation (agents/particles self-organize into targets) | 14 | 0 | 0 | 0 | 0 | 0% |
| Diegetic data visualization (charts as in-world objects) | 16 | 0 | 0 | 0 | 0 | 0% |
| Physical-process rendering (force-of-nature and craft draw the math) | 6 | 0 | 0 | 0 | 0 | 0% |
| Light & shadow as data | 3 | 0 | 1 | 0 | 0 | 33% |
| Animation: growth, reveal & build | 3 | 0 | 0 | 0 | 0 | 0% |
| Animation: data-driven & utility | 1 | 0 | 0 | 0 | 0 | 0% |
| **TOTAL (wave 2)** | **59** | **2** | **2** | **0** | **0** | **7%** |

## Quality tiers (R39/D-006 — handoff contract; depth per verified niche)

Per verified-capability niche (the gate-v2 numerator), HOW it is covered. `full_generator` = real procedural add-on/GN generator; `composed_procedural` = recipe of vaulted operators + built-ins; `asset_fed_minimal` = recipe leaning on an imported static asset (answered the premise, NOT generator sophistication). Stage-2 prefers depth.

- **full_generator** (12): `cliff_rockface_generator`, `cracked_earth_shader`, `erosion_sim`, `fern_generator`, `gas_giant_shader`, `ice_shader`, `organic_cell_shader`, `snow_accumulation`, `snow_ice_shader`, `space_colonization_growth`, `terrain_generator`, `tree_generator`
- **composed_procedural** (1): `orchard_row_scatter`
- **asset_fed_minimal** (10): `anemone_generator`, `bioluminescent_flora`, `coral_generator`, `flower_generator`, `grass_meadow_scatter`, `kelp_forest_generator`, `moss_lichen_growth`, `mushroom_generator`, `scree_talus_scatter`, `succulent_generator`

## Verb × medium grid (R22 — verified operators; Stage-2 consumer metric)

Count of VERIFIED (pass/partial) operators by physical verb × medium. Niches are substitutable; verbs are not — this is what the metaphor resolver queries.

| verb | ground | water | air | urban | organic | abstract |
|---|---|---|---|---|---|---|
| accumulate | 1 | 0 | 0 | 0 | 0 | 0 |
| branch | 0 | 0 | 0 | 0 | 5 | 0 |
| deform | 0 | 0 | 0 | 0 | 0 | 1 |
| deplete | 3 | 0 | 0 | 0 | 0 | 0 |
| fill | 3 | 0 | 1 | 0 | 1 | 0 |
| generate | 7 | 0 | 1 | 0 | 5 | 11 |
| illuminate | 0 | 0 | 0 | 0 | 0 | 1 |
| reveal | 0 | 0 | 0 | 0 | 1 | 1 |
| scatter | 0 | 0 | 1 | 0 | 1 | 0 |
| simulate | 3 | 0 | 0 | 0 | 0 | 0 |
| trace | 0 | 0 | 0 | 0 | 2 | 1 |
