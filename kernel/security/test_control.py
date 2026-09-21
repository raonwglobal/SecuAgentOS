from .control import Decision, MemoryAuditSink, SecurityController, SecurityRequest, StaticPolicy

def request(action: str, capabilities: set[str]) -> SecurityRequest:
    return SecurityRequest("test-1", "agent:test", action, "local:test", frozenset(capabilities))

def test_policy_denial_happens_before_capability():
    c = SecurityController(StaticPolicy([]), MemoryAuditSink())
    r = c.authorize(request("system.health.read", {"system.health.read"}), "system.health.read")
    assert r.decision is Decision.DENY
    assert r.reason == "policy_denied"

def test_missing_capability_is_denied():
    c = SecurityController(StaticPolicy(["system.health.read"]), MemoryAuditSink())
    r = c.authorize(request("system.health.read", set()), "system.health.read")
    assert r.decision is Decision.DENY
    assert r.reason == "capability_missing"

def test_high_risk_requires_approval():
    c = SecurityController(StaticPolicy(["system.restart"]), MemoryAuditSink())
    r = c.authorize(request("system.restart", {"system.restart"}), "system.restart")
    assert r.decision is Decision.REQUIRE_APPROVAL

def test_high_risk_can_be_approved():
    c = SecurityController(StaticPolicy(["system.restart"]), MemoryAuditSink())
    r = c.authorize(request("system.restart", {"system.restart"}), "system.restart", approved=True)
    assert r.decision is Decision.ALLOW
