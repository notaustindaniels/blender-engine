# Coverage Report — L1+L2 (terrain, vegetation)

Deterministic (`coverage.py` over `corpus.db`). Wave-1 drives the gate (§12.1(4)); denominators are PRESENT niches (§12.1(5)); every table splits full-pass vs partial (§12.2).

## Gate metrics (PRD §4 wrong-condition)

- **Terrain + Vegetation coverage (wave-1): 7/59 = 11.9%**  (4 full-pass + 3 partial-only) — PRD stop-line <40%.
- **Acquisition pass-rate: 13/21 = 61.9%** (pass/partial on ≥1 compatible version; skipped-incompatible cells excluded) — PRD stop-line <30%.
- **Probe-recipe backlog:** 4 niche(s) partial-only (see `reports/probe-recipes.md`).

## Covered niches (Terrain + Vegetation, wave-1)

| niche | category | best | covered by |
|---|---|---|---|
| `terrain_generator` | terrain | partial | community__a-n-t-landscape, lmesaric__bsc-thesis-fer-2020, nicolaspriniotakis__srtm-terrain-importer, zets__terrain-mixer |
| `heightmap_stack_tools` | terrain | partial | nicolaspriniotakis__srtm-terrain-importer, zets__terrain-mixer |
| `erosion_sim` | terrain | pass | community__a-n-t-landscape, petak5__bp, varkenvarken__erosion |
| `snow_accumulation` | terrain | pass | nacioss__real-snow |
| `tree_generator` | vegetation | pass | brandyn-britton__modular-tree, community__sapling-tree-gen, jacob-johnston__easy-tree, ls__space-colonization-tree-generator |
| `space_colonization_growth` | vegetation | pass | ls__space-colonization-tree-generator |
| `ivy_generator` | vegetation | partial | community__ivygen |

## Coverage by category (wave-1)

| category | present | covered | full-pass | partial-only | % |
|---|---:|---:|---:|---:|---:|
| Terrain & landscape | 36 | 4 | 2 | 2 | 11% |
| Vegetation & organic | 23 | 3 | 2 | 1 | 13% |
| Cities & urban | 18 | 0 | 0 | 0 | 0% |
| Buildings & architecture | 17 | 0 | 0 | 0 | 0% |
| Rooms & interiors | 12 | 0 | 0 | 0 | 0% |
| Characters & creatures | 8 | 0 | 0 | 0 | 0% |
| Hard surface & props | 17 | 0 | 0 | 0 | 0% |
| Fabric & soft goods | 5 | 0 | 0 | 0 | 0% |
| Nature elements & FX geometry | 20 | 0 | 0 | 0 | 0% |
| Abstract, mograph & design | 11 | 0 | 0 | 0 | 0% |
| Materials & texturing | 19 | 0 | 0 | 0 | 0% |
| Simulation-adjacent | 14 | 0 | 0 | 0 | 0% |
| Animation: motion fundamentals | 6 | 0 | 0 | 0 | 0% |
| Animation: character & creature | 12 | 0 | 0 | 0 | 0% |
| Animation: mechanical | 9 | 0 | 0 | 0 | 0% |
| Animation: nature & environment | 8 | 0 | 0 | 0 | 0% |
| Animation: growth, reveal & build | 7 | 0 | 0 | 0 | 0% |
| Animation: cloth, rope & soft proxies | 5 | 0 | 0 | 0 | 0% |
| Animation: camera & cinematic | 5 | 0 | 0 | 0 | 0% |
| Animation: FX & particles | 6 | 0 | 0 | 0 | 0% |
| Animation: data-driven & utility | 7 | 0 | 0 | 0 | 0% |
| Animation: stylized / NPR | 4 | 0 | 0 | 0 | 0% |
| **TOTAL (wave 1)** | **269** | **7** | **4** | **3** | **3%** |

## Wave-2 coverage (separate; does NOT move the gate)

| category | present | covered | full-pass | partial-only | % |
|---|---:|---:|---:|---:|---:|
| Terrain & landscape | 3 | 0 | 0 | 0 | 0% |
| Vegetation & organic | 2 | 1 | 0 | 1 | 50% |
| Nature elements & FX geometry | 4 | 0 | 0 | 0 | 0% |
| Abstract, mograph & design | 3 | 0 | 0 | 0 | 0% |
| Materials & texturing | 3 | 0 | 0 | 0 | 0% |
| Simulation-adjacent | 1 | 0 | 0 | 0 | 0% |
| Emergent formation (agents/particles self-organize into targets) | 14 | 0 | 0 | 0 | 0% |
| Diegetic data visualization (charts as in-world objects) | 16 | 0 | 0 | 0 | 0% |
| Physical-process rendering (force-of-nature and craft draw the math) | 6 | 0 | 0 | 0 | 0% |
| Light & shadow as data | 3 | 0 | 0 | 0 | 0% |
| Animation: growth, reveal & build | 3 | 0 | 0 | 0 | 0% |
| Animation: data-driven & utility | 1 | 0 | 0 | 0 | 0% |
| **TOTAL (wave 2)** | **59** | **1** | **0** | **1** | **2%** |
