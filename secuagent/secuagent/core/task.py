"""Task and execution models for the SecuAgentOS runtime."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional
from uuid import uuid4


class ExecutionMode(str, Enum):
    """Controls how an action may be executed."""

    OBSERVE = "observe"
    SIMULATE = "simulate"
    APPROVAL_REQUIRED = "approval_required"
    CONTROLLED = "controlled"
    AUTONOMOUS = "autonomous"


@dataclass(frozen=True)
class SecurityTask:
    """A normalized unit of work submitted to the AgentOS runtime."""

    agent: str
    action: str
    input: Dict[str, Any] = field(default_factory=dict)
    task_id: str = field(default_factory=lambda: str(uuid4()))
    requested_by: str = "system"
    execution_mode: ExecutionMode = ExecutionMode.APPROVAL_REQUIRED
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class TaskResult:
    """Normalized result returned by the runtime."""

    task_id: str
    status: str
    output: Any = None
    error: Optional[str] = None
    agent: Optional[str] = None
    action: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
