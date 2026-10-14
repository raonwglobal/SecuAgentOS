# Package Quarantine v1

## 목적
패키지 무결성 경보 또는 보안 검토 결과가 발생하면 실행 중인 외부 보안 애플리케이션을 즉시 격리하고 Agent 및 Tool Gateway 권한을 회수한다.

## 계약
- Package Manager는 활성 패키지에 대해 `quarantine(name, reason)`을 제공한다.
- 상태를 `ACTIVATED`에서 `QUARANTINED`로 전환하고 감사 이벤트에 패키지명, 상태, 이벤트, 사유를 기록한다.
- 격리된 패키지는 sandbox context를 제공받지 못한다.
- Agent Runtime의 실행 가능 여부 확인은 패키지 상태를 매 요청마다 확인한다.
- Tool Gateway는 격리된 패키지의 Agent 요청을 adapter 실행 전에 거부한다.
- 활성화되지 않은 패키지는 quarantine 대상으로 허용하지 않는다.

## 검증
- Package Manager 상태 전환 및 감사 이벤트 테스트
- 격리 이후 sandbox context 차단 테스트
- 통합 테스트에서 Agent 실행 가능 여부 및 Tool Adapter 호출 차단 확인

## 범위
v1은 동기식 상태 전환과 in-memory audit 계약을 구현한다. 지속성 있는 격리 기록, 자동 탐지 정책, 복구/재활성화 절차는 후속 단계에서 설계한다.
