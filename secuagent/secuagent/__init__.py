"""
SecuAgent - Security-Focused AgentOS Library

보안 솔루션에 특화된 AI 에이전트 운영체제 구축을 위한 라이브러리
"""

__version__ = "0.1.0"
__author__ = "SecuAgent Team"

from secuagent.core.context import SecurityContext, SecurityLevel, UserRole
from secuagent.core.agent import SecureAgent
from secuagent.core.events import SecurityEvent, SecurityEventType, EventQueue

from secuagent.security.crypto import EncryptionService, KeyManager
from secuagent.security.auth import AuthenticationManager, AuthorizationManager, RBACRole
from secuagent.security.validator import InputValidator, ValidationRule
from secuagent.security.audit import AuditLogger, AuditEntry

from secuagent.agents.base import BaseSecurityAgent
from secuagent.agents.detector import ThreatDetectorAgent
from secuagent.agents.responder import IncidentResponderAgent

from secuagent.utils.logger import SecureLogger

__all__ = [
    # Core
    "SecurityContext",
    "SecurityLevel",
    "UserRole",
    "SecureAgent",
    "SecurityEvent",
    "SecurityEventType",
    "EventQueue",
    # Security
    "EncryptionService",
    "KeyManager",
    "AuthenticationManager",
    "AuthorizationManager",
    "RBACRole",
    "InputValidator",
    "ValidationRule",
    "AuditLogger",
    "AuditEntry",
    # Agents
    "BaseSecurityAgent",
    "ThreatDetectorAgent",
    "IncidentResponderAgent",
    # Utils
    "SecureLogger",
]
