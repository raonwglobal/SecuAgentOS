# SecuAgentOS

**x86-64 하드웨어와 가상 머신을 위한 보안 특화 Agent 운영체제 기반**

SecuAgentOS는 보안 에이전트와 외부 보안 솔루션을 설치·격리·인가·감사·운영하기 위한 OS 및 런타임 플랫폼입니다. SecuAgentOS 자체가 단일 보안 애플리케이션이 되는 것이 아니라, 별도 패키지로 제공되는 SecuAgent 및 다른 보안 솔루션을 실행하는 기반을 목표로 합니다.

## 현재 개발 상태

- x86-64 및 Ubuntu Server 24.04 LTS 기반 VM 프로토타입
- Security Control Plane, Agent Runtime, Package Manager 및 Tool Gateway의 핵심 제어 계약
- 패키지 권한 검증, 격리 상태 및 복구 승인에 대한 Python 단위 테스트
- GitHub Actions에서 Ubuntu VM 빌드, QEMU 부팅 및 readiness marker 검증
- 설치 ISO, Proxmox 배포, 운영 인증·감사 저장소, 패키지 서명, 실제 SecuAgent 통합은 추가 검증/구현 필요

현재 프로젝트는 개발 프로토타입이며 운영 환경에 바로 사용할 수 있는 완성된 보안 OS가 아닙니다. 최신 검증 결과는 [GitHub Actions](https://github.com/raonwglobal/SecuAgentOS/actions)를 확인하세요.

## 아키텍처

```text
x86-64 hardware / VM
        |
Ubuntu Linux foundation (kernel, systemd, filesystem, networking)
        |
SecuAgentOS platform
  - Security Control Plane
  - Identity / Policy / Capability / Risk / Audit
  - Agent Runtime
  - Package Manager and sandbox boundary
  - Tool Gateway
        |
Installable security packages
  - SecuAgent (future integration)
  - EDR / SIEM / IAM / Firewall integrations
```

Ubuntu는 기반 OS이며 보안 정책의 최종 권한 주체는 SecuAgentOS를 목표로 합니다. 외부 보안 도구는 Tool Gateway의 정책·권한·감사 경계를 통해 호출되어야 합니다.

## VM 개발

Ubuntu x86-64 VM 빌드와 실행:

```sh
tools/vm/build.sh
tools/vm/run.sh
tools/vm/health-check.sh
```

CI는 VM 이미지 생성과 QEMU 부팅을 검증합니다. 이 결과만으로 Installer ISO의 무인 설치, Proxmox 실환경 부팅 또는 물리 하드웨어 호환성이 검증되었다고 볼 수 없습니다.

## 개발 문서

설계·구현 계획·검증 현황은 [`docs/dev/`](docs/dev/) 아래에 주제별로 기록합니다. 최신 통합 갭과 순차 실행 계획은 [Repository Integration Audit](docs/dev/08-testing-validation/04-repository-integration-audit-2026-10-20.md)을 참고하세요.

## SecuAgent와의 관계

- `SecuAgentOS`: OS/플랫폼 및 런타임
- `raonwglobal/SecuAgent`: 향후 SecuAgentOS에 설치할 별도 보안 애플리케이션/규칙 패키지 대상

개발 보조 도구는 OS 런타임 구성요소가 아니며 SecuAgentOS 제품 코드와 분리합니다.

## 로드맵

1. Ubuntu VM 부팅 및 CI 안정화
2. cloud-init 프로토타입을 실제 SecuAgentOS systemd 서비스로 대체
3. OS 수준 애플리케이션 격리 강화
4. 패키지 서명 및 발행자 신뢰 검증
5. `sos` 패키지 관리 CLI 구현
6. SecuAgent 설치 패키지 통합
7. 실제 SIEM/EDR/IAM/방화벽 어댑터
8. 공유 에이전트 컨텍스트 및 메모리
9. 자율 관찰·진단·조치·검증·롤백 루프
10. 물리 x86-64 하드웨어 검증
11. 재현 가능하고 서명된 OS/패키지 릴리스

## 보안 경계

현재 코드와 CI는 일부 보안 제어 계약을 검증하는 프로토타입입니다. 실제 IdP 연동, 변조 방지 감사 저장, 운영용 패키지 서명, OS 수준 격리, 보안 릴리스 검증은 별도 완료 조건입니다.

## 라이선스

저장소에 포함된 `LICENSE` 및 각 구성요소의 개별 라이선스를 참고하세요.
