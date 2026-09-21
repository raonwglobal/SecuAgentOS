# VM Build Reliability v1

## 목적
SecuAgentOS x86-64 VM Bootstrap의 build failure와 guest boot failure를 분리하고 GitHub Actions에서 실제 부트 단계를 확인한다.

## 장애 기록
- Alpine asset 404: versioned netboot 경로 의존을 제거하고 stable endpoint를 사용.
- GRUB mformat 실패: mtools 의존성을 CI와 build preflight에 명시.
- Guest Boot Validation 실패: QEMU가 시작되어도 SecuAgentOS marker가 보이지 않는 경우가 존재했으며, 원인을 firmware/GRUB/kernel/initramfs/serial 중 하나로 추정하지 않고 로그로 분기해야 한다.

## 현재 실행 계약
tools/vm/run.sh는 split OVMF CODE/VARS를 우선 사용하고 VARS는 매 실행마다 임시 복사본을 만든다. split firmware가 없으면 monolithic OVMF를 사용한다.

QEMU stdout은 -display none -monitor none -serial stdio로 guest serial만 전달한다. 따라서 monitor multiplexing으로 인한 진단 혼선을 제거한다.

## Boot validation
정상 순서:
FOUNDATION_READY -> SECURITY_READY -> SERVICES_READY -> RUNTIME_READY -> SYSTEM_READY -> HEALTH=READY

PID 1은 계속 실행되므로 timeout(124)은 정상 성공 종료 방식이다. 그 외 QEMU 종료는 실패다.

## 진단 분기
| 관찰 | 다음 점검 |
|---|---|
| 출력 없음 | UEFI/ISO boot path/console |
| GRUB만 출력 | kernel/initramfs load |
| kernel 출력만 있음 | initramfs/PID1 |
| marker 일부 | system/init |
| 모든 marker + health | bootstrap 성공 |

## 재현성
ALPINE_VERSION=3.24.2는 현재 compatibility target이며 latest-stable endpoint를 사용한다. release-grade pipeline에서는 pinned release, checksum/signature verification, reproducible build로 강화한다.
