# SecuAgent - Security-Focused AgentOS Library

보안 솔루션에 특화된 AI 에이전트 운영체제 (AgentOS) 를 구축하기 위한 Python 라이브러리입니다.

## 주요 기능

### 🔐 보안 코어
- **SecurityContext**: 보안 컨텍스트 관리, 권한 수준 제어
- **SecureAgent**: 보안 기능이 내장된 기본 에이전트 클래스
- **SecurityEvent**: 보안 이벤트 시스템 및 큐 관리

### 🛡️ 보안 서비스
- **EncryptionService**: AES-256-GCM, RSA-4096 암호화 및 키 관리
- **AuthenticationManager**: 다중 인증 (MFA), JWT 세션, 계정 잠금
- **AuthorizationManager**: RBAC(역할 기반 접근 제어), 권한 검증
- **InputValidator**: SQL 인젝션, XSS, 명령어 인젝션, 경로 순회 방지
- **AuditLogger**: 규정 준수 (GDPR, HIPAA, PCI-DSS) 감사 로그

### 🤖 전문 에이전트
- **ThreatDetectorAgent**: 위협 탐지 및 패턴 분석
- **IncidentResponderAgent**: 사고 대응 자동화

## 설치

```bash
# 개발 모드로 설치
pip install -e .[dev]

# 일반 설치
pip install secuagent
```

## 빠른 시작

```python
from secuagent import SecurityContext, SecureAgent, SecurityLevel

# 보안 컨텍스트 생성
ctx = SecurityContext(
    security_level=SecurityLevel.HIGH,
    user_id="admin",
    roles=["security_admin"]
)

# 보안 에이전트 생성
agent = SecureAgent(name="SecurityBot", context=ctx)

# 입력 검증
from secuagent.security import InputValidator
validator = InputValidator()
if validator.validate_input(user_input):
    # 안전한 처리
    pass
```

## 프로젝트 구조

```
secuagent/
├── secuagent/
│   ├── core/           # 핵심 모듈 (context, agent, events)
│   ├── security/       # 보안 서비스 (crypto, auth, validator, audit)
│   ├── agents/         # 전문 에이전트 (detector, responder)
│   └── utils/          # 유틸리티 (logger)
├── examples/           # 예제 코드
├── tests/              # 테스트
└── pyproject.toml      # 패키지 설정
```

## 라이선스

MIT License
