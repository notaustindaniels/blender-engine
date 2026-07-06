# Prescan Findings — batched review (SPEC §12.2)

- artifacts scanned: **26**
- flagged `needs_review` (gating hit): **11**
- allowlist-downgraded to clean (benign patterns only): **4**
- human-cleared (with cited rationale): **8**
- **false-positive rate: 72.7%** (flagged-then-cleared / flagged) — high FP means the scanner is over-aggressive and the allowlist should grow
- **still blocked (awaiting review): 3** ['charlesss07__blender-python-nodes.zip', 'dingdio__witcher3-blender-tools.zip', 'itscubetime__fastpbr.zip']

| artifact | status | gating patterns | allowlisted (informational) |
|---|---|---|---|
| `aachman98__sorcar.zip` | cleared | urllib, eval(, exec( | open-write |
| `add-on-modular-tree-v5.5.2-linux-x64.zip` | clean | — | socket |
| `charlesss07__blender-python-nodes.zip` | needs_review | eval(, urllib, requests | socket |
| `add-on-antlandscape-v0.2.0.zip` | clean | — | open-write |
| `add-on-ivygen-v0.1.5.zip` | clean | — | — |
| `add-on-sapling-tree-gen-v0.3.7.zip` | cleared | eval( | — |
| `add-on-scatter-objects-v0.2.0.zip` | clean | — | — |
| `dingdio__witcher3-blender-tools.zip` | needs_review | base64-decode, ctypes, __import__, subprocess, eval( | open-write, socket, driver-expression |
| `emgi96__trailprint3d.zip` | cleared | subprocess, ctypes, requests | socket, open-write |
| `grimrukh__soulstruct-blender.zip` | cleared | subprocess | open-write, socket, driver-expression |
| `itscubetime__fastpbr.zip` | needs_review | subprocess, os.system, exec(, ctypes | open-write |
| `add-on-easy-tree-v1.0.1.zip` | clean | — | — |
| `kalwalt__terragen-utils.zip` | clean | — | open-write |
| `add-on-bagapie-v11.0.10.zip` | cleared | subprocess, exec( | open-write, socket |
| `lmesaric__bsc-thesis-fer-2020.zip` | cleared | subprocess, requests | — |
| `ln-12__blainder-range-scanner.zip` | cleared | subprocess | — |
| `add-on-space-colonization-tree-generator-v1.0.0.zip` | clean | — | — |
| `add-on-real-snow-v1.3.2.zip` | clean | — | — |
| `nerk987__txa-ant.zip` | clean | — | — |
| `add-on-srtm-terrain-importer-v1.0.5.zip` | clean | — | — |
| `ozikazina__hydra.zip` | cleared | subprocess, requests | — |
| `petak5__bp.zip` | clean | — | — |
| `tlabaltoh__realistic-terrain.zip` | clean | — | — |
| `varkenvarken__erosion.zip` | clean | — | open-write |
| `wolfgangp__quicktree.zip` | clean | — | — |
| `add-on-terrainmixer-v3.1.3.zip` | clean | — | — |
