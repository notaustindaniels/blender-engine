# Coverage Report — L1 Thin Slice (terrain, vegetation)

Computed deterministically by `coverage.py` from `corpus.db`. Wave-1 drives the gate (§12.1(4)); denominators are PRESENT niches (§12.1(5)).

## Gate metrics (PRD §4 wrong-condition)

- **Terrain + Vegetation coverage (wave-1): 7/59 = 11.9%**  — PRD stop-line is <40% (evaluated after L1+L2).
- **Acquisition pass-rate: 10/11 = 90.9%** (pass/partial on ≥1 version) — PRD stop-line is <30%.

## Covered niches (Terrain + Vegetation, wave-1)

| niche | category | covered by |
|---|---|---|
| `terrain_generator` | terrain | community__a-n-t-landscape, nicolaspriniotakis__srtm-terrain-importer, zets__terrain-mixer |
| `heightmap_stack_tools` | terrain | nicolaspriniotakis__srtm-terrain-importer, zets__terrain-mixer |
| `erosion_sim` | terrain | community__a-n-t-landscape |
| `snow_accumulation` | terrain | nacioss__real-snow |
| `tree_generator` | vegetation | brandyn-britton__modular-tree, community__sapling-tree-gen, jacob-johnston__easy-tree, ls__space-colonization-tree-generator |
| `space_colonization_growth` | vegetation | ls__space-colonization-tree-generator |
| `ivy_generator` | vegetation | community__ivygen |

## Coverage by category (wave-1)

| category | present | covered | % |
|---|---:|---:|---:|
| Terrain & landscape | 36 | 4 | 11% |
| Vegetation & organic | 23 | 3 | 13% |
| Cities & urban | 18 | 0 | 0% |
| Buildings & architecture | 17 | 0 | 0% |
| Rooms & interiors | 12 | 0 | 0% |
| Characters & creatures | 8 | 0 | 0% |
| Hard surface & props | 17 | 0 | 0% |
| Fabric & soft goods | 5 | 0 | 0% |
| Nature elements & FX geometry | 20 | 0 | 0% |
| Abstract, mograph & design | 11 | 0 | 0% |
| Materials & texturing | 19 | 0 | 0% |
| Simulation-adjacent | 14 | 0 | 0% |
| Animation: motion fundamentals | 6 | 0 | 0% |
| Animation: character & creature | 12 | 0 | 0% |
| Animation: mechanical | 9 | 0 | 0% |
| Animation: nature & environment | 8 | 0 | 0% |
| Animation: growth, reveal & build | 7 | 0 | 0% |
| Animation: cloth, rope & soft proxies | 5 | 0 | 0% |
| Animation: camera & cinematic | 5 | 0 | 0% |
| Animation: FX & particles | 6 | 0 | 0% |
| Animation: data-driven & utility | 7 | 0 | 0% |
| Animation: stylized / NPR | 4 | 0 | 0% |
| **TOTAL (wave 1)** | **269** | **7** | **3%** |

## Wave-2 coverage (separate; does NOT move the gate)

| category | present | covered | % |
|---|---:|---:|---:|
| Terrain & landscape | 3 | 0 | 0% |
| Vegetation & organic | 2 | 1 | 50% |
| Nature elements & FX geometry | 4 | 0 | 0% |
| Abstract, mograph & design | 3 | 0 | 0% |
| Materials & texturing | 3 | 0 | 0% |
| Simulation-adjacent | 1 | 0 | 0% |
| Emergent formation (agents/particles self-organize into targets) | 14 | 0 | 0% |
| Diegetic data visualization (charts as in-world objects) | 16 | 0 | 0% |
| Physical-process rendering (force-of-nature and craft draw the math) | 6 | 0 | 0% |
| Light & shadow as data | 3 | 0 | 0% |
| Animation: growth, reveal & build | 3 | 0 | 0% |
| Animation: data-driven & utility | 1 | 0 | 0% |
| **TOTAL (wave 2)** | **59** | **1** | **2%** |
