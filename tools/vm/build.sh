#!/bin/sh
set -eu

ROOT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
OUT_DIR="${ROOT_DIR}/.build/vm"
WORK_DIR="${OUT_DIR}/work"
# The versioned Alpine netboot directory is published, but individual boot
# assets can be rotated independently. Use the maintained stable netboot
# endpoint by default and allow CI/local tests to pin an exact base explicitly.
ALPINE_VERSION="${ALPINE_VERSION:-3.24.2}"
ALPINE_NETBOOT_BASE="${ALPINE_NETBOOT_BASE:-https://dl-cdn.alpinelinux.org/alpine/latest-stable/releases/x86_64/netboot}"
KERNEL_URL="${ALPINE_NETBOOT_BASE}/vmlinuz-lts"
INITRAMFS_URL="${ALPINE_NETBOOT_BASE}/initramfs-lts"

need() { command -v "$1" >/dev/null 2>&1 || { echo "missing required command: $1" >&2; exit 1; }; }
need curl
need cpio
need gzip
need grub-mkrescue
need mformat
need xorriso
need sha256sum

rm -rf "$OUT_DIR"
mkdir -p "$WORK_DIR/initramfs" "$WORK_DIR/iso/boot/grub"

echo "Downloading Alpine x86_64 netboot assets..."
echo "Alpine compatibility target: ${ALPINE_VERSION}"
echo "Netboot source: ${ALPINE_NETBOOT_BASE}"
# Fail early with a useful diagnostic instead of producing a later gzip/GRUB error.
curl -fsSI "$KERNEL_URL" >/dev/null
curl -fsSI "$INITRAMFS_URL" >/dev/null
curl -fsSL --retry 3 --retry-delay 2 "$KERNEL_URL" -o "$WORK_DIR/iso/boot/vmlinuz"
curl -fsSL --retry 3 --retry-delay 2 "$INITRAMFS_URL" -o "$WORK_DIR/initramfs.base"
[ -s "$WORK_DIR/iso/boot/vmlinuz" ] || { echo "empty Alpine kernel asset" >&2; exit 1; }
[ -s "$WORK_DIR/initramfs.base" ] || { echo "empty Alpine initramfs asset" >&2; exit 1; }

gzip -dc "$WORK_DIR/initramfs.base" | (cd "$WORK_DIR/initramfs" && cpio -idm --quiet)
cp "$ROOT_DIR/system/init/secuagentos-init" "$WORK_DIR/initramfs/init"
chmod 0755 "$WORK_DIR/initramfs/init"

printf '%s\n' "set timeout=0" "set default=0" > "$WORK_DIR/iso/boot/grub/grub.cfg"
printf '%s\n' "menuentry 'SecuAgentOS x86-64 VM' {" "  linux /boot/vmlinuz console=ttyS0,115200n8 loglevel=4" "  initrd /boot/initramfs-secuagentos" "}" >> "$WORK_DIR/iso/boot/grub/grub.cfg"

(cd "$WORK_DIR/initramfs" && find . -print | cpio -H newc -o --quiet | gzip -n > "$WORK_DIR/iso/boot/initramfs-secuagentos")

grub-mkrescue -o "$OUT_DIR/secuagentos-x86_64-uefi.iso" "$WORK_DIR/iso" >/dev/null
sha256sum "$OUT_DIR/secuagentos-x86_64-uefi.iso" > "$OUT_DIR/secuagentos-x86_64-uefi.iso.sha256"
printf '%s\n' "Built: $OUT_DIR/secuagentos-x86_64-uefi.iso" "Alpine compatibility target: $ALPINE_VERSION" "Netboot source: $ALPINE_NETBOOT_BASE"
