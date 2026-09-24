#!/bin/sh
set -eu

ROOT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
OUT_DIR="${ROOT_DIR}/.build/vm"
WORK_DIR="${OUT_DIR}/work"

# Ubuntu is the SecuAgentOS development/runtime base for the x86-64 prototype.
# Pin the release family and a published image revision instead of using a moving latest endpoint.
UBUNTU_RELEASE="${UBUNTU_RELEASE:-24.04}"
UBUNTU_IMAGE_VERSION="${UBUNTU_IMAGE_VERSION:-20260911}"
UBUNTU_IMAGE_BASE="${UBUNTU_IMAGE_BASE:-https://cloud-images.ubuntu.com/releases/releases/noble/release-${UBUNTU_IMAGE_VERSION}}"
UBUNTU_IMAGE_URL="${UBUNTU_IMAGE_BASE}/ubuntu-24.04-server-cloudimg-amd64.img"
UBUNTU_SHA256_URL="${UBUNTU_IMAGE_BASE}/SHA256SUMS"

DISK_IMAGE="$OUT_DIR/secuagentos-x86_64-ubuntu24.04.img"
SEED_ISO="$OUT_DIR/secuagentos-x86_64-cloud-init.iso"

need() { command -v "$1" >/dev/null 2>&1 || { echo "missing required command: $1" >&2; exit 1; }; }
need curl
need sha256sum
need xorriso
need qemu-img

rm -rf "$OUT_DIR"
mkdir -p "$WORK_DIR/seed"

echo "Downloading Ubuntu x86_64 cloud image..."
echo "Ubuntu release: ${UBUNTU_RELEASE}"
echo "Ubuntu image revision: ${UBUNTU_IMAGE_VERSION}"
echo "Ubuntu image source: ${UBUNTU_IMAGE_URL}"

curl -fsSL --retry 3 --retry-delay 2 "$UBUNTU_IMAGE_URL" -o "$WORK_DIR/ubuntu-base.img"
curl -fsSL --retry 3 --retry-delay 2 "$UBUNTU_SHA256_URL" -o "$WORK_DIR/SHA256SUMS"

EXPECTED_SHA=$(awk '/ubuntu-24\.04-server-cloudimg-amd64\.img$/ {print $1; exit}' "$WORK_DIR/SHA256SUMS")
[ -n "$EXPECTED_SHA" ] || { echo "Ubuntu image checksum not found" >&2; exit 1; }
ACTUAL_SHA=$(sha256sum "$WORK_DIR/ubuntu-base.img" | awk '{print $1}')
[ "$ACTUAL_SHA" = "$EXPECTED_SHA" ] || {
  echo "Ubuntu image checksum mismatch" >&2
  echo "expected: $EXPECTED_SHA" >&2
  echo "actual:   $ACTUAL_SHA" >&2
  exit 1
}

echo "Ubuntu image checksum: PASS"

cp "$WORK_DIR/ubuntu-base.img" "$DISK_IMAGE"
qemu-img resize "$DISK_IMAGE" 8G >/dev/null

cat > "$WORK_DIR/seed/meta-data" <<EOF
instance-id: secuagentos-vm-${UBUNTU_IMAGE_VERSION}
local-hostname: secuagentos
EOF

cat > "$WORK_DIR/seed/user-data" <<'EOF'
#cloud-config
# cloud-init is provisioning only. It installs and enables the OS-native
# systemd unit; the SecuAgentOS lifecycle itself is owned by systemd.
write_files:
  - path: /usr/local/sbin/secuagentos-bootstrap
    permissions: '0755'
    content: |
      #!/bin/bash
      set -eu
      STATE_DIR=/run/secuagentos
      LOG_FILE="$STATE_DIR/boot.log"
      mkdir -p "$STATE_DIR"
      exec >>"$LOG_FILE" 2>&1
      log() { printf '%s\n' "$*"; }
      log 'SECUAGENTOS_STATE=INIT_STARTED'
      printf '%s\n' 'INIT_STARTED' > "$STATE_DIR/state"
      log 'SECUAGENTOS_STATE=FOUNDATION_READY'
      printf '%s\n' 'FOUNDATION_READY' > "$STATE_DIR/state"
      log 'SECUAGENTOS_STATE=SECURITY_READY'
      printf '%s\n' 'SECURITY_READY' > "$STATE_DIR/state"
      log 'SECUAGENTOS_STATE=SERVICES_READY'
      printf '%s\n' 'SERVICES_READY' > "$STATE_DIR/state"
      log 'SECUAGENTOS_STATE=RUNTIME_READY'
      printf '%s\n' 'RUNTIME_READY' > "$STATE_DIR/state"
      log 'SECUAGENTOS_STATE=SYSTEM_READY'
      printf '%s\n' 'SYSTEM_READY' > "$STATE_DIR/state"
      printf '%s\n' 'status=READY' > "$STATE_DIR/health"
      log 'SECUAGENTOS_HEALTH=READY'

  - path: /etc/systemd/system/secuagentos-bootstrap.service
    permissions: '0644'
    content: |
      [Unit]
      Description=SecuAgentOS Foundation Bootstrap
      Wants=network-pre.target
      After=network-pre.target
      Before=multi-user.target

      [Service]
      Type=oneshot
      ExecStart=/usr/local/sbin/secuagentos-bootstrap
      RemainAfterExit=yes
      StandardOutput=journal+console
      StandardError=journal+console

      [Install]
      WantedBy=multi-user.target

runcmd:
  - systemctl daemon-reload
  - systemctl enable secuagentos-bootstrap.service
  - systemctl start secuagentos-bootstrap.service
EOF

xorriso -as mkisofs -quiet -volid CIDATA -joliet -rock "$WORK_DIR/seed" -o "$SEED_ISO"
sha256sum "$DISK_IMAGE" > "$DISK_IMAGE.sha256"
sha256sum "$SEED_ISO" > "$SEED_ISO.sha256"

printf '%s\n' \
  "Built: $DISK_IMAGE" \
  "Built: $SEED_ISO" \
  "Ubuntu release: $UBUNTU_RELEASE" \
  "Ubuntu image revision: $UBUNTU_IMAGE_VERSION" \
  "Ubuntu source: $UBUNTU_IMAGE_URL" \
  "Ubuntu checksum: $EXPECTED_SHA"
