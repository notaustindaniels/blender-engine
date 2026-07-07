#!/usr/bin/env bash
# Run probe_asset.py for ONE asset (.blend/.gltf/.glb/.fbx/.obj) in the sandbox — the A-lane /
# asset-delivery import-and-render gate (D-004 R27). SAME containment as run_probe.sh (§5.2, §7;
# PRD guardrail #1): --network none, read-only, non-root, cap-drop ALL, no-new-privileges, resource
# caps. The asset is mounted READ-ONLY. Prescan (driver/embedded-script scan for .blend) MUST have
# passed upstream before this is called — this runner assumes it.
#
# usage: run_asset.sh <3.6|4.2|4.5> <host-asset-path> [container-name] [cap-seconds]
set -euo pipefail
VER="${1:?blender series tag: 3.6|4.2|4.5}"
ASSET="${2:?path to asset}"
NAME="${3:-asset-$$}"
CAP="${4:-110}"

ART_DIR="$(cd "$(dirname "$ASSET")" && pwd)"
ART_BASE="$(basename "$ASSET")"
SANDBOX_DIR="$(cd "$(dirname "$0")" && pwd)"
IMAGE="blender-probe:${VER}"

exec docker run --rm \
  --name "$NAME" \
  --platform=linux/amd64 \
  --network none \
  --read-only \
  --tmpfs /tmp:rw,size=1g,exec \
  --tmpfs /home/prober:rw,size=512m,uid=1000,gid=1000 \
  --memory 6g --memory-swap 6g \
  --pids-limit 512 \
  --cap-drop ALL \
  --security-opt no-new-privileges \
  -v "$ART_DIR/$ART_BASE":/work/asset/"$ART_BASE":ro \
  -v "$SANDBOX_DIR/probe_asset.py":/work/probe_asset.py:ro \
  "$IMAGE" \
  -b --factory-startup -noaudio -P /work/probe_asset.py -- \
  "/work/asset/$ART_BASE" "$CAP"
