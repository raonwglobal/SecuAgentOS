#!/bin/sh
set -eu

ROOT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
OUT_DIR="${ROOT_DIR}/.build/vm/proxmox"
WORK_DIR="${OUT_DIR}/work"
mkdir -p "$WORK_DIR"

# Proxmox VE accepts qcow2 directly for importdisk, and raw is also suitable
# for direct attachment. Keep qcow2 as the default because the source image
# is already qcow2 and preserves sparse storage.
SOURCE="${ROOT_DIR}/.build/vm/secuagentos-x86_64-ubuntu24.04.img"
TARGET="$OUT_DIR/secuagentos-x86_64-ubuntu24.04.qcow2"

[ -f "$SOURCE" ] || {
  echo "missing VM image: $SOURCE" >&2
  echo "run tools/vm/build.sh first" >&2
  exit 1
}

command -v qemu-img >/dev/null 2>&1 || {
  echo "missing required command: qemu-img" >&2
  exit 1
}

qemu-img convert -p -O qcow2 "$SOURCE" "$TARGET"
qemu-img info "$TARGET"
sha256sum "$TARGET" > "$TARGET.sha256"

cat > "$OUT_DIR/PROXMOX-IMPORT.txt" <<'EOF'
SecuAgentOS Proxmox VM import

Recommended VM:
  Machine: q35
  BIOS: OVMF (UEFI)
  CPU: host, 2 cores
  Memory: 4096 MB
  Disk: import this qcow2 image as SCSI0 or VirtIO Block
  Network: VirtIO

Example on Proxmox host:
  qm create 9000 --name secuagentos --memory 4096 --cores 2 --machine q35 --bios ovmf --net0 virtio,bridge=vmbr0
  qm importdisk 9000 secuagentos-x86_64-ubuntu24.04.qcow2 local-lvm
  qm set 9000 --scsihw virtio-scsi-single --scsi0 local-lvm:vm-9000-disk-0
  qm set 9000 --boot order=scsi0
  qm start 9000

If an EFI disk is required by the local Proxmox configuration:
  qm set 9000 --efidisk0 local-lvm:0,efitype=4m,pre-enrolled-keys=0
EOF

echo "Built: $TARGET"
echo "Guide: $OUT_DIR/PROXMOX-IMPORT.txt"
