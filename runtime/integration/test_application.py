from kernel.security.control import MemoryAuditSink, SecurityController, StaticPolicy
from runtime.agent.runtime import AgentRuntime, AgentState
from runtime.integration.application import ApplicationRuntime
from runtime.package.manager import PackageManager, PackageManifest, RecoveryApproval

class Trust:
    def verify(self, manifest): return True

class Runtime:
    def compatible(self, minimum_version): return True

class RecoveryApprovalVerifier:
    def verify(self, approval, package_name, reason):
        return (approval.approver_id == "security-reviewer"
                and approval.credential == "trusted-token"
                and package_name == "secuagent" and bool(reason.strip()))


def recovery_approval():
    return RecoveryApproval("security-reviewer", "trusted-token")

class Adapter:
    def __init__(self): self.calls = 0
    def execute(self, request):
        self.calls += 1
        return {"status": "ok"}

def make_package_manager():
    return PackageManager(
        Trust(), Runtime(), MemoryAuditSink(),
        recovery_approval_verifier=RecoveryApprovalVerifier(),
    )

def install_package(pm, manifest):
    pm.discover(manifest)
    pm.verify(manifest.name)
    pm.stage(manifest.name)
    pm.install(manifest.name)
    pm.activate(manifest.name)

def test_activated_package_drives_agent_and_tool_authority():
    pm = make_package_manager()
    manifest = PackageManifest(
        "secuagent", "1.0.0", "security-application", "0.5.0",
        frozenset({"event.read"}), frozenset({"event.read"}),
        frozenset({"siem.query"})
    )
    install_package(pm, manifest)
    agents = AgentRuntime(pm)
    app = ApplicationRuntime(pm, agents)
    app.activate_agent("agent:secuagent", "secuagent")

    audit = MemoryAuditSink()
    controller = SecurityController(StaticPolicy({"event.read"}), audit)
    gateway = __import__("runtime.tool.gateway", fromlist=["ToolGateway"]).ToolGateway(
        controller,
        principal_allowed=app.is_executable,
        capability_provider=app.capabilities_for,
        execution_state_provider=app.is_executable,
        tool_provider=app.tools_for,
    )
    adapter = Adapter()
    gateway.register("siem.query", "event.read", adapter)

    # Caller attempts to inject an undeclared capability; authoritative
    # package/runtime capabilities must win.
    from runtime.tool.gateway import ToolRequest
    response = gateway.execute(ToolRequest(
        "r1", "agent:secuagent", "siem.query", "event.read", "target",
        frozenset({"event.read", "firewall.block"})
    ))
    assert response.success
    assert adapter.calls == 1

    agents.quarantine("agent:secuagent")
    denied = gateway.execute(ToolRequest(
        "r2", "agent:secuagent", "siem.query", "event.read", "target",
        frozenset({"event.read"})
    ))
    assert not denied.success
    assert denied.error == "principal_not_allowed"
    assert adapter.calls == 1

def test_unactivated_package_cannot_register_agent():
    pm = make_package_manager()
    pm.discover(PackageManifest(
        "secuagent", "1.0.0", "security-application", "0.5.0",
        frozenset({"event.read"})
    ))
    agents = AgentRuntime(pm)
    try:
        agents.register_package_agent("agent:secuagent", "secuagent")
    except PermissionError as exc:
        assert str(exc) == "package_not_activated"
    else:
        raise AssertionError("inactive package must not register")


def test_disabling_package_revokes_agent_and_tool_execution():
    pm = make_package_manager()
    manifest = PackageManifest(
        "secuagent", "1.0.0", "security-application", "0.5.0",
        frozenset({"event.read"}), frozenset({"event.read"}),
        frozenset({"siem.query"})
    )
    install_package(pm, manifest)
    agents = AgentRuntime(pm)
    app = ApplicationRuntime(pm, agents)
    app.activate_agent("agent:secuagent", "secuagent")
    agents.bind("health", lambda task: {"ok": True})

    audit = MemoryAuditSink()
    controller = SecurityController(StaticPolicy({"event.read"}), audit)
    gateway = __import__("runtime.tool.gateway", fromlist=["ToolGateway"]).ToolGateway(
        controller,
        principal_allowed=app.is_executable,
        capability_provider=app.capabilities_for,
        execution_state_provider=app.is_executable,
        tool_provider=app.tools_for,
    )
    adapter = Adapter()
    gateway.register("siem.query", "event.read", adapter)

    pm.disable("secuagent")

    from runtime.agent.runtime import AgentTask
    try:
        agents.execute(AgentTask("task-disabled", "agent:secuagent", "health"))
    except PermissionError as exc:
        assert str(exc) == "agent_not_executable"
    else:
        raise AssertionError("disabled package agent must not execute")

    from runtime.tool.gateway import ToolRequest
    response = gateway.execute(ToolRequest(
        "r-disabled", "agent:secuagent", "siem.query", "event.read", "target",
        frozenset({"event.read"})
    ))
    assert not response.success
    assert response.error == "principal_not_allowed"
    assert adapter.calls == 0



