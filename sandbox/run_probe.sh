#!/usr/bin/env bash
# Run probe.py inside the sandbox for ONE artifact against ONE Blender version.
#
# ALL containment flags live HERE (SPEC §5.2, §7; PRD guardrail #1) so the security posture
# is auditable in one place:
#   --network none          no network for harvested code, EVER (PRD guardrail #1)
#   --read-only             immutable root fs; only tmpfs scratch is writable
#   --cap-drop ALL          drop every Linux capability
#   --security-opt no-new-privileges
#   non-root                image runs as uid 1000 'prober'
#   --memory / --pids-limit resource caps
#   artifact + probe.py     mounted READ-ONLY
#
# usage: run_probe.sh <3.6|4.2|4.5> <host-artifact-path> [container-name]
set -euo pipefail
VER="${1:?blender series tag: 3.6|4.2|4.5}"
ARTIFACT="${2:?path to artifact}"
NAME="${3:-probe-$$}"
CAP="${4:-110}"        # internal probe wall-clock cap (seconds); scales on the 2x retry

ART_DIR="$(cd "$(dirname "$ARTIFACT")" && pwd)"
ART_BASE="$(basename "$ARTIFACT")"
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
  -v "$ART_DIR/$ART_BASE":/work/artifact/"$ART_BASE":ro \
  -v "$SANDBOX_DIR/probe.py":/work/probe.py:ro \
  "$IMAGE" \
  -b --factory-startup -noaudio -P /work/probe.py -- \
  "/work/artifact/$ART_BASE" "$VER" "$CAP"
