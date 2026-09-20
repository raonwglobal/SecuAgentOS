"""
Authentication & Authorization - 인증 및 인가 관리

MFA, JWT 세션, RBAC(역할 기반 접근 제어), 계정 잠금
"""

from typing import Optional, Dict, Any, List, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import secrets
import hashlib
import time

import jwt

from secuagent.core.context import SecurityContext, UserRole


class RBACRole(Enum):
    """RBAC 역할 정의"""
    GUEST = "guest"
    USER = "user"
    ANALYST = "analyst"
    ADMIN = "admin"
    SECURITY_ADMIN = "security_admin"
    SYSTEM = "system"
    
    @property
    def privilege_level(self) -> int:
        """권한 레벨 반환 (1-5)"""
        levels = {
            RBACRole.GUEST: 1,
            RBACRole.USER: 2,
            RBACRole.ANALYST: 3,
            RBACRole.ADMIN: 4,
            RBACRole.SECURITY_ADMIN: 5,
            RBACRole.SYSTEM: 5,
        }
        return levels.get(self, 1)


@dataclass
class UserAccount:
    """사용자 계정 정보"""
    user_id: str
    username: str
    password_hash: str
    email: Optional[str] = None
    roles: Set[RBACRole] = field(default_factory=lambda: {RBACRole.USER})
    is_active: bool = True
    is_locked: bool = False
    failed_login_attempts: int = 0
    last_login: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    mfa_enabled: bool = False
    mfa_secret: Optional[str] = None
    
    def lock(self) -> None:
        """계정 잠금"""
        self.is_locked = True
    
    def unlock(self) -> None:
        """계정 잠금 해제"""
        self.is_locked = False
        self.failed_login_attempts = 0
    
    def record_failed_login(self) -> None:
        """실패한 로그인 기록"""
        self.failed_login_attempts += 1
    
    def record_success_login(self) -> None:
        """성공한 로그인 기록"""
        self.failed_login_attempts = 0
        self.last_login = datetime.utcnow()


class AuthenticationManager:
    """
    인증 관리자
    
    사용자 인증, MFA, JWT 세션 관리, 계정 잠금 처리
    """
    
    def __init__(
        self,
        jwt_secret: Optional[str] = None,
        jwt_expiry_hours: int = 24,
        max_failed_attempts: int = 5,
        lockout_duration_minutes: int = 30
    ):
        self.jwt_secret = jwt_secret or secrets.token_hex(32)
        self.jwt_expiry_hours = jwt_expiry_hours
        self.max_failed_attempts = max_failed_attempts
        self.lockout_duration_minutes = lockout_duration_minutes
        
        self._users: Dict[str, UserAccount] = {}
        self._sessions: Dict[str, Dict[str, Any]] = {}
        self._mfa_codes: Dict[str, Dict[str, Any]] = {}
    
    def _hash_password(self, password: str, salt: Optional[str] = None) -> tuple[str, str]:
        """비밀번호 해시 (SHA-256 + salt)"""
        if salt is None:
            salt = secrets.token_hex(16)
        
        salted = f"{salt}{password}".encode('utf-8')
        password_hash = hashlib.sha256(salted).hexdigest()
        
        return password_hash, salt
    
    def register_user(
        self,
        user_id: str,
        username: str,
        password: str,
        email: Optional[str] = None,
        roles: Optional[List[RBACRole]] = None
    ) -> UserAccount:
        """사용자 등록"""
        if user_id in self._users:
            raise ValueError(f"User already exists: {user_id}")
        
        password_hash, salt = self._hash_password(password)
        
        user = UserAccount(
            user_id=user_id,
            username=username,
            password_hash=password_hash,
            email=email,
            roles=set(roles) if roles else {RBACRole.USER}
        )
        
        # salt 는 실제 구현에서는 별도 저장
        user.password_hash = f"{salt}:{password_hash}"
        
        self._users[user_id] = user
        return user
    
    def authenticate(
        self,
        user_id: str,
        password: str
    ) -> tuple[bool, Optional[str], Optional[str]]:
        """
        사용자 인증
        
        Returns:
            (success, token_or_error, message)
        """
        user = self._users.get(user_id)
        
        if user is None:
            return False, None, "User not found"
        
        if user.is_locked:
            return False, None, "Account is locked"
        
        if not user.is_active:
            return False, None, "Account is deactivated"
        
        # 비밀번호 검증
        stored = user.password_hash.split(":")
        if len(stored) != 2:
            return False, None, "Invalid password format"
        
        salt, stored_hash = stored
        test_hash, _ = self._hash_password(password, salt)
        
        if test_hash != stored_hash:
            user.record_failed_login()
            
            # 계정 잠금 확인
            if user.failed_login_attempts >= self.max_failed_attempts:
                user.lock()
                return False, None, "Account locked due to too many failed attempts"
            
            return False, None, "Invalid password"
        
        # 인증 성공
        user.record_success_login()
        
        # JWT 토큰 생성
        token = self._generate_jwt_token(user)
        
        return True, token, "Authentication successful"
    
    def _generate_jwt_token(self, user: UserAccount) -> str:
        """JWT 토큰 생성"""
        payload = {
            "user_id": user.user_id,
            "username": user.username,
            "roles": [role.value for role in user.roles],
            "exp": datetime.utcnow() + timedelta(hours=self.jwt_expiry_hours),
            "iat": datetime.utcnow(),
            "jti": secrets.token_hex(16)
        }
        
        token = jwt.encode(payload, self.jwt_secret, algorithm="HS256")
        
        # 세션 저장
        self._sessions[payload["jti"]] = {
            "user_id": user.user_id,
            "created_at": datetime.utcnow(),
            "expires_at": payload["exp"]
        }
        
        return token
    
    def verify_token(self, token: str) -> tuple[bool, Optional[Dict[str, Any]], str]:
        """JWT 토큰 검증"""
        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=["HS256"])
            
            # 세션 확인
            jti = payload.get("jti")
            if jti and jti not in self._sessions:
                return False, None, "Session not found"
            
            return True, payload, "Token valid"
        
        except jwt.ExpiredSignatureError:
            return False, None, "Token expired"
        except jwt.InvalidTokenError as e:
            return False, None, f"Invalid token: {str(e)}"
    
    def generate_mfa_code(self, user_id: str) -> str:
        """MFA 코드 생성"""
        user = self._users.get(user_id)
        if user is None:
            raise ValueError("User not found")
        
        code = secrets.token_hex(3)[:6].upper()  # 6 자리 코드
        
        self._mfa_codes[user_id] = {
            "code": code,
            "created_at": datetime.utcnow(),
            "expires_at": datetime.utcnow() + timedelta(minutes=5)
        }
        
        return code
    
    def verify_mfa_code(self, user_id: str, code: str) -> bool:
        """MFA 코드 검증"""
        mfa_data = self._mfa_codes.get(user_id)
        
        if mfa_data is None:
            return False
        
        if datetime.utcnow() > mfa_data["expires_at"]:
            del self._mfa_codes[user_id]
            return False
        
        if mfa_data["code"] != code.upper():
            return False
        
        # 코드 사용 후 삭제
        del self._mfa_codes[user_id]
        return True
    
    def logout(self, token: str) -> bool:
        """로그아웃 (세션 무효화)"""
        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=["HS256"])
            jti = payload.get("jti")
            
            if jti and jti in self._sessions:
                del self._sessions[jti]
                return True
            
            return False
        
        except jwt.InvalidTokenError:
            return False
    
    def get_user(self, user_id: str) -> Optional[UserAccount]:
        """사용자 정보 조회"""
        return self._users.get(user_id)
    
    def unlock_account(self, user_id: str) -> bool:
        """계정 잠금 해제"""
        user = self._users.get(user_id)
        if user:
            user.unlock()
            return True
        return False


