"""
Security Context - 보안 컨텍스트 관리

보안 수준, 사용자 권한, 세션 정보를 관리하는 핵심 클래스
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta


class SecurityLevel(Enum):
    """보안 수준 정의"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class UserRole(Enum):
    """사용자 역할 정의 (RBAC)"""
    GUEST = "guest"
    USER = "user"
    ANALYST = "analyst"
    ADMIN = "admin"
    SECURITY_ADMIN = "security_admin"
    SYSTEM = "system"


@dataclass
class SecurityContext:
    """
    보안 컨텍스트 클래스
    
    에이전트의 보안 수준, 사용자 정보, 권한, 세션 상태를 관리
    """
    security_level: SecurityLevel = SecurityLevel.MEDIUM
    user_id: str = "anonymous"
    roles: List[UserRole] = field(default_factory=lambda: [UserRole.GUEST])
    session_id: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # 접근 제어 설정
    max_privilege_level: int = 3  # 최대 권한 레벨 (1-5)
    require_mfa: bool = False
    ip_whitelist: List[str] = field(default_factory=list)
    ip_blacklist: List[str] = field(default_factory=list)
    
    # 감사 로깅 설정
    audit_enabled: bool = True
    log_level: str = "INFO"
    
    def __post_init__(self):
        """초기화 후 검증 및 설정"""
        if self.expires_at is None:
            # 기본 세션 만료 시간: 24 시간
            self.expires_at = self.created_at + timedelta(hours=24)
        
        # 보안 수준에 따른 자동 설정
        self._apply_security_level()
    
    def _apply_security_level(self):
        """보안 수준에 따른 자동 설정 적용"""
        if self.security_level == SecurityLevel.LOW:
            self.max_privilege_level = 2
            self.require_mfa = False
        elif self.security_level == SecurityLevel.MEDIUM:
            self.max_privilege_level = 3
            self.require_mfa = False
        elif self.security_level == SecurityLevel.HIGH:
            self.max_privilege_level = 4
            self.require_mfa = True
        elif self.security_level == SecurityLevel.CRITICAL:
            self.max_privilege_level = 5
            self.require_mfa = True
            self.audit_enabled = True
            self.log_level = "DEBUG"
    
    def has_role(self, role: UserRole) -> bool:
        """특정 역할 보유 여부 확인"""
        return role in self.roles
    
    def has_any_role(self, roles: List[UserRole]) -> bool:
        """주어진 역할 중 하나라도 보유 여부 확인"""
        return any(role in self.roles for role in roles)
    
    def has_all_roles(self, roles: List[UserRole]) -> bool:
        """주어진 모든 역할을 보유 여부 확인"""
        return all(role in self.roles for role in roles)
    
    def is_session_valid(self) -> bool:
        """세션 유효성 검사"""
        now = datetime.utcnow()
        if self.expires_at and now > self.expires_at:
            return False
        return True
    
    def can_access(self, required_level: int) -> bool:
        """접근 권한 확인"""
        return self.max_privilege_level >= required_level
    
    def add_role(self, role: UserRole) -> None:
        """역할 추가"""
        if role not in self.roles:
            self.roles.append(role)
    
    def remove_role(self, role: UserRole) -> None:
        """역할 제거"""
        if role in self.roles:
            self.roles.remove(role)
    
    def extend_session(self, hours: int = 24) -> None:
        """세션 연장"""
        self.expires_at = datetime.utcnow() + timedelta(hours=hours)
    
    def invalidate_session(self) -> None:
        """세션 무효화"""
        self.expires_at = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환 (직렬화용)"""
        return {
            "security_level": self.security_level.value,
            "user_id": self.user_id,
            "roles": [role.value for role in self.roles],
            "session_id": self.session_id,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "max_privilege_level": self.max_privilege_level,
            "require_mfa": self.require_mfa,
            "audit_enabled": self.audit_enabled,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SecurityContext":
        """딕셔너리에서 생성"""
        data = data.copy()
        data["security_level"] = SecurityLevel(data.get("security_level", "medium"))
        data["roles"] = [UserRole(r) for r in data.get("roles", ["guest"])]
        data["created_at"] = datetime.fromisoformat(data["created_at"]) if "created_at" in data else datetime.utcnow()
        data["expires_at"] = datetime.fromisoformat(data["expires_at"]) if data.get("expires_at") else None
        return cls(**data)
