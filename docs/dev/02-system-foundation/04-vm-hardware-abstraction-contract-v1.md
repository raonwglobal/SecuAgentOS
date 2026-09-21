# VM Hardware Abstraction Contract v1.0

## Purpose
Define the minimum platform-neutral system interfaces required by SecuAgentOS above the hypervisor-specific layer.

## Contract

### CPU
Expose:
- architecture
- logical CPU count
- feature flags
- time source

Do not expose QEMU-specific objects.

### Memory
Expose:
- total memory
- available memory
- allocation/pressure telemetry

### Storage
Expose:
- device identity
- block read/write
- capacity
- health
- mount/storage lifecycle

### Network
Expose:
- interface identity
- link state
- address configuration
- packet/byte counters
- policy attachment point

### Clock and timer
Expose:
- monotonic time
- wall-clock time
- timer scheduling

### Console
Expose:
- boot log
- structured system log
- emergency/recovery output

### Device
Expose:
- device discovery
- state
- driver binding
- isolation state

### Trust
Expose:
- platform identity
- optional vTPM availability
- measured-boot status when supported

## Rule
Upper layers depend only on these contracts. QEMU, KVM, virtio, firmware and host-specific APIs belong beneath the implementation boundary.

## Initial implementation
Linux kernel facilities provide the first implementation. The contract remains the stable SecuAgentOS boundary.
