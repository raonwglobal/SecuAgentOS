"""
Base Security Agent - 기본 보안 에이전트

모든 전문 보안 에이전트의 베이스 클래스
"""

from typing import Optional, Dict, Any, List, Callable
from abc import ABC, abstractmethod
from datetime import datetime

from secuagent.core.context import SecurityContext, SecurityLevel, UserRole
from secuagent.core.agent import SecureAgent
from secuagent.core.events import SecurityEvent, SecurityEventType, EventQueue
from secuagent.security.audit import AuditLogger, AuditEventType


class BaseSecurityAgent(SecureAgent, ABC):
    """
    기본 보안 에이전트 추상 클래스
    
    모든 전문 보안 에이전트가 상속받는 베이스 클래스
    """
    
    def __init__(
        self,
        name: str,
        context: Optional[SecurityContext] = None,
        event_queue: Optional[EventQueue] = None,
        audit_logger: Optional[AuditLogger] = None,
        **kwargs
    ):
        super().__init__(name=name, context=context, event_queue=event_queue)
        
        self.audit_logger = audit_logger or AuditLogger()
        self._capabilities: List[str] = []
        self._handlers: Dict[str, Callable] = {}
        
        # 에이전트 메타데이터
        self._metadata.update({
            "agent_type": "base_security_agent",
            "version": "1.0.0",
            "capabilities": self._capabilities
        })
    
    @abstractmethod
    def execute(self, action: str, **kwargs) -> Dict[str, Any]:
        """
        작업 실행 (추상 메서드)
        
        하위 클래스에서 구현해야 함
        """
        pass
    
    def register_capability(self, capability: str, handler: Callable) -> None:
        """기능 등록"""
        self._capabilities.append(capability)
        self._handlers[capability] = handler
        self._metadata["capabilities"] = self._capabilities
    
    def has_capability(self, capability: str) -> bool:
        """기능 보유 여부 확인"""
        return capability in self._capabilities
    
    def get_capabilities(self) -> List[str]:
        """보유한 기능 목록 반환"""
        return self._capabilities.copy()
    
    def _audit_log(
        self,
        event_type: AuditEventType,
        action: str,
        description: str,
        success: bool = True,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """감사 로그 기록"""
        if self.context.audit_enabled:
            self.audit_logger.log(
                event_type=event_type,
                user_id=self.context.user_id,
                session_id=self.context.session_id,
                action=action,
                description=description,
                success=success,
                metadata=metadata,
                severity="info" if success else "warning"
            )
    
    def get_status(self) -> Dict[str, Any]:
        """에이전트 상태 반환"""
        status = super().get_status()
        status.update({
            "agent_type": "base_security_agent",
            "capabilities": self._capabilities,
            "audit_enabled": self.context.audit_enabled
        })
        return status
