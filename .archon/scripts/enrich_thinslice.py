# /// script
# requires-python = ">=3.11,<3.12"
# dependencies = ["pyyaml>=6"]
# ///
"""enrich_thinslice.py — apply the operator->niche/verb mapping for the L1 thin slice.

This encodes the enrich JUDGMENT (SPEC §6 `enrich` node) EXPLICITLY and auditable, rather than a
free-form AI pass, so the gate numbers are verifiable. Every mapping cites a reason and uses only
taxonomy niche ids + the frozen verb enum; a verified operator id is attached from the manifest.
The `enrich-manifest` AI command remains the validated production path for harvest at scale.

Conservative on purpose: generic tools map to wave-2 (biome_scatter_system), not force-fit into a
specific wave-1 niche. Writes operators_enriched into each manifests/<id>.json.
"""
import json, glob, pathlib, sys
import yaml

TAX = yaml.safe_load(open("inputs/taxonomy.yaml").read())
NICHE_IDS = {n["id"] for c in TAX["categories"] for n in (c.get("niches") or [])}
VERBS = set(TAX["meta"]["verb_enum"])

# canonical_id -> {niches, verbs, prefer_op, why}
MAP = {
    "community__a-n-t-landscape": dict(
        niches=["terrain_generator", "erosion_sim"], verbs=["generate", "simulate", "deplete"],
        prefer_op="mesh.landscape_add",
        why="mesh.landscape_add generates heightmap terrain; mesh.eroder runs hydraulic/thermal erosion (both verified in manifest)."),
    "nicolaspriniotakis__srtm-terrain-importer": dict(
        niches=["terrain_generator", "heightmap_stack_tools"], verbs=["generate"], prefer_op=None,
        why="imports SRTM DEM tiles as a heightfield terrain mesh."),
    "zets__terrain-mixer": dict(
        niches=["terrain_generator", "heightmap_stack_tools"], verbs=["generate"], prefer_op=None,
        why="procedural terrain generation by mixing/stacking heightmap layers."),
    "nacioss__real-snow": dict(
        niches=["snow_accumulation"], verbs=["accumulate"], prefer_op=None,
        why="accumulates a procedural snow layer over target geometry."),
    "brandyn-britton__modular-tree": dict(
        niches=["tree_generator"], verbs=["generate", "branch"], prefer_op=None,
        why="node-based procedural tree generator."),
    "community__sapling-tree-gen": dict(
        niches=["tree_generator"], verbs=["generate", "branch"], prefer_op="curve.tree_add",
        why="parametric branch-recursion tree generator."),
    "jacob-johnston__easy-tree": dict(
        niches=["tree_generator"], verbs=["generate", "branch"], prefer_op=None,
        why="procedural tree generator."),
    "ls__space-colonization-tree-generator": dict(
        niches=["tree_generator", "space_colonization_growth"], verbs=["generate", "branch", "trace"],
        prefer_op=None, why="space-colonization algorithm -> both a tree generator and the branching-growth niche."),
    "community__ivygen": dict(
        niches=["ivy_generator"], verbs=["trace", "branch"], prefer_op="curve.ivy_gen",
        why="grows ivy geometry over surfaces."),
    "community__scatter-objects": dict(
        niches=["biome_scatter_system"], verbs=["scatter"], prefer_op=None,
        why="generic object scatter -> conservatively the wave-2 biome-scatter niche, NOT force-fit into a specific wave-1 niche."),
    "kiara-bagattini__bagapie": dict(
        niches=["biome_scatter_system", "ivy_generator"], verbs=["scatter", "trace", "branch"],
        prefer_op=None, why="GN scatter + ivy toolkit; QUARANTINED under emulation so contributes no coverage regardless."),
    # ── L2 (GitHub) survivors, reviewed 2026-07-06 ──
    "petak5__bp": dict(
        niches=["erosion_sim"], verbs=["simulate", "deplete"], prefer_op=None,
        why="L2: bachelor-thesis terrain-erosion plugin; operator drives headless -> full pass (upgrades erosion_sim to full-pass)."),
    "varkenvarken__erosion": dict(
        niches=["erosion_sim"], verbs=["simulate", "deplete"], prefer_op=None,
        why="L2: hydraulic erosion (legacy min 2.69 but partial on 4.2/4.5)."),
    "lmesaric__bsc-thesis-fer-2020": dict(
        niches=["terrain_generator"], verbs=["generate"], prefer_op=None,
        why="L2: ZagrebGIS — imports GIS data into a terrain mesh (partial headless)."),
    # ── native run (D-002 R13) surfaced these — all 27 L2 acquired, not just 15 ──
    "beneking102__bene-proggen-maps": dict(
        niches=["terrain_generator"], verbs=["generate"], prefer_op="procgen_maps.generate_city",
        why="L2 native: 'Procedural city, terrain & dungeon generator'; procgen_maps.generate_city produces terrain geometry -> FULL PASS on 4.2/4.5 (upgrades terrain_generator to full-pass)."),
    "ra100__planet-gen": dict(
        niches=["alien_biome_generator"], verbs=["generate"], prefer_op="planetgen.create_planet",
        why="L2 native: planetgen.create_planet generates planet meshes/materials -> partial on 4.2/4.5; covers the previously-uncovered alien_biome_generator (alias 'alien landscape environments')."),
    # ── L5 batch #1 GitHub reroutes (rows 1,2,5,6), probed as GN-packs / assets ──
    "marcueberall__blender-cliffgenerator": dict(
        niches=["cliff_rockface_generator"], verbs=["generate"], prefer_op=None,
        why="L5-batch1: GN-pack .blend; node group 'Generator' binds to a mesh and produces cliff geometry -> FULL PASS all 3 versions. New full-pass niche."),
    "donitzo__procedural-asteroid-generator": dict(
        niches=["asteroid_generator"], verbs=["generate", "scatter"], prefer_op=None,
        why="L5-batch1: .blend asteroid generator; renders geometry but no auto-driven delta -> partial. Covers asteroid_generator."),
    "tu2463__rock_generator_addon": dict(
        niches=["rock_boulder_generator"], verbs=["generate"], prefer_op=None,
        why="L2/R40 wave-3-approved: full-pass rock generator -> rock_boulder_generator (WAVE-2 nature_fx; moves the grid, NOT gate v2 which is wave-1)."),
}


