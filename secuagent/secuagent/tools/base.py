"""Tool-provider SPI used to connect external security products to AgentOS."""

from abc import ABC, abstractmethod
from typing import Any, Dict


class SecurityTool(ABC):
    """Adapter contract for EDR, SIEM, firewall, IAM, cloud and other tools."""

    name: str = "tool"
    version: str = "0.1.0"

    @abstractmethod
    def capabilities(self) -> set[str]:
        """Return action names exposed by this tool."""
        raise NotImplementedError

    @abstractmethod
    async def execute(self, action: str, **kwargs: Any) -> Dict[str, Any]:
        """Execute one tool action after policy enforcement."""
        raise NotImplementedError


class ToolRegistry:
    """Registry for external security tool adapters."""

    def __init__(self) -> None:
        self._tools: Dict[str, SecurityTool] = {}

    def register(self, tool: SecurityTool) -> None:
        if tool.name in self._tools:
            raise ValueError(f"Tool already registered: {tool.name}")
        self._tools[tool.name] = tool

    def get(self, name: str) -> SecurityTool:
        try:
            return self._tools[name]
        except KeyError as exc:
            raise KeyError(f"Unknown tool: {name}") from exc

    def list(self) -> tuple[SecurityTool, ...]:
        return tuple(self._tools.values())


class ToolGateway:
    """Single execution boundary for external security-system actions."""

    def __init__(self, registry: ToolRegistry) -> None:
        self.registry = registry

    async def execute(self, tool: str, action: str, **kwargs: Any) -> Dict[str, Any]:
        adapter = self.registry.get(tool)
        if action not in adapter.capabilities():
            raise PermissionError(f"Tool '{tool}' does not expose action '{action}'")
        return await adapter.execute(action, **kwargs)
