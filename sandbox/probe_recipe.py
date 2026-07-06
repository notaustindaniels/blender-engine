"""probe_recipe.py — runs INSIDE the sandbox; the recipe-probe mode (D-003 R21).

A recipe covers a niche by COMPOSING operators (from vaulted add-ons) and/or built-in Blender
features. This script installs the recipe's add-on(s), enables them, then attempts to DRIVE the
composition to a geometry delta — trying, in order: plain call, EXEC_DEFAULT, EXEC_DEFAULT with a
VIEW_3D context override, and (for built-in modifier steps) adding the modifier and evaluating.
A recipe is `recipe_verified` ONLY if the composition produces a non-empty geometry/material delta
AND a frame renders (same bar as a single-operator pass, §3.1). Otherwise `recipe_unverified`.

Invoked:  blender -b --factory-startup -noaudio -P probe_recipe.py -- <recipe_json> <ver> [cap]
  recipe_json = {"niche","steps":[{"artifact":"/path.zip","module_hint":"","op":"mesh.x"} | {"builtin":"OCEAN"}]}
Emits ONE line:  RECIPE_RESULT_JSON:{"niche","state":"recipe_verified|recipe_unverified","notes",...}

DEFENSIVE: every bpy call guarded; a crash => recipe_unverified, never a harness abort. Reuses the
exact containment the single-probe uses (mounted read-only, --network none — set by run_recipe.sh).
"""
import bpy, sys, os, json, re, io, zipfile, signal, contextlib, traceback

RESULT = {"niche": None, "state": "recipe_unverified", "render_ok": False, "steps_ok": [], "notes": ""}


def emit(**kw):
    RESULT.update(kw)
    sys.stdout.write("RECIPE_RESULT_JSON:" + json.dumps(RESULT) + "\n"); sys.stdout.flush()
    os._exit(0)


def _to(sig, frame): emit(state="recipe_unverified", notes="recipe wall-clock cap")
signal.signal(signal.SIGALRM, _to)
_argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
try:
    _CAP = int(_argv[2]) if len(_argv) >= 3 else 110
except Exception:
    _CAP = 110
signal.alarm(max(30, _CAP))
VER = bpy.app.version


def counts():
    d = bpy.data
    return len(d.meshes) + len(d.curves) + len(d.objects) + len(d.materials) + len(d.node_groups)


def normalize_archive(path):
    """GitHub archives wrap the add-on in 'repo-branch/'. If nested >=2 deep, repack ONLY the add-on
    so addon_install/extensions see a clean package (same fix as probe.py). Ephemeral; provenance
    unaffected."""
    if not path.lower().endswith(".zip"):
        return path
    try:
        z = zipfile.ZipFile(path); names = z.namelist()
    except Exception:
        return path
    mans = sorted([n for n in names if n.endswith("blender_manifest.toml")], key=lambda p: p.count("/"))
    root = None
    if mans:
        root = mans[0].rsplit("/", 1)[0] if "/" in mans[0] else ""
    else:
        for n in sorted([n for n in names if n.endswith("__init__.py")], key=lambda p: p.count("/")):
            try:
                if b"bl_info" in z.read(n):
                    root = n.rsplit("/", 1)[0] if "/" in n else ""; break
            except Exception:
                pass
    if root is None or root.count("/") < 1:
        return path
    pkg = root.rsplit("/", 1)[-1]; out = "/tmp/clean_recipe_addon.zip"; prefix = root + "/"
    try:
        with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zo:
            for n in names:
                if n.startswith(prefix) and not n.endswith("/"):
                    zo.writestr(f"{pkg}/{n[len(prefix):]}", z.read(n))
        return out
    except Exception:
        return path


def install_enable(path):
    """Install+enable an add-on zip (extension or legacy). Returns module name or None."""
    stderr = io.StringIO()
    path = normalize_archive(path)   # repack GitHub-wrapped archives first (bugfix)
    try:
        z = zipfile.ZipFile(path); names = z.namelist()
    except Exception:
        return None
    man = [n for n in names if n.endswith("blender_manifest.toml")]
    if man and VER >= (4, 2):
        pid = re.search(r'^\s*id\s*=\s*"([^"]+)"', z.read(man[0]).decode("utf-8", "ignore"), re.M)
        try:
            with contextlib.redirect_stderr(stderr):
                bpy.ops.extensions.package_install_files(filepath=path, repo="user_default", enable_on_install=True)
        except Exception:
            pass
        mod = f"bl_ext.user_default.{pid.group(1)}" if pid else None
        if mod and mod in bpy.context.preferences.addons:
            return mod
    # legacy
    import addon_utils
    try:
        before = {m.__name__ for m in addon_utils.modules()}
        with contextlib.redirect_stderr(stderr):
            bpy.ops.preferences.addon_install(filepath=path, overwrite=True)
        addon_utils.modules_refresh()
        for mod in ({m.__name__ for m in addon_utils.modules()} - before):
            try:
                bpy.ops.preferences.addon_enable(module=mod)
                if mod in bpy.context.preferences.addons:
                    return mod
            except Exception:
                pass
    except Exception:
        pass
    return None


