#!/bin/sh
set -eu
ROOT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
ISO="\${SECUAGENTOS_ISO:-$ROOT_DIR/.build/vm/secuagentos-x86_64-uefi.iso}"
[ -f "$ISO" ] || { echo "VM image not found: $ISO" >&2; exit 1; }
command -v qemu-system-x86_64 >/dev/null 2>&1 || { echo "missing required command: qemu-system-x86_64" >&2; exit 1; }

OVMF_CODE="\${OVMF_CODE:-}"
OVMF_VARS_TEMPLATE="\${OVMF_VARS:-}"
for candidate in /usr/share/OVMF/OVMF_CODE_4M.fd /usr/share/OVMF/OVMF_CODE.fd /usr/share/OVMF/OVMF_CODE_4M.ms.fd /usr/share/edk2/ovmf/OVMF_CODE.fd /opt/homebrew/share/qemu/edk2-x86_64-code.fd /usr/local/share/qemu/edk2-x86_64-code.fd; do
  if [ -z "$OVMF_CODE" ] && [ -f "$candidate" ] && [ -r "$candidate" ]; then OVMF_CODE="$candidate"; fi
done
for candidate in /usr/share/OVMF/OVMF_VARS_4M.fd /usr/share/OVMF/OVMF_VARS.fd /usr/share/edk2/ovmf/OVMF_VARS.fd /opt/homebrew/share/qemu/edk2-x86_64-vars.fd /usr/local/share/qemu/edk2-x86_64-vars.fd; do
  if [ -z "$OVMF_VARS_TEMPLATE" ] && [ -f "$candidate" ] && [ -r "$candidate" ]; then OVMF_VARS_TEMPLATE="$candidate"; fi
done
OVMF_MONOLITHIC="\${OVMF_MONOLITHIC:-}"
for candidate in /usr/share/qemu/OVMF.fd /usr/share/edk2/ovmf/OVMF.fd; do
  if [ -z "$OVMF_CODE" ] && [ -z "$OVMF_MONOLITHIC" ] && [ -f "$candidate" ] && [ -r "$candidate" ]; then OVMF_MONOLITHIC="$candidate"; fi
done

if [ -n "$OVMF_CODE" ]; then
  echo "Using split OVMF CODE: $OVMF_CODE" >&2
else
  [ -n "$OVMF_MONOLITHIC" ] || { echo "OVMF firmware not found" >&2; exit 1; }
  echo "Using monolithic OVMF: $OVMF_MONOLITHIC" >&2
fi

ACCEL="\${SECUAGENTOS_ACCEL:-}"
if [ -z "$ACCEL" ]; then
  if [ -r /dev/kvm ] && [ -w /dev/kvm ]; then ACCEL=kvm; else ACCEL=tcg; fi
fi
echo "QEMU accelerator: $ACCEL" >&2

TMP_DIR=""
cleanup() { [ -z "$TMP_DIR" ] || rm -rf "$TMP_DIR"; }
trap cleanup EXIT INT TERM
FIRMWARE_ARGS=""
if [ -n "$OVMF_CODE" ]; then
  if [ -n "$OVMF_VARS_TEMPLATE" ]; then
    TMP_DIR=$(mktemp -d "\${TMPDIR:-/tmp}/secuagentos-ovmf.XXXXXX")
    OVMF_VARS="$TMP_DIR/OVMF_VARS.fd"
    cp "$OVMF_VARS_TEMPLATE" "$OVMF_VARS"
    FIRMWARE_ARGS="-drive if=pflash,format=raw,readonly=on,file=$OVMF_CODE -drive if=pflash,format=raw,file=$OVMF_VARS"
  else
    FIRMWARE_ARGS="-drive if=pflash,format=raw,readonly=on,file=$OVMF_CODE"
  fi
else
  FIRMWARE_ARGS="-bios $OVMF_MONOLITHIC"
fi

# Keep stdout as guest serial only; do not multiplex the QEMU monitor.
# shellcheck disable=SC2086
exec qemu-system-x86_64 \
  -machine "q35,accel=$ACCEL" \
  -cpu max \
  -m "\${SECUAGENTOS_RAM_MB:-4096}" \
  -smp "\${SECUAGENTOS_VCPU:-2}" \
  $FIRMWARE_ARGS \
  -cdrom "$ISO" \
  -boot order=d,menu=off \
  -display none \
  -monitor none \
  -serial stdio \
  -no-reboot
