"""
Audit Logger - 감사 로그

규정 준수 (GDPR, HIPAA, PCI-DSS) 를 위한 불변 감사 로그 시스템
"""

from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json
import hashlib
import uuid


class AuditEventType(Enum):
    """감사 이벤트 타입"""
    # 데이터 접근
    DATA_ACCESS = "data_access"
    DATA_CREATE = "data_create"
    DATA_UPDATE = "data_update"
    DATA_DELETE = "data_delete"
    DATA_EXPORT = "data_export"
    
    # 인증/인가
    LOGIN = "login"
    LOGOUT = "logout"
    ACCESS_GRANTED = "access_granted"
    ACCESS_DENIED = "access_denied"
    PERMISSION_CHANGE = "permission_change"
    
    # 보안 이벤트
    SECURITY_VIOLATION = "security_violation"
    THREAT_DETECTED = "threat_detected"
    POLICY_VIOLATION = "policy_violation"
    
    # 시스템
    CONFIG_CHANGE = "config_change"
    SYSTEM_STARTUP = "system_startup"
    SYSTEM_SHUTDOWN = "system_shutdown"
    
    # 규정 준수 관련
    CONSENT_GRANTED = "consent_granted"  # GDPR
    CONSENT_REVOKED = "consent_revoked"  # GDPR
    DATA_SUBJECT_REQUEST = "data_subject_request"  # GDPR
    PHI_ACCESS = "phi_access"  # HIPAA
    PHI_DISCLOSURE = "phi_disclosure"  # HIPAA
    CARD_DATA_ACCESS = "card_data_access"  # PCI-DSS


@dataclass
class AuditEntry:
    """
    감사 로그 엔트리
    
    모든 감사 가능한 이벤트를 기록
    """
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.utcnow)
    event_type: AuditEventType = AuditEventType.DATA_ACCESS
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    action: str = ""
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    description: str = ""
    severity: str = "info"  # debug, info, warning, error, critical
    success: bool = True
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # 규정 준수 태그
    gdpr_relevant: bool = False
    hipaa_relevant: bool = False
    pci_dss_relevant: bool = False
    
    # 무결성 검증용
    previous_hash: Optional[str] = None
    current_hash: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            "event_id": self.event_id,
            "timestamp": self.timestamp.isoformat(),
            "event_type": self.event_type.value,
            "user_id": self.user_id,
            "session_id": self.session_id,
            "action": self.action,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "description": self.description,
            "severity": self.severity,
            "success": self.success,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "metadata": self.metadata,
            "gdpr_relevant": self.gdpr_relevant,
            "hipaa_relevant": self.hipaa_relevant,
            "pci_dss_relevant": self.pci_dss_relevant,
            "previous_hash": self.previous_hash,
            "current_hash": self.current_hash,
        }
    
    def compute_hash(self) -> str:
        """엔트리 해시 계산"""
        data = {
            "event_id": self.event_id,
            "timestamp": self.timestamp.isoformat(),
            "event_type": self.event_type.value,
            "user_id": self.user_id,
            "action": self.action,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "success": self.success,
            "previous_hash": self.previous_hash,
        }
        data_str = json.dumps(data, sort_keys=True)
        return hashlib.sha256(data_str.encode('utf-8')).hexdigest()
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AuditEntry":
        """딕셔너리에서 생성"""
        data = data.copy()
        data["event_type"] = AuditEventType(data["event_type"])
        data["timestamp"] = datetime.fromisoformat(data["timestamp"])
        return cls(**data)


