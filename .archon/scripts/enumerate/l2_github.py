# /// script
# requires-python = ">=3.11,<3.12"
# ///
"""L2 enumerator — GitHub (SPEC §2.2 L2, §5.3). STAGE-1 STUB.

Build-sequencing step 5 (OUT of the Stage-1 thin-slice scope, KICKOFF §3). This file exists
per the SPEC §2.3 directory contract and documents the intended design; it does NOT harvest.

Design (step 5): gh code-search for `bl_info` / `blender_manifest.toml` signatures, partitioned
by signature × language × star-bucket to stay under API caps; `topic:` filters; awesome-list
expansion; seed star-graph to depth 2 (from inputs/seed-anchors.yaml); hard candidate ceiling
(default 5,000). Requires GH_TOKEN via env injection (SPEC §6.5) — never in YAML.
"""
import argparse, sys, pathlib, json

ap = argparse.ArgumentParser()
ap.add_argument("--out", default="candidates/L2.jsonl")
a = ap.parse_args()
pathlib.Path(a.out).parent.mkdir(parents=True, exist_ok=True)
pathlib.Path(a.out).write_text("")  # empty; no harvesting in Stage 1
print(json.dumps({"lane": "L2", "status": "stub", "note": "GitHub lane = build-seq step 5 (out of Stage-1 scope)"}))
print("[L2] STAGE-1 STUB — GitHub lane is build-sequencing step 5; not implemented in the thin slice.", file=sys.stderr)
