# Prescan review batch — Wave 1 (D-008 R6/R47) · 2026-07-08

Native-CI prescan flagged **159** add-ons. **143 hit a NEVER_ALLOW pattern** (subprocess/eval/
ctypes/urllib/requests/base64-decode/__import__) — these STAY quarantined permanently (R6, never
cleared, never run beyond the sandbox check). **16 are human-clearable** (benign-in-context
patterns only: socket/open-write). A human may review these against policies/prescan-allowlist.yaml
and clear the benign ones for re-probe. Clearing is a SAFETY decision, separate from niche-relevance
(triage relevance first — most are UI/utility tools).

| canonical_id | name | flagged patterns |
|---|---|---|
| pioverfour__per-camera-resolution | Per-Camera Resolution | c, l, e, a |
| yb__yb-animator-tool | YB Animator Tool | c, l, e, a |
| acggit-lj__place-helper | Place Helper | c, l, e, a |
| lumpengnom__node-color-tools-pie | Node Color Tools Pie | c, l, e, a |
| robert-kezives__k-tools-sync-lock-viewport | K-Tools: Sync | Lock Viewp | c, l, e, a |
| theanine3d__material-batch-tools | Material Batch Tools | socket |
| hisanimations__id-tools | ID Tools | c, l, e, a |
| mabaci__sprite-sheet-generator | Sprite Sheet Generator | open-write |
| linkage__linkage-marking-menu | Linkage Marking Menu | c, l, e, a |
| antoniov__storypencil-storyboard-tools | Storypencil - Storyboard T | c, l, e, a |
| atetraxx__editorbar | EditorBar | c, l, e, a |
| matthiaspatscheider__simple-renaming | Simple Renaming | c, l, e, a |
| theanine3d__source-engine-collision-tools | Source Engine Collision To | open-write |
| mr-bir__tool-hub | Tool Hub | open-write |
| xinyu-zhu__szm | szm/首字母 | c, l, e, a |
| 1p2d__scene-view-workspace-switcher | Scene/View/Workspace Switc | c, l, e, a |
