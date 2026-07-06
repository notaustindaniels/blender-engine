#!/usr/bin/env bash
# Run probe_recipe.py for ONE recipe in the sandbox (D-003 R21). SAME containment as run_probe.sh
# (§5.2, §7): --network none, read-only, non-root, cap-drop, resource caps. The recipe JSON is
# passed as an arg; artifact zips are mounted read-only from the vault into /work/artifacts/.
set -euo pipefail
VER="${1:?blender series tag}"
RECIPE_JSON="${2:?recipe json string}"
VAULT_DIR="${3:?abs path to vault}"
CAP="${4:-110}"
NAME="recipe-$$-${VER}"
SANDBOX_DIR="$(cd "$(dirname "$0")" && pwd)"

exec docker run --rm --name "$NAME" \
  --platform=linux/amd64 --network none --read-only \
  --tmpfs /tmp:rw,size=1g,exec \
  --tmpfs /home/prober:rw,size=512m,uid=1000,gid=1000 \
  --memory 6g --memory-swap 6g --pids-limit 512 \
  --cap-drop ALL --security-opt no-new-privileges \
  -v "$VAULT_DIR":/work/vault:ro \
  -v "$SANDBOX_DIR/probe_recipe.py":/work/probe_recipe.py:ro \
  "blender-probe:${VER}" \
  -b --factory-startup -noaudio -P /work/probe_recipe.py -- \
  "$RECIPE_JSON" "$VER" "$CAP"
