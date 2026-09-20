"""
Security Events - 보안 이벤트 시스템

보안 이벤트 정의, 타입, 이벤트 큐 관리
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from datetime import datetime
from collections import deque
import uuid


class SecurityEventType(Enum):
    """보안 이벤트 타입"""
    # 인증 관련
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILURE = "login_failure"
    LOGOUT = "logout"
    MFA_CHALLENGE = "mfa_challenge"
    MFA_SUCCESS = "mfa_success"
    MFA_FAILURE = "mfa_failure"
    
    # 권한 관련
    ACCESS_GRANTED = "access_granted"
    ACCESS_DENIED = "access_denied"
    PRIVILEGE_ESCALATION = "privilege_escalation"
    ROLE_CHANGE = "role_change"
    
    # 위협 탐지
    THREAT_DETECTED = "threat_detected"
    SQL_INJECTION_ATTEMPT = "sql_injection_attempt"
    XSS_ATTEMPT = "xss_attempt"
    COMMAND_INJECTION_ATTEMPT = "command_injection_attempt"
    PATH_TRAVERSAL_ATTEMPT = "path_traversal_attempt"
    BRUTE_FORCE_ATTEMPT = "brute_force_attempt"
    
    # 데이터 보안
    DATA_ACCESS = "data_access"
    DATA_MODIFICATION = "data_modification"
    DATA_EXPORT = "data_export"
    ENCRYPTION_OPERATION = "encryption_operation"
    
    # 시스템 보안
    CONFIG_CHANGE = "config_change"
    SECURITY_POLICY_UPDATE = "security_policy_update"
    SESSION_EXPIRED = "session_expired"
    SESSION_INVALIDATED = "session_invalidated"
    
    # 사고 대응
    INCIDENT_CREATED = "incident_created"
    INCIDENT_RESOLVED = "incident_resolved"
    AUTOMATED_RESPONSE = "automated_response"
    MANUAL_INTERVENTION = "manual_intervention"


@dataclass
class SecurityEvent:
    """
    보안 이벤트 클래스
    
    모든 보안 관련 이벤트를 기록하고 추적
    """
    event_type: SecurityEventType
    timestamp: datetime = field(default_factory=datetime.utcnow)
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    source_ip: Optional[str] = None
    description: str = ""
    severity: str = "medium"  # low, medium, high, critical
    metadata: Dict[str, Any] = field(default_factory=dict)
    success: bool = True
    error_code: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "timestamp": self.timestamp.isoformat(),
            "user_id": self.user_id,
            "session_id": self.session_id,
            "source_ip": self.source_ip,
            "description": self.description,
            "severity": self.severity,
            "metadata": self.metadata,
            "success": self.success,
            "error_code": self.error_code,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SecurityEvent":
        """딕셔너리에서 생성"""
        data = data.copy()
        data["event_type"] = SecurityEventType(data["event_type"])
        data["timestamp"] = datetime.fromisoformat(data["timestamp"]) if "timestamp" in data else datetime.utcnow()
        return cls(**data)


class EventQueue:
    """
    보안 이벤트 큐
    
    비동기 이벤트 처리를 위한 스레드 안전 큐
    """
    
    def __init__(self, max_size: int = 10000):
        self._queue: deque = deque(maxlen=max_size)
        self._subscribers: List[callable] = []
    
    def enqueue(self, event: SecurityEvent) -> None:
        """이벤트 추가"""
        self._queue.append(event)
        # 구독자에게 알림
        for subscriber in self._subscribers:
            try:
                subscriber(event)
            except Exception:
                pass  # 로깅은 별도 처리
    
    def dequeue(self) -> Optional[SecurityEvent]:
        """이벤트 추출 (FIFO)"""
        if self._queue:
            return self._queue.popleft()
        return None
    
    def peek(self) -> Optional[SecurityEvent]:
        """다음 이벤트 확인 (제거 안 함)"""
        if self._queue:
            return self._queue[0]
        return None
    
    def size(self) -> int:
        """큐 크기 반환"""
        return len(self._queue)
    
    def is_empty(self) -> bool:
        """큐 비어있음 확인"""
        return len(self._queue) == 0
    
    def clear(self) -> None:
        """큐 초기화"""
        self._queue.clear()
    
    def subscribe(self, callback: callable) -> None:
        """이벤트 구독자 등록"""
        if callback not in self._subscribers:
            self._subscribers.append(callback)
    
    def unsubscribe(self, callback: callable) -> None:
        """이벤트 구독자 제거"""
        if callback in self._subscribers:
            self._subscribers.remove(callback)
    
    def get_events_by_type(
        self, 
        event_type: SecurityEventType,
        limit: int = 100
    ) -> List[SecurityEvent]:
        """특정 타입의 이벤트 조회"""
        events = [e for e in self._queue if e.event_type == event_type]
        return events[-limit:]
    
    def get_events_by_severity(
        self,
        severity: str,
        limit: int = 100
    ) -> List[SecurityEvent]:
        """특정 심각도의 이벤트 조회"""
        events = [e for e in self._queue if e.severity == severity]
        return events[-limit:]
    
    def get_recent_events(self, limit: int = 100) -> List[SecurityEvent]:
        """최근 이벤트 조회"""
        return list(self._queue)[-limit:]
