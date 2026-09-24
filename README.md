# SecuAgentOS

**Security-focused Agent Operating System for x86-64 hardware and virtual machines**

SecuAgentOS is the foundation layer for a security-specialized Agent OS. The goal is not to create another standalone security application or Python package, but to provide an OS/runtime platform on which independently packaged security agents and external security solutions can be installed, isolated, authorized, observed, and orchestrated.

> **Design principle:** SecuAgentOS is the platform. `SecuAgent` and other security applications are installable packages that run on the platform.

## Project Status

Current development baseline:

- x86-64 hardware/VM architecture defined
- Ubuntu Server 24.04 LTS guest baseline selected for the x86-64 prototype
- UEFI/QEMU bootstrap foundation implemented
- Security Control Plane and policy enforcement primitives implemented
- Agent Runtime lifecycle implemented
- Package Manager and application sandbox contract implemented
- Package → Agent Runtime → Tool Gateway integration implemented
- Tool Gateway provides the controlled boundary to external security tools
- VM smoke/build/boot workflow implemented in GitHub Actions
- `SecuAgent` application packaging is the next integration milestone

This is an active development prototype, not a production-ready security OS.

## Architecture

```text
┌──────────────────────────────────────────────────────────────┐
│                         Hardware                             │
│                    x86-64 / VM / QEMU                       │
└─────────────────────────────┬────────────────────────────────┘
                              │
┌─────────────────────────────▼────────────────────────────────┐
│                 Ubuntu Linux Foundation                      │
│  UEFI / Kernel / systemd / Device / Filesystem / Networking │
└─────────────────────────────┬────────────────────────────────┘
                              │
┌─────────────────────────────▼────────────────────────────────┐
│                      SecuAgentOS                             │
│                                                              │
│  OS / Security Foundation                                    │
│  ├─ System lifecycle / health                               │
│  ├─ Security Control Plane                                  │
│  ├─ Identity / Policy / Capability / Risk / Audit            │
│  ├─ Event / Context services                                │
│  ├─ Agent Runtime                                           │
│  ├─ Package Manager                                         │
│  └─ Tool Gateway                                            │
└─────────────────────────────┬────────────────────────────────┘
                              │
                 ┌────────────▼────────────┐
                 │ Installable Security    │
                 │ Applications / Packages │
                 │                         │
                 │ SecuAgent               │
                 │ EDR / SIEM Agents       │
                 │ IAM / FW Agents         │
                 │ Other Security Apps     │
                 └─────────────────────────┘
```

Ubuntu is the base OS and execution substrate. It is not the security authority. SecuAgentOS owns the security control plane, package trust, capability resolution, policy enforcement, agent lifecycle, tool authorization, audit, and future autonomous remediation loops.

## Application Model

Applications are not part of the OS core merely because they provide security functionality. They are packages with an explicit manifest and lifecycle:

```text
DISCOVERED
    ↓
VERIFIED
    ↓
STAGED
    ↓
INSTALLED
    ↓
ACTIVATED
    ↓
RUNNING
```

A package cannot become active until trust and runtime compatibility checks succeed. Agent capabilities originate from the package manifest and are not accepted from an untrusted caller.

The intended future CLI model is:

```text
sos search secuagent
sos install secuagent
sos verify secuagent
sos enable secuagent
sos disable secuagent
sos update secuagent
sos rollback secuagent
```

## Security Execution Path

External security systems are accessed through a controlled path rather than direct application calls:

```text
Application Package
      ↓
Agent Runtime
      ↓
Authoritative Capability Resolution
      ↓
Security Control Plane
      ↓
Policy / Risk / Approval
      ↓
Tool Gateway
      ↓
Tool Adapter
      ↓
Result Verification
      ↓
Audit
```

This is intended to prevent capability spoofing, unauthorized tool execution, package bypasses, and execution by quarantined agents.

## VM Development Environment

The current development target is **x86-64** with QEMU/UEFI virtualization and an Ubuntu Server 24.04 LTS guest baseline. The repository contains scripts for building and running the VM:

```text
./tools/vm/build.sh
./tools/vm/run.sh
./tools/vm/health-check.sh
```

The GitHub Actions workflow validates the bootstrap path using an Ubuntu runner, downloads a pinned official Ubuntu cloud image, verifies its SHA256 checksum, boots it with QEMU/UEFI, injects the SecuAgentOS bootstrap service through a NoCloud seed ISO, captures the serial console, and verifies the SecuAgentOS lifecycle states.

The previous Alpine initramfs path is retained only as historical development material. It is no longer the primary VM runtime path.

## Repository Structure

```text
SecuAgentOS/
├── docs/dev/                 # Architecture and development records
├── kernel/security/          # Security control-plane primitives
├── runtime/                  # Agent, package, tool and integration runtime
│   ├── agent/
│   ├── package/
│   ├── tool/
│   └── integration/
├── system/init/              # Historical bootstrap; Ubuntu service migration in progress
├── tools/vm/                 # x86-64 Ubuntu VM build/run helpers
├── tests/vm/                 # VM smoke tests
└── .github/workflows/        # CI/VM validation
```

## Development Documentation

Development decisions and architecture definitions are maintained under `docs/dev/`. This is the authoritative project-development documentation location.

Important areas include:

- OS architecture and x86-64 virtualization
- Ubuntu base migration and boot/lifecycle design
- security control plane
- Agent Runtime
- package management and sandboxing
- Tool Gateway
- package/runtime/tool integration
- VM testing and CI

## SecuAgent Separation

The repository `raonwglobal/SecuAgent` represents a security application/rule package direction. It must not be treated as the SecuAgentOS kernel or OS runtime.

The intended relationship is:

```text
SecuAgentOS
    └── installable application package
            └── SecuAgent
```

Development-support tooling such as `luna-chat-coder` is not part of the SecuAgentOS runtime architecture. It may exist in the repository for development workflow support, but it is explicitly excluded from the OS/application runtime design.

## Roadmap

1. Stabilize Ubuntu-based x86-64 VM bootstrap and CI
2. Replace the cloud-init bootstrap prototype with native SecuAgentOS system services
3. Complete process-level application isolation
4. Implement signed package and publisher trust verification
5. Implement `sos` package-management CLI
6. Build the first installable `SecuAgent` package
7. Add real SIEM/EDR/IAM/firewall adapters
8. Add shared agent context and memory
9. Add autonomous observation, diagnosis, remediation and verification loops
10. Harden for physical x86-64 hardware
11. Establish reproducible, signed OS/package release artifacts

## Current Security Invariants

- Unverified packages cannot be activated.
- Incompatible packages cannot be activated.
- Agent capabilities must match the package authority.
- Tool requests cannot elevate capability by caller-supplied data.
- Quarantined agents cannot use the Tool Gateway.
- Tool execution is policy-controlled and auditable.
- Application failure must not directly bypass the OS security control plane.

## License

The repository's existing license applies to the project unless a component explicitly states otherwise.
