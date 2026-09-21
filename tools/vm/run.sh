#!/bin/sh
set -eu

ROOT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
ISO="${SECUAGENTOS_ISO:-$ROOT_DIR/.build/vm/secuagentos-x86_64-uefi.iso}"

[ -f "$ISO" ] || { echo "VM image not found: $ISO" >&2; echo "Run tools/vm/build.sh first." >&2; exit 1; }
command -v qemu-system-x86_64 >/dev/null 2>&1 || { echo "missing required command: qemu-system-x86_64" >&2; exit 1; }

# Ubuntu/Debian OVMF packages expose both split CODE images and a monolithic
# /usr/share/qemu/OVMF.fd. Prefer the monolithic image for CI portability.
OVMF_CODE="${OVMF_CODE:-}"
if [ -z "$OVMF_CODE" ]; then
  for candidate in \
    /usr/share/qemu/OVMF.fd \
    /usr/share/OVMF/OVMF_CODE_4M.fd \
    /usr/share/OVMF/OVMF_CODE.fd \
    /usr/share/OVMF/OVMF_CODE_4M.ms.fd \
    /usr/share/edk2/ovmf/OVMF_CODE.fd \
    /opt/homebrew/share/qemu/edk2-x86_64-code.fd \
    /usr/local/share/qemu/edk2-x86_64-code.fd; do
    if [ -f "$candidate" ] && [ -r "$candidate" ]; then OVMF_CODE="$candidate"; break; fi
  done
fi

[ -n "$OVMF_CODE" ] && [ -f "$OVMF_CODE" ] && [ -r "$OVMF_CODE" ] || { echo "OVMF firmware not found; set OVMF_CODE=/path/to/OVMF.fd" >&2; exit 1; }

echo "Using OVMF firmware: $OVMF_CODE" >&2

# GitHub-hosted runners do not guarantee /dev/kvm access. Use KVM only when
# it is actually usable; otherwise explicitly select TCG instead of relying
# on QEMU's implicit fallback. Local x86-64 hosts can still use KVM.
ACCEL="${SECUAGENTOS_ACCEL:-}"
if [ -z "$ACCEL" ]; then
  if [ -r /dev/kvm ] && [ -w /dev/kvm ]; then
    ACCEL="kvm"
  else
    ACCEL="tcg"
  fi
fi

echo "QEMU accelerator: $ACCEL" >&2

exec qemu-system-x86_64 \
  -machine "q35,accel=${ACCEL}" \
  -cpu max \
  -m "${SECUAGENTOS_RAM_MB:-4096}" \
  -smp "${SECUAGENTOS_VCPU:-2}" \
  -bios "$OVMF_CODE" \
  -cdrom "$ISO" \
  -nographic \
  -serial mon:stdio \
  -no-reboot
