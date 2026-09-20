# Package → Agent Runtime → Tool Gateway Integration v1

## 목적

SecuAgentOS의 설치 가능한 Security Application이 실제 실행 경로에 들어갈 때
Package Manager, Agent Runtime, Tool Gateway 사이의 신뢰 경계를 하나의 계약으로 연결한다.

## 권위 있는 capability source

Capability의 최종 출처는 호출자가 제출한 ToolRequest가 아니라 다음 경로다.

`Package Manifest → Package Manager → AgentDescriptor → Agent Runtime → Tool Gateway → Security Controller`

따라서 ToolRequest의 `capabilities`는 v1에서 호환성 입력일 뿐 권위 정보가 아니다.
Tool Gateway에 capability provider가 연결되면 provider가 반환한 capability만 SecurityController에 전달한다.

## 실행 조건

1. Package는 VERIFIED 상태를 거쳐야 한다.
2. Package는 INSTALLED 후 ACTIVATED 되어야 한다.
3. Package Agent는 ACTIVATED package에서만 등록된다.
4. AgentDescriptor.capabilities는 PackageManifest.capabilities와 일치해야 한다.
5. QUARANTINED/STOPPED/FAILED Agent는 Tool Gateway 실행 권한이 없다.
6. Tool Gateway는 Agent Runtime의 executable 상태를 확인한다.
7. Tool Gateway는 Agent Runtime/Package에서 가져온 capability를 SecurityController에 전달한다.
8. HIGH/CRITICAL action은 기존 Security Control Plane 승인 정책을 통과해야 한다.
9. 모든 거부/실행/검증 결과는 audit 대상이다.

## 실행 흐름

`Package Discover → Verify → Stage → Install → Activate
→ Agent Register → Agent Executable
→ Tool Request → Runtime State Check
→ Authoritative Capability Resolution
→ SecurityController → Tool Gateway → Adapter
→ Verification → Audit`

## 보안 목적

이 통합으로 다음 elevation 경로를 차단한다.

- 미활성 package가 Agent를 등록하는 것
- Agent가 manifest에 없는 capability를 선언하는 것
- caller가 ToolRequest capability를 위조하여 권한을 상승시키는 것
- quarantine된 Agent가 외부 보안 시스템을 호출하는 것
- Tool Gateway를 우회하여 adapter를 직접 호출하는 것

## v1 구현 경계

현재는 in-process Agent Runtime, Package Manager, Tool Gateway를 사용한다.
실제 process/container/VM isolation, cryptographic package signature, remote package registry는 후속 단계다.

## 다음 단계

1. SecuAgent sample package manifest 추가
2. package installation CLI의 최소 프로토타입
3. process-level sandbox 경계
4. signed package verification
5. 실제 SIEM/EDR adapter 계약
6. A2A/shared context와 Agent Memory 통합
