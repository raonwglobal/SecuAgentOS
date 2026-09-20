"""SecuAgentOS - Security-focused Agent Operating System library.

The package provides a security kernel and extension points for installing
specialized security agents and external security-tool adapters.
"""

__version__ = "0.2.0"
__author__ = "SecuAgent Team"

from secuagent.core.context import SecurityContext, SecurityLevel, UserRole
from secuagent.core.agent import SecureAgent
from secuagent.core.events import SecurityEvent, SecurityEventType, EventQueue
from secuagent.core.registry import AgentRegistry, AgentSpec
from secuagent.core.runtime import AgentRuntime
from secuagent.core.task import ExecutionMode, SecurityTask, TaskResult

from secuagent.security.crypto import EncryptionService, KeyManager
from secuagent.security.auth import AuthenticationManager, AuthorizationManager, RBACRole
from secuagent.security.policy import Capability, PolicyDecision, SecurityPolicy
from secuagent.security.validator import InputValidator, ValidationRule
from secuagent.security.audit import AuditLogger, AuditEntry

from secuagent.agents.base import BaseSecurityAgent
from secuagent.agents.detector import ThreatDetectorAgent
from secuagent.agents.responder import IncidentResponderAgent
from secuagent.tools.base import SecurityTool, ToolGateway, ToolRegistry
from secuagent.utils.logger import SecureLogger

__all__ = [
    "SecurityContext", "SecurityLevel", "UserRole", "SecureAgent",
    "SecurityEvent", "SecurityEventType", "EventQueue",
    "AgentRegistry", "AgentSpec", "AgentRuntime",
    "ExecutionMode", "SecurityTask", "TaskResult",
    "EncryptionService", "KeyManager", "AuthenticationManager",
    "AuthorizationManager", "RBACRole", "Capability", "PolicyDecision",
    "SecurityPolicy", "InputValidator", "ValidationRule", "AuditLogger", "AuditEntry",
    "BaseSecurityAgent", "ThreatDetectorAgent", "IncidentResponderAgent",
    "SecurityTool", "ToolGateway", "ToolRegistry", "SecureLogger",
]
