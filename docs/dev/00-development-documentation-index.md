# SecuAgentOS Development Documentation Index

This directory is the authoritative development-design record for SecuAgentOS. Architecture decisions, system boundaries, implementation plans, and development assumptions are recorded here by subject.

## Rules
1. Every major design decision must have a document under docs/dev/.
2. Documents are organized by subject, not by chat/session.
3. Implementation changes must be traceable to the relevant design document.
4. .agents/skills/luna-chat-coder/ is development tooling and is not part of the SecuAgentOS runtime architecture.
5. SecuAgentOS is the platform/OS; SecuAgent is a future installable security application/package.

## Initial subjects
- 01-architecture/ — overall OS and layer architecture
- 02-system-foundation/ — x86-64, boot, kernel, VM and hardware abstraction
- 03-security-kernel/ — identity, capability, policy, trust, risk and audit
- 04-agent-runtime/ — agent lifecycle, task, scheduler, event bus and A2A
- 05-application-package/ — application and package model
- 06-tool-integration/ — tool gateway, package-declared tool allowlists, and external security systems
- 07-self-healing/ — diagnosis, remediation, verification and rollback
- 08-testing-validation/ — VM testbed, integration and security validation
- 09-migration/ — migration from the current repository structure
- 10-decisions/ — architecture decision records

This index is created before source refactoring so repository changes remain architecture-led rather than namespace-led.
