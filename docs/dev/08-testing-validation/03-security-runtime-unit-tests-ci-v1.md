# Security and Runtime Unit Tests in CI v1

## Purpose

The VM bootstrap job proves that the Ubuntu x86-64 guest builds and reaches the expected boot/readiness markers. It does not, by itself, prove the Python Security Control Plane, Package Manager, Agent Runtime, and Tool Gateway contracts.

## CI contract

The `x86-64-vm-bootstrap` workflow runs these checks in order:

1. Install Python 3.12 and pytest.
2. Run `python -m pytest -q kernel runtime`.
3. Run the VM shell smoke contract.
4. Build and checksum the Ubuntu VM disk and cloud-init seed ISO.
5. Boot the VM and verify Foundation and Agent Runtime readiness.
6. Upload boot/build diagnostics.

A CI pass now requires both application-level tests and the boot integration smoke test.

## Security validation areas

- Policy denial and capability mismatch fail closed.
- HIGH/CRITICAL operations require approval.
- Package verification and runtime compatibility gate activation.
- Agent capability authority matches the package manifest.
- Quarantined agents cannot execute tasks.
- Tool Gateway rejects unknown tools and denied principals.
- Adapter results are verified when a verifier is configured.

## Known prototype boundary

These Python modules are in-process reference implementations. A passing unit test does not establish operating-system-level isolation, cryptographic package signing, tamper-proof audit storage, or production readiness. Those remain explicit hardening tasks.

## Next step after CI

Use the combined test result to close security-boundary gaps before implementing the sample SecuAgent package or package-install CLI. Prioritize authoritative capability lookup and executable-state enforcement at the Tool Gateway.
