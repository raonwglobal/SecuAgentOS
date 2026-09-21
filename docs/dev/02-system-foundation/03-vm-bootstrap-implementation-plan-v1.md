# VM Bootstrap Implementation Plan v1.0

## Goal
Create the first reproducible x86-64 SecuAgentOS VM bootstrap without moving application-specific SecuAgent code into the platform.

## Milestone
A developer can build a boot artifact, start it with QEMU, reach a serial console, and observe explicit SecuAgentOS startup states.

## Components
- boot/ — boot configuration and future image assembly boundary
- system/init/ — first userspace initialization boundary
- tools/vm/ — developer VM lifecycle commands/scripts
- tests/vm/ — automated boot and health smoke tests
- docs/dev/ — design authority

## First implementation strategy
Use a minimal Linux-based guest foundation for the prototype. Keep the SecuAgentOS-specific init contract explicit so the underlying Linux distribution can later be replaced or hardened without changing the upper architecture.

## Required outputs
1. VM image build artifact
2. QEMU launch configuration
3. serial console output
4. SYSTEM_READY health signal
5. automated boot smoke test
6. reproducible developer instructions

## Security requirements
- VM must not require privileged host networking for the first smoke test.
- Test network must be isolated from production networks.
- Build artifacts must have deterministic version metadata.
- Boot logs must be retained for failed CI runs.
- Application packages are not part of the bootstrap image.

## Exit criteria
- clean checkout can build the prototype
- VM boots without interactive steps
- startup state reaches SYSTEM_READY
- health check succeeds
- controlled startup failure enters a detectable failure state
