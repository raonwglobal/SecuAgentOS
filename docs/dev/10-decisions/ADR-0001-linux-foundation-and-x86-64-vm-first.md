# ADR-0001: Linux Foundation and x86-64 VM First

## Status
Accepted

## Context

SecuAgentOS is intended to become an operating-system/platform layer for security agents. A completely new kernel and hardware stack would significantly delay validation of the Agent Runtime, security control plane and package architecture.

The first development environment also needs to be reproducible and destructive-test friendly.

## Decision

1. The first SecuAgentOS system foundation uses a hardened Linux kernel.
2. x86-64 is the first supported hardware architecture.
3. QEMU/KVM is the reference virtualization target.
4. UEFI is the reference boot interface.
5. SecuAgentOS-specific functionality begins above the base kernel boundary.
6. Hardware-specific details are isolated behind system/hardware interfaces.
7. The VM target is treated as a first-class deployment target.
8. Bare-metal x86-64 support follows after the VM architecture is stable.

## Consequences

### Positive
- rapid bootable-system validation
- mature hardware and virtualization support
- easier automated integration testing
- easier snapshots and recovery
- early focus on security and agentic platform differentiation

### Constraints
- Linux remains a foundational dependency in v1
- a future custom or reduced kernel path requires a separate architecture decision
- kernel hardening becomes part of the system-foundation work

## Revisit conditions

Reconsider the foundation only after:
- VM boot is stable
- security control plane is stable
- agent runtime is stable
- package isolation is validated
- hardware abstraction is proven
- concrete requirements exist that Linux cannot satisfy
