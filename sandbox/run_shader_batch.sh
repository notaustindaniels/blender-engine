#!/usr/bin/env bash
# Run probe_shader_batch.py over MANY materials in ONE sandbox container (D-008 L6 throughput).
# SAME containment as run_shader.sh: --network none, read-only, non-root, cap-drop ALL. Prescan MUST
# have passed upstream for every .blend. The materials dir is mounted read-only; the batch manifest
# lists /work/mats/<file> paths.
#
# usage: run_shader_batch.sh <3.6|4.2|4.5> <host-mats-dir> <host-batch-json> [name] [cap-seconds]
set -euo pipefail
VER="${1:?blender series tag}"
MATS="${2:?host dir of material .blends}"
BATCH="${3:?host batch.json}"
NAME="${4:-shbatch-$$}"
CAP="${5:-540}"
SANDBOX_DIR="$(cd "$(dirname "$0")" && pwd)"
IMAGE="blender-probe:${VER}"
MATS_ABS="$(cd "$MATS" && pwd)"
BATCH_ABS="$(cd "$(dirname "$BATCH")" && pwd)/$(basename "$BATCH")"

exec docker run --rm --name "$NAME" --platform=linux/amd64 --network none --read-only \
  --tmpfs /tmp:rw,size=2g,exec --tmpfs /home/prober:rw,size=512m,uid=1000,gid=1000 \
  --memory 6g --memory-swap 6g --pids-limit 512 --cap-drop ALL --security-opt no-new-privileges \
  -v "$SANDBOX_DIR/probe_shader_batch.py":/work/probe_shader_batch.py:ro \
  -v "$MATS_ABS":/work/mats:ro \
  -v "$BATCH_ABS":/work/batch.json:ro \
  "$IMAGE" -b --factory-startup -noaudio -P /work/probe_shader_batch.py -- /work/batch.json "$CAP"
