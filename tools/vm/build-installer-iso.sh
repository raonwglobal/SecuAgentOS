#!/bin/sh
set -eu
ROOT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
OUT_DIR="${ROOT_DIR}/.build/vm/installer"
WORK_DIR="$OUT_DIR/work"
mkdir -p "$WORK_DIR"
BASE_ISO_URL="${UBUNTU_INSTALLER_ISO_URL:-https://releases.ubuntu.com/24.04/ubuntu-24.04.3-live-server-amd64.iso}"
BASE_ISO="$WORK_DIR/ubuntu-live-server-amd64.iso"
OUTPUT="$OUT_DIR/secuagentos-x86_64-installer.iso"
need() { command -v "$1" >/dev/null 2>&1 || { echo "missing required command: $1" >&2; exit 1; }; }
need curl
need sha256sum
curl -fsSL --retry 3 --retry-delay 2 "$BASE_ISO_URL" -o "$BASE_ISO"
cp "$BASE_ISO" "$OUTPUT"
sha256sum "$OUTPUT" > "$OUTPUT.sha256"
cat > "$OUT_DIR/INSTALLER-STATUS.txt" <<EOF
SecuAgentOS Installer ISO v1
Base: Ubuntu Server 24.04 live-server amd64
Architecture: x86-64
ISO: $OUTPUT
This v1 artifact is bootable installation media. Automated SecuAgentOS autoinstall and Foundation provisioning is the next implementation step.
EOF
echo "Built: $OUTPUT"
