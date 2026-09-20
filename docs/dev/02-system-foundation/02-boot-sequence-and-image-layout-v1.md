# SecuAgentOS Boot Sequence and Image Layout v1.0

## 1. Goal

Define the first bootable x86-64 VM contract without prematurely implementing a custom kernel or bootloader.

## 2. Boot stages

1. UEFI firmware initializes the virtual machine.
2. Bootloader locates the SecuAgentOS kernel and boot configuration.
3. Linux kernel initializes CPU, memory, devices and networking primitives.
4. SecuAgentOS system initialization starts.
5. Base system services start.
6. Security control plane starts before agent applications.
7. Agent Runtime starts.
8. Package/application services become available.
9. Health manager publishes SYSTEM_READY.

## 3. Startup dependency order

System initialization must enforce this order:

System Foundation
→ Identity/Trust
→ Policy
→ Audit
→ System Services
→ Event Bus
→ Agent Runtime
→ Package Manager
→ Applications

An application must not become RUNNING before the security control plane is READY.

## 4. Initial disk model

The first VM image should reserve logical areas for:

- boot
- immutable/system
- persistent configuration
- packages/applications
- audit
- evidence
- recovery/rollback

The exact filesystem and partition implementation will be selected during the bootstrap implementation.

## 5. Recovery

Boot must have a recovery path capable of:

- detecting failed system activation
- entering maintenance/recovery mode
- preserving audit information
- selecting a previous known-good system state
- preventing failed applications from automatically restarting

## 6. Health states

The initial system state model is:

BOOTING
→ FOUNDATION_READY
→ SECURITY_READY
→ SERVICES_READY
→ RUNTIME_READY
→ SYSTEM_READY

Failure states:

BOOT_FAILED
SECURITY_FAILED
SERVICE_FAILED
RUNTIME_FAILED
RECOVERY

## 7. First implementation boundary

The bootstrap prototype is successful when a VM can:

- boot automatically
- expose a serial console
- report each startup state
- persist a system identity
- expose a local health command
- enter recovery mode after a controlled failure

No application-specific security agent is required for this milestone.
