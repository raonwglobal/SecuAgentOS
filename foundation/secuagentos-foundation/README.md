# SecuAgentOS Foundation

Core runtime foundation for SecuAgentOS.

This component is intentionally independent from the `SecuAgent` application package.

## Initial responsibilities

- OS/runtime identity
- configuration contract
- runtime state directory
- lifecycle/readiness state
- foundation health contract

## Planned interfaces

- `secuagentos-foundation status`
- `secuagentos-foundation health`
- `secuagentos-foundation version`

The implementation will be expanded incrementally after the VM Bootstrap v1 baseline remains green.
