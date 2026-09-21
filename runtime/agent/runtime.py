"""Minimal deterministic Agent Runtime for SecuAgentOS."""
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Mapping, TYPE_CHECKING

if TYPE_CHECKING:
    from runtime.package.manager import PackageManager

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
    package_name: str | None = None

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
    def __init__(self, package_manager: PackageManager | None = None) -> None:
        self.agents: dict[str, AgentRecord] = {}
        self.handlers: dict[str, Callable[[AgentTask], object]] = {}
        self._package_manager = package_manager

    def register(self, descriptor: AgentDescriptor) -> None:
        if descriptor.agent_id in self.agents:
            raise ValueError("agent_already_registered")
        if descriptor.package_name is not None:
            if self._package_manager is None:
                raise RuntimeError("package_manager_required")
            package = self._package_manager.get(descriptor.package_name)
            from runtime.package.manager import PackageState
            if package.state is not PackageState.ACTIVATED:
                raise PermissionError("package_not_activated")
            if descriptor.capabilities != package.manifest.capabilities:
                raise PermissionError("capabilities_must_match_package")
        self.agents[descriptor.agent_id] = AgentRecord(descriptor, AgentState.READY)

    def register_package_agent(self, agent_id: str, package_name: str) -> None:
        if self._package_manager is None:
            raise RuntimeError("package_manager_required")
        package = self._package_manager.get(package_name)
        descriptor = AgentDescriptor(
            agent_id=agent_id,
            version=package.manifest.version,
            capabilities=package.manifest.capabilities,
            resources=package.manifest.resources,
            package_name=package_name,
        )
        self.register(descriptor)

    def is_executable(self, agent_id: str) -> bool:
        record = self.agents.get(agent_id)
        return record is not None and record.state in (AgentState.READY, AgentState.WAITING)

    def capabilities_for(self, agent_id: str) -> frozenset[str]:
        record = self.agents[agent_id]
        return record.descriptor.capabilities

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
