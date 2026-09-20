import pytest
from .runtime import AgentDescriptor, AgentRuntime, AgentState, AgentTask

def make_runtime():
    r = AgentRuntime()
    r.register(AgentDescriptor("agent:test", "0.1", frozenset({"system.health.read"})))
    r.bind("health", lambda task: {"ok": True})
    return r

def test_register_and_execute():
    r = make_runtime()
    result = r.execute(AgentTask("task-1", "agent:test", "health"))
    assert result == {"ok": True}
    assert r.agents["agent:test"].state is AgentState.WAITING

def test_quarantined_agent_cannot_execute():
    r = make_runtime()
    r.quarantine("agent:test")
    with pytest.raises(PermissionError):
        r.execute(AgentTask("task-1", "agent:test", "health"))

def test_failed_task_quarantinable_state():
    r = AgentRuntime()
    r.register(AgentDescriptor("agent:fail", "0.1"))
    def fail(task):
        raise RuntimeError("boom")
    r.bind("fail", fail)
    with pytest.raises(RuntimeError):
        r.execute(AgentTask("task-1", "agent:fail", "fail"))
    assert r.agents["agent:fail"].state is AgentState.FAILED
