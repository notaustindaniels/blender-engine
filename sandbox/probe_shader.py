"""probe_shader.py — runs INSIDE the sandbox; the SHADER probe variant (D-006 R37a).

Some niches are covered by a *material / shader node setup*, not mesh geometry — the geometry
probe (net_delta) and the asset probe (verts>0) both read them as empty because a shader emits NO
geometry. This probe measures a SHADER DELTA instead: apply the artifact's material to a fixed test
object under fixed lighting, render, and compare against a baseline render with the default material.
A meaningful pixel delta => the shader does something => pass.

Steps: build test scene (subdivided sphere + sun) → baseline render (default material) → apply the
candidate material (from a .blend's first material, or a named node group) → render → mean abs pixel
delta over the two frames. pass if delta >= THRESH ; partial if a material bound but delta ~0 ;
fail if no material could be bound. No external libs — pixel compare via bpy image .pixels.

Invoked:  blender -b --factory-startup -noaudio -P probe_shader.py -- <asset_path|--selftest> [cap]
Emits ONE line:  SHADER_RESULT_JSON:{"state","material","delta","render_ok"}

Same containment as the other probes (set by the runner: --network none, read-only, non-root).
"""
import bpy, sys, os, json, signal, traceback

RESULT = {"state": "fail", "material": None, "delta": 0.0, "render_ok": False, "notes": ""}
THRESH = 0.02   # mean abs pixel delta (0..1) that counts as a real shading change


def emit(**kw):
    RESULT.update(kw)
    sys.stdout.write("SHADER_RESULT_JSON:" + json.dumps(RESULT) + "\n"); sys.stdout.flush()
    os._exit(0)


def _to(s, f): emit(state="quarantine", notes="shader wall-clock cap")
signal.signal(signal.SIGALRM, _to)
_argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
try:
    _CAP = int(_argv[1]) if len(_argv) >= 2 else 110
except Exception:
    _CAP = 110
signal.alarm(max(30, _CAP))


def reset_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    for eng in ("BLENDER_EEVEE_NEXT", "BLENDER_EEVEE", "CYCLES"):   # 4.3+ , 3.6/4.2 , fallback
        try:
            sc.render.engine = eng
            break
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
    if n == 0:
        return 0.0
    return sum(abs(pa[i] - pb[i]) for i in range(n)) / n


def make_selftest_material():
    """A deliberately high-contrast procedural material so the self-test exercises the PASS branch
    (a real shader niche — lava, marble, emission FX — produces a delta of this order). Noise drives
    a black/white ramp into emission (lighting-independent), unmistakably different from default gray."""
    m = bpy.data.materials.new("selftest_proc"); m.use_nodes = True
    nt = m.node_tree
    tex = nt.nodes.new("ShaderNodeTexNoise")
    tex.inputs["Scale"].default_value = 6.0
    ramp = nt.nodes.new("ShaderNodeValToRGB")     # default is black→white full contrast
    bsdf = next((n for n in nt.nodes if n.type == "BSDF_PRINCIPLED"), None)
    nt.links.new(tex.outputs["Fac"], ramp.inputs["Fac"])
    if bsdf:
        nt.links.new(ramp.outputs["Color"], bsdf.inputs["Base Color"])
        for sock in ("Emission Color",):
            if sock in bsdf.inputs:
                nt.links.new(ramp.outputs["Color"], bsdf.inputs[sock])
        if "Emission Strength" in bsdf.inputs:
            bsdf.inputs["Emission Strength"].default_value = 2.0
    return m


def candidate_material(path):
    """First material from a .blend (or None)."""
    ext = os.path.splitext(path)[1].lower()
    if ext != ".blend":
        return None
    with bpy.data.libraries.load(path, link=False) as (src, dst):
        dst.materials = list(src.materials)
    return bpy.data.materials[0] if bpy.data.materials else None


def main():
    if not _argv:
        emit(state="quarantine", notes="no asset path / --selftest")
    obj = reset_scene()
    base = "/tmp/shader_base.png"; shaded = "/tmp/shader_after.png"
    if not render_to(base):
        emit(state="fail", notes="baseline render failed")

    if _argv[0] == "--selftest":
        mat = make_selftest_material()
    else:
        mat = candidate_material(_argv[0])
    if mat is None:
        emit(state="fail", notes="no material could be bound from artifact")
    RESULT["material"] = mat.name

    obj.data.materials.clear(); obj.data.materials.append(mat)
    RESULT["render_ok"] = render_to(shaded)
    if not RESULT["render_ok"]:
        emit(state="partial", notes="material bound but shaded render failed")
    d = mean_abs_delta(base, shaded)
    RESULT["delta"] = round(d, 5)
    emit(state="pass" if d >= THRESH else "partial",
         notes=f"material={mat.name} delta={d:.5f} thresh={THRESH}")


try:
    main()
except Exception:
    emit(state="quarantine", notes="shader probe crashed:\n" + traceback.format_exc()[:500])
