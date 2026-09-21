# Agent Runtime v1.0

## Purpose
Provide a platform-neutral lifecycle for security agents without embedding concrete SecuAgent application logic in the OS.

## Runtime lifecycle
REGISTERED -> READY -> RUNNING -> WAITING -> STOPPING -> STOPPED

Exceptional states:
- QUARANTINED
- FAILED

An agent cannot enter RUNNING unless identity, package trust, policy, and required capabilities have been validated.

## Organic operating loop
Observe -> Understand -> Assess -> Plan -> Decide -> Act -> Verify -> Learn -> Improve -> Observe

The runtime orchestrates this loop; domain-specific reasoning remains in applications.

## Core objects
- AgentDescriptor — identity, version, capabilities, resources.
- AgentTask — bounded unit of work with correlation ID and deadline.
- AgentContext — references to approved state, memory, evidence, and policy context.
- AgentEvent — lifecycle or domain event.
- AgentRuntime — scheduler and lifecycle coordinator.

## Security boundary
Every privileged task must call the Security Control Plane before execution. Runtime scheduling is not authorization.

## Isolation
A quarantined or failed agent receives no new executable task. Restart policy is controlled by policy and service lifecycle rules.

## Initial implementation
The first runtime implementation is an in-process deterministic scheduler suitable for unit testing. Later versions may use worker processes, containers, VMs, or other isolation backends without changing the logical runtime contract.
