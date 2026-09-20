"""
Input Validator - 입력 검증기

SQL 인젝션, XSS, 명령어 인젝션, 경로 순회 등 다양한 공격 벡터로부터 보호
"""

import re
from typing import Optional, List, Dict, Any, Callable
from dataclasses import dataclass, field
from enum import Enum


class AttackType(Enum):
    """공격 타입"""
    SQL_INJECTION = "sql_injection"
    XSS = "xss"
    COMMAND_INJECTION = "command_injection"
    PATH_TRAVERSAL = "path_traversal"
    LDAP_INJECTION = "ldap_injection"
    XXE = "xxe"
    SSRF = "ssrf"
    FILE_UPLOAD = "file_upload"


@dataclass
class ValidationRule:
    """검증 규칙"""
    name: str
    pattern: Optional[str] = None
    validator: Optional[Callable[[str], bool]] = None
    attack_type: AttackType = AttackType.SQL_INJECTION
    severity: str = "high"  # low, medium, high, critical
    enabled: bool = True
    description: str = ""


@dataclass
class ValidationResult:
    """검증 결과"""
    is_valid: bool
    input_value: str
    violations: List[Dict[str, Any]] = field(default_factory=list)
    sanitized_value: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_valid": self.is_valid,
            "input_value": self.input_value[:100] + "..." if len(self.input_value) > 100 else self.input_value,
            "violations": self.violations,
            "sanitized_value": self.sanitized_value
        }


