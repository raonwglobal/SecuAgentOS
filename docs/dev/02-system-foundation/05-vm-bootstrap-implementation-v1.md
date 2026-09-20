# VM Bootstrap Implementation v1.0

## Status
Implemented on `architecture/x86-64-vm-v1` as the first executable VM bootstrap boundary.

## Prototype strategy
The first boot artifact uses Alpine Linux x86-64 as the minimal Linux foundation. Alpine 3.24.2 is pinned at the release-branch level for this prototype. The guest kernel and initramfs are fetched from the Alpine x86-64 netboot repository during the build. The SecuAgentOS PID 1 contract is injected into the initramfs, keeping application-specific SecuAgent code outside the platform bootstrap.

## Build pipeline

`Alpine kernel/initramfs → inject SecuAgentOS init → GRUB UEFI ISO → QEMU/KVM`

The build requires `curl`, `cpio`, `gzip`, `grub-mkrescue`, and `xorriso` on the developer/CI host.

## Boot contract

The init process emits these states in order:

`FOUNDATION_READY → SECURITY_READY → SERVICES_READY → RUNTIME_READY → SYSTEM_READY`

After `SYSTEM_READY`, `/run/secuagentos/health` contains a machine-readable READY state. The prototype keeps PID 1 alive so later services can attach to a stable lifecycle anchor.

## Failure injection

The kernel command line supports:

`secuagentos.fail=<STATE>`

When the requested state is reached, the init process records a FAILED health state and opens a maintenance shell. This is intentionally a prototype mechanism for validating failure detection and recovery handling.

## UEFI/QEMU execution

`tools/vm/run.sh` requires QEMU x86-64 and an OVMF UEFI firmware image. It prefers KVM and falls back to TCG through QEMU's accelerator selection. No host network interface is created by the default command.

## Validation boundary

`tests/vm/smoke.sh` validates the lifecycle contract statically. A full boot smoke test must execute on a runner with QEMU + OVMF and capture serial output. The repository does not claim a VM boot succeeded unless such a runner actually executes it.

## Next hardening steps

1. Verify downloaded Alpine artifacts against published checksums/signatures.
2. Make the boot artifact fully deterministic by pinning immutable artifact digests.
3. Add CI with QEMU/OVMF and serial-log capture.
4. Add persistent system identity storage.
5. Separate immutable system, configuration, audit, evidence, and recovery storage.
6. Replace prototype PID 1 shell lifecycle with the SecuAgentOS system service manager.
7. Add measured boot/vTPM and signed artifact verification.
