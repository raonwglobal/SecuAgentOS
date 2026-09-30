#!/bin/sh
set -eu

ROOT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")/../../.." && pwd)
OUT_DIR="$ROOT_DIR/.build/vm/installer-v2"
WORK_DIR="$OUT_DIR/work"
SEED_DIR="$WORK_DIR/seed"
mkdir -p "$SEED_DIR"

BASE_ISO_URL="${UBUNTU_INSTALLER_ISO_URL:-https://releases.ubuntu.com/24.04/ubuntu-24.04.3-live-server-amd64.iso}"
BASE_ISO="$WORK_DIR/ubuntu-live-server-amd64.iso"
OUTPUT="$OUT_DIR/secuagentos-x86_64-installer-v2.iso"

need() { command -v "$1" >/dev/null 2>&1 || { echo "missing required command: $1" >&2; exit 1; }; }
need curl
need sha256sum
need xorriso

curl -fsSL --retry 3 --retry-delay 2 "$BASE_ISO_URL" -o "$BASE_ISO"

# Keep credentials deployment-specific; do not embed a production password.
cp "$ROOT_DIR/tools/vm/installer/autoinstall/user-data" "$SEED_DIR/user-data"
cat > "$SEED_DIR/meta-data" <<'EOF'
instance-id: secuagentos-installer-v2
local-hostname: secuagentos
EOF

# The seed is kept as a separate reproducible artifact for now. The base ISO
# remains the authoritative Ubuntu installer media until boot-menu integration
# is validated in QEMU.
SEED_ISO="$OUT_DIR/secuagentos-autoinstall-seed.iso"
xorriso -as mkisofs -quiet -volid CIDATA -joliet -rock "$SEED_DIR" -o "$SEED_ISO"
cp "$BASE_ISO" "$OUTPUT"
sha256sum "$OUTPUT" > "$OUTPUT.sha256"
sha256sum "$SEED_ISO" > "$SEED_ISO.sha256"

cat > "$OUT_DIR/BUILD-MANIFEST.txt" <<EOF
SecuAgentOS Installer v2
Base ISO: Ubuntu Server 24.04
Architecture: amd64
Boot media: $OUTPUT
Autoinstall seed: $SEED_ISO
Foundation boundary: /opt/secuagentos
Service Manager boundary: systemd
Validation target: QEMU unattended install with attached CIDATA seed
EOF

echo "Built: $OUTPUT"
echo "Built: $SEED_ISO"
