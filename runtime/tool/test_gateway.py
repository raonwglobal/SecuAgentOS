from __future__ import annotations

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

def make_gateway(allowed=("event.read", "firewall.block"), principal_allowed=None):
    audit = MemoryAuditSink()
    controller = SecurityController(StaticPolicy(allowed), audit)
    return ToolGateway(controller, principal_allowed), audit

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

def test_missing_capability_prevents_adapter_call():
    gw, _ = make_gateway()
    adapter = Adapter()
    gw.register("siem.query", "event.read", adapter)
    response = gw.execute(req(caps=frozenset()))
    assert not response.success
    assert response.error == "capability_missing"
    assert adapter.calls == 0

def test_high_risk_requires_approval():
    gw, _ = make_gateway()
    adapter = Adapter()
    gw.register("firewall.block", "firewall.block", adapter)
    response = gw.execute(
        req("firewall.block", frozenset({"firewall.block"}))
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
