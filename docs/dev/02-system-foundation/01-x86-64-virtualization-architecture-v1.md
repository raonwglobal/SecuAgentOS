# x86-64 Virtualization Architecture v1.0

## 1. Objective
Provide a repeatable virtual hardware target where SecuAgentOS can boot and be tested as an independent OS/platform instance before bare-metal deployment.

## 2. Reference VM
| Resource | Minimum | Recommended |
|---|---:|---:|
| Architecture | x86-64 | x86-64 |
| vCPU | 2 | 4 |
| RAM | 4 GiB | 8 GiB |
| Disk | 20 GiB | 40–50 GiB |
| NIC | 1 | 2 |
| UEFI | required | required |
| Serial console | required | required |
| vTPM | optional | recommended |
| Snapshot | recommended | required for destructive tests |

## 3. Host virtualization
Preferred development path:
Developer Host
→ QEMU
→ KVM / native hardware virtualization
→ SecuAgentOS VM

The same guest architecture should remain portable to other x86-64 hypervisors.

## 4. Virtual hardware contract
SecuAgentOS v1 should depend on an explicit virtual hardware contract:
- x86-64 CPU
- UEFI firmware
- virtual block device
- virtual network interface
- serial console
- virtual timer/interrupt facilities
- optional virtual TPM
- predictable device enumeration

QEMU-specific details belong below the hardware abstraction layer.

## 5. Boot sequence
UEFI
→ Bootloader
→ Linux kernel
→ SecuAgentOS init
→ System services
→ Security control plane
→ Agent runtime
→ Package/application services

## 6. Storage layout target
The first image should reserve logical separation for:
- system image
- persistent configuration
- application/package data
- audit data
- evidence/data volume
- recovery/rollback area

Exact filesystem technology is an implementation decision after the boot prototype.

## 7. Network layout
A single-NIC mode is required for basic boot tests.

A dual-NIC mode is the reference security test configuration:
- NIC 1: management/control
- NIC 2: security/test or protected network

Network policy must be enforced above the raw device layer.

## 8. VM lifecycle
Development scripts should eventually support:
build → create → boot → health-check → test → snapshot → destructive-test → rollback → collect logs

## 9. Security testbed topology
Host
→ Hypervisor
→ Management Network → SecuAgentOS VM
→ Test Network → SIEM / Server / Attacker

The attacker VM is a controlled test component. Tests must be isolated from production networks.

## 10. Hardware abstraction rule
All upper layers must consume interfaces such as:
- CPU service
- memory service
- block storage service
- network service
- device service
- clock/timer service
- console service

rather than calling QEMU internals directly.

## 11. Bare-metal migration target
Same SecuAgentOS system interfaces:
- QEMU/KVM
- x86-64 bare metal

The VM is therefore a first-class platform target, not a temporary mock.
