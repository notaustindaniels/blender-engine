# Probe-Recipe Backlog (SPEC §12.2)

Niches whose only covering operators reached `partial` (registered + rendered, but the operator could not be auto-driven to a geometry delta headless — typically a dialog/modal generator). Each needs a per-operator probe recipe (params/context to make it emit geometry) to upgrade `partial -> pass`. These COUNT toward coverage but are tracked here so partials never silently masquerade as full passes.

- `alien_biome_generator` (terrain) ← `ra100__planet-gen:planetgen.create_planet`  — recipe TODO
- `asteroid_generator` (terrain) ← `donitzo__procedural-asteroid-generator:donitzo__procedural-asteroid-generator`  — recipe TODO
- `biome_scatter_system` (vegetation) ← `community__scatter-objects:object.scatter`  — recipe TODO
- `data_import` (anim_data_utility) ← `community__export-pointcache-format-pc2:export_shape.pc2`  — recipe TODO
- `data_import` (anim_data_utility) ← `jan-hendrik-m-ller__csv-importer:csv.reload_data`  — recipe TODO
- `data_import` (anim_data_utility) ← `k-naoki__tracker-to-nuke:clip.nuke_copy_distortion`  — recipe TODO
- `data_import` (anim_data_utility) ← `kiran-kumawat__robotics-animation-bone-coordinate-exporter:robotics.export_coords`  — recipe TODO
- `data_import` (anim_data_utility) ← `sharpened__attrio-csv:attrio.add_csv_import_object`  — recipe TODO
- `data_import` (anim_data_utility) ← `smonbrogg__spreadsheet-import:import.spreadsheet`  — recipe TODO
- `data_import` (anim_data_utility) ← `vicky-at-24fps__export-to-nuke-script:export.nuke_transform_fixed`  — recipe TODO
- `heightmap_stack_tools` (terrain) ← `nicolaspriniotakis__srtm-terrain-importer:import_mesh.hgt_displacement`  — recipe TODO
- `heightmap_stack_tools` (terrain) ← `zets__terrain-mixer:object.add_tm_workspaces`  — recipe TODO
- `ivy_generator` (vegetation) ← `community__ivygen:curve.ivy_gen`  — recipe TODO
- `light_matrix_data` (light_shadow_data) ← `vicky-at-24fps__export-to-nuke-script:export.nuke_transform_fixed`  — recipe TODO
