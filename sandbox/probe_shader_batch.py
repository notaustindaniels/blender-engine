"""probe_shader_batch.py — BATCHED shader probe (D-008 L6 throughput). Same logic as probe_shader.py
but amortizes the expensive parts across MANY materials in ONE Blender session: build the test scene +
render the baseline ONCE, then for each material .blend { append its material, apply, render, delta vs
the shared baseline, purge }. Turns per-material cost from (container+Blender startup+baseline+applied
render) into just (one applied render) — the throughput fix for the 600-material L6 sweep under emulation.

Invoked:  blender -b --factory-startup -noaudio -P probe_shader_batch.py -- <batch.json> [percap_s]
  batch.json = [{"cid": "...", "path": "/work/mats/<cid>.blend"}, ...]
Emits ONE line:  SHADER_BATCH_JSON:[{"cid","state","delta","material","render_ok"}, ...]
Containment set by the runner (--network none, read-only, non-root). No external libs.
"""
import bpy, sys, os, json, signal, traceback

THRESH = 0.02
_argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
RESULTS = []


def emit():
    sys.stdout.write("SHADER_BATCH_JSON:" + json.dumps(RESULTS) + "\n"); sys.stdout.flush()
    os._exit(0)


def _to(s, f):
    # wall-clock cap for the whole batch: whatever's done is emitted; the rest is unrun
    emit()
signal.signal(signal.SIGALRM, _to)
try:
    _CAP = int(_argv[1]) if len(_argv) >= 2 else 540
except Exception:
    _CAP = 540
signal.alarm(max(60, _CAP))


def reset_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    for eng in ("BLENDER_EEVEE_NEXT", "BLENDER_EEVEE", "CYCLES"):
        try:
            sc.render.engine = eng; break
        except Exception:
            continue
    sc.render.resolution_x = sc.render.resolution_y = 128
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=3)
    obj = bpy.context.active_object
    bpy.ops.object.shade_smooth()
    light = bpy.data.objects.new("sun", bpy.data.lights.new("sun", "SUN"))
    bpy.context.collection.objects.link(light); light.location = (4, -4, 6)
    cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam"))
    bpy.context.collection.objects.link(cam); cam.location = (0, -4, 0)
    cam.rotation_euler = (1.5708, 0, 0); sc.camera = cam
    return obj


def render_to(path):
    bpy.context.scene.render.filepath = path
    bpy.ops.render.render(write_still=True)
    return os.path.exists(path) and os.path.getsize(path) > 0


def mean_abs_delta(p1, p2):
    a = bpy.data.images.load(p1); b = bpy.data.images.load(p2)
    pa, pb = list(a.pixels), list(b.pixels)
    n = min(len(pa), len(pb))
    bpy.data.images.remove(a); bpy.data.images.remove(b)
    if n == 0:
        return 0.0
    return sum(abs(pa[i] - pb[i]) for i in range(n)) / n


def append_new_material(path):
    """Append materials from a .blend and return the FIRST NEWLY-added one (not a stale [0])."""
    if os.path.splitext(path)[1].lower() != ".blend":
        return None, []
    before = set(m.name for m in bpy.data.materials)
    try:
        with bpy.data.libraries.load(path, link=False) as (src, dst):
            dst.materials = list(src.materials)
    except Exception:
        return None, []
    added = [m for m in bpy.data.materials if m.name not in before]
    return (added[0] if added else None), added


def main():
    if not _argv:
        emit()
    batch = json.loads(open(_argv[0]).read())
    obj = reset_scene()
    base = "/tmp/base.png"
    if not render_to(base):
        for e in batch:
            RESULTS.append({"cid": e["cid"], "state": "fail", "delta": 0.0, "render_ok": False, "notes": "baseline failed"})
        emit()
    for i, e in enumerate(batch):
        rec = {"cid": e["cid"], "state": "fail", "delta": 0.0, "render_ok": False, "material": None}
        try:
            mat, added = append_new_material(e["path"])
            if mat is None:
                rec["notes"] = "no material bound"
            else:
                rec["material"] = mat.name
                obj.data.materials.clear(); obj.data.materials.append(mat)
                shaded = f"/tmp/s{i}.png"
                rec["render_ok"] = render_to(shaded)
                if rec["render_ok"]:
                    d = round(mean_abs_delta(base, shaded), 5)
                    rec["delta"] = d
                    rec["state"] = "pass" if d >= THRESH else "partial"
                    try:
                        os.remove(shaded)
                    except Exception:
                        pass
                else:
                    rec["state"] = "partial"
            # purge appended materials so the next iteration's "new" detection is clean + memory stays flat
            obj.data.materials.clear()
            for m in added:
                try:
                    bpy.data.materials.remove(m)
                except Exception:
                    pass
        except Exception:
            rec["state"] = "quarantine"; rec["notes"] = "probe error"
        RESULTS.append(rec)
    emit()


try:
    main()
except Exception:
    RESULTS.append({"cid": "_batch", "state": "quarantine", "notes": traceback.format_exc()[:300]})
    emit()
