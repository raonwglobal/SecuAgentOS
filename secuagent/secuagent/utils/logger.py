"""
Secure Logger - 보안 로그

민감정보 마스킹 및 안전한 로깅
"""

import logging
import re
from typing import Optional, Dict, Any, List


class SecureLogger:
    """
    보안 로그 클래스
    
    민감정보를 자동으로 마스킹하여 안전한 로깅 제공
    """
    
    # 마스킹 패턴
    PATTERNS = {
        "credit_card": r"\b(?:\d{4}[- ]?){3}\d{4}\b",
        "ssn": r"\b\d{3}-\d{2}-\d{4}\b",
        "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
        "phone": r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b",
        "ip_address": r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b",
        "api_key": r"\b(?:api[_-]?key|apikey)[\"']?\s*[:=]\s*[\"']?[A-Za-z0-9_-]{20,}[\"']?",
        "password": r"\b(?:password|passwd|pwd)[\"']?\s*[:=]\s*[\"']?[^\"'\s]+[\"']?",
        "jwt_token": r"\beyJ[A-Za-z0-9_-]+\.eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\b",
    }
    
    def __init__(
        self,
        name: str,
        level: int = logging.INFO,
        mask_enabled: bool = True,
        custom_patterns: Optional[Dict[str, str]] = None
    ):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)
        
        # 핸들러가 없으면 기본 스트림 핸들러 추가
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            handler.setLevel(level)
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S"
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
        
        self.mask_enabled = mask_enabled
        self._patterns = self.PATTERNS.copy()
        
        # 커스텀 패턴 추가
        if custom_patterns:
            self._patterns.update(custom_patterns)
    
    def _mask_sensitive(self, message: str) -> str:
        """민감정보 마스킹"""
        if not self.mask_enabled:
            return message
        
        masked = message
        
        for pattern_name, pattern in self._patterns.items():
            if pattern_name == "api_key" or pattern_name == "password":
                # 키/비밀번호는 값만 마스킹
                def replace_key(match):
                    return match.group(0).split("=")[0] + "=***MASKED***"
                masked = re.sub(pattern, replace_key, masked, flags=re.IGNORECASE)
            else:
                # 기타 패턴은 전체 마스킹
                replacement = f"***MASKED_{pattern_name.upper()}***"
                masked = re.sub(pattern, replacement, masked, flags=re.IGNORECASE)
        
        return masked
    
    def debug(self, msg: str, *args, **kwargs) -> None:
        """디버그 레벨 로깅"""
        self.logger.debug(self._mask_sensitive(msg), *args, **kwargs)
    
    def info(self, msg: str, *args, **kwargs) -> None:
        """정보 레벨 로깅"""
        self.logger.info(self._mask_sensitive(msg), *args, **kwargs)
    
    def warning(self, msg: str, *args, **kwargs) -> None:
        """경고 레벨 로깅"""
        self.logger.warning(self._mask_sensitive(msg), *args, **kwargs)
    
    def error(self, msg: str, *args, **kwargs) -> None:
        """에러 레벨 로깅"""
        self.logger.error(self._mask_sensitive(msg), *args, **kwargs)
    
    def critical(self, msg: str, *args, **kwargs) -> None:
        """치명적 에러 레벨 로깅"""
        self.logger.critical(self._mask_sensitive(msg), *args, **kwargs)
    
    def log(self, level: int, msg: str, *args, **kwargs) -> None:
        """지정된 레벨로 로깅"""
        self.logger.log(level, self._mask_sensitive(msg), *args, **kwargs)
    
    def set_mask_enabled(self, enabled: bool) -> None:
        """마스킹 활성화/비활성화"""
        self.mask_enabled = enabled
    
    def add_mask_pattern(self, name: str, pattern: str) -> None:
        """커스텀 마스킹 패턴 추가"""
        self._patterns[name] = pattern
    
    def remove_mask_pattern(self, name: str) -> bool:
        """마스킹 패턴 제거"""
        if name in self._patterns and name not in self.PATTERNS:
            del self._patterns[name]
            return True
        return False
