"""Agent and provider registries for SecuAgentOS."""

from dataclasses import dataclass, field
from importlib.metadata import entry_points
from typing import Any, Dict, Iterable, Type


@dataclass(frozen=True)
class AgentSpec:
    """Describes an installable/runtime-loadable security agent."""

    name: str
    version: str
    agent_class: Type[Any]
    capabilities: tuple[str, ...] = ()
    description: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


class AgentRegistry:
    """Registry for built-in and third-party AgentOS packages."""

    ENTRY_POINT_GROUP = "secuagentos.agents"

    def __init__(self) -> None:
        self._agents: Dict[str, AgentSpec] = {}

    def register(self, spec: AgentSpec) -> None:
        if spec.name in self._agents:
            raise ValueError(f"Agent already registered: {spec.name}")
        self._agents[spec.name] = spec

    def unregister(self, name: str) -> None:
        self._agents.pop(name, None)

    def get(self, name: str) -> AgentSpec:
        try:
            return self._agents[name]
        except KeyError as exc:
            raise KeyError(f"Unknown agent: {name}") from exc

    def contains(self, name: str) -> bool:
        return name in self._agents

    def list(self) -> Iterable[AgentSpec]:
        return tuple(self._agents.values())

    def create(self, name: str, **kwargs: Any) -> Any:
        return self.get(name).agent_class(**kwargs)

    def load_installed_packages(self) -> list[str]:
        """Load AgentSpec providers published by installed Python packages."""
        loaded: list[str] = []
        discovered = entry_points()
        group = (
            discovered.select(group=self.ENTRY_POINT_GROUP)
            if hasattr(discovered, "select")
            else discovered.get(self.ENTRY_POINT_GROUP, [])
        )
        for ep in group:
            provider = ep.load()
            spec = provider() if callable(provider) else provider
            if not isinstance(spec, AgentSpec):
                raise TypeError(f"Entry point '{ep.name}' did not provide AgentSpec")
            self.register(spec)
            loaded.append(spec.name)
        return loaded
