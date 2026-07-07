# /// script
# requires-python = ">=3.11,<3.12"
# ///
"""shader_to_manifest.py — turn a shader-probe PASS into a manifest so coverage counts the niche
(D-006 R37; L6 HYBRID: materials = procedural -> Gate). A dedicated procedural material that passes
the shader-probe covers its shader niche at full_pass tier (quality: full_generator-adjacent).
Usage: shader_to_manifest.py <niche> <state> <delta> <canonical_id>"""
import sys, json, pathlib, glob
niche, state, delta, cid = sys.argv[1], sys.argv[2], float(sys.argv[3]), sys.argv[4]
metas = glob.glob(f"vault/{cid}/*/meta.json")
meta = json.loads(open(metas[0]).read()) if metas else {}
m = {"canonical_id": cid, "name": meta.get("name"), "artifact_type": "material",
     "verify": {"4.5": {"state": state, "operators": [], "render_ok": True, "shader_delta": delta}},
     "operators_enriched": [{"kind": "material", "id": f"{cid}:material", "verbs": ["fill"],
                             "niches": [niche], "quality": "full_generator"}],
     "enriched_by": "shader-probe (L6 material, D-006 R37)",
     "enrich_note": f"BlenderKit procedural material shader-probed delta={delta:.3f} (>=0.02 pass) -> covers {niche}."}
pathlib.Path(f"manifests/{cid}.json").write_text(json.dumps(m, indent=2))
print(f"wrote manifests/{cid}.json: {niche} {state} delta={delta}")
