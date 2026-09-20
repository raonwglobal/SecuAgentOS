#!/bin/sh
set -eu

ROOT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
ISO="${SECUAGENTOS_ISO:-$ROOT_DIR/.build/vm/secuagentos-x86_64-uefi.iso}"

[ -f "$ISO" ] || { echo "VM image not found: $ISO" >&2; echo "Run tools/vm/build.sh first." >&2; exit 1; }
command -v qemu-system-x86_64 >/dev/null 2>&1 || { echo "missing required command: qemu-system-x86_64" >&2; exit 1; }

OVMF_CODE="${OVMF_CODE:-}"
if [ -z "$OVMF_CODE" ]; then
  for candidate in \
    /usr/share/OVMF/OVMF_CODE_4M.fd \
    /usr/share/OVMF/OVMF_CODE.fd \
    /usr/share/edk2/ovmf/OVMF_CODE.fd \
    /opt/homebrew/share/qemu/edk2-x86_64-code.fd \
    /usr/local/share/qemu/edk2-x86_64-code.fd; do
    if [ -f "$candidate" ]; then OVMF_CODE="$candidate"; break; fi
  done
fi

[ -n "$OVMF_CODE" ] && [ -f "$OVMF_CODE" ] || { echo "OVMF_CODE not found; set OVMF_CODE=/path/to/OVMF_CODE.fd" >&2; exit 1; }

exec qemu-system-x86_64 \
  -machine q35,accel=kvm:tcg \
  -cpu max \
  -m "${SECUAGENTOS_RAM_MB:-4096}" \
  -smp "${SECUAGENTOS_VCPU:-2}" \
  -bios "$OVMF_CODE" \
  -cdrom "$ISO" \
  -nographic \
  -serial mon:stdio \
  -no-reboot
