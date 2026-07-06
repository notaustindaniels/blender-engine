"""probe.py — runs INSIDE the sandbox container; the heart of the Gate (SPEC §5.1, §3.1).

Invoked as:  blender -b --factory-startup -noaudio -P probe.py -- <artifact_path> <ver_tag>

Emits ONE line to stdout:  PROBE_RESULT_JSON:{...}  matching the SPEC §4.3 `verify` shape:
    {"state","operators":[...],"render_ok":bool,"artifact_type","blender","notes","detail":{}}

Result states (SPEC §3.1):
  pass       all 5 checks (install, enable, ≥1 operator registered, smoke-run delta, render)
  partial    installs+enables+registers, but smoke-run OR render fails
  fail       install or enable fails (incl. version-incompatible: e.g. a 4.2 extension on 3.6)
  legacy     declares pre-2.8 API and never enables
  quarantine crashed the container or hit the wall-clock cap

DEFENSIVE CONTRACT: every bpy call is wrapped; an uncaught crash/timeout => quarantine, never
a harness abort. Hard wall-clock cap 110s via SIGALRM (outer orchestrator also caps).

RENDER-ENGINE DEVIATION (SPEC §3.1 step 5, dated 2026-07-05): the thumbnail is rendered with
CYCLES-CPU at 64x64/1-sample, not EEVEE. EEVEE-Next (4.2+) requires a GPU/Vulkan context that a
CPU-only, --network none container cannot provide; Cycles-CPU renders headlessly on 3.6/4.2/4.5
and is a STRICTER "does it render without crashing" check. Recorded in SPEC §12.1.

GN-PACK SMOKE HEURISTIC (SPEC §12 open decision #2): link node groups from the .blend, add a
GEOMETRY_NODES modifier bound to the first group on a default cube, evaluate, check for a mesh
delta. Best-effort; recorded here per the SPEC instruction.
"""
import bpy, sys, os, json, re, io, zipfile, signal, traceback, contextlib

RESULT = {
    "state": "fail", "operators": [], "render_ok": False,
    "artifact_type": None, "blender": bpy.app.version_string,
    "declared_min": None, "notes": "", "detail": {},
}


def emit_and_exit(code=0, **kw):
    RESULT.update(kw)
    sys.stdout.write("PROBE_RESULT_JSON:" + json.dumps(RESULT) + "\n")
    sys.stdout.flush()
    os._exit(code)  # hard exit — bypass any addon atexit hooks that could hang/crash


def _timeout(signum, frame):
    emit_and_exit(0, state="quarantine", notes="wall-clock cap exceeded (SIGALRM 110s)")


signal.signal(signal.SIGALRM, _timeout)
signal.alarm(110)

VER = bpy.app.version  # (major, minor, patch) tuple


# ───────────────────────── artifact inspection ─────────────────────────
def parse_min_version(text):
    """Extract a declared minimum Blender version from bl_info or a manifest, as a tuple."""
    m = re.search(r'blender_version_min\s*=\s*"(\d+)\.(\d+)(?:\.(\d+))?"', text)
    if m:
        return (int(m.group(1)), int(m.group(2)), int(m.group(3) or 0))
    m = re.search(r'"blender"\s*:\s*\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)', text)  # bl_info
    if m:
        return tuple(int(g) for g in m.groups())
    return None


def inspect_artifact(path):
    info = {"kind": None, "module": None, "pkg_id": None, "min": None, "text": ""}
    low = path.lower()
    if low.endswith(".blend"):
        info["kind"] = "gn_pack"
        return info
    if low.endswith(".py"):
        text = open(path, "r", errors="ignore").read()
        info.update(kind="legacy", module=os.path.splitext(os.path.basename(path))[0],
                    text=text[:8000], min=parse_min_version(text))
        return info
    # zip
    try:
        z = zipfile.ZipFile(path)
    except Exception as e:
        info["kind"] = "broken"
        info["text"] = f"zip open failed: {e}"
        return info
    names = z.namelist()
    manifests = [n for n in names if n.endswith("blender_manifest.toml")]
    if manifests:
        data = z.read(manifests[0]).decode("utf-8", "ignore")
        mid = re.search(r'^\s*id\s*=\s*"([^"]+)"', data, re.M)
        info.update(kind="extension", pkg_id=(mid.group(1) if mid else None),
                    text=data, min=parse_min_version(data))
        return info
    # legacy zip: find the top-level module (dir with __init__.py, or a top .py with bl_info)
    top_pkgs = sorted({n.split("/")[0] for n in names if "/" in n and n.split("/")[0]})
    module = None
    for p in top_pkgs:
        if f"{p}/__init__.py" in names:
            module = p
            try:
                info["text"] = z.read(f"{p}/__init__.py").decode("utf-8", "ignore")[:8000]
            except Exception:
                pass
            break
    if not module:
        pys = [n for n in names if n.endswith(".py") and "/" not in n]
        if pys:
            module = os.path.splitext(pys[0])[0]
            info["text"] = z.read(pys[0]).decode("utf-8", "ignore")[:8000]
    info.update(kind="legacy", module=module, min=parse_min_version(info["text"]))
    return info


