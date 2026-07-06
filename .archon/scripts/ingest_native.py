# /// script
# requires-python = ">=3.11,<3.12"
# ///
"""ingest_native.py — overlay the native-probe run's manifests onto the local corpus (D-002 R13).

The native GitHub Actions run (native amd64, no emulation) re-probed the full matrix. Its
manifests are decision-grade and SUPERSEDE the emulated ones for every artifact it covered
(emulation quarantines/crashes are replaced by real native states). This copies native manifests
over local ones, records which artifacts changed state vs emulation, and leaves everything else
(vault provenance, recipes) untouched. Deterministic. Rebuild index+coverage after.

Usage: ingest_native.py <native_artifact_dir>   (dir containing native-probe-results/manifests/)
"""
import sys, json, glob, os, shutil, pathlib

if len(sys.argv) < 2:
    print("usage: ingest_native.py <native_artifact_dir>", file=sys.stderr); sys.exit(2)
src_root = pathlib.Path(sys.argv[1])
# find the manifests dir inside the downloaded artifact (structure: <dir>/<artifact-name>/manifests/)
cands = list(src_root.rglob("manifests"))
native_man = next((c for c in cands if c.is_dir() and list(c.glob("*.json"))), None)
if not native_man:
    print(json.dumps({"error": "no native manifests found in artifact", "searched": str(src_root)}))
    sys.exit(1)

local_man = pathlib.Path("manifests")
local_man.mkdir(exist_ok=True)
VERSIONS = ["3.6", "4.2", "4.5"]
changes = []
for nf in sorted(native_man.glob("*.json")):
    if nf.parent.name != "manifests":
        continue
    cid = nf.stem
    if "/golden/" in str(nf) or nf.parent.name == "golden":
        continue
    native = json.loads(nf.read_text())
    lf = local_man / f"{cid}.json"
    old = json.loads(lf.read_text()) if lf.exists() else {}
    old_states = {v: (old.get("verify", {}).get(v, {}) or {}).get("state") for v in VERSIONS}
    new_states = {v: (native.get("verify", {}).get(v, {}) or {}).get("state") for v in VERSIONS}
    # preserve any local enrichment (operators_enriched) if native lacks it
    if "operators_enriched" in old and "operators_enriched" not in native:
        native["operators_enriched"] = old["operators_enriched"]
        native["enriched_by"] = old.get("enriched_by")
        native["enrich_note"] = old.get("enrich_note")
    native["probed_natively"] = True
    lf.write_text(json.dumps(native, indent=2))
    if old_states != new_states:
        changes.append({"cid": cid, "was": old_states, "now": new_states})

print(json.dumps({"native_manifests_ingested": len(list(native_man.glob("*.json"))),
                  "state_changes_vs_emulation": changes}, indent=2))
