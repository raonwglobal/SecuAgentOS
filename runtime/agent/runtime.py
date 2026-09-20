"""Minimal deterministic Agent Runtime for SecuAgentOS."""
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Mapping

class AgentState(str, Enum):
    REGISTERED = "REGISTERED"
    READY = "READY"
    RUNNING = "RUNNING"
    WAITING = "WAITING"
    STOPPING = "STOPPING"
    STOPPED = "STOPPED"
    QUARANTINED = "QUARANTINED"
    FAILED = "FAILED"

@dataclass(frozen=True)
class AgentDescriptor:
    agent_id: str
    version: str
    capabilities: frozenset[str] = frozenset()
    resources: Mapping[str, str] = field(default_factory=dict)

@dataclass(frozen=True)
class AgentTask:
    task_id: str
    agent_id: str
    action: str
    payload: Mapping[str, object] = field(default_factory=dict)

@dataclass
class AgentRecord:
    descriptor: AgentDescriptor
    state: AgentState = AgentState.REGISTERED

class AgentRuntime:
    def __init__(self) -> None:
        self.agents: dict[str, AgentRecord] = {}
        self.handlers: dict[str, Callable[[AgentTask], object]] = {}

    def register(self, descriptor: AgentDescriptor) -> None:
        if descriptor.agent_id in self.agents:
            raise ValueError("agent_already_registered")
        self.agents[descriptor.agent_id] = AgentRecord(descriptor, AgentState.READY)

    def quarantine(self, agent_id: str) -> None:
        self.agents[agent_id].state = AgentState.QUARANTINED

    def stop(self, agent_id: str) -> None:
        record = self.agents[agent_id]
        record.state = AgentState.STOPPING
        record.state = AgentState.STOPPED

    def bind(self, action: str, handler: Callable[[AgentTask], object]) -> None:
        self.handlers[action] = handler

    def execute(self, task: AgentTask) -> object:
        record = self.agents[task.agent_id]
        if record.state is AgentState.QUARANTINED:
            raise PermissionError("agent_quarantined")
        if record.state is not AgentState.READY:
            raise RuntimeError(f"agent_not_ready:{record.state.value}")
        handler = self.handlers.get(task.action)
        if handler is None:
            raise LookupError("task_handler_not_found")
        record.state = AgentState.RUNNING
        try:
            result = handler(task)
            record.state = AgentState.WAITING
            return result
        except Exception:
            record.state = AgentState.FAILED
            raise
