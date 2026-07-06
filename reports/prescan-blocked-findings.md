# Prescan-Blocked Findings — recorded quarantines (SPEC §3.4; D-002 R12)

Artifacts the human review (2026-07-06, source-inspected) confirmed should STAY prescan-blocked:
records, not verified, contributing no coverage. The exec/network-capable patterns can never be
allowlisted (`prescan.py` `NEVER_ALLOW`), so these remain human-gated by design.

| artifact | gating patterns | finding | disposition |
|---|---|---|---|
| `charlesss07__blender-python-nodes` | `eval(`, urllib, requests | A "2D Python IDE" whose `PythonEvalStatementNode` runs `eval(self.arbitrary_code)` — arbitrary-Python execution IS its purpose; `PythonRequestURLNode` fetches URLs. Its operators are **inadmissible** for the corpus (an agent must never auto-invoke arbitrary-eval). | **BLOCKED — confirmed code-executor** |
| `dingdio__witcher3-blender-tools` | base64, ctypes, `__import__`, subprocess, `eval(` | Windows game-modding tool: `ctypes.windll` reads Witcher-3 game binaries, `explorer` file-browser, base64 is display-truncation of image-byte strings. `eval`/`__import__` not line-by-line vetted. Not Terrain/Vegetation. | **BLOCKED — pending deeper review** |
| `itscubetime__fastpbr` | subprocess, os.system, `exec(`, ctypes | Windows-centric PBR viewport tool: `os.system('explorer …')` file browser; `exec`/subprocess/ctypes not fully vetted. Not Terrain/Vegetation. | **BLOCKED — pending deeper review** |

**Cleared in the same review** (see `reviews/prescan_clearances.yaml`):
`aachman98__sorcar` (opt-in `ScCustomPythonScript` node not fired by verification; numeric node-value
`eval`; updater `urllib` — recovers abstract `parametric_surface_nodes`) and `emgi96__trailprint3d`
(exec/`__import__` were test-only; rest is network-blocked map-fetching; min Blender 5.1 → skipped on
our 3.6/4.2/4.5 matrix).

Coverage recovery from R12 is therefore modest and honest: **Sorcar** (abstract node coverage) is the
one real recovery; trailprint3d is version-out-of-range; the 3 above stay quarantined records.