class InputValidator:
    """
    입력 검증기
    
    다양한 공격 벡터로부터 시스템을 보호하는 입력 검증 및 살균 (sanitization)
    """
    
    def __init__(self):
        self._rules: Dict[str, ValidationRule] = {}
        self._blocked_chars: Dict[str, List[str]] = {}
        self._max_lengths: Dict[str, int] = {
            "default": 10000,
            "username": 50,
            "password": 128,
            "email": 254,
            "url": 2048,
            "filepath": 255,
        }
        
        # 기본 규칙 등록
        self._init_default_rules()
    
    def _init_default_rules(self) -> None:
        """기본 검증 규칙 초기화"""
        
        # SQL 인젝션 패턴
        sql_patterns = [
            r"(?i)(SELECT|INSERT|UPDATE|DELETE|DROP|UNION|ALTER|CREATE|TRUNCATE)\s",
            r"(?i)--\s*$",
            r"(?i);\s*(SELECT|INSERT|UPDATE|DELETE|DROP)",
            r"(?i)'\s*(OR|AND)\s*'?\d*'?\s*=\s*'?\d*",
            r"(?i)'\s*(OR|AND)\s*'?'[^']*'?\s*=\s*'?'[^']*",
            r"(?i)EXEC\s*\(",
            r"(?i)EXECUTE\s+.*@",
        ]
        
        for i, pattern in enumerate(sql_patterns):
            self.add_rule(ValidationRule(
                name=f"sql_injection_{i}",
                pattern=pattern,
                attack_type=AttackType.SQL_INJECTION,
                severity="critical",
                description="SQL injection attempt detected"
            ))
        
        # XSS 패턴
        xss_patterns = [
            r"<script[^>]*>",
            r"</script>",
            r"javascript:",
            r"on(load|error|click|mouse|focus|blur|change|submit)\s*=",
            r"<iframe[^>]*>",
            r"<object[^>]*>",
            r"<embed[^>]*>",
            r"<svg[^>]*onload",
        ]
        
        for i, pattern in enumerate(xss_patterns):
            self.add_rule(ValidationRule(
                name=f"xss_{i}",
                pattern=pattern,
                attack_type=AttackType.XSS,
                severity="high",
                description="XSS attempt detected"
            ))
        
        # 명령어 인젝션 패턴
        cmd_patterns = [
            r"[;&|`$]",
            r"\$\([^)]+\)",
            r"`[^`]+`",
            r"\|\s*\w+",
            r";\s*\w+",
            r">\s*/",
            r"<\s*/",
            r"\.\./",
        ]
        
        for i, pattern in enumerate(cmd_patterns):
            self.add_rule(ValidationRule(
                name=f"cmd_injection_{i}",
                pattern=pattern,
                attack_type=AttackType.COMMAND_INJECTION,
                severity="critical",
                description="Command injection attempt detected"
            ))
        
        # 경로 순회 패턴
        path_patterns = [
            r"\.\./",
            r"\.\.\\",
            r"%2e%2e%2f",
            r"%2e%2e/",
            r"\.\.%2f",
            r"%2e%2e\\",
        ]
        
        for i, pattern in enumerate(path_patterns):
            self.add_rule(ValidationRule(
                name=f"path_traversal_{i}",
                pattern=pattern,
                attack_type=AttackType.PATH_TRAVERSAL,
                severity="high",
                description="Path traversal attempt detected"
            ))
    
    def add_rule(self, rule: ValidationRule) -> None:
        """검증 규칙 추가"""
        self._rules[rule.name] = rule
    
    def remove_rule(self, name: str) -> bool:
        """검증 규칙 제거"""
        if name in self._rules:
            del self._rules[name]
            return True
        return False
    
    def validate_input(
        self,
        value: str,
        input_type: str = "default",
        check_all: bool = True
    ) -> ValidationResult:
        """
        입력값 검증
        
        Args:
            value: 검증할 입력값
            input_type: 입력 타입 (username, email, url 등)
            check_all: 모든 규칙을 확인할지 (True) 또는 첫 위반 시 중단할지 (False)
        
        Returns:
            ValidationResult: 검증 결과
        """
        violations = []
        
        # 길이 제한 확인
        max_len = self._max_lengths.get(input_type, self._max_lengths["default"])
        if len(value) > max_len:
            violations.append({
                "rule": "max_length",
                "message": f"Input exceeds maximum length of {max_len}",
                "severity": "medium"
            })
            if not check_all:
                return ValidationResult(
                    is_valid=False,
                    input_value=value,
                    violations=violations
                )
        
        # 빈 입력 확인 (null byte 등)
        if '\x00' in value:
            violations.append({
                "rule": "null_byte",
                "message": "Null byte detected in input",
                "severity": "high"
            })
            if not check_all:
                return ValidationResult(
                    is_valid=False,
                    input_value=value,
                    violations=violations
                )
        
        # 등록된 규칙들 확인
        for rule_name, rule in self._rules.items():
            if not rule.enabled:
                continue
            
            if rule.pattern:
                if re.search(rule.pattern, value):
                    violations.append({
                        "rule": rule_name,
                        "attack_type": rule.attack_type.value,
                        "message": rule.description,
                        "severity": rule.severity,
                        "pattern": rule.pattern
                    })
                    
                    if not check_all:
                        break
            
            elif rule.validator:
                if not rule.validator(value):
                    violations.append({
                        "rule": rule_name,
                        "attack_type": rule.attack_type.value,
                        "message": rule.description,
                        "severity": rule.severity
                    })
                    
                    if not check_all:
                        break
        
        # 살균된 값 생성
        sanitized = self.sanitize_input(value) if violations else value
        
        return ValidationResult(
            is_valid=len(violations) == 0,
            input_value=value,
            violations=violations,
            sanitized_value=sanitized
        )
    
    def sanitize_input(self, value: str) -> str:
        """
        입력값 살균 (위험 문자 제거/인코딩)
        """
        if not value:
            return value
        
        # HTML 특수 문자 인코딩
        html_escape_table = {
            "&": "&amp;",
            '"': "&quot;",
            "'": "&#x27;",
            ">": "&gt;",
            "<": "&lt;",
        }
        
        result = value
        for char, escape in html_escape_table.items():
            result = result.replace(char, escape)
        
        # SQL 특수 문자 이스케이프
        sql_chars = ["'", '"', ";", "--", "/*", "*/"]
        for char in sql_chars:
            result = result.replace(char, f"\\{char}")
        
        # 명령어 특수 문자 제거
        cmd_chars = ["$", "`", "(", ")", "{", "}", "[", "]", "|", "&", ";", "<", ">", "\\", "\n", "\r"]
        for char in cmd_chars:
            result = result.replace(char, "")
        
        return result
    
    def validate_email(self, email: str) -> bool:
        """이메일 형식 검증"""
        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        return bool(re.match(pattern, email)) and len(email) <= self._max_lengths["email"]
    
    def validate_username(self, username: str) -> bool:
        """사용자명 형식 검증"""
        if not username or len(username) > self._max_lengths["username"]:
            return False
        
        # 영문, 숫자, 밑줄, 하이픈만 허용
        pattern = r"^[a-zA-Z][a-zA-Z0-9_-]{2,49}$"
        return bool(re.match(pattern, username))
    
    def validate_url(self, url: str, allowed_schemes: Optional[List[str]] = None) -> bool:
        """URL 형식 및 프로토콜 검증"""
        if not url or len(url) > self._max_lengths["url"]:
            return False
        
        # 기본 허용 스키마
        if allowed_schemes is None:
            allowed_schemes = ["https"]
        
        pattern = r"^([a-zA-Z][a-zA-Z0-9+.-]*):\/\/"
        match = re.match(pattern, url)
        
        if not match:
            return False
        
        scheme = match.group(1).lower()
        return scheme in allowed_schemes
    
    def validate_filepath(self, filepath: str, base_dir: Optional[str] = None) -> bool:
        """파일 경로 검증 (경로 순회 방지)"""
        if not filepath:
            return False
        
        # 경로 순회 패턴 확인
        result = self.validate_input(filepath, input_type="filepath")
        if not result.is_valid:
            return False
        
        # 절대 경로 제한
        if filepath.startswith("/"):
            return False
        
        # base_dir 가 주어지면 해당 디렉토리 내에 있는지 확인
        if base_dir:
            import os
            resolved = os.path.realpath(os.path.join(base_dir, filepath))
            if not resolved.startswith(os.path.realpath(base_dir)):
                return False
        
        return True
    
    def is_safe(self, value: str, input_type: str = "default") -> bool:
        """간단한 안전성 확인"""
        return self.validate_input(value, input_type, check_all=False).is_valid
