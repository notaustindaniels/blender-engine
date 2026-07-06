# /// script
# requires-python = ">=3.11,<3.12"
# ///
"""L3 enumerator — BlenderArtists forum / Discourse (SPEC §2.2 L3). STAGE-1 STUB.

Build-sequencing step 6 (OUT of Stage-1 scope). Exists per SPEC §2.3. Design: append `.json`
to any Discourse thread/category URL (no browser), extract outbound links, route each to L2 or
L5, dead links -> graveyard.jsonl. Crawl the Released-Scripts category to a configurable depth.
"""
import argparse, sys, pathlib, json

ap = argparse.ArgumentParser()
ap.add_argument("--out", default="candidates/L3.jsonl")
a = ap.parse_args()
pathlib.Path(a.out).parent.mkdir(parents=True, exist_ok=True)
pathlib.Path(a.out).write_text("")
print(json.dumps({"lane": "L3", "status": "stub", "note": "forum link-router = build-seq step 6 (out of Stage-1 scope)"}))
print("[L3] STAGE-1 STUB — forum link-router is build-sequencing step 6.", file=sys.stderr)
