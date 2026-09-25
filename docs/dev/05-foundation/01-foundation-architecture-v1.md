# SecuAgentOS Foundation Architecture v1

## 목적

SecuAgentOS를 단순 패키지가 아닌 보안 특화 Agent OS의 기반으로 정의한다.

## 계층

```text
Hardware / VM
  -> Ubuntu 24.04 + Linux + systemd
  -> SecuAgentOS Foundation
     -> Security Control Plane
     -> Event Bus
     -> Health Manager
     -> Audit Manager
     -> Service Manager
     -> Agent Runtime
     -> Package Manager
  -> Security application packages
```

## Foundation 책임

- OS identity 및 version contract
- 표준 디렉터리와 runtime state
- lifecycle 및 readiness 관리
- 내부 event contract
- health/readiness contract
- audit/event 기록 기반 제공
- service/package 실행 경계 제공

## 패키지 원칙

`SecuAgent`는 OS core가 아니다. 향후 `SecuAgent`는 Foundation이 제공하는 package contract를 사용하는 독립 보안 애플리케이션/룰 패키지로 등록한다.

외부 솔루션도 동일한 contract를 통해 수용한다.

## 구현 순서

1. Foundation identity/config/state
2. Event Bus
3. Health Manager
4. Audit Manager
5. Service Manager
6. Agent Runtime
7. Package Manager
8. SecuAgent package adapter