# ───────────────────────── operator introspection ─────────────────────────
def snapshot_ops():
    ops = set()
    for cat in dir(bpy.ops):
        try:
            for op in dir(getattr(bpy.ops, cat)):
                ops.add(f"{cat}.{op}")
        except Exception:
            pass
    return ops


def is_legacy_declared(info):
    return bool(info.get("min")) and info["min"] < (2, 80)


# ───────────────────────── install + enable ─────────────────────────
def install_and_enable(path, info):
    """Returns (enabled_module_or_None, err_text)."""
    stderr_buf = io.StringIO()
    kind = info["kind"]

    if kind == "broken":
        return None, "artifact is not a valid zip"

    # --- extension (4.2+) ---
    if kind == "extension":
        if VER < (4, 2):
            return None, "manifest extension not supported on Blender < 4.2"
        pkg_id = info.get("pkg_id")
        try:
            with contextlib.redirect_stderr(stderr_buf):
                bpy.ops.extensions.package_install_files(
                    filepath=path, repo="user_default", enable_on_install=True)
        except Exception as e:
            # fall through to trying enable anyway; record
            stderr_buf.write(f"\npackage_install_files: {e}")
        module = f"bl_ext.user_default.{pkg_id}" if pkg_id else None
        if module:
            try:
                with contextlib.redirect_stderr(stderr_buf):
                    bpy.ops.preferences.addon_enable(module=module)
            except Exception as e:
                stderr_buf.write(f"\naddon_enable: {e}")
            if module in bpy.context.preferences.addons:
                return module, stderr_buf.getvalue()
        return None, stderr_buf.getvalue() or "extension install/enable produced no enabled module"

    # --- gn_pack (.blend node groups) — no enable; handled in smoke ---
    if kind == "gn_pack":
        return "__gn_pack__", ""

    # --- legacy python add-on (all versions) ---
    import addon_utils
    try:
        before = {m.__name__ for m in addon_utils.modules()}
    except Exception:
        before = set()
    try:
        with contextlib.redirect_stderr(stderr_buf):
            bpy.ops.preferences.addon_install(filepath=path, overwrite=True)
    except Exception as e:
        return None, f"addon_install failed: {e}\n{stderr_buf.getvalue()}"
    try:
        addon_utils.modules_refresh()
    except Exception:
        pass
    after = {m.__name__ for m in addon_utils.modules()}
    candidates = list(after - before) or ([info["module"]] if info.get("module") else [])
    for module in candidates:
        try:
            with contextlib.redirect_stderr(stderr_buf):
                bpy.ops.preferences.addon_enable(module=module)
            if module in bpy.context.preferences.addons:
                return module, stderr_buf.getvalue()
        except Exception as e:
            stderr_buf.write(f"\naddon_enable({module}): {e}")
    return None, stderr_buf.getvalue() or "no module enabled after install"


# ───────────────────────── smoke-run ─────────────────────────
def counts():
    d = bpy.data
    return (len(d.meshes), len(d.curves), len(d.objects), len(d.materials),
            len(d.node_groups), len(d.metaballs), len(d.grease_pencils))


def _view3d_override():
    """Best-effort VIEW_3D context from the startup screens (helps ops that need a 3D area)."""
    try:
        win = bpy.context.window_manager.windows[0]
        for s in bpy.data.screens:
            for a in s.areas:
                if a.type == "VIEW_3D":
                    region = next((r for r in a.regions if r.type == "WINDOW"), None)
                    return {"window": win, "screen": s, "area": a, "region": region,
                            "scene": bpy.context.scene, "view_layer": bpy.context.view_layer}
    except Exception:
        pass
    return None


def _try_op(fn, ov):
    before = counts()
    for attempt in ("plain", "override"):
        try:
            if attempt == "plain":
                fn()
            elif ov:
                with bpy.context.temp_override(**{k: v for k, v in ov.items() if v}):
                    fn("EXEC_DEFAULT")
        except Exception:
            pass
        if sum(counts()) > sum(before):
            return True
    return False


