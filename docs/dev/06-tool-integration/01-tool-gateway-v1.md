# Tool Gateway v1

## 목적
Agent가 외부 보안 시스템(SIEM, EDR, Firewall, IAM 등)에 직접 접근하지 못하도록 Tool Gateway를 유일한 실행 경계로 둔다.

## 실행 경계
```
Agent → ToolRequest → SecurityController → Capability / Policy / Risk / Approval → ToolGateway → ToolAdapter → External System → Verification → Audit
```

## 원칙
1. Agent는 raw external client를 직접 호출하지 않는다.
2. 모든 ToolRequest는 SecurityController를 통과한다.
3. Package Manifest에 선언되지 않은 capability는 DENY한다.
4. Package Manifest의 tools allowlist에 없는 tool은 DENY한다.
5. 패키지 비활성화, 격리 또는 실행 불가 상태는 즉시 권한 회수로 처리한다.
6. 정책 거부는 adapter 호출 전에 종료한다.
7. HIGH/CRITICAL은 승인 없이는 실행하지 않는다.
8. 알 수 없는 tool은 DENY한다.
9. adapter 오류와 verification 실패는 audit에 기록한다.
10. 권한 제공자 누락/오류는 fail-closed로 처리한다.
11. ToolAdapter는 외부 제품별 구현을 격리한다.

## 요청/응답
- ToolRequest: request_id, principal, tool, action, resource, capabilities, parameters, context, approved
- ToolResponse: request_id, success, result, verification, error

비밀정보는 audit에 직접 기록하지 않는다.

## Adapter 계약
Adapter는 `execute(request)`를 제공한다. Gateway는 등록된 tool 이름으로 adapter를 선택하고 보안 승인 이후에만 호출한다. 실행 전 principal의 활성 상태, Package Manifest에 선언된 tool, authoritative capability, 정책, risk 및 approval을 모두 확인한다. 요청자가 전달한 capability 목록은 권한 근거로 사용하지 않는다. Verification은 선택적 verifier 계약으로 수행한다.

## 실패/타임아웃
- authorization 실패: adapter 미호출
- unknown tool: DENY
- adapter exception/timeout: 실패 응답 + audit
- verification failure: 실패 응답 + audit
- quarantined/비활성 principal 또는 패키지: adapter 미호출 (Package Manager quarantine은 실행 권한을 즉시 회수하고 audit에 사유를 기록)
- 재시도는 idempotency와 risk policy가 정의된 경우에만 허용한다.

## 통합 보안 검증
- Package Manager에서 활성화된 Manifest의 tools allowlist가 Gateway 실행 권한의 기준이다.
- tool authority 제공자 조회 예외/누락은 fail-closed이며 adapter를 호출하지 않는다.
- HIGH/CRITICAL 작업은 패키지와 capability가 허용하더라도 명시적 approval 없이는 실행하지 않는다.
- 승인 전/후 실행 결과와 adapter 호출 횟수를 통합 테스트로 검증한다.

## v1 범위
로컬 in-process adapter와 deterministic tests를 사용한다. 실제 SIEM/EDR/Firewall/IAM connector는 이후 package/integration 계층에서 추가한다.

## 다음 단계
Package Manager/Application Sandbox와 Tool Adapter 패키징을 연결한다.
