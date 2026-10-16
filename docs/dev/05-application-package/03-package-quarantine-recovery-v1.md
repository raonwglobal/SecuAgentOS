# Package Quarantine Recovery v1

## 보안 원칙
격리 상태를 일반 `verify()` 호출만으로 해제할 수 없다. 격리 해제는 승인자와 사유가 명시된 `recover_quarantined(name, approved_by, reason)` 호출로만 시작한다.

## 복구 계약
- 대상 패키지 상태가 `QUARANTINED`여야 한다.
- `approved_by`와 `reason`은 공백이 아닌 값이어야 한다.
- 복구 시 TrustVerifier 및 RuntimeCompatibility를 다시 실행한다.
- 검증 실패 시 패키지는 계속 `QUARANTINED` 상태이며, 감사 로그에 실패 사유를 기록한다.
- 검증 성공 시 상태는 `VERIFIED`로만 전환한다. Agent/Tool 실행 권한은 자동 복구되지 않는다.
- 실행 재개에는 일반 lifecycle인 `stage → install → activate`를 별도로 완료해야 한다.
- 성공 감사 이벤트는 승인자, 사유, 이벤트명 및 최종 상태를 기록한다.

## 위협 완화
- 일반 verify 우회로 격리 해제 방지
- 신뢰 검증 또는 런타임 호환성 실패 시 fail-closed
- 승인 필드 없는 복구 방지
- 승인된 복구와 실제 재활성화를 분리해 의도치 않은 즉시 실행 방지

## 제한
v1은 승인자 문자열을 감사 증적으로 기록한다. 승인자의 신원 인증/권한 검증과 영속 감사 저장소는 아직 별도 통합 대상이며, 호출자 문자열만으로 실제 인증이 보장되지는 않는다.
