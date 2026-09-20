# Current Repository to SecuAgentOS Architecture Mapping v1.0

## 1. Current state
The repository currently contains:
- .agents/skills/luna-chat-coder/
- top-level Luna-oriented README/AGENTS documentation
- secuagent/ Python package
- agent implementations
- core runtime/context/event/registry/task code
- security/auth/audit/crypto/policy/validator code
- tool base interfaces

The current secuagent/ package is not yet a complete OS layer.

## 2. Development tooling boundary
.agents/skills/luna-chat-coder/ remains in the repository as development support.

It is not:
- SecuAgentOS runtime code
- an OS service
- an Agent Runtime component
- an installed application

It must not be included in the runtime/package architecture.

## 3. Current package disposition
### Keep conceptually, refactor by layer
- core/context.py → Security/Agent Context services
- core/events.py → Event Bus abstraction
- core/task.py → Task model
- core/runtime.py → Agent Runtime foundation
- core/registry.py → Registry services
- security/audit.py → Audit service
- security/policy.py → Policy engine
- security/auth.py → Identity/authentication services
- security/crypto.py → Cryptographic provider abstraction
- security/validator.py → validation/trust boundary
- tools/base.py → Tool SPI / Tool Gateway foundation

These are architectural candidates, not evidence that current implementations are production-ready.

### Move out of OS core
The current concrete security agents such as detector/responder are application-level behavior. They should ultimately belong to SecuAgent or another installable application package rather than the OS core.

## 4. Namespace decision
Do not perform a blind rename of secuagent to secuagentos yet.

First establish the target layer structure and packaging model.

The intended boundary is:
SecuAgentOS repository
→ OS/system/runtime SDK namespace
→ package/application interfaces
→ SecuAgent application (future separate package/repository)

A compatibility migration may be required rather than an abrupt rename.

## 5. Target repository direction
SecuAgentOS/
├── boot/
├── system/
│   ├── init/
│   ├── process/
│   ├── network/
│   ├── storage/
│   ├── device/
│   └── ipc/
├── kernel/
│   ├── security/
│   ├── policy/
│   ├── capability/
│   ├── identity/
│   └── trust/
├── runtime/
│   ├── agent/
│   ├── task/
│   ├── workflow/
│   ├── scheduler/
│   ├── event/
│   └── memory/
├── services/
│   ├── package-manager/
│   ├── service-manager/
│   ├── update-manager/
│   └── telemetry/
├── sdk/
│   └── secuagentos/
├── packages/
│   └── manifests/
├── applications/
│   └── examples/
├── tests/
├── tools/
├── docs/
│   └── dev/
└── .agents/
    └── skills/
        └── luna-chat-coder/

This is a target architecture, not yet a request to create all directories or replace the current implementation in one change.

## 6. Migration rule
No source migration should begin until the corresponding architectural contract exists under docs/dev/.

Migration sequence:
1. architecture documentation
2. VM/system foundation
3. security control plane
4. agent runtime
5. package/application framework
6. tool gateway
7. tests
8. SecuAgent extraction/application package
9. self-healing services
10. bare-metal enablement

## 7. Immediate next implementation
The next implementation unit is the x86-64 VM bootstrap/test harness, not the SecuAgent namespace rename.

First milestone:
Build VM image
→ Boot SecuAgentOS
→ Reach system console
→ Report OS health
→ Run automated smoke test
