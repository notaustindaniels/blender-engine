# /// script
# requires-python = ">=3.11,<3.12"
# ///
"""Generate the SYNTHETIC golden-set fixtures (SPEC §8) into tests/fixtures/golden/.

These are deliberately-crafted test artifacts (NOT corpus/vault entries) that pin the probe's
result states: a clean generator (-> pass), a 2.7x add-on (-> legacy), a broken zip (-> fail),
a no-op add-on (-> partial), and a dangerous-API add-on (-> prescan needs_review). Real
hash-verified anchors (antlandscape, ivygen, ...) are downloaded separately and complete the
known-good set. Deterministic; re-running reproduces byte-identical zips (fixed mtime).
"""
import os, zipfile, pathlib

GOLD = pathlib.Path(__file__).resolve().parent / "fixtures" / "golden"
GOLD.mkdir(parents=True, exist_ok=True)
ZINFO_DATE = (1980, 1, 1, 0, 0, 0)  # fixed for reproducibility


def write_zip(name, files: dict):
    p = GOLD / name
    with zipfile.ZipFile(p, "w", zipfile.ZIP_DEFLATED) as z:
        for arc, content in files.items():
            zi = zipfile.ZipInfo(arc, date_time=ZINFO_DATE)
            z.writestr(zi, content)
    return p


# 1) GOOD — clean generator whose operator runs headless (bmesh cube). -> pass on all versions.
GOOD = '''\
bl_info = {"name": "Golden Good Cube", "author": "golden-fixture", "version": (1, 0, 0),
           "blender": (3, 0, 0), "category": "Add Mesh",
           "description": "test fixture: registers a headless-drivable generator"}
import bpy, bmesh

class GOLDEN_OT_make_cube(bpy.types.Operator):
    bl_idname = "object.golden_make_cube"
    bl_label = "Golden Make Cube"
    def execute(self, context):
        me = bpy.data.meshes.new("golden_cube")
        bm = bmesh.new(); bmesh.ops.create_cube(bm, size=2.0); bm.to_mesh(me); bm.free()
        ob = bpy.data.objects.new("golden_cube", me)
        context.collection.objects.link(ob)
        return {"FINISHED"}

def register(): bpy.utils.register_class(GOLDEN_OT_make_cube)
def unregister(): bpy.utils.unregister_class(GOLDEN_OT_make_cube)
'''

# 2) LEGACY — declares 2.7x and uses register_module (removed in 2.8). -> legacy on all versions.
LEGACY = '''\
bl_info = {"name": "Golden Legacy 27x", "author": "golden-fixture", "version": (0, 1),
           "blender": (2, 7, 9), "category": "Mesh",
           "description": "test fixture: pre-2.8 API, must not enable on 2.8+"}
import bpy

def register():
    bpy.utils.register_module(__name__)     # AttributeError on Blender 2.8+

def unregister():
    bpy.utils.unregister_module(__name__)
'''

# 3) NOOP — enables + registers an operator but produces no geometry. -> partial on all versions.
NOOP = '''\
bl_info = {"name": "Golden Noop", "author": "golden-fixture", "version": (1, 0),
           "blender": (3, 0, 0), "category": "Object",
           "description": "test fixture: enables and registers but generates nothing"}
import bpy

class GOLDEN_OT_noop(bpy.types.Operator):
    bl_idname = "object.golden_noop"
    bl_label = "Golden Noop"
    def execute(self, context):
        return {"FINISHED"}   # deliberately no geometry delta

def register(): bpy.utils.register_class(GOLDEN_OT_noop)
def unregister(): bpy.utils.unregister_class(GOLDEN_OT_noop)
'''

# 4) DANGER — contains dangerous-API patterns for prescan (§3.4). -> prescan: needs_review.
DANGER = '''\
bl_info = {"name": "Golden Danger", "author": "golden-fixture", "version": (1, 0),
           "blender": (3, 0, 0), "category": "System",
           "description": "test fixture: trips the danger prescan; must NOT reach the container"}
import bpy, os, subprocess

def _oops():
    subprocess.Popen(["/bin/true"])          # subprocess -> flagged
    eval("1 + 1")                            # eval( -> flagged
    __import__("urllib.request")             # __import__ + urllib -> flagged

def register(): pass
def unregister(): pass
'''

write_zip("golden_good_cube.zip", {"golden_good_cube/__init__.py": GOOD})
write_zip("golden_legacy_27x.zip", {"golden_legacy_27x/__init__.py": LEGACY})
write_zip("golden_noop.zip", {"golden_noop/__init__.py": NOOP})
write_zip("golden_danger.zip", {"golden_danger/__init__.py": DANGER})

# 5) BROKEN — not a valid zip at all. -> fail (broken archive) on all versions.
(GOLD / "golden_broken.zip").write_bytes(b"PK\x03\x04 this is not a real zip file \x00\xff\xfe garbage")

print("golden fixtures written to", GOLD)
for f in sorted(GOLD.glob("golden_*")):
    print(f"  {f.name}  ({f.stat().st_size} bytes)")
