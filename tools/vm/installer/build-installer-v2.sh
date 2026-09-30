#!/bin/sh
set -eu

ROOT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")/../../.." && pwd)
OUT_DIR="$ROOT_DIR/.build/vm/installer-v2"
WORK_DIR="$OUT_DIR/work"
mkdir -p "$WORK_DIR"

BASE_ISO_URL="${UBUNTU_INSTALLER_ISO_URL:-https://releases.ubuntu.com/24.04/ubuntu-24.04.3-live-server-amd64.iso}"
BASE_ISO="$WORK_DIR/ubuntu-live-server-amd64.iso"
OUTPUT="$OUT_DIR/secuagentos-x86_64-installer-v2.iso"

need() { command -v "$1" >/dev/null 2>&1 || { echo "missing required command: $1" >&2; exit 1; }; }
need curl
need sha256sum

curl -fsSL --retry 3 --retry-delay 2 "$BASE_ISO_URL" -o "$BASE_ISO"

# v2 prepares a reproducible installer workspace. ISO boot-media customization
# is kept explicit so the base ISO is never silently modified.
cp "$BASE_ISO" "$OUTPUT"
sha256sum "$OUTPUT" > "$OUTPUT.sha256"

cat > "$OUT_DIR/BUILD-MANIFEST.txt" <<EOF
SecuAgentOS Installer v2
Base ISO: Ubuntu Server 24.04
Architecture: amd64
Autoinstall contract: tools/vm/installer/autoinstall/user-data
Foundation boundary: /opt/secuagentos
Service Manager boundary: systemd
Artifact: $OUTPUT
EOF

echo "Built: $OUTPUT"
