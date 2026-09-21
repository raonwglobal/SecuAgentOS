# Package Manager + Application Sandbox v1

## 목적
SecuAgentOS에서 Security Application과 Agent를 OS 위에 설치·검증·활성화하기 위한 최소 package lifecycle과 sandbox 계약을 정의한다.

## 역할 분리
- Package Manager: 검색, 설치, 검증, 활성화, 비활성화, 업데이트, rollback을 관리한다.
- Trust Verifier: package signature/publisher trust를 검증한다.
- Sandbox: application의 capability, permission, resource, network 경계를 적용한다.
- Agent Runtime: 검증·활성화된 agent의 lifecycle과 task execution을 관리한다.
- Tool Gateway: 외부 보안 시스템 접근의 최종 실행 경계다.

## Package Lifecycle
DISCOVERED → VERIFIED → STAGED → INSTALLED → ACTIVATED → RUNNING

실패/비활성 상태: REJECTED, DISABLED, QUARANTINED, FAILED, ROLLBACK

UNVERIFIED package는 ACTIVATED 또는 RUNNING이 될 수 없다.

## Manifest v1
필수: name, version, type, runtime.min, capabilities, permissions
선택: tools, resources, network, publisher, signature

## Trust Boundary
Package → Manifest Parse → Signature/Publisher Trust → Runtime Compatibility → Capability/Permission Review → Resource/Network Policy → Sandbox → Install → Activate

v1에서는 실제 cryptographic signature backend 대신 TrustVerifier protocol을 추상화하고 deterministic test verifier를 사용한다. 운영 환경에서는 서명 검증과 publisher trust store를 구현한다.

## Sandbox
v1은 in-process policy contract다. 실제 process/container/VM isolation은 후속 구현한다.

## SecuAgent 설치 모델
향후 CLI: sos search secuagent / sos install secuagent / sos verify secuagent / sos enable secuagent / sos disable secuagent / sos update secuagent / sos rollback secuagent

pip는 SDK/development packaging에 사용할 수 있으나 OS application lifecycle의 기준은 Package Manager다.

## 보안 불변식
1. unverified package는 activation 불가
2. runtime incompatibility package는 activation 불가
3. declared capability만 sandbox context에 노출
4. package failure가 OS control plane을 변경하지 못한다
5. rollback은 known-good package state로 복귀한다
6. package lifecycle 변경은 audit 대상이다

## v1 범위
파일 기반 local package registry와 deterministic trust verifier를 사용한다. 실제 remote repository, signed bundle, container/VM sandbox는 후속 단계에서 추가한다.
