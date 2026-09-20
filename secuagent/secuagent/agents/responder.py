"""
Incident Responder Agent - 사고 대응 에이전트

자동화된 보안 사고 대응 및 플레이북 실행
"""

from typing import Optional, Dict, Any, List, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from secuagent.core.context import SecurityContext
from secuagent.core.events import SecurityEventType, EventQueue
from secuagent.agents.base import BaseSecurityAgent
from secuagent.security.audit import AuditLogger, AuditEventType


class IncidentSeverity(Enum):
    """사고 심각도"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class IncidentStatus(Enum):
    """사고 상태"""
    NEW = "new"
    INVESTIGATING = "investigating"
    CONTAINED = "contained"
    RESOLVED = "resolved"
    CLOSED = "closed"


@dataclass
class Incident:
    """보안 사고"""
    incident_id: str
    created_at: datetime
    title: str
    description: str
    severity: IncidentSeverity
    status: IncidentStatus = IncidentStatus.NEW
    assigned_to: Optional[str] = None
    related_events: List[str] = field(default_factory=list)
    affected_systems: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    resolved_at: Optional[datetime] = None
    resolution_notes: str = ""


@dataclass
class ResponseAction:
    """대응 작업"""
    action_id: str
    name: str
    description: str
    handler: Callable[[Incident], bool]
    auto_execute: bool = False
    requires_approval: bool = True
    executed: bool = False
    execution_result: Optional[str] = None


class IncidentResponderAgent(BaseSecurityAgent):
    """
    사고 대응 에이전트
    
    자동화된 보안 사고 대응 및 플레이북 실행
    """
    
    def __init__(
        self,
        name: str = "IncidentResponder",
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
        
        self._incidents: Dict[str, Incident] = {}
        self._playbooks: Dict[str, List[ResponseAction]] = {}
        self._response_handlers: Dict[str, Callable] = {}
        
        # 기본 플레이북 등록
        self._init_default_playbooks()
        
        self._metadata["agent_type"] = "incident_responder"
        self._metadata["capabilities"] = [
            "incident_management",
            "automated_response",
            "playbook_execution",
            "containment",
            "eradication"
        ]
    
    def _init_default_playbooks(self) -> None:
        """기본 플레이북 초기화"""
        
        # SQL 인젝션 대응 플레이북
        self._playbooks["sql_injection"] = [
            ResponseAction(
                action_id="block_ip",
                name="Block Source IP",
                description="일시적으로 소스 IP 차단",
                handler=self._block_source_ip,
                auto_execute=True,
                requires_approval=False
            ),
            ResponseAction(
                action_id="alert_admin",
                name="Alert Security Admin",
                description="보안 관리자에게 알림",
                handler=self._alert_admin,
                auto_execute=True,
                requires_approval=False
            ),
            ResponseAction(
                action_id="enable_enhanced_logging",
                name="Enable Enhanced Logging",
                description="상세 로깅 활성화",
                handler=self._enable_enhanced_logging,
                auto_execute=True,
                requires_approval=False
            )
        ]
        
        # XSS 대응 플레이북
        self._playbooks["xss"] = [
            ResponseAction(
                action_id="sanitize_input",
                name="Sanitize Input",
                description="입력값 살균",
                handler=self._sanitize_input,
                auto_execute=True,
                requires_approval=False
            ),
            ResponseAction(
                action_id="alert_admin",
                name="Alert Security Admin",
                description="보안 관리자에게 알림",
                handler=self._alert_admin,
                auto_execute=True,
                requires_approval=False
            )
        ]
        
        # DDoS 대응 플레이북
        self._playbooks["ddos"] = [
            ResponseAction(
                action_id="rate_limit",
                name="Apply Rate Limiting",
                description="속도 제한 적용",
                handler=self._apply_rate_limit,
                auto_execute=True,
                requires_approval=False
            ),
            ResponseAction(
                action_id="enable_ddos_protection",
                name="Enable DDoS Protection",
                description="DDoS 방어 모드 활성화",
                handler=self._enable_ddos_protection,
                auto_execute=False,
                requires_approval=True
            )
        ]
    
    def create_incident(
        self,
        title: str,
        description: str,
        severity: IncidentSeverity,
        related_events: Optional[List[str]] = None,
        affected_systems: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Incident:
        """사고 생성"""
        import uuid
        
        incident = Incident(
            incident_id=f"INC-{uuid.uuid4().hex[:8].upper()}",
            created_at=datetime.utcnow(),
            title=title,
            description=description,
            severity=severity,
            related_events=related_events or [],
            affected_systems=affected_systems or [],
            metadata=metadata or {}
        )
        
        self._incidents[incident.incident_id] = incident
        
        # 감사 로그
        self._audit_log(
            event_type=AuditEventType.INCIDENT_CREATED,
            action="create_incident",
            description=f"Created incident: {incident.incident_id}",
            success=True,
            metadata={"incident_id": incident.incident_id, "severity": severity.value}
        )
        
        # 이벤트 발생
        self._emit_event(
            event_type=SecurityEventType.INCIDENT_CREATED,
            description=f"Incident created: {title}",
            severity=severity.value,
            metadata={"incident_id": incident.incident_id}
        )
        
        return incident
    
    def update_incident_status(
        self,
        incident_id: str,
        status: IncidentStatus,
        notes: str = ""
    ) -> bool:
        """사고 상태 업데이트"""
        incident = self._incidents.get(incident_id)
        if not incident:
            return False
        
        incident.status = status
        
        if status == IncidentStatus.RESOLVED:
            incident.resolved_at = datetime.utcnow()
            incident.resolution_notes = notes
        
        self._audit_log(
            event_type=AuditEventType.CONFIG_CHANGE,
            action="update_incident",
            description=f"Updated incident {incident_id} status to {status.value}",
            success=True
        )
        
        return True
    
    def execute_playbook(
        self,
        incident_id: str,
        playbook_name: str,
        auto_only: bool = False
    ) -> Dict[str, Any]:
        """플레이북 실행"""
        incident = self._incidents.get(incident_id)
        if not incident:
            return {"success": False, "error": "Incident not found"}
        
        playbook = self._playbooks.get(playbook_name)
        if not playbook:
            return {"success": False, "error": f"Playbook '{playbook_name}' not found"}
        
        results = []
        
        for action in playbook:
            # auto_only 모드에서는 자동 실행 작업만
            if auto_only and not action.auto_execute:
                continue
            
            # 승인 필요 작업은 컨텍스트 확인
            if action.requires_approval:
                if not self.context.has_role("security_admin"):
                    results.append({
                        "action": action.name,
                        "status": "skipped",
                        "reason": "Requires approval"
                    })
                    continue
            
            # 작업 실행
            try:
                success = action.handler(incident)
                action.executed = True
                action.execution_result = "success" if success else "failed"
                
                results.append({
                    "action": action.name,
                    "status": "executed",
                    "result": "success" if success else "failed"
                })
                
            except Exception as e:
                action.executed = True
                action.execution_result = f"error: {str(e)}"
                
                results.append({
                    "action": action.name,
                    "status": "error",
                    "error": str(e)
                })
        
        return {
            "success": True,
            "incident_id": incident_id,
            "playbook": playbook_name,
            "results": results
        }
    
    # 대응 작업 핸들러들
    def _block_source_ip(self, incident: Incident) -> bool:
        """소스 IP 차단 (실제 구현은 외부 시스템 연동 필요)"""
        source_ip = incident.metadata.get("source_ip")
        if source_ip:
            # 실제 구현에서는 방화벽이나 WAF 에 차단 요청
            self.logger.info(f"Blocking IP: {source_ip}")
            return True
        return False
    
    def _alert_admin(self, incident: Incident) -> bool:
        """관리자 알림"""
        # 실제 구현에서는 이메일, Slack, PagerDuty 등으로 알림
        self.logger.warning(f"ALERT: Incident {incident.incident_id} - {incident.title}")
        return True
    
    def _enable_enhanced_logging(self, incident: Incident) -> bool:
        """상세 로깅 활성화"""
        self.context.log_level = "DEBUG"
        self.logger.info("Enhanced logging enabled")
        return True
    
    def _sanitize_input(self, incident: Incident) -> bool:
        """입력값 살균"""
        # 실제 구현에서는 입력 필터링 강화
        self.logger.info("Input sanitization enhanced")
        return True
    
    def _apply_rate_limit(self, incident: Incident) -> bool:
        """속도 제한 적용"""
        self.logger.info("Rate limiting applied")
        return True
    
    def _enable_ddos_protection(self, incident: Incident) -> bool:
        """DDoS 방어 모드 활성화"""
        self.logger.info("DDoS protection enabled")
        return True
    
    def get_incident(self, incident_id: str) -> Optional[Incident]:
        """사고 조회"""
        return self._incidents.get(incident_id)
    
    def get_incidents(
        self,
        status: Optional[IncidentStatus] = None,
        severity: Optional[IncidentSeverity] = None,
        limit: int = 100
    ) -> List[Incident]:
        """사고 목록 조회"""
        results = []
        
        for incident in reversed(list(self._incidents.values())):
            if status and incident.status != status:
                continue
            if severity and incident.severity != severity:
                continue
            
            results.append(incident)
            
            if len(results) >= limit:
                break
        
        return results
    
    def get_statistics(self) -> Dict[str, Any]:
        """사고 대응 통계"""
        stats = {
            "total_incidents": len(self._incidents),
            "by_status": {},
            "by_severity": {},
            "open_incidents": 0,
            "resolved_incidents": 0
        }
        
        for incident in self._incidents.values():
            # 상태별
            s = incident.status.value
            stats["by_status"][s] = stats["by_status"].get(s, 0) + 1
            
            # 심각도별
            sev = incident.severity.value
            stats["by_severity"][sev] = stats["by_severity"].get(sev, 0) + 1
            
            if incident.status in [IncidentStatus.NEW, IncidentStatus.INVESTIGATING]:
                stats["open_incidents"] += 1
            elif incident.status in [IncidentStatus.RESOLVED, IncidentStatus.CLOSED]:
                stats["resolved_incidents"] += 1
        
        return stats
    
    def execute(self, action: str, **kwargs) -> Dict[str, Any]:
        """
        작업 실행
        
        Supported actions:
        - create_incident: 사고 생성
        - update_status: 상태 업데이트
        - execute_playbook: 플레이북 실행
        - get_incident: 사고 조회
        - get_incidents: 사고 목록 조회
        - get_statistics: 통계 조회
        """
        if action == "create_incident":
            incident = self.create_incident(
                title=kwargs.get("title", "Untitled"),
                description=kwargs.get("description", ""),
                severity=IncidentSeverity(kwargs.get("severity", "medium")),
                related_events=kwargs.get("related_events"),
                affected_systems=kwargs.get("affected_systems"),
                metadata=kwargs.get("metadata")
            )
            return {
                "status": "success",
                "action": action,
                "incident_id": incident.incident_id
            }
        
        elif action == "update_status":
            success = self.update_incident_status(
                incident_id=kwargs.get("incident_id"),
                status=IncidentStatus(kwargs.get("status", "new")),
                notes=kwargs.get("notes", "")
            )
            return {
                "status": "success" if success else "error",
                "action": action
            }
        
        elif action == "execute_playbook":
            result = self.execute_playbook(
                incident_id=kwargs.get("incident_id"),
                playbook_name=kwargs.get("playbook", "sql_injection"),
                auto_only=kwargs.get("auto_only", False)
            )
            return result
        
        elif action == "get_incident":
            incident = self.get_incident(kwargs.get("incident_id"))
            if incident:
                return {
                    "status": "success",
                    "action": action,
                    "incident": incident.__dict__
                }
            return {"status": "error", "message": "Incident not found"}
        
        elif action == "get_incidents":
            incidents = self.get_incidents(
                status=IncidentStatus(kwargs["status"]) if kwargs.get("status") else None,
                severity=IncidentSeverity(kwargs["severity"]) if kwargs.get("severity") else None,
                limit=kwargs.get("limit", 100)
            )
            return {
                "status": "success",
                "action": action,
                "count": len(incidents),
                "incidents": [i.__dict__ for i in incidents]
            }
        
        elif action == "get_statistics":
            return {
                "status": "success",
                "action": action,
                "statistics": self.get_statistics()
            }
        
        else:
            return {"status": "error", "action": action, "message": f"Unknown action: {action}"}
