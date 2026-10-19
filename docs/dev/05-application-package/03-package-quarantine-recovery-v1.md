# Package Quarantine Recovery v1

## 보안 원칙
격리 상태를 일반 `verify()` 호출만으로 해제할 수 없다. 복구에는 신뢰된 인증·승인 시스템이 발급한 불투명 자격 증명을 담은 `RecoveryApproval` 객체가 필요하며, `recover_quarantined(name, approval, reason)`에서 검증한다.

## 복구 계약
- 대상 패키지 상태가 `QUARANTINED`여야 한다.
- 승인자 ID, 불투명 자격 증명, `reason`은 공백이 아닌 값이어야 한다.
- 주입된 `RecoveryApprovalVerifier`가 자격 증명과 패키지·사유 범위를 검증해야 한다. 검증기 누락, 거부 또는 예외는 모두 거부한다.
- 자격 증명 원문은 감사 로그에 기록하지 않는다.
- 복구 시 TrustVerifier 및 RuntimeCompatibility를 다시 실행한다.
- 검증 실패 시 패키지는 계속 `QUARANTINED` 상태이며, 감사 로그에 실패 사유를 기록한다.
- 검증 성공 시 상태는 `VERIFIED`로만 전환한다. Agent/Tool 실행 권한은 자동 복구되지 않는다.
- 실행 재개에는 일반 lifecycle인 `stage → install → activate`를 별도로 완료해야 한다.
- 성공 감사 이벤트는 승인자, 사유, 이벤트명 및 최종 상태를 기록한다.

## 위협 완화
- 일반 verify 우회로 격리 해제 방지
- 신뢰 검증 또는 런타임 호환성 실패 시 fail-closed
- 승인 필드 없는 복구 방지
- 승인자 이름만으로 인증하지 않으며, 자격 증명 검증기 누락/오류 시 fail-closed
- 위조된 자격 증명 거부 및 자격 증명 원문 비기록
- 승인된 복구와 실제 재활성화를 분리해 의도치 않은 즉시 실행 방지

## 정책 통합 경계
`RecoveryApprovalVerifier`는 실제 운영의 신뢰할 수 있는 인증·승인 시스템에 연결해야 한다. `RecoveryApproval`은 전달용 자료형일 뿐 자체적으로 신원을 증명하지 않는다. 현재 CI 테스트 검증기는 고정 테스트 자격 증명만 검사하므로 운영 환경에 사용하면 안 된다. 실제 IdP/OIDC 또는 서명된 단기 승인 토큰 검증과 영속 감사 저장소 연결은 별도 운영 통합 단계다.
