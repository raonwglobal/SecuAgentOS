# x86-64 VM Test Strategy v1.0

## 1. Purpose

The VM is the first integration platform for SecuAgentOS. Tests must validate both normal operation and security boundaries.

## 2. Test levels

### Level 0 — Build
- source validation
- dependency validation
- image creation
- artifact checksum

### Level 1 — Boot
- UEFI boot
- kernel startup
- console availability
- system identity
- startup state progression

### Level 2 — System
- process lifecycle
- filesystem access
- network initialization
- IPC
- service lifecycle
- health reporting

### Level 3 — Security Control Plane
- identity creation
- authentication
- capability enforcement
- policy evaluation
- denied action audit
- approval workflow
- package trust verification

### Level 4 — Agent Runtime
- agent registration
- lifecycle transitions
- task creation
- scheduling
- event delivery
- A2A messaging
- context propagation

### Level 5 — Tool Gateway
- tool registration
- capability check
- policy check
- risk check
- approval
- adapter execution
- verification
- audit

### Level 6 — Application
- package installation
- package verification
- application start/stop
- application isolation
- rollback

### Level 7 — Resilience
- service crash
- agent crash
- network interruption
- storage fault simulation
- policy failure
- package rollback
- recovery boot

## 3. Security invariants

The following must become automated assertions:

1. An undeclared capability cannot be used.
2. A denied policy action cannot reach a tool adapter.
3. A high-risk action cannot bypass required approval.
4. Every privileged action has an audit record.
5. A quarantined agent cannot execute tasks.
6. An unverified package cannot activate.
7. Application failure cannot corrupt the system layer.
8. Recovery can return the system to a known-good state.

## 4. Test network

The reference integration environment is isolated from production networks.

Components:
- SecuAgentOS VM
- attacker/test VM
- target server VM
- optional SIEM/EDR simulator
- management host

## 5. Snapshot policy

Snapshots are required before destructive tests.

Every destructive test records:
- test ID
- image version
- snapshot identifier
- configuration
- action
- expected result
- actual result
- recovery result

## 6. CI target

The long-term CI pipeline should be:

source
→ unit tests
→ build
→ VM image
→ boot test
→ integration tests
→ security tests
→ artifact signing
→ publish

The initial milestone only requires build and boot smoke tests.
