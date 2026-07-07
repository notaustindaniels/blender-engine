#!/usr/bin/env bash
# Run probe_shader.py for ONE artifact (or --selftest) in the sandbox — the SHADER-delta gate
# (D-006 R37a). SAME containment as run_probe.sh (§5.2, §7): --network none, read-only, non-root,
# cap-drop ALL, no-new-privileges, resource caps. Prescan MUST have passed upstream for .blend.
#
# usage: run_shader.sh <3.6|4.2|4.5> <host-asset-path|--selftest> [container-name] [cap-seconds]
set -euo pipefail
VER="${1:?blender series tag: 3.6|4.2|4.5}"
ASSET="${2:?path to asset OR --selftest}"
NAME="${3:-shader-$$}"
CAP="${4:-110}"
SANDBOX_DIR="$(cd "$(dirname "$0")" && pwd)"
IMAGE="blender-probe:${VER}"

COMMON=(docker run --rm --name "$NAME" --platform=linux/amd64 --network none --read-only
  --tmpfs /tmp:rw,size=1g,exec --tmpfs /home/prober:rw,size=512m,uid=1000,gid=1000
  --memory 6g --memory-swap 6g --pids-limit 512 --cap-drop ALL --security-opt no-new-privileges
  -v "$SANDBOX_DIR/probe_shader.py":/work/probe_shader.py:ro)

if [ "$ASSET" = "--selftest" ]; then
  exec "${COMMON[@]}" "$IMAGE" -b --factory-startup -noaudio -P /work/probe_shader.py -- --selftest "$CAP"
else
  ART_DIR="$(cd "$(dirname "$ASSET")" && pwd)"; ART_BASE="$(basename "$ASSET")"
  exec "${COMMON[@]}" -v "$ART_DIR/$ART_BASE":/work/asset/"$ART_BASE":ro \
    "$IMAGE" -b --factory-startup -noaudio -P /work/probe_shader.py -- "/work/asset/$ART_BASE" "$CAP"
fi
