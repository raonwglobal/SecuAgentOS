#!/bin/sh
set -eu

ROOT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
OUT_DIR="${ROOT_DIR}/.build/vm"
WORK_DIR="${OUT_DIR}/work"
ALPINE_VERSION="${ALPINE_VERSION:-3.24.2}"
ALPINE_BASE="https://dl-cdn.alpinelinux.org/alpine/v${ALPINE_VERSION}/releases/x86_64/netboot"
KERNEL_URL="${ALPINE_BASE}/vmlinuz-lts"
INITRAMFS_URL="${ALPINE_BASE}/initramfs-lts"

need() { command -v "$1" >/dev/null 2>&1 || { echo "missing required command: $1" >&2; exit 1; }; }
need curl
need cpio
need gzip
need grub-mkrescue
need xorriso

rm -rf "$OUT_DIR"
mkdir -p "$WORK_DIR/initramfs" "$WORK_DIR/iso/boot/grub"

curl -fsSL "$KERNEL_URL" -o "$WORK_DIR/iso/boot/vmlinuz"
curl -fsSL "$INITRAMFS_URL" -o "$WORK_DIR/initramfs.base"

mkdir -p "$WORK_DIR/initramfs"
gzip -dc "$WORK_DIR/initramfs.base" | (cd "$WORK_DIR/initramfs" && cpio -idm --quiet)
cp "$ROOT_DIR/system/init/secuagentos-init" "$WORK_DIR/initramfs/init"
chmod 0755 "$WORK_DIR/initramfs/init"

printf '%s\n' "set timeout=0" "set default=0" > "$WORK_DIR/iso/boot/grub/grub.cfg"
printf '%s\n' "menuentry 'SecuAgentOS x86-64 VM' {" "  linux /boot/vmlinuz console=ttyS0,115200n8 loglevel=4" "  initrd /boot/initramfs-secuagentos" "}" >> "$WORK_DIR/iso/boot/grub/grub.cfg"

(cd "$WORK_DIR/initramfs" && find . -print | cpio -H newc -o --quiet | gzip -n > "$WORK_DIR/iso/boot/initramfs-secuagentos")

grub-mkrescue -o "$OUT_DIR/secuagentos-x86_64-uefi.iso" "$WORK_DIR/iso" >/dev/null
sha256sum "$OUT_DIR/secuagentos-x86_64-uefi.iso" > "$OUT_DIR/secuagentos-x86_64-uefi.iso.sha256"
printf '%s\n' "Built: $OUT_DIR/secuagentos-x86_64-uefi.iso" "Alpine base: $ALPINE_VERSION"
