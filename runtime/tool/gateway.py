"""Security-mediated tool execution gateway for SecuAgentOS."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Mapping, Protocol

from kernel.security.control import Decision, SecurityController, SecurityRequest


@dataclass(frozen=True)
class ToolRequest:
    request_id: str
    principal: str
    tool: str
    action: str
    resource: str
    capabilities: frozenset[str] = frozenset()
    parameters: Mapping[str, Any] = field(default_factory=dict)
    context: Mapping[str, str] = field(default_factory=dict)
    approved: bool = False


@dataclass(frozen=True)
class ToolResponse:
    request_id: str
    success: bool
    result: Any = None
    verification: bool = False
    error: str | None = None


class ToolAdapter(Protocol):
    def execute(self, request: ToolRequest) -> Any: ...


class ToolVerifier(Protocol):
    def verify(self, request: ToolRequest, result: Any) -> bool: ...


class ToolGateway:
    """Execute tools only when identity, runtime state, capability and policy checks pass.

    The runtime-state and capability providers are authoritative. Missing or failing
    providers fail closed; caller-supplied ToolRequest.capabilities are never trusted.
    """

    def __init__(
        self,
        controller: SecurityController,
        principal_allowed: Callable[[str], bool] | None = None,
        capability_provider: Callable[[str], frozenset[str]] | None = None,
        execution_state_provider: Callable[[str], bool] | None = None,
        tool_provider: Callable[[str], frozenset[str]] | None = None,
    ) -> None:
        self._controller = controller
        self._adapters: dict[str, tuple[str, ToolAdapter, ToolVerifier | None]] = {}
        self._principal_allowed = principal_allowed or (lambda principal: True)
        self._capability_provider = capability_provider
        self._execution_state_provider = execution_state_provider
        self._tool_provider = tool_provider

    def register(
        self,
        tool: str,
        required_capability: str,
        adapter: ToolAdapter,
        verifier: ToolVerifier | None = None,
    ) -> None:
        if not tool or not required_capability:
            raise ValueError("tool_and_required_capability_must_be_nonempty")
        if tool in self._adapters:
            raise ValueError(f"tool already registered: {tool}")
        self._adapters[tool] = (required_capability, adapter, verifier)

    def _deny(self, request: ToolRequest, reason: str) -> ToolResponse:
        self._controller.audit.append({
            "request_id": request.request_id,
            "principal": request.principal,
            "tool": request.tool,
            "decision": Decision.DENY.value,
            "reason": reason,
        })
        return ToolResponse(request.request_id, False, error=reason)

    def execute(self, request: ToolRequest) -> ToolResponse:
        try:
            if not self._principal_allowed(request.principal):
                return self._deny(request, "principal_not_allowed")
        except Exception:
            return self._deny(request, "principal_check_failed")

        if self._execution_state_provider is None:
            return self._deny(request, "execution_state_unavailable")
        try:
            executable = self._execution_state_provider(request.principal)
        except Exception:
            return self._deny(request, "execution_state_check_failed")
        if not executable:
            return self._deny(request, "principal_not_executable")

        entry = self._adapters.get(request.tool)
        if entry is None:
            return self._deny(request, "unknown_tool")

        required_capability, adapter, verifier = entry
        if self._capability_provider is None:
            return self._deny(request, "capability_authority_unavailable")
        try:
            capabilities = frozenset(self._capability_provider(request.principal))
        except Exception:
            return self._deny(request, "capability_lookup_failed")

        if self._tool_provider is None:
            return self._deny(request, "tool_authority_unavailable")
        try:
            declared_tools = frozenset(self._tool_provider(request.principal))
        except Exception:
            return self._deny(request, "tool_lookup_failed")
        if request.tool not in declared_tools:
            return self._deny(request, "tool_not_declared_by_package")

        security_request = SecurityRequest(
            request_id=request.request_id,
            principal=request.principal,
            action=request.action,
            resource=request.resource,
            capabilities=capabilities,
            context=request.context,
        )
        decision = self._controller.authorize(
            security_request,
            required_capability,
            approved=request.approved,
        )
        if decision.decision is not Decision.ALLOW:
            return ToolResponse(request.request_id, False, error=decision.reason)

        try:
            result = adapter.execute(request)
        except Exception as exc:
            self._controller.audit.append({
                "request_id": request.request_id,
                "principal": request.principal,
                "tool": request.tool,
                "decision": Decision.ALLOW.value,
                "outcome": "adapter_failure",
                "error_type": type(exc).__name__,
            })
            return ToolResponse(request.request_id, False, error="adapter_failure")

        try:
            verified = True if verifier is None else bool(verifier.verify(request, result))
        except Exception:
            verified = False
        self._controller.audit.append({
            "request_id": request.request_id,
            "principal": request.principal,
            "tool": request.tool,
            "decision": Decision.ALLOW.value,
            "outcome": "success" if verified else "verification_failure",
            "verified": verified,
        })
        if not verified:
            return ToolResponse(
                request.request_id, False, result=result,
                verification=False, error="verification_failed"
            )
        return ToolResponse(
            request.request_id, True, result=result, verification=True
        )
