from __future__ import annotations

import pytest

from kernel.security.control import MemoryAuditSink, SecurityController, StaticPolicy
from runtime.tool.gateway import ToolGateway, ToolRequest


class Adapter:
    def __init__(self, result="ok", fail=False):
        self.calls = 0
        self.result = result
        self.fail = fail

    def execute(self, request):
        self.calls += 1
        if self.fail:
            raise RuntimeError("boom")
        return self.result


class Verifier:
    def __init__(self, value=True):
        self.value = value

    def verify(self, request, result):
        return self.value


DEFAULT_CAPABILITIES = frozenset({"event.read", "firewall.block"})


def make_gateway(
    allowed=("event.read", "firewall.block"),
    principal_allowed=None,
    capability_provider=None,
    execution_state_provider=None,
    tool_provider=None,
):
    audit = MemoryAuditSink()
    controller = SecurityController(StaticPolicy(allowed), audit)
    gateway = ToolGateway(
        controller,
        principal_allowed=principal_allowed,
        capability_provider=capability_provider or (lambda principal: DEFAULT_CAPABILITIES),
        execution_state_provider=execution_state_provider or (lambda principal: True),
        tool_provider=tool_provider or (lambda principal: frozenset({"siem.query", "firewall.block"})),
    )
    return gateway, audit


def req(action="event.read", caps=frozenset({"event.read"}), approved=False, tool="siem.query"):
    return ToolRequest(
        "r1", "agent-1", tool, action, "target",
        caps, approved=approved
    )


def test_policy_denial_prevents_adapter_call():
    gw, _ = make_gateway()
    adapter = Adapter()
    gw.register("siem.query", "event.read", adapter)
    response = gw.execute(req(action="denied.action"))
    assert not response.success
    assert adapter.calls == 0


def test_missing_authoritative_capability_prevents_adapter_call():
    gw, _ = make_gateway(capability_provider=lambda principal: frozenset())
    adapter = Adapter()
    gw.register("siem.query", "event.read", adapter)
    # Caller claims a capability, but the trusted provider grants none.
    response = gw.execute(req(caps=frozenset({"event.read"})))
    assert not response.success
    assert response.error == "capability_missing"
    assert adapter.calls == 0


def test_caller_supplied_capabilities_are_not_authoritative():
    gw, _ = make_gateway(capability_provider=lambda principal: frozenset())
    adapter = Adapter()
    gw.register("siem.query", "event.read", adapter)
    response = gw.execute(req(caps=frozenset({"event.read"})))
    assert response.error == "capability_missing"
    assert adapter.calls == 0


def test_missing_capability_provider_fails_closed():
    audit = MemoryAuditSink()
    controller = SecurityController(StaticPolicy(("event.read",)), audit)
    gw = ToolGateway(controller, execution_state_provider=lambda principal: True)
    adapter = Adapter()
    gw.register("siem.query", "event.read", adapter)
    response = gw.execute(req())
    assert response.error == "capability_authority_unavailable"
    assert adapter.calls == 0


def test_high_risk_requires_approval():
    gw, _ = make_gateway()
    adapter = Adapter()
    gw.register("firewall.block", "firewall.block", adapter)
    response = gw.execute(
        req("firewall.block", frozenset({"firewall.block"}), tool="firewall.block")
    )
    assert not response.success
    assert response.error == "approval_required"
    assert adapter.calls == 0


def test_approved_high_risk_reaches_adapter():
    gw, _ = make_gateway()
    adapter = Adapter()
    gw.register("firewall.block", "firewall.block", adapter)
    response = gw.execute(
        req("firewall.block", frozenset({"firewall.block"}), approved=True, tool="firewall.block")
    )
    assert response.success
    assert adapter.calls == 1


def test_adapter_failure_is_audited():
    gw, audit = make_gateway()
    adapter = Adapter(fail=True)
    gw.register("siem.query", "event.read", adapter)
    response = gw.execute(req())
    assert not response.success
    assert response.error == "adapter_failure"
    assert any(r.get("outcome") == "adapter_failure" for r in audit.records)


