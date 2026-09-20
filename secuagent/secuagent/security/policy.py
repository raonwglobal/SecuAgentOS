"""Policy and capability enforcement for security-agent execution."""

from dataclasses import dataclass, field
from typing import Dict, Iterable, Optional, Set


@dataclass(frozen=True)
class Capability:
    """A least-privilege capability granted to an agent."""

    name: str
    description: str = ""


@dataclass(frozen=True)
class PolicyDecision:
    allowed: bool
    reason: str
    requires_approval: bool = False


@dataclass
class SecurityPolicy:
    """Minimal policy engine that is intentionally independent of RBAC."""

    agent_capabilities: Dict[str, Set[str]] = field(default_factory=dict)
    denied_actions: Set[str] = field(default_factory=set)
    approval_actions: Set[str] = field(default_factory=set)

    def grant(self, agent: str, *capabilities: str) -> None:
        self.agent_capabilities.setdefault(agent, set()).update(capabilities)

    def revoke(self, agent: str, *capabilities: str) -> None:
        self.agent_capabilities.setdefault(agent, set()).difference_update(capabilities)

    def set_denied(self, actions: Iterable[str]) -> None:
        self.denied_actions = set(actions)

    def set_approval_required(self, actions: Iterable[str]) -> None:
        self.approval_actions = set(actions)

    def evaluate(self, agent: str, action: str, capability: Optional[str] = None) -> PolicyDecision:
        if action in self.denied_actions:
            return PolicyDecision(False, f"Action denied by policy: {action}")

        required = capability or action
        if required not in self.agent_capabilities.get(agent, set()):
            return PolicyDecision(False, f"Agent '{agent}' lacks capability: {required}")

        if action in self.approval_actions:
            return PolicyDecision(True, "Approval required by policy", requires_approval=True)

        return PolicyDecision(True, "Allowed by policy")