def view3d_override():
    try:
        win = bpy.context.window_manager.windows[0]
        for s in bpy.data.screens:
            for a in s.areas:
                if a.type == "VIEW_3D":
                    reg = next((r for r in a.regions if r.type == "WINDOW"), None)
                    return {"window": win, "screen": s, "area": a, "region": reg,
                            "scene": bpy.context.scene, "view_layer": bpy.context.view_layer}
    except Exception:
        pass
    return None


def drive_op(op_id, params, ov):
    """Return 'delta' (added geometry), 'ran' (FINISHED, in-place modify — fine for a step), or
    'noop' (never executed — dialog-gated/cancelled). A recipe needs a NET delta overall, not a
    delta per step, so an in-place 'ran' step (e.g. erosion) is acceptable."""
    cat, name = op_id.split(".", 1)
    try:
        fn = getattr(getattr(bpy.ops, cat), name)
    except Exception:
        return "noop"
    before = counts()
    for how in ("exec_params", "plain", "override"):
        ret = None
        try:
            if how == "exec_params":
                ret = fn('EXEC_DEFAULT', **(params or {}))
            elif how == "plain":
                ret = fn()
            elif ov:
                with bpy.context.temp_override(**{k: v for k, v in ov.items() if v}):
                    ret = fn('EXEC_DEFAULT', **(params or {}))
        except Exception:
            ret = None
        if counts() > before:
            return "delta"
        if ret and "FINISHED" in ret:
            return "ran"
    return "noop"


def add_builtin_modifier(mtype):
    try:
        if not bpy.context.selected_objects:
            bpy.ops.mesh.primitive_grid_add()
        obj = bpy.context.active_object
        before = counts()
        obj.modifiers.new("m", mtype)
        bpy.context.view_layer.update()
        obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
        return True
    except Exception:
        return False


def render():
    try:
        sc = bpy.context.scene; sc.render.engine = "CYCLES"
        try:
            sc.cycles.device = "CPU"; sc.cycles.samples = 1
        except Exception:
            pass
        sc.render.resolution_x = sc.render.resolution_y = 64
        sc.render.filepath = "/tmp/recipe_render.png"
        if not any(o.type == "CAMERA" for o in bpy.data.objects):
            c = bpy.data.cameras.new("c"); co = bpy.data.objects.new("c", c)
            bpy.context.collection.objects.link(co); sc.camera = co
        bpy.ops.render.render(write_still=True)
        return os.path.exists("/tmp/recipe_render.png") and os.path.getsize("/tmp/recipe_render.png") > 0
    except Exception:
        return False


def main():
    recipe = json.loads(_argv[0])
    RESULT["niche"] = recipe.get("niche")
    ov = view3d_override()
    baseline = counts()          # factory scene (cube+cam+light)
    no_step_errored = True
    for st in recipe.get("steps", []):
        if st.get("builtin"):
            status = "ran" if add_builtin_modifier(st["builtin"]) else "noop"
        else:
            art = st.get("artifact")
            if art and os.path.exists(art):
                install_enable(art)
            status = drive_op(st["op"], st.get("params"), ov) if st.get("op") else "noop"
        RESULT["steps_ok"].append({"step": st.get("op") or st.get("builtin"), "status": status})
        if status == "noop":     # a step that never executed breaks the composition
            no_step_errored = False
    net_delta = counts() > baseline
    RESULT["render_ok"] = render()
    # VERIFIED iff: every step executed (no noop) AND the recipe produced NET new geometry AND renders
    verified = no_step_errored and net_delta and RESULT["render_ok"]
    emit(state="recipe_verified" if verified else "recipe_unverified",
         notes=f"steps={[s['status'] for s in RESULT['steps_ok']]} net_delta={net_delta} render={RESULT['render_ok']}")


try:
    main()
except Exception:
    emit(state="recipe_unverified", notes="recipe probe crashed:\n" + traceback.format_exc()[:600])