def test_package_cannot_execute_undeclared_tool():
    pm = make_package_manager()
    manifest = PackageManifest(
        "secuagent", "1.0.0", "security-application", "0.5.0",
        frozenset({"event.read"}), frozenset({"event.read"}),
        frozenset({"siem.query"})
    )
    install_package(pm, manifest)
    agents = AgentRuntime(pm)
    app = ApplicationRuntime(pm, agents)
    app.activate_agent("agent:secuagent", "secuagent")

    audit = MemoryAuditSink()
    controller = SecurityController(StaticPolicy({"event.read"}), audit)
    gateway = __import__("runtime.tool.gateway", fromlist=["ToolGateway"]).ToolGateway(
        controller,
        principal_allowed=app.is_executable,
        capability_provider=app.capabilities_for,
        execution_state_provider=app.is_executable,
        tool_provider=app.tools_for,
    )
    adapter = Adapter()
    gateway.register("shell.exec", "event.read", adapter)

    from runtime.tool.gateway import ToolRequest
    response = gateway.execute(ToolRequest(
        "r-undeclared", "agent:secuagent", "shell.exec", "event.read", "target",
        frozenset({"event.read"})
    ))
    assert not response.success
    assert response.error == "tool_not_declared_by_package"
    assert adapter.calls == 0
    assert audit.records[-1]["reason"] == "tool_not_declared_by_package"

def test_package_tool_still_requires_high_risk_approval():
    pm = make_package_manager()
    manifest = PackageManifest(
        "secuagent", "1.0.0", "security-application", "0.5.0",
        frozenset({"firewall.block"}), frozenset({"firewall.block"}),
        frozenset({"firewall.block"})
    )
    install_package(pm, manifest)
    agents = AgentRuntime(pm)
    app = ApplicationRuntime(pm, agents)
    app.activate_agent("agent:secuagent", "secuagent")

    audit = MemoryAuditSink()
    controller = SecurityController(StaticPolicy({"firewall.block"}), audit)
    from runtime.tool.gateway import ToolGateway, ToolRequest
    gateway = ToolGateway(
        controller,
        principal_allowed=app.is_executable,
        capability_provider=app.capabilities_for,
        execution_state_provider=app.is_executable,
        tool_provider=app.tools_for,
    )
    adapter = Adapter()
    gateway.register("firewall.block", "firewall.block", adapter)

    request = ToolRequest(
        "r-high-risk", "agent:secuagent", "firewall.block",
        "firewall.block", "host:example", frozenset({"firewall.block"})
    )
    denied = gateway.execute(request)
    assert not denied.success
    assert denied.error == "approval_required"
    assert adapter.calls == 0

    from dataclasses import replace
    approved = gateway.execute(replace(request, request_id="r-high-risk-approved", approved=True))
    assert approved.success
    assert adapter.calls == 1

def test_quarantining_package_revokes_agent_and_tool_execution():
    pm = make_package_manager()
    manifest = PackageManifest(
        "secuagent", "1.0.0", "security-application", "0.5.0",
        frozenset({"event.read"}), frozenset({"event.read"}),
        frozenset({"siem.query"})
    )
    install_package(pm, manifest)
    agents = AgentRuntime(pm)
    app = ApplicationRuntime(pm, agents)
    app.activate_agent("agent:secuagent", "secuagent")

    audit = MemoryAuditSink()
    controller = SecurityController(StaticPolicy({"event.read"}), audit)
    from runtime.tool.gateway import ToolGateway, ToolRequest
    gateway = ToolGateway(
        controller,
        principal_allowed=app.is_executable,
        capability_provider=app.capabilities_for,
        execution_state_provider=app.is_executable,
        tool_provider=app.tools_for,
    )
    adapter = Adapter()
    gateway.register("siem.query", "event.read", adapter)

    pm.quarantine("secuagent", reason="integrity_alert")
    assert not app.is_executable("agent:secuagent")
    try:
        app.tools_for("agent:secuagent")
    except PermissionError as exc:
        assert str(exc) == "agent_not_executable"
    else:
        raise AssertionError("quarantined package must lose tool authority")

    response = gateway.execute(ToolRequest(
        "r-quarantined", "agent:secuagent", "siem.query",
        "event.read", "target", frozenset({"event.read"})
    ))
    assert not response.success
    assert response.error == "principal_not_allowed"
    assert adapter.calls == 0

    recovered = pm.recover_quarantined(
        "secuagent", approval=recovery_approval(), reason="integrity-cleared"
    )
    assert recovered.state.value == "VERIFIED"
    assert not app.is_executable("agent:secuagent")
    try:
        app.tools_for("agent:secuagent")
    except PermissionError as exc:
        assert str(exc) == "agent_not_executable"
    else:
        raise AssertionError("approved recovery must not immediately restore execution")

    pm.stage("secuagent")
    pm.install("secuagent")
    pm.activate("secuagent")
    assert app.is_executable("agent:secuagent")
    response_after_reactivation = gateway.execute(ToolRequest(
        "r-recovered", "agent:secuagent", "siem.query",
        "event.read", "target", frozenset({"event.read"})
    ))
    assert response_after_reactivation.success
    assert adapter.calls == 1


