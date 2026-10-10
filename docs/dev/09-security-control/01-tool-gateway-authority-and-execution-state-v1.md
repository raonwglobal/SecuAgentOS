# Tool Gateway Authority and Execution-State Enforcement v1

## Change

The Tool Gateway now treats the caller-supplied `ToolRequest.capabilities` as informational only. Authorization capabilities must come from a trusted `capability_provider(principal)`. An `execution_state_provider(principal)` must confirm that the principal is currently executable before any adapter can run.

## Fail-closed rules

- Missing runtime-state authority denies with `execution_state_unavailable`.
- Runtime-state lookup errors deny with `execution_state_check_failed`.
- A non-executable principal is denied with `principal_not_executable`.
- Missing capability authority denies with `capability_authority_unavailable`.
- Capability lookup errors deny with `capability_lookup_failed`.
- Policy denial, missing capability, and high-risk approval requirements remain enforced by the Security Controller.
- Verifier exceptions count as verification failures; they do not turn a tool result into success.
- Denial paths do not call the tool adapter and emit an audit record.

## Integration contract

Construct the gateway with authoritative callbacks, for example:

- `capability_provider=agent_runtime.capabilities_for`
- `execution_state_provider=agent_runtime.is_executable`

The caller's principal identity must map to the Agent Runtime's canonical agent ID. Provider callbacks must themselves be protected and should not be derived from untrusted request fields.

## Validation

CI tests caller capability spoofing, missing/failed authority providers, non-executable agents, approval gating, adapter failures, verifier failures, and policy denials.

## Prototype boundary

These callbacks enforce in-process contracts only. They do not provide OS process isolation, protection from a compromised Python process, cryptographic package signatures, or tamper-proof audit storage. Those remain separate hardening work.
