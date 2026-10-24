# Installer ISO v2 — integrated autoinstall

## Goal

Produce one bootable Ubuntu Server 24.04 amd64 ISO with the SecuAgentOS NoCloud autoinstall seed embedded and GRUB boot entries configured for unattended installation.

## Build

Provide a deployment-specific SHA-512 crypt password hash through a secure environment variable. Do not commit credentials or use a shared/default password.

```sh
SECUAGENTOS_PASSWORD_HASH='<SHA-512 crypt hash>' tools/vm/installer/build-installer-v2.sh
```

The builder refuses to run without a valid hash. It downloads the Ubuntu base ISO, injects the NoCloud user-data and meta-data into the installer ISO, patches BIOS and UEFI GRUB Linux entries with the autoinstall/NoCloud kernel arguments, replays the original boot metadata with xorriso, and writes a SHA256 checksum.

Output: `.build/vm/installer-v2/secuagentos-x86_64-installer-v2.iso`.

## Validation status

The existing VM bootstrap CI passing does not by itself prove unattended installer behavior. The next validation is to boot this exact generated ISO under QEMU/OVMF, verify autoinstall reaches reboot, and confirm SecuAgentOS Foundation and health markers on the installed disk. Do not distribute an ISO until that end-to-end validation succeeds.
