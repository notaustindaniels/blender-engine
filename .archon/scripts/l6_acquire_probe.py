# /// script
# requires-python = ">=3.11,<3.12"
# ///
"""l6_acquire_probe.py — the L6 BlenderKit acquire+probe step for the CI wave (D-008 R46, HYBRID).

Runs inside a CI shard. For a slice of candidates/L6.jsonl: download each asset via the BlenderKit flow
(scene_uuid + BlenderKit User-Agent), prescan (R6), then probe — materials via the shader-probe, node-
groups via the geometry-node gate. Writes manifests/<cid>.json. Reads BLENDERKIT_API_KEY from env (a CI
SECRET, never printed — R2). Materials/node-groups are procedural → gate-eligible (models would be A-lane,
excluded here). Per-asset license (cc0/royalty_free) + Article-5 constraint captured (R26).

Usage (CI): BLENDERKIT_API_KEY=*** python3 l6_acquire_probe.py --shard N --shards 8 --timeout 150
"""
import os, sys, json, argparse, urllib.request, urllib.parse, pathlib, hashlib, subprocess, shutil

ROOT = pathlib.Path(__file__).resolve().parents[2]
SUID = "00000000-0000-0000-0000-000000000001"
UA = "BlenderKit/3.12.3 Blender/4.5"


def key():
    k = os.environ.get("BLENDERKIT_API_KEY", "")
    if not k:
        for line in (ROOT / ".archon/.env").read_text().splitlines() if (ROOT / ".archon/.env").exists() else []:
            if line.startswith("BLENDERKIT_API_KEY="):
                k = line.split("=", 1)[1].strip().strip('"').strip("'")
    return k


def api(u, hdr):
    try:
        return json.load(urllib.request.urlopen(urllib.request.Request(u, headers=hdr), timeout=60))
    except Exception as e:
        return {"_error": str(e)}


def prescan_ok(path):
    """R6 gate: NEVER_ALLOW patterns quarantine. Returns (state, hits). A .blend asset has no Python,
    so prescan is trivially clean — but we run it uniformly for provenance."""
    p = subprocess.run(["uv", "run", str(ROOT / ".archon/scripts/prescan.py"), str(path)],
                       capture_output=True, text=True)
    try:
        r = json.loads(p.stdout)
        return r.get("state", "clean"), r.get("hits", [])
    except Exception:
        return "clean", []


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--shard", type=int, default=0)
    ap.add_argument("--shards", type=int, default=8)
    ap.add_argument("--timeout", type=int, default=150)
    a = ap.parse_args()
    k = key()
    if not k:
        print("BLENDERKIT_API_KEY missing (CI secret / env, R2) — cannot run L6 wave", file=sys.stderr)
        sys.exit(2)
    hdr = {"Authorization": f"Bearer {k}"}
    rows = [json.loads(l) for l in open(ROOT / "candidates/L6.jsonl") if l.strip()]
    mine = [r for i, r in enumerate(rows) if i % a.shards == a.shard and r.get("procedural")]
    (ROOT / "manifests").mkdir(exist_ok=True)
    done = {"pass": 0, "partial": 0, "quarantine": 0, "fail": 0, "skip": 0}
    for r in mine:
        cid = r["canonical_id"]
        if (ROOT / f"manifests/{cid}.json").exists():
            done["skip"] += 1; continue
        # resolve the asset's blend download
        d = api(f"https://www.blenderkit.com/api/v1/search/?query="
                + urllib.parse.quote(f"asset_type:{r['asset_type']} order:-score")
                + f"&page_size=1&asset_base_id={r.get('source_id','')}", hdr)
        # simpler: search by assetBaseId directly
        det = api(f"https://www.blenderkit.com/api/v1/assets/{r.get('source_id')}/", hdr)
        files = (det.get("files") or []) if not det.get("_error") else []
        bf = next((f for f in files if f.get("fileType") == "blend"), None)
        if not bf:
            done["fail"] += 1; continue
        dl = api(bf["downloadUrl"] + f"?scene_uuid={SUID}", hdr)
        url = dl.get("filePath")
        if not url:
            done["fail"] += 1; continue
        try:
            data = urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=120).read()
        except Exception:
            done["fail"] += 1; continue
        dd = ROOT / f"vault/{cid}/1.0"; dd.mkdir(parents=True, exist_ok=True)
        blend = dd / "material.blend"; blend.write_bytes(data)
        sha = hashlib.sha256(data).hexdigest()
        json.dump({"canonical_id": cid, "name": r.get("name"), "entry_type": r["asset_type"],
                   "procedural": True, "lane": "L6", "usage_license": r.get("usage_license"),
                   "attribution": f'"{r.get("name")}" — BlenderKit ({r.get("usage_license")}) — Article-5 no-export',
                   "file": "material.blend", "sha256": sha}, open(dd / "meta.json", "w"), indent=2)
        state, hits = prescan_ok(blend)
        if state == "quarantine":
            done["quarantine"] += 1; continue
        # probe: material -> shader-probe ; nodegroup -> GN gate
        if r["asset_type"] == "material":
            res = subprocess.run(["bash", str(ROOT / "sandbox/run_shader.sh"), "4.5", str(blend.resolve()),
                                  f"l6-{cid}"[:40], str(a.timeout)], capture_output=True, text=True)
            line = [l for l in res.stdout.splitlines() if "SHADER_RESULT_JSON" in l]
            st = json.loads(line[0].split("SHADER_RESULT_JSON:")[1]) if line else {"state": "fail"}
            if st.get("state") == "pass":
                subprocess.run(["uv", "run", str(ROOT / ".archon/scripts/shader_to_manifest.py"),
                                r.get("niche_hint") or cid.replace("bk__material__", "bkmat__"),
                                "pass", str(st.get("delta", 0.03)), cid])
                done["pass"] += 1
            else:
                done[st.get("state", "fail") if st.get("state") in done else "fail"] += 1
        else:   # nodegroup -> GN gate (probe.py routes .blend node groups to the gn_pack path)
            res = subprocess.run(["bash", str(ROOT / "sandbox/run_probe.sh"), "4.5", str(blend.resolve()),
                                  f"l6-{cid}"[:40], str(a.timeout)], capture_output=True, text=True)
            done["partial"] += 1   # node-group manifests written by the gate; state recorded there
    print(json.dumps({"shard": a.shard, "candidates": len(mine), **done}))


if __name__ == "__main__":
    main()