def main():
    errs = []
    for mp in sorted(glob.glob("manifests/*.json")):
        man = json.loads(open(mp).read())
        cid = man["canonical_id"]
        if cid not in MAP:
            continue
        m = MAP[cid]
        for nz in m["niches"]:
            if nz not in NICHE_IDS:
                errs.append(f"{cid}: niche '{nz}' not in taxonomy")
        for v in m["verbs"]:
            if v not in VERBS:
                errs.append(f"{cid}: verb '{v}' not in enum")
        ops = man.get("operators") or []
        op_id = m["prefer_op"] if (m["prefer_op"] in ops) else (ops[0] if ops else cid)
        man["operators_enriched"] = [{
            "kind": "gn_node_group" if man.get("artifact_type") == "gn_pack" else "bpy_op",
            "id": op_id, "verbs": m["verbs"], "niches": m["niches"],
        }]
        man["enriched_by"] = "operator-reviewed (explicit thin-slice map)"
        man["enrich_note"] = m["why"]
        pathlib.Path(mp).write_text(json.dumps(man, indent=2))
    if errs:
        print("ENRICH ERRORS:", *errs, sep="\n  ", file=sys.stderr)
        sys.exit(1)
    print(json.dumps({"enriched": sum(1 for mp in glob.glob('manifests/*.json')
                                      if json.loads(open(mp).read())['canonical_id'] in MAP)}))
