"""Security AgentOS runtime and execution control plane."""

from typing import Any, Dict, Optional

from secuagent.core.registry import AgentRegistry
from secuagent.core.task import SecurityTask, TaskResult
from secuagent.security.policy import SecurityPolicy


class AgentRuntime:
    """Coordinates agent lifecycle and enforces policy before agent execution.

    External products should be connected through ToolGateway rather than called
    directly by an agent. This class intentionally stays framework-agnostic.
    """

    def __init__(
        self,
        registry: Optional[AgentRegistry] = None,
        policy: Optional[SecurityPolicy] = None,
    ) -> None:
        self.registry = registry or AgentRegistry()
        self.policy = policy or SecurityPolicy()
        self._instances: Dict[str, Any] = {}

    def register(self, spec: Any) -> None:
        self.registry.register(spec)

    def start(self, agent: str, **kwargs: Any) -> Any:
        if agent in self._instances:
            return self._instances[agent]
        instance = self.registry.create(agent, **kwargs)
        if hasattr(instance, "activate"):
            instance.activate()
        self._instances[agent] = instance
        return instance

    def stop(self, agent: str) -> None:
        instance = self._instances.pop(agent, None)
        if instance is not None and hasattr(instance, "deactivate"):
            instance.deactivate()

    async def execute(self, task: SecurityTask, **agent_kwargs: Any) -> TaskResult:
        decision = self.policy.evaluate(task.agent, task.action)
        if not decision.allowed:
            return TaskResult(
                task_id=task.task_id,
                status="denied",
                error=decision.reason,
                agent=task.agent,
                action=task.action,
            )

        if decision.requires_approval:
            return TaskResult(
                task_id=task.task_id,
                status="approval_required",
                error=decision.reason,
                agent=task.agent,
                action=task.action,
            )

        instance = self.start(task.agent, **agent_kwargs)
        try:
            output = instance.execute(task.action, **task.input)
            return TaskResult(
                task_id=task.task_id,
                status="completed",
                output=output,
                agent=task.agent,
                action=task.action,
            )
        except Exception as exc:
            return TaskResult(
                task_id=task.task_id,
                status="failed",
                error=str(exc),
                agent=task.agent,
                action=task.action,
            )
