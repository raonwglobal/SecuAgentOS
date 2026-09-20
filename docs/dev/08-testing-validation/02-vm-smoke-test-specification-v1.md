# VM Smoke Test Specification v1.0

## Test objective
Verify that a clean SecuAgentOS development artifact boots and reaches a trusted runtime-ready state.

## Preconditions
- x86-64 host
- hardware virtualization where available
- QEMU installed
- SecuAgentOS image artifact available

## Test sequence
1. Validate artifact checksum.
2. Start QEMU with UEFI and serial console.
3. Observe bootloader/kernel startup.
4. Observe SecuAgentOS initialization.
5. Confirm FOUNDATION_READY.
6. Confirm SECURITY_READY.
7. Confirm SERVICES_READY.
8. Confirm RUNTIME_READY.
9. Confirm SYSTEM_READY.
10. Run local health query.
11. Shut down cleanly.

## Pass conditions
All required states appear in order and health returns success.

## Failure conditions
- missing startup state
- state transition out of order
- unexpected privileged host dependency
- console unavailable
- health failure
- VM crash/hang

## Future security extensions
- verify measured boot
- verify vTPM identity
- verify signed system artifact
- verify filesystem integrity
- verify network isolation
- verify recovery boot
