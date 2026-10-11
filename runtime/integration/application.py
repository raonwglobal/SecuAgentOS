"""Application activation bridge for SecuAgentOS v1."""
from __future__ import annotations

from runtime.agent.runtime import AgentRuntime
from runtime.package.manager import PackageManager

class ApplicationRuntime:
    """Binds an activated package to an Agent Runtime and Tool Gateway."""

    def __init__(self, packages: PackageManager, agents: AgentRuntime) -> None:
        self.packages = packages
        self.agents = agents

    def activate_agent(self, agent_id: str, package_name: str) -> None:
        self.agents.register_package_agent(agent_id, package_name)

    def is_executable(self, principal: str) -> bool:
        return self.agents.is_executable(principal)

    def capabilities_for(self, principal: str) -> frozenset[str]:
        return self.agents.capabilities_for(principal)

    def tools_for(self, principal: str) -> frozenset[str]:
        """Return only tools declared by the active package backing this agent."""
        if not self.agents.is_executable(principal):
            raise PermissionError("agent_not_executable")
        record = self.agents.agents[principal]
        package_name = record.descriptor.package_name
        if package_name is None:
            return frozenset()
        package = self.packages.get(package_name)
        from runtime.package.manager import PackageState
        if package.state is not PackageState.ACTIVATED:
            raise PermissionError("package_not_activated")
        return package.manifest.tools