class AuthorizationManager:
    """
    인가 관리자
    
    RBAC 기반 권한 검증 및 접근 제어
    """
    
    def __init__(self):
        self._permissions: Dict[str, Set[str]] = {}  # role -> permissions
        self._resource_policies: Dict[str, Dict[str, Any]] = {}
        
        # 기본 권한 매핑
        self._init_default_permissions()
    
    def _init_default_permissions(self) -> None:
        """기본 권한 설정"""
        self._permissions = {
            RBACRole.GUEST: {"read:public"},
            RBACRole.USER: {"read:own", "write:own", "delete:own"},
            RBACRole.ANALYST: {"read:all", "analyze:all", "export:reports"},
            RBACRole.ADMIN: {"read:all", "write:all", "delete:all", "manage:users"},
            RBACRole.SECURITY_ADMIN: {"read:all", "write:all", "delete:all", "manage:security", "manage:users", "audit:all"},
            RBACRole.SYSTEM: {"*"},  # 모든 권한
        }
    
    def has_permission(
        self,
        roles: List[RBACRole],
        permission: str
    ) -> bool:
        """권한 확인"""
        for role in roles:
            role_perms = self._permissions.get(role, set())
            
            # 와일드카드 권한 확인
            if "*" in role_perms:
                return True
            
            if permission in role_perms:
                return True
        
        return False
    
    def can_access_resource(
        self,
        roles: List[RBACRole],
        resource_type: str,
        action: str,
        resource_id: Optional[str] = None
    ) -> bool:
        """리소스 접근 권한 확인"""
        permission = f"{action}:{resource_type}"
        
        # 특정 리소스 정책 확인
        if resource_id and resource_id in self._resource_policies:
            policy = self._resource_policies[resource_id]
            if not self._evaluate_policy(policy, roles, action):
                return False
        
        return self.has_permission(roles, permission)
    
    def _evaluate_policy(
        self,
        policy: Dict[str, Any],
        roles: List[RBACRole],
        action: str
    ) -> bool:
        """정책 평가"""
        allowed_roles = policy.get("allowed_roles", [])
        denied_roles = policy.get("denied_roles", [])
        
        role_values = [r.value for r in roles]
        
        # 거부된 역할 확인
        for denied in denied_roles:
            if denied in role_values:
                return False
        
        # 허용된 역할 확인
        if allowed_roles:
            return any(r in role_values for r in allowed_roles)
        
        return True
    
    def add_resource_policy(
        self,
        resource_id: str,
        resource_type: str,
        allowed_roles: Optional[List[str]] = None,
        denied_roles: Optional[List[str]] = None
    ) -> None:
        """리소스 정책 추가"""
        self._resource_policies[resource_id] = {
            "resource_type": resource_type,
            "allowed_roles": allowed_roles or [],
            "denied_roles": denied_roles or []
        }
    
    def get_effective_permissions(self, roles: List[RBACRole]) -> Set[str]:
        """유효한 권한 목록 반환"""
        effective = set()
        
        for role in roles:
            role_perms = self._permissions.get(role, set())
            if "*" in role_perms:
                return {"*"}  # 모든 권한
            effective.update(role_perms)
        
        return effective
    
    def check_role_hierarchy(
        self,
        user_roles: List[RBACRole],
        required_role: RBACRole
    ) -> bool:
        """역할 계층 구조 확인 (동급 이상인지)"""
        required_level = required_role.privilege_level
        
        for role in user_roles:
            if role.privilege_level >= required_level:
                return True
        
        return False
