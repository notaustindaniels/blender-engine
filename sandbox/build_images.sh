#!/usr/bin/env bash
# Build the digest-pinned probe images, one per Blender LTS (SPEC §5.2; §12.1(1) amendment).
# Blender tarballs pinned by SHA-256, verified live 2026-07-05 from download.blender.org.
#   usage: build_images.sh [all|3.6|4.2|4.5]
set -euo pipefail
SANDBOX_DIR="$(cd "$(dirname "$0")" && pwd)"

# "<full-version> <sha256>"  (series tag = major.minor)
MATRIX=(
  "3.6.23 0e9a18af4d0060b825e9617e24a775f759e0f9f67271c062f3d53a539030af00"
  "4.2.22 b0064f2879b269787375f6b9021fefa6ae478e1d16aca839f5c63ac36fb02fe3"
  "4.5.11 05ed7bd41bf3e61ae4f4a7cdc364c43088bf8b3fed702c2269c018fdf63a2188"
)

build_one() {
  local ver="$1" sha="$2" series="${1%.*}"
  local url="https://download.blender.org/release/Blender${series}/blender-${ver}-linux-x64.tar.xz"
  echo ">>> building blender-probe:${series}  (Blender ${ver})"
  docker build --platform=linux/amd64 \
    -f "$SANDBOX_DIR/Dockerfile.probe" \
    --build-arg BLENDER_URL="$url" \
    --build-arg BLENDER_SHA256="$sha" \
    --build-arg BLENDER_VER="$ver" \
    -t "blender-probe:${series}" \
    "$SANDBOX_DIR"
}

want="${1:-all}"
for row in "${MATRIX[@]}"; do
  read -r ver sha <<<"$row"
  series="${ver%.*}"
  [[ "$want" == "all" || "$want" == "$series" ]] && build_one "$ver" "$sha"
done
echo "build_images: done ($want)."
