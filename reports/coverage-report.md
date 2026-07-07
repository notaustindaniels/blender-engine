# Coverage Report — L1+L2 (terrain, vegetation)

Deterministic (`coverage.py` over `corpus.db`). Wave-1 drives the gate (§12.1(4)); denominators are PRESENT niches (§12.1(5)); every table splits full-pass vs partial (§12.2).

## Gate metrics (PRD §4 wrong-condition)

- **GATE v2 (R18/D-003 — the governing metric): 7/54 = 13.0%** = (full_pass + recipe_verified) / 54 ATTAINABLE Terrain+Veg wave-1 niches. Threshold **40%** (final verdict after L5b, R19). `partial` and `recipe_unverified` do NOT count in v2.
  - excluded as unattainable (paid_only/none, R15): `anemone_generator`, `coral_atoll_generator`, `coral_generator`, `karst_formation`, `kelp_forest_generator`
- **Tripwire (R19): pass-rate of-all-acquisitions 42.5%** vs 30% floor → OK.
- _v1 (legacy, all-present denom): 11/59 = 18.6% (6 full-pass + 4 partial + 1 recipe✓; 5 recipe claims not counted)._
- **Acquisition pass-rate (both framings, R16/D-002):** of-probed 17/30 = 56.7%; of-all-acquisitions 17/40 = 42.5% — PRD stop-line <30%.
- **Probe-recipe backlog:** 5 niche(s) partial-only (see `reports/probe-recipes.md`).

## Covered niches (Terrain + Vegetation, wave-1)

| niche | category | best | covered by |
|---|---|---|---|
| `terrain_generator` | terrain | pass | beneking102__bene-proggen-maps, community__a-n-t-landscape, lmesaric__bsc-thesis-fer-2020, nicolaspriniotakis__srtm-terrain-importer, zets__terrain-mixer |
| `heightmap_stack_tools` | terrain | partial | nicolaspriniotakis__srtm-terrain-importer, zets__terrain-mixer |
| `erosion_sim` | terrain | pass | community__a-n-t-landscape, petak5__bp, varkenvarken__erosion |
| `cliff_rockface_generator` | terrain | pass | marcueberall__blender-cliffgenerator |
| `snow_accumulation` | terrain | pass | nacioss__real-snow |
| `asteroid_generator` | terrain | partial | donitzo__procedural-asteroid-generator |
| `alien_biome_generator` | terrain | partial | ra100__planet-gen |
| `tree_generator` | vegetation | pass | brandyn-britton__modular-tree, community__sapling-tree-gen, jacob-johnston__easy-tree, ls__space-colonization-tree-generator |
| `space_colonization_growth` | vegetation | pass | ls__space-colonization-tree-generator |
| `ivy_generator` | vegetation | partial | community__ivygen |

## Coverage by category (wave-1)

| category | present | full-pass | partial | recipe✓ | recipe? (claim) | decision % |
|---|---:|---:|---:|---:|---:|---:|
| Terrain & landscape | 36 | 4 | 3 | 0 | 4 | 19% |
| Vegetation & organic | 23 | 2 | 1 | 1 | 1 | 17% |
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
| Animation: camera & cinematic | 5 | 0 | 0 | 0 | 0 | 0% |
| Animation: FX & particles | 6 | 0 | 0 | 0 | 0 | 0% |
| Animation: data-driven & utility | 7 | 0 | 0 | 0 | 0 | 0% |
| Animation: stylized / NPR | 4 | 0 | 0 | 0 | 0 | 0% |
| **TOTAL (wave 1)** | **269** | **6** | **4** | **1** | **5** | **4%** |

## Wave-2 coverage (separate; does NOT move the gate)

| category | present | full-pass | partial | recipe✓ | recipe? (claim) | decision % |
|---|---:|---:|---:|---:|---:|---:|
| Terrain & landscape | 3 | 0 | 0 | 0 | 0 | 0% |
| Vegetation & organic | 2 | 0 | 1 | 0 | 0 | 50% |
| Nature elements & FX geometry | 4 | 0 | 0 | 0 | 0 | 0% |
| Abstract, mograph & design | 3 | 0 | 0 | 0 | 0 | 0% |
| Materials & texturing | 3 | 0 | 0 | 0 | 0 | 0% |
| Simulation-adjacent | 1 | 0 | 0 | 0 | 0 | 0% |
| Emergent formation (agents/particles self-organize into targets) | 14 | 0 | 0 | 0 | 0 | 0% |
| Diegetic data visualization (charts as in-world objects) | 16 | 0 | 0 | 0 | 0 | 0% |
| Physical-process rendering (force-of-nature and craft draw the math) | 6 | 0 | 0 | 0 | 0 | 0% |
| Light & shadow as data | 3 | 0 | 0 | 0 | 0 | 0% |
| Animation: growth, reveal & build | 3 | 0 | 0 | 0 | 0 | 0% |
| Animation: data-driven & utility | 1 | 0 | 0 | 0 | 0 | 0% |
| **TOTAL (wave 2)** | **59** | **0** | **1** | **0** | **0** | **2%** |

## Verb × medium grid (R22 — verified operators; Stage-2 consumer metric)

Count of VERIFIED (pass/partial) operators by physical verb × medium. Niches are substitutable; verbs are not — this is what the metaphor resolver queries.

| verb | ground | water | air | urban | organic | abstract |
|---|---|---|---|---|---|---|
| accumulate | 1 | 0 | 0 | 0 | 0 | 0 |
| branch | 0 | 0 | 0 | 0 | 5 | 0 |
| deplete | 3 | 0 | 0 | 0 | 0 | 0 |
| generate | 7 | 0 | 1 | 0 | 4 | 0 |
| scatter | 0 | 0 | 1 | 0 | 1 | 0 |
| simulate | 3 | 0 | 0 | 0 | 0 | 0 |
| trace | 0 | 0 | 0 | 0 | 2 | 0 |
