"""Minimal Security Control Plane decision kernel for SecuAgentOS."""
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Iterable, Mapping, Protocol

class Decision(str, Enum):
    ALLOW = "ALLOW"
    DENY = "DENY"
    REQUIRE_APPROVAL = "REQUIRE_APPROVAL"

class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

@dataclass(frozen=True)
class SecurityRequest:
    request_id: str
    principal: str
    action: str
    resource: str
    capabilities: frozenset[str] = frozenset()
    context: Mapping[str, str] = field(default_factory=dict)

@dataclass(frozen=True)
class SecurityDecision:
    request_id: str
    decision: Decision
    risk: RiskLevel
    reason: str
    matched_capability: bool
    policy_allowed: bool
    approval_required: bool

class AuditSink(Protocol):
    def append(self, record: Mapping[str, object]) -> None: ...

class MemoryAuditSink:
    def __init__(self) -> None:
        self.records: list[Mapping[str, object]] = []
    def append(self, record: Mapping[str, object]) -> None:
        self.records.append(dict(record))

class SecurityPolicy(Protocol):
    def allows(self, request: SecurityRequest) -> bool: ...

class StaticPolicy:
    def __init__(self, allowed_actions: Iterable[str]) -> None:
        self._allowed = frozenset(allowed_actions)
    def allows(self, request: SecurityRequest) -> bool:
        return request.action in self._allowed

class RiskClassifier:
    _levels = {
        "event.read": RiskLevel.LOW,
        "evidence.read": RiskLevel.LOW,
        "process.inspect": RiskLevel.LOW,
        "network.inspect": RiskLevel.LOW,
        "system.health.read": RiskLevel.LOW,
    }
    def classify(self, request: SecurityRequest) -> RiskLevel:
        return self._levels.get(request.action, RiskLevel.HIGH)

class SecurityController:
    def __init__(self, policy: SecurityPolicy, audit: AuditSink, risk: RiskClassifier | None = None) -> None:
        self.policy = policy
        self.audit = audit
        self.risk = risk or RiskClassifier()

    def authorize(self, request: SecurityRequest, required_capability: str, approved: bool = False) -> SecurityDecision:
        risk = self.risk.classify(request)
        capability_ok = required_capability in request.capabilities
        policy_ok = self.policy.allows(request)

        if not policy_ok:
            decision, reason = Decision.DENY, "policy_denied"
        elif not capability_ok:
            decision, reason = Decision.DENY, "capability_missing"
        elif risk in (RiskLevel.HIGH, RiskLevel.CRITICAL) and not approved:
            decision, reason = Decision.REQUIRE_APPROVAL, "approval_required"
        else:
            decision, reason = Decision.ALLOW, "authorized"

        result = SecurityDecision(
            request_id=request.request_id,
            decision=decision,
            risk=risk,
            reason=reason,
            matched_capability=capability_ok,
            policy_allowed=policy_ok,
            approval_required=decision is Decision.REQUIRE_APPROVAL,
        )
        self.audit.append({
            "request_id": request.request_id,
            "principal": request.principal,
            "action": request.action,
            "resource": request.resource,
            "decision": result.decision.value,
            "risk": result.risk.value,
            "reason": result.reason,
        })
        return result
