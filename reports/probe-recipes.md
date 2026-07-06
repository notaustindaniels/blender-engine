# Probe-Recipe Backlog (SPEC §12.2)

Niches whose only covering operators reached `partial` (registered + rendered, but the operator could not be auto-driven to a geometry delta headless — typically a dialog/modal generator). Each needs a per-operator probe recipe (params/context to make it emit geometry) to upgrade `partial -> pass`. These COUNT toward coverage but are tracked here so partials never silently masquerade as full passes.

- `alien_biome_generator` (terrain) ← `ra100__planet-gen:planetgen.create_planet`  — recipe TODO
- `biome_scatter_system` (vegetation) ← `community__scatter-objects:object.scatter`  — recipe TODO
- `heightmap_stack_tools` (terrain) ← `nicolaspriniotakis__srtm-terrain-importer:import_mesh.hgt_displacement`  — recipe TODO
- `heightmap_stack_tools` (terrain) ← `zets__terrain-mixer:object.add_tm_workspaces`  — recipe TODO
- `ivy_generator` (vegetation) ← `community__ivygen:curve.ivy_gen`  — recipe TODO
