# Package Disable Revocation v1

## Goal

Disabling an installed application package must revoke execution immediately, including agents that were registered while the package was active.

## Enforcement

- Agent Runtime checks the backing package state on every executable-state check and task execution.
- Package-backed agents are executable only while their package is `ACTIVATED`.
- Capability lookup is denied when an agent is not executable.
- Tool Gateway receives the same authoritative executable-state callback, so disabled packages cannot call adapters.
- A package disable does not silently delete agent records; reactivation and lifecycle recovery remain explicit operations.

## Validation

CI covers direct Agent Runtime execution after package disable, Tool Gateway adapter denial, and repeated task execution from the normal `WAITING` state.

## Prototype boundary

This is in-process state enforcement. It does not terminate an already-running external process or replace OS-level sandboxing. Production activation/disable must also coordinate process supervision, in-flight task cancellation, and persistent audit guarantees.
