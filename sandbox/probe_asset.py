"""probe_asset.py — runs INSIDE the sandbox; the ASSET probe variant (D-004 R27).

A-lane items are ASSETS (models), not add-ons — so the gate is import-and-render, not install/enable/
smoke-run. Steps: import (gltf/glb/fbx/obj/blend) → assert non-empty geometry → workbench render
thumbnail → capture format. License+attribution are captured by the acquire step (from the source
API/page), not here. Pure mesh formats carry no code; `.blend` still gets a driver/embedded-script
scan UPSTREAM (prescan) — this probe assumes that already passed.

Invoked:  blender -b --factory-startup -noaudio -P probe_asset.py -- <asset_path> [cap]
Emits ONE line:  ASSET_RESULT_JSON:{"state":"pass|partial|fail|quarantine","format","verts","render_ok"}
  pass = imported + non-empty geometry + rendered ; partial = imported geometry but render failed ;
  fail = import produced no geometry / unsupported ; quarantine = crash/timeout.

Same containment as the other probes (set by the runner: --network none, read-only, non-root).
"""
import bpy, sys, os, json, signal, traceback

RESULT = {"state": "fail", "format": None, "verts": 0, "render_ok": False, "notes": ""}


def emit(**kw):
    RESULT.update(kw)
    sys.stdout.write("ASSET_RESULT_JSON:" + json.dumps(RESULT) + "\n"); sys.stdout.flush()
    os._exit(0)


def _to(s, f): emit(state="quarantine", notes="asset wall-clock cap")
signal.signal(signal.SIGALRM, _to)
_argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
try:
    _CAP = int(_argv[1]) if len(_argv) >= 2 else 110
except Exception:
    _CAP = 110
signal.alarm(max(30, _CAP))


def total_verts():
    """Count geometry the asset actually yields. Uses DEPSGRAPH-EVALUATED meshes so a
    geometry-nodes generator (small/empty base mesh, geometry produced by the GN modifier at
    eval time) is measured by what it emits, not its placeholder base — otherwise a real GN
    generator with a 0-vert base would falsely read as 'zero geometry'. Falls back to base
    verts if evaluation is unavailable."""
    n = 0
    try:
        deps = bpy.context.evaluated_depsgraph_get()
    except Exception:
        deps = None
    for o in bpy.data.objects:
        if o.type != "MESH":
            continue
        counted = False
        if deps is not None:
            try:
                oe = o.evaluated_get(deps)
                me = oe.to_mesh()
                if me is not None:
                    n += len(me.vertices); counted = True
                    oe.to_mesh_clear()
            except Exception:
                pass
        if not counted and o.data:
            n += len(o.data.vertices)
    return n


def do_import(path):
    ext = os.path.splitext(path)[1].lower()
    RESULT["format"] = ext
    try:
        if ext in (".gltf", ".glb"):
            bpy.ops.import_scene.gltf(filepath=path)
        elif ext == ".fbx":
            bpy.ops.import_scene.fbx(filepath=path)
        elif ext == ".obj":
            try:
                bpy.ops.wm.obj_import(filepath=path)      # 4.x
            except Exception:
                bpy.ops.import_scene.obj(filepath=path)   # 3.6
        elif ext == ".blend":
            with bpy.data.libraries.load(path, link=False) as (src, dst):
                dst.objects = list(src.objects)
            for o in bpy.data.objects:
                if o.name not in bpy.context.scene.objects:
                    try:
                        bpy.context.collection.objects.link(o)
                    except Exception:
                        pass
        else:
            return False, f"unsupported format {ext}"
        return True, "imported"
    except Exception as e:
        return False, f"import failed: {e}"


def render():
    try:
        sc = bpy.context.scene
        sc.render.engine = "BLENDER_WORKBENCH"     # cheapest, no material eval needed
        sc.render.resolution_x = sc.render.resolution_y = 128
        sc.render.filepath = "/tmp/asset_render.png"
        if not any(o.type == "CAMERA" for o in bpy.data.objects):
            c = bpy.data.cameras.new("c"); co = bpy.data.objects.new("c", c)
            bpy.context.collection.objects.link(co); sc.camera = co
            # frame the imported geometry
            try:
                bpy.ops.object.select_all(action="SELECT")
                bpy.ops.view3d.camera_to_view_selected()
            except Exception:
                co.location = (6, -6, 4)
        bpy.ops.render.render(write_still=True)
        return os.path.exists("/tmp/asset_render.png") and os.path.getsize("/tmp/asset_render.png") > 0
    except Exception as e:
        RESULT["notes"] = f"render err: {str(e)[:200]}"
        return False


def main():
    if not _argv:
        emit(state="quarantine", notes="no asset path")
    path = _argv[0]
    ok, note = do_import(path)
    if not ok:
        emit(state="fail", notes=note)
    v = total_verts()
    RESULT["verts"] = v
    if v == 0:
        emit(state="fail", notes="imported but zero geometry")
    RESULT["render_ok"] = render()
    emit(state="pass" if RESULT["render_ok"] else "partial",
         notes=f"verts={v} render={RESULT['render_ok']}")


try:
    main()
except Exception:
    emit(state="quarantine", notes="asset probe crashed:\n" + traceback.format_exc()[:500])
