# Ubuntu Base Migration v1

## Decision

SecuAgentOS x86-64 VM development baseline is migrated from the Alpine initramfs bootstrap to Ubuntu Server 24.04 LTS.

This is not because Ubuntu and Alpine are inherently incompatible. The previous failure was caused by executing a guest Alpine BusyBox binary from the Ubuntu GitHub runner. However, the Alpine initramfs model also created an unnecessary cross-root execution boundary for the current AgentOS prototype. Ubuntu provides a fuller userspace, systemd service model, package ecosystem, and a direct path toward the target OS/runtime architecture.

## Base image

- OS: Ubuntu Server 24.04 LTS (Noble)
- Architecture: x86-64 / amd64
- Image source: official Ubuntu Cloud Images
- CI image revision: `20260911`
- Image URL is pinned to the published release revision.
- SHA256 is verified before the guest is booted.

Ubuntu publishes the amd64 cloud image as a UEFI/GPT bootable disk image. The VM pipeline therefore consumes the guest image directly rather than reconstructing an Alpine initramfs on the runner.

## VM boot architecture

```text
GitHub Actions Ubuntu runner
        |
        | build/verify only
        v
Pinned Ubuntu 24.04 guest image
        |
        +-- UEFI / OVMF
        +-- Ubuntu Linux
        +-- systemd
        +-- cloud-init seed
        |
        v
SecuAgentOS bootstrap service
        |
        +-- FOUNDATION
        +-- SECURITY
        +-- SERVICES
        +-- RUNTIME
        +-- SYSTEM_READY
```

## Why this is preferable for SecuAgentOS

1. The guest OS and CI runner no longer need to execute one another's user-space binaries.
2. systemd gives SecuAgentOS a natural service lifecycle boundary.
3. Ubuntu's amd64 cloud image is already UEFI/GPT bootable.
4. Package installation and future external security-solution integration can use a standard Linux userspace while the SecuAgentOS security control plane remains authoritative.
5. The prototype can evolve from a bootstrap service into native OS services without keeping an Alpine-specific initramfs implementation as the primary runtime path.

## Security boundary

Ubuntu is the base operating system, not the security authority. SecuAgentOS remains responsible for package trust, capability resolution, policy, audit, agent lifecycle, tool gateway authorization, and future self-healing orchestration.

The intended layering is:

```text
Hardware / VM
    |
Ubuntu Linux Foundation
    |
SecuAgentOS Core
    |-- Security Control Plane
    |-- Agent Runtime
    |-- Package Manager
    |-- Tool Gateway
    |-- Event / Context Services
    |
Installable Security Applications
    |-- SecuAgent
    |-- EDR/SIEM/IAM/FW adapters
    `-- Other trusted packages
```

## Migration rule

The previous Alpine-specific `system/init/secuagentos-init` and initramfs boot-contract files are retained as historical development records until the Ubuntu-native service architecture is complete. They are no longer the primary VM boot path.

## Next implementation stage

1. Replace the cloud-init bootstrap prototype with a native `secuagentos-foundation.service`.
2. Define persistent `/var/lib/secuagentos` state and audit locations.
3. Introduce a systemd service dependency graph for Security Control Plane, Event Bus, Agent Runtime, and Tool Gateway.
4. Add package installation/verification as an OS-native lifecycle operation.
5. Keep QEMU/UEFI as the regression test target before physical x86-64 hardware enablement.