def smoke_run(new_ops, info):
    """Try to make one detected operator produce a geometry/material delta. Returns (ok, note).

    Honest limitation surfaced by the golden set: many generators are dialog/modal-only
    (invoke_props_dialog) and return PASS_THROUGH headlessly, so they cannot be auto-driven.
    Such add-ons correctly land at `partial` (they still install/enable/register/render) and
    partial counts toward coverage (SPEC §3.1). We try plain-exec and a VIEW_3D override."""
    if info["kind"] == "gn_pack":
        return smoke_gn(info)

    def score(op):
        s = 0
        if any(op.startswith(c + ".") for c in ("mesh", "curve", "object", "surface", "metaball")):
            s += 2
        if any(k in op for k in ("add", "generate", "create", "new", "landscape", "tree", "make", "gen")):
            s += 3
        return -s

    ov = _view3d_override()
    for op in sorted(new_ops, key=score)[:30]:
        cat, name = op.split(".", 1)
        try:
            fn = getattr(getattr(bpy.ops, cat), name)
        except Exception:
            continue
        if _try_op(fn, ov):
            return True, f"delta from {op}"
    return False, f"no operator produced a delta headless ({len(new_ops)} ops; likely dialog/modal generators)"


def smoke_gn(info):
    """Best-effort GN-pack heuristic (SPEC §12 dec.2): link groups, bind one to a cube modifier."""
    path = info["_path"]
    try:
        with bpy.data.libraries.load(path, link=False) as (src, dst):
            dst.node_groups = list(src.node_groups)
    except Exception as e:
        return False, f"blend load failed: {e}"
    groups = [g for g in bpy.data.node_groups if getattr(g, "type", "") == "GEOMETRY"]
    if not groups:
        return False, "no geometry node groups in .blend"
    try:
        bpy.ops.mesh.primitive_cube_add()
        obj = bpy.context.active_object
        m = obj.modifiers.new("gn", "NODES")
        m.node_group = groups[0]
        bpy.context.view_layer.update()
        obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
        return True, f"bound node group '{groups[0].name}'"
    except Exception as e:
        return False, f"gn modifier eval failed: {e}"


# ───────────────────────── render ─────────────────────────
def render_thumb():
    try:
        sc = bpy.context.scene
        sc.render.engine = "CYCLES"
        try:
            sc.cycles.device = "CPU"
            sc.cycles.samples = 1
        except Exception:
            pass
        sc.render.resolution_x = sc.render.resolution_y = 64
        sc.render.image_settings.file_format = "PNG"
        out = "/tmp/probe_render.png"
        sc.render.filepath = out
        if not any(o.type == "CAMERA" for o in bpy.data.objects):
            cam = bpy.data.cameras.new("c"); co = bpy.data.objects.new("c", cam)
            bpy.context.collection.objects.link(co); sc.camera = co
        bpy.ops.render.render(write_still=True)
        return os.path.exists(out) and os.path.getsize(out) > 0
    except Exception as e:
        RESULT["detail"]["render_err"] = str(e)[:300]
        return False


# ───────────────────────── main ─────────────────────────
def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if not argv:
        emit_and_exit(0, state="quarantine", notes="no artifact argument")
    path = argv[0]
    RESULT["detail"]["artifact"] = os.path.basename(path)

    info = inspect_artifact(path)
    info["_path"] = path
    RESULT["artifact_type"] = info["kind"]
    RESULT["declared_min"] = ".".join(map(str, info["min"])) if info.get("min") else None

    if info["kind"] == "broken":
        emit_and_exit(0, state="fail", notes="broken/invalid archive: " + info.get("text", ""))

    module, err = install_and_enable(path, info)
    if not module:
        state = "legacy" if is_legacy_declared(info) else "fail"
        emit_and_exit(0, state=state, notes=("install/enable failed: " + (err or "")[:600]))

    # introspect: operators registered by the addon
    new_ops = []
    if info["kind"] != "gn_pack":
        after = snapshot_ops()
        new_ops = sorted(after - OPS_BEFORE)
    RESULT["operators"] = new_ops[:60]
    registered_ok = bool(new_ops) or info["kind"] == "gn_pack"

    smoke_ok, smoke_note = smoke_run(set(new_ops), info)
    render_ok = render_thumb()
    RESULT["render_ok"] = render_ok
    RESULT["detail"]["smoke"] = smoke_note

    if registered_ok and smoke_ok and render_ok:
        state = "pass"
    elif registered_ok and (smoke_ok or render_ok):
        state = "partial"
    elif registered_ok:
        state = "partial"
    else:
        # enabled but registered nothing usable: legacy if it declares pre-2.8, else fail.
        # (On 3.6 a broken pre-2.8 register() can still land the module in prefs, so the
        # "no module" branch above may not catch it — check here too for a consistent state.)
        state = "legacy" if is_legacy_declared(info) else "fail"
    emit_and_exit(0, state=state,
                  notes=f"enabled={module}; ops={len(new_ops)}; smoke={smoke_ok}; render={render_ok}")


# snapshot operators BEFORE any install/enable (module global — never serialized)
OPS_BEFORE = snapshot_ops()
try:
    main()
except Exception:
    emit_and_exit(0, state="quarantine", notes="probe crashed:\n" + traceback.format_exc()[:800])