class AuditLogger:
    """
    감사 로그 관리자
    
    불변 감사 로그 체인 유지 및 규정 준수 보고
    """
    
    def __init__(
        self,
        storage_backend: Optional[callable] = None,
        enable_chain_verification: bool = True
    ):
        self._entries: List[AuditEntry] = []
        self._storage = storage_backend
        self._enable_chain = enable_chain_verification
        self._last_hash: Optional[str] = None
        
        # 필터 설정
        self._min_severity = "debug"
        self._include_event_types: Optional[List[AuditEventType]] = None
        self._exclude_event_types: Optional[List[AuditEventType]] = None
    
    def log(
        self,
        event_type: AuditEventType,
        user_id: Optional[str] = None,
        action: str = "",
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        description: str = "",
        severity: str = "info",
        success: bool = True,
        session_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        gdpr_relevant: bool = False,
        hipaa_relevant: bool = False,
        pci_dss_relevant: bool = False
    ) -> AuditEntry:
        """
        감사 로그 기록
        """
        # 심각도 필터 확인
        if not self._should_log(severity):
            return None
        
        # 이벤트 타입 필터 확인
        if not self._should_log_event_type(event_type):
            return None
        
        entry = AuditEntry(
            event_type=event_type,
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            description=description,
            severity=severity,
            success=success,
            session_id=session_id,
            ip_address=ip_address,
            user_agent=user_agent,
            metadata=metadata or {},
            gdpr_relevant=gdpr_relevant,
            hipaa_relevant=hipaa_relevant,
            pci_dss_relevant=pci_dss_relevant,
            previous_hash=self._last_hash
        )
        
        # 해시 체인 생성
        if self._enable_chain:
            entry.current_hash = entry.compute_hash()
            self._last_hash = entry.current_hash
        
        # 저장
        self._entries.append(entry)
        
        if self._storage:
            self._storage(entry)
        
        return entry
    
    def _should_log(self, severity: str) -> bool:
        """심각도 기반 로깅 여부 확인"""
        severity_levels = {
            "debug": 0,
            "info": 1,
            "warning": 2,
            "error": 3,
            "critical": 4
        }
        
        min_level = severity_levels.get(self._min_severity, 0)
        current_level = severity_levels.get(severity, 1)
        
        return current_level >= min_level
    
    def _should_log_event_type(self, event_type: AuditEventType) -> bool:
        """이벤트 타입 기반 로깅 여부 확인"""
        if self._include_event_types:
            return event_type in self._include_event_types
        
        if self._exclude_event_types:
            return event_type not in self._exclude_event_types
        
        return True
    
    def set_min_severity(self, severity: str) -> None:
        """최소 심각도 설정"""
        self._min_severity = severity
    
    def include_event_types(self, event_types: List[AuditEventType]) -> None:
        """로깅할 이벤트 타입 포함 설정"""
        self._include_event_types = event_types
    
    def exclude_event_types(self, event_types: List[AuditEventType]) -> None:
        """로깅할 이벤트 타입 제외 설정"""
        self._exclude_event_types = event_types
    
    def get_entries(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        user_id: Optional[str] = None,
        event_type: Optional[AuditEventType] = None,
        limit: int = 1000
    ) -> List[AuditEntry]:
        """감사 로그 조회"""
        results = []
        
        for entry in reversed(self._entries):
            # 시간 필터
            if start_time and entry.timestamp < start_time:
                continue
            if end_time and entry.timestamp > end_time:
                continue
            
            # 사용자 필터
            if user_id and entry.user_id != user_id:
                continue
            
            # 이벤트 타입 필터
            if event_type and entry.event_type != event_type:
                continue
            
            results.append(entry)
            
            if len(results) >= limit:
                break
        
        return results
    
    def verify_chain_integrity(self) -> tuple[bool, Optional[str]]:
        """
        해시 체인 무결성 검증
        
        Returns:
            (is_valid, first_invalid_entry_id)
        """
        if not self._enable_chain:
            return True, None
        
        prev_hash = None
        for entry in self._entries:
            if entry.previous_hash != prev_hash:
                return False, entry.event_id
            
            expected_hash = entry.compute_hash()
            if entry.current_hash != expected_hash:
                return False, entry.event_id
            
            prev_hash = entry.current_hash
        
        return True, None
    
    def export_for_compliance(
        self,
        regulation: str,  # "GDPR", "HIPAA", "PCI-DSS"
        start_time: datetime,
        end_time: datetime,
        format: str = "json"
    ) -> str:
        """
        규정 준수 보고서 내보내기
        """
        entries = self.get_entries(start_time=start_time, end_time=end_time, limit=100000)
        
        # 규제 관련 엔트리만 필터링
        if regulation == "GDPR":
            entries = [e for e in entries if e.gdpr_relevant or e.event_type in [
                AuditEventType.CONSENT_GRANTED,
                AuditEventType.CONSENT_REVOKED,
                AuditEventType.DATA_SUBJECT_REQUEST,
                AuditEventType.DATA_ACCESS,
                AuditEventType.DATA_EXPORT
            ]]
        elif regulation == "HIPAA":
            entries = [e for e in entries if e.hipaa_relevant or e.event_type in [
                AuditEventType.PHI_ACCESS,
                AuditEventType.PHI_DISCLOSURE
            ]]
        elif regulation == "PCI-DSS":
            entries = [e for e in entries if e.pci_dss_relevant or e.event_type in [
                AuditEventType.CARD_DATA_ACCESS,
                AuditEventType.DATA_ACCESS
            ]]
        
        if format == "json":
            return json.dumps([e.to_dict() for e in entries], indent=2)
        elif format == "csv":
            # CSV 포맷팅
            import csv
            import io
            
            output = io.StringIO()
            if entries:
                writer = csv.DictWriter(output, fieldnames=entries[0].to_dict().keys())
                writer.writeheader()
                for entry in entries:
                    writer.writerow(entry.to_dict())
            
            return output.getvalue()
        
        return str(entries)
    
    def get_statistics(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """감사 로그 통계"""
        entries = self.get_entries(start_time=start_time, end_time=end_time, limit=100000)
        
        stats = {
            "total_entries": len(entries),
            "by_severity": {},
            "by_event_type": {},
            "by_user": {},
            "success_rate": 0.0,
            "violations": 0
        }
        
        success_count = 0
        for entry in entries:
            # 심각도별
            sev = entry.severity
            stats["by_severity"][sev] = stats["by_severity"].get(sev, 0) + 1
            
            # 이벤트 타입별
            etype = entry.event_type.value
            stats["by_event_type"][etype] = stats["by_event_type"].get(etype, 0) + 1
            
            # 사용자별
            uid = entry.user_id or "anonymous"
            stats["by_user"][uid] = stats["by_user"].get(uid, 0) + 1
            
            # 성공률
            if entry.success:
                success_count += 1
            
            # 위반 카운트
            if entry.severity in ["error", "critical"]:
                stats["violations"] += 1
        
        if entries:
            stats["success_rate"] = success_count / len(entries) * 100
        
        return stats
    
    def clear(self) -> int:
        """로그 초기화 (주의: 규정 준수 목적에서는 사용 금지)"""
        count = len(self._entries)
        self._entries.clear()
        self._last_hash = None
        return count
