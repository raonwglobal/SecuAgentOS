"""
Threat Detector Agent - 위협 탐지 에이전트

패턴 기반 위협 탐지 및 이상 탐지
"""

from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import re

from secuagent.core.context import SecurityContext
from secuagent.core.events import SecurityEventType, EventQueue
from secuagent.agents.base import BaseSecurityAgent
from secuagent.security.audit import AuditLogger, AuditEventType
from secuagent.security.validator import InputValidator


@dataclass
class ThreatPattern:
    """위협 패턴"""
    name: str
    pattern: str
    threat_type: str
    severity: str  # low, medium, high, critical
    description: str = ""
    enabled: bool = True
    false_positive_rate: float = 0.0


@dataclass
class ThreatDetection:
    """탐지된 위협"""
    detection_id: str
    timestamp: datetime
    pattern_name: str
    threat_type: str
    severity: str
    source: str
    input_data: str
    confidence: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)


class ThreatDetectorAgent(BaseSecurityAgent):
    """
    위협 탐지 에이전트
    
    실시간 위협 탐지 및 분석
    """
    
    def __init__(
        self,
        name: str = "ThreatDetector",
        context: Optional[SecurityContext] = None,
        event_queue: Optional[EventQueue] = None,
        audit_logger: Optional[AuditLogger] = None,
        **kwargs
    ):
        super().__init__(
            name=name,
            context=context,
            event_queue=event_queue,
            audit_logger=audit_logger
        )
        
        self._patterns: Dict[str, ThreatPattern] = {}
        self._detections: List[ThreatDetection] = []
        self._validator = InputValidator()
        
        # 기본 위협 패턴 등록
        self._init_default_patterns()
        
        self._metadata["agent_type"] = "threat_detector"
        self._metadata["capabilities"] = ["pattern_detection", "anomaly_detection", "real_time_scanning"]
    
    def _init_default_patterns(self) -> None:
        """기본 위협 패턴 초기화"""
        # SQL 인젝션
        self.add_pattern(ThreatPattern(
            name="sql_injection_basic",
            pattern=r"(?i)(SELECT|INSERT|UPDATE|DELETE|DROP|UNION)\s",
            threat_type="sql_injection",
            severity="critical",
            description="Basic SQL injection attempt"
        ))
        
        # XSS
        self.add_pattern(ThreatPattern(
            name="xss_script",
            pattern=r"<script[^>]*>",
            threat_type="xss",
            severity="high",
            description="XSS script tag detected"
        ))
        
        # 명령어 인젝션
        self.add_pattern(ThreatPattern(
            name="command_injection",
            pattern=r"[;&|`$]",
            threat_type="command_injection",
            severity="critical",
            description="Command injection characters detected"
        ))
        
        # 경로 순회
        self.add_pattern(ThreatPattern(
            name="path_traversal",
            pattern=r"\.\./",
            threat_type="path_traversal",
            severity="high",
            description="Path traversal attempt"
        ))
    
    def add_pattern(self, pattern: ThreatPattern) -> None:
        """위협 패턴 추가"""
        self._patterns[pattern.name] = pattern
    
    def remove_pattern(self, name: str) -> bool:
        """위협 패턴 제거"""
        if name in self._patterns:
            del self._patterns[name]
            return True
        return False
    
    def enable_pattern(self, name: str) -> bool:
        """패턴 활성화"""
        if name in self._patterns:
            self._patterns[name].enabled = True
            return True
        return False
    
    def disable_pattern(self, name: str) -> bool:
        """패턴 비활성화"""
        if name in self._patterns:
            self._patterns[name].enabled = False
            return True
        return False
    
    def detect(self, input_data: str, source: str = "unknown") -> List[ThreatDetection]:
        """
        입력 데이터에서 위협 탐지
        
        Args:
            input_data: 검사할 데이터
            source: 데이터 소스 (IP, 사용자 ID 등)
        
        Returns:
            탐지된 위협 목록
        """
        detections = []
        
        for pattern_name, pattern in self._patterns.items():
            if not pattern.enabled:
                continue
            
            if re.search(pattern.pattern, input_data):
                detection = ThreatDetection(
                    detection_id=f"det_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{pattern_name}",
                    timestamp=datetime.utcnow(),
                    pattern_name=pattern_name,
                    threat_type=pattern.threat_type,
                    severity=pattern.severity,
                    source=source,
                    input_data=input_data[:500],  # 첫 500 자만 저장
                    metadata={
                        "pattern": pattern.pattern,
                        "description": pattern.description
                    }
                )
                
                detections.append(detection)
                self._detections.append(detection)
                
                # 이벤트 발생
                self._emit_threat_event(detection)
        
        return detections
    
    def _emit_threat_event(self, detection: ThreatDetection) -> None:
        """위험 이벤트 발생"""
        event_type_map = {
            "sql_injection": SecurityEventType.SQL_INJECTION_ATTEMPT,
            "xss": SecurityEventType.XSS_ATTEMPT,
            "command_injection": SecurityEventType.COMMAND_INJECTION_ATTEMPT,
            "path_traversal": SecurityEventType.PATH_TRAVERSAL_ATTEMPT
        }
        
        event_type = event_type_map.get(detection.threat_type, SecurityEventType.THREAT_DETECTED)
        
        self._emit_event(
            event_type=event_type,
            description=f"Threat detected: {detection.pattern_name}",
            severity=detection.severity,
            metadata={
                "detection_id": detection.detection_id,
                "threat_type": detection.threat_type,
                "source": detection.source
            }
        )
        
        # 감사 로그
        self._audit_log(
            event_type=AuditEventType.THREAT_DETECTED,
            action="threat_detection",
            description=f"Detected {detection.threat_type} from {detection.source}",
            success=True,
            metadata={"detection_id": detection.detection_id}
        )
    
    def scan_request(
        self,
        method: str,
        path: str,
        headers: Dict[str, str],
        body: Optional[str] = None
    ) -> List[ThreatDetection]:
        """HTTP 요청 스캔"""
        detections = []
        
        # URL 경로 검사
        detections.extend(self.detect(path, source=f"http_{method}_path"))
        
        # 헤더 검사
        for key, value in headers.items():
            detections.extend(self.detect(value, source=f"http_header_{key}"))
        
        # 바디 검사
        if body:
            detections.extend(self.detect(body, source=f"http_{method}_body"))
        
        return detections
    
    def get_detections(
        self,
        threat_type: Optional[str] = None,
        severity: Optional[str] = None,
        limit: int = 100
    ) -> List[ThreatDetection]:
        """탐지 기록 조회"""
        results = []
        
        for detection in reversed(self._detections):
            if threat_type and detection.threat_type != threat_type:
                continue
            if severity and detection.severity != severity:
                continue
            
            results.append(detection)
            
            if len(results) >= limit:
                break
        
        return results
    
    def get_statistics(self) -> Dict[str, Any]:
        """탐지 통계 반환"""
        stats = {
            "total_detections": len(self._detections),
            "by_threat_type": {},
            "by_severity": {},
            "patterns_count": len(self._patterns),
            "active_patterns": sum(1 for p in self._patterns.values() if p.enabled)
        }
        
        for detection in self._detections:
            # 위협 타입별
            tt = detection.threat_type
            stats["by_threat_type"][tt] = stats["by_threat_type"].get(tt, 0) + 1
            
            # 심각도별
            sev = detection.severity
            stats["by_severity"][sev] = stats["by_severity"].get(sev, 0) + 1
        
        return stats
    
    def execute(self, action: str, **kwargs) -> Dict[str, Any]:
        """
        작업 실행
        
        Supported actions:
        - detect: 위협 탐지
        - scan_request: HTTP 요청 스캔
        - get_detections: 탐지 기록 조회
        - get_statistics: 통계 조회
        """
        if action == "detect":
            input_data = kwargs.get("input", "")
            source = kwargs.get("source", "unknown")
            detections = self.detect(input_data, source)
            return {
                "status": "success",
                "action": action,
                "detections_count": len(detections),
                "detections": [d.__dict__ for d in detections]
            }
        
        elif action == "scan_request":
            method = kwargs.get("method", "GET")
            path = kwargs.get("path", "/")
            headers = kwargs.get("headers", {})
            body = kwargs.get("body")
            detections = self.scan_request(method, path, headers, body)
            return {
                "status": "success",
                "action": action,
                "detections_count": len(detections),
                "detections": [d.__dict__ for d in detections]
            }
        
        elif action == "get_detections":
            threat_type = kwargs.get("threat_type")
            severity = kwargs.get("severity")
            limit = kwargs.get("limit", 100)
            detections = self.get_detections(threat_type, severity, limit)
            return {
                "status": "success",
                "action": action,
                "count": len(detections),
                "detections": [d.__dict__ for d in detections]
            }
        
        elif action == "get_statistics":
            return {
                "status": "success",
                "action": action,
                "statistics": self.get_statistics()
            }
        
        else:
            return {"status": "error", "action": action, "message": f"Unknown action: {action}"}