def test_verification_failure_is_recorded():
    gw, audit = make_gateway()
    adapter = Adapter()
    gw.register("siem.query", "event.read", adapter, Verifier(False))
    response = gw.execute(req())
    assert not response.success
    assert response.error == "verification_failed"
    assert any(r.get("outcome") == "verification_failure" for r in audit.records)


def test_verifier_exception_fails_closed():
    class BrokenVerifier:
        def verify(self, request, result):
            raise RuntimeError("verification backend unavailable")

    gw, _ = make_gateway()
    adapter = Adapter()
    gw.register("siem.query", "event.read", adapter, BrokenVerifier())
    response = gw.execute(req())
    assert not response.success
    assert response.error == "verification_failed"


def test_unknown_tool_denied():
    gw, audit = make_gateway()
    response = gw.execute(req())
    assert not response.success
    assert response.error == "unknown_tool"
    assert audit.records[-1]["reason"] == "unknown_tool"


def test_quarantined_agent_cannot_execute_tool():
    gw, audit = make_gateway(principal_allowed=lambda principal: False)
    adapter = Adapter()
    gw.register("siem.query", "event.read", adapter)
    response = gw.execute(req())
    assert not response.success
    assert response.error == "principal_not_allowed"
    assert adapter.calls == 0
    assert audit.records[-1]["reason"] == "principal_not_allowed"


def test_non_executable_agent_cannot_execute_tool():
    gw, audit = make_gateway(execution_state_provider=lambda principal: False)
    adapter = Adapter()
    gw.register("siem.query", "event.read", adapter)
    response = gw.execute(req())
    assert response.error == "principal_not_executable"
    assert adapter.calls == 0
    assert audit.records[-1]["reason"] == "principal_not_executable"


def test_execution_state_provider_exception_fails_closed():
    def broken_state(principal):
        raise RuntimeError("runtime unavailable")

    gw, _ = make_gateway(execution_state_provider=broken_state)
    adapter = Adapter()
    gw.register("siem.query", "event.read", adapter)
    response = gw.execute(req())
    assert response.error == "execution_state_check_failed"
    assert adapter.calls == 0


def test_capability_provider_exception_fails_closed():
    def broken_capabilities(principal):
        raise RuntimeError("capability authority unavailable")

    gw, _ = make_gateway(capability_provider=broken_capabilities)
    adapter = Adapter()
    gw.register("siem.query", "event.read", adapter)
    response = gw.execute(req())
    assert response.error == "capability_lookup_failed"
    assert adapter.calls == 0



def test_undeclared_tool_is_denied_before_adapter_call():
    gw, audit = make_gateway(tool_provider=lambda principal: frozenset({"siem.query"}))
    adapter = Adapter()
    gw.register("firewall.block", "firewall.block", adapter)
    response = gw.execute(req(
        action="firewall.block",
        caps=frozenset({"firewall.block"}),
        approved=True,
        tool="firewall.block",
    ))
    assert not response.success
    assert response.error == "tool_not_declared_by_package"
    assert adapter.calls == 0
    assert audit.records[-1]["reason"] == "tool_not_declared_by_package"


def test_missing_tool_authority_fails_closed():
    audit = MemoryAuditSink()
    controller = SecurityController(StaticPolicy(("event.read",)), audit)
    gw = ToolGateway(
        controller,
        capability_provider=lambda principal: frozenset({"event.read"}),
        execution_state_provider=lambda principal: True,
    )
    adapter = Adapter()
    gw.register("siem.query", "event.read", adapter)
    response = gw.execute(req())
    assert not response.success
    assert response.error == "tool_authority_unavailable"
    assert adapter.calls == 0

def test_tool_authority_provider_exception_fails_closed():
    def broken_tools(principal):
        raise RuntimeError("package authority unavailable")

    gw, audit = make_gateway(tool_provider=broken_tools)
    adapter = Adapter()
    gw.register("siem.query", "event.read", adapter)
    response = gw.execute(req())
    assert not response.success
    assert response.error == "tool_lookup_failed"
    assert adapter.calls == 0
    assert audit.records[-1]["reason"] == "tool_lookup_failed"

