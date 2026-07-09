# /// script
# requires-python = ">=3.11,<3.12"
# ///
"""l6_niche_sweep.py — coverage-targeted L6 material sweep (D-008 R46, throughput-optimized).
Downloads one BlenderKit procedural material per uncovered shader niche, then BATCH-probes them all in
ONE sandbox container (run_shader_batch.sh) — the fast path for local L6 execution. Writes a manifest
per passing niche. Reads BLENDERKIT_API_KEY from env/.env (R2). The full 600-material long-tail sweep
runs via l6-wave.yml in CI; this covers the distinct shader niches locally.
Usage: l6_niche_sweep.py --niches n1,n2,...  [--query-map ...]
"""
import os, sys, json, urllib.request, urllib.parse, pathlib, hashlib, subprocess, shutil, argparse
ROOT = pathlib.Path(__file__).resolve().parents[2]
SUID="00000000-0000-0000-0000-000000000001"; UA="BlenderKit/3.12.3 Blender/4.5"
QMAP={"brick_shader":"procedural brick wall","tile_grout_shader":"procedural tiles grout","car_paint_shader":"car paint procedural",
 "toon_npr_shader":"toon shader stylized","lava_shader":"lava magma procedural","hologram_shader":"hologram scifi procedural",
 "glitch_shader":"glitch procedural","aurora_sky":"aurora sky procedural","planet_shader":"planet surface procedural",
 "metal_shader":"procedural metal scratched","interior_parallax_shader":"interior parallax window","wet_surface_puddles":"wet puddle procedural",
 "fabric_weave_shader":"fabric weave procedural","imperfection_overlays":"imperfection grunge procedural","skybox_generator":"sky procedural",
 "pattern_generator":"geometric pattern procedural","clothing_pattern_3d":"cloth fabric procedural","knit_weave_generator":"knit wool procedural"}
def key():
    for line in open(ROOT/".archon/.env"):
        if line.startswith("BLENDERKIT_API_KEY="): return line.split("=",1)[1].strip().strip('"').strip("'")
    return os.environ.get("BLENDERKIT_API_KEY","")
def api(u,h):
    try: return json.load(urllib.request.urlopen(urllib.request.Request(u,headers=h),timeout=60))
    except Exception as e: return {"_error":str(e)}
def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--niches",required=True); ap.add_argument("--cap",default="540"); a=ap.parse_args()
    k=key(); H={"Authorization":f"Bearer {k}"}
    niches=[n.strip() for n in a.niches.split(",") if n.strip()]
    mats=pathlib.Path("/tmp/l6sweep"); shutil.rmtree(mats,ignore_errors=True); mats.mkdir(parents=True)
    batch=[]; meta={}
    for niche in niches:
        if (ROOT/f"manifests/bkmat__{niche}.json").exists(): continue
        q=QMAP.get(niche,niche.replace("_"," ")+" procedural")
        d=api("https://www.blenderkit.com/api/v1/search/?query="+urllib.parse.quote(q+" asset_type:material")+"&page_size=8",H)
        pick=None
        for m in (d.get("results") or []):
            if not m.get("canDownload"): continue
            bf=next((f for f in (m.get("files") or []) if f.get("fileType")=="blend"),None)
            sz=(bf or {}).get("fileUploadSize") or 0
            if bf and sz and sz<5_000_000: pick=(m,bf); break
        if not pick: print(f"{niche}: no material",flush=True); continue
        m,bf=pick; r=api(bf["downloadUrl"]+f"?scene_uuid={SUID}",H); url=r.get("filePath")
        if not url: print(f"{niche}: no url",flush=True); continue
        try: data=urllib.request.urlopen(urllib.request.Request(url,headers={"User-Agent":UA}),timeout=90).read()
        except Exception as e: print(f"{niche}: dl {e}",flush=True); continue
        cid=f"bkmat__{niche}"; (mats/f"{cid}.blend").write_bytes(data)
        batch.append({"cid":cid,"path":f"/work/mats/{cid}.blend"})
        meta[cid]={"niche":niche,"name":m.get("name"),"license":m.get("license"),"sha":hashlib.sha256(data).hexdigest()}
        print(f"{niche}: {str(m.get('name'))[:24]} downloaded",flush=True)
    if not batch: print("no materials to probe"); return
    json.dump(batch,open("/tmp/l6batch.json","w"))
    print(f"BATCH-PROBING {len(batch)} materials...",flush=True)
    res=subprocess.run(["bash",str(ROOT/"sandbox/run_shader_batch.sh"),"4.5","/tmp/l6sweep","/tmp/l6batch.json","l6sweep",a.cap],capture_output=True,text=True)
    line=[l for l in res.stdout.splitlines() if "SHADER_BATCH_JSON" in l]
    results=json.loads(line[0].split("SHADER_BATCH_JSON:")[1]) if line else []
    npass=0
    for rec in results:
        cid=rec["cid"]; mm=meta.get(cid,{})
        if rec["state"]=="pass":
            dd=ROOT/f"vault/{cid}/1.0"; dd.mkdir(parents=True,exist_ok=True)
            shutil.copy(mats/f"{cid}.blend",dd/"material.blend")
            json.dump({"canonical_id":cid,"name":mm.get("name"),"entry_type":"material","procedural":True,"lane":"L6",
                       "usage_license":mm.get("license"),"attribution":f'"{mm.get("name")}" — BlenderKit ({mm.get("license")}) — Article-5 no-export',
                       "file":"material.blend","sha256":mm.get("sha")},open(dd/"meta.json","w"),indent=2)
            subprocess.run(["uv","run",str(ROOT/".archon/scripts/shader_to_manifest.py"),mm["niche"],"pass",str(rec.get("delta",0.03)),cid])
            npass+=1
        print(f"  {mm.get('niche',cid)}: {rec['state']} d={rec.get('delta',0):.3f}",flush=True)
    print(f"L6 SWEEP: {npass}/{len(batch)} passed -> manifests written",flush=True)
if __name__=="__main__": main()
