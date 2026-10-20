# SecuAgentOS Development Documentation Index

This directory is the authoritative development-design and progress record for SecuAgentOS. Architecture decisions, system boundaries, implementation plans, verification evidence, and known gaps are recorded here by subject.

## Rules
1. Every major design decision and implementation-status change must be traceable to a document under `docs/dev/`.
2. Documents are organized by subject, not by chat/session.
3. Explicitly distinguish design, code implementation, CI verification, VM boot verification, installer verification, Proxmox verification, and physical hardware verification.
4. Development-support tools and chat-specific skills are not SecuAgentOS product/runtime components and should remain outside this repository.
5. SecuAgentOS is the platform/OS; SecuAgent is a separate future installable security application/package.

## Subjects
- `01-architecture/` — overall OS and layer architecture
- `02-system-foundation/` — x86-64, boot, kernel, VM and hardware abstraction
- `03-security-kernel/` — identity, capability, policy, trust, risk and audit
- `04-agent-runtime/` — agent lifecycle, task, scheduler, event bus and A2A
- `05-application-package/` — application and package model
- `06-tool-integration/` — tool gateway, package-declared tool allowlists, and external security systems
- `07-self-healing/` — diagnosis, remediation, verification and rollback
- `08-testing-validation/` — test strategy, CI evidence, VM/install validation, integration audits
- `09-migration/` — migration from the current repository structure
- `10-decisions/` — architecture decision records

Implementation changes must update the relevant subject document and the repository integration audit when they materially change project status.
