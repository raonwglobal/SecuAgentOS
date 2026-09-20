"""
Secure Agent - 보안 기능이 내장된 기본 에이전트 클래스
"""

from typing import Optional, Dict, Any, List
from datetime import datetime
import logging

from secuagent.core.context import SecurityContext, SecurityLevel, UserRole
from secuagent.core.events import SecurityEvent, SecurityEventType, EventQueue


class SecureAgent:
    """
    보안 기능이 내장된 기본 에이전트 클래스
    
    모든 SecuAgent 기반 에이전트의 부모 클래스
    """
    
    def __init__(
        self,
        name: str,
        context: Optional[SecurityContext] = None,
        event_queue: Optional[EventQueue] = None,
        logger: Optional[logging.Logger] = None
    ):
        self.name = name
        self.context = context or SecurityContext()
        self.event_queue = event_queue or EventQueue()
        self.logger = logger or logging.getLogger(f"secuagent.{name}")
        
        self.created_at = datetime.utcnow()
        self.is_active = True
        self._metadata: Dict[str, Any] = {}
        
        # 초기화 이벤트 기록
        self._emit_event(
            SecurityEventType.CONFIG_CHANGE,
            description=f"Agent '{name}' initialized",
            severity="low"
        )
    
    def _emit_event(
        self,
        event_type: SecurityEventType,
        description: str = "",
        severity: str = "medium",
        metadata: Optional[Dict[str, Any]] = None,
        success: bool = True,
        error_code: Optional[str] = None
    ) -> SecurityEvent:
        """보안 이벤트 발생 및 큐에 추가"""
        event = SecurityEvent(
            event_type=event_type,
            user_id=self.context.user_id,
            session_id=self.context.session_id,
            description=description,
            severity=severity,
            metadata=metadata or {},
            success=success,
            error_code=error_code
        )
        
        self.event_queue.enqueue(event)
        
        # 로깅
        log_level = getattr(logging, self.context.log_level.upper(), logging.INFO)
        self.logger.log(log_level, f"[{event_type.value}] {description}")
        
        return event
    
    def check_permission(self, required_role: UserRole) -> bool:
        """권한 확인"""
        if not self.context.is_session_valid():
            self._emit_event(
                SecurityEventType.ACCESS_DENIED,
                description="Session expired or invalid",
                severity="medium"
            )
            return False
        
        if not self.context.has_role(required_role):
            self._emit_event(
                SecurityEventType.ACCESS_DENIED,
                description=f"User lacks required role: {required_role.value}",
                severity="medium",
                metadata={"required_role": required_role.value}
            )
            return False
        
        self._emit_event(
            SecurityEventType.ACCESS_GRANTED,
            description=f"Access granted for role: {required_role.value}",
            severity="low"
        )
        return True
    
    def check_security_level(self, required_level: SecurityLevel) -> bool:
        """보안 수준 확인"""
        level_order = {
            SecurityLevel.LOW: 1,
            SecurityLevel.MEDIUM: 2,
            SecurityLevel.HIGH: 3,
            SecurityLevel.CRITICAL: 4
        }
        
        current = level_order[self.context.security_level]
        required = level_order[required_level]
        
        if current < required:
            self._emit_event(
                SecurityEventType.ACCESS_DENIED,
                description=f"Security level insufficient: {self.context.security_level.value} < {required_level.value}",
                severity="high"
            )
            return False
        
        return True
    
    def validate_context(self) -> bool:
        """컨텍스트 유효성 검사"""
        if not self.context.is_session_valid():
            self.logger.warning("Session expired")
            return False
        
        if self.context.require_mfa and not self._is_mfa_verified():
            self.logger.warning("MFA verification required")
            return False
        
        return True
    
    def _is_mfa_verified(self) -> bool:
        """MFA 인증 여부 확인 (하위 클래스에서 구현)"""
        # 기본적으로는 메타데이터에서 확인
        return self._metadata.get("mfa_verified", False)
    
    def set_metadata(self, key: str, value: Any) -> None:
        """메타데이터 설정"""
        self._metadata[key] = value
    
    def get_metadata(self, key: str, default: Any = None) -> Any:
        """메타데이터 조회"""
        return self._metadata.get(key, default)
    
    def activate(self) -> None:
        """에이전트 활성화"""
        self.is_active = True
        self._emit_event(
            SecurityEventType.CONFIG_CHANGE,
            description=f"Agent '{self.name}' activated",
            severity="low"
        )
    
    def deactivate(self) -> None:
        """에이전트 비활성화"""
        self.is_active = False
        self._emit_event(
            SecurityEventType.CONFIG_CHANGE,
            description=f"Agent '{self.name}' deactivated",
            severity="low"
        )
    
    def execute(self, action: str, **kwargs) -> Dict[str, Any]:
        """
        작업 실행 (하위 클래스에서 구현)
        
        보안 검증을 포함하는 기본 실행 프레임워크
        """
        if not self.is_active:
            raise RuntimeError(f"Agent '{self.name}' is not active")
        
        if not self.validate_context():
            raise PermissionError("Security context validation failed")
        
        # 하위 클래스에서 실제 구현
        return {"status": "not_implemented", "action": action}
    
    def get_status(self) -> Dict[str, Any]:
        """에이전트 상태 반환"""
        return {
            "name": self.name,
            "is_active": self.is_active,
            "security_level": self.context.security_level.value,
            "user_id": self.context.user_id,
            "roles": [r.value for r in self.context.roles],
            "session_valid": self.context.is_session_valid(),
            "created_at": self.created_at.isoformat(),
            "event_queue_size": self.event_queue.size(),
        }
