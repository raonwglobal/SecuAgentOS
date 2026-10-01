# Installer ISO v2 Build

## 목표

Ubuntu Server 24.04 설치 미디어를 기반으로 SecuAgentOS 자동 설치 구조를 준비한다.

## 현재 구현

- Ubuntu Server 24.04 amd64 base ISO 다운로드
- SHA256 기록
- reproducible installer workspace
- autoinstall contract 연결
- Foundation 및 Service Manager 설치 경계 정의

## 다음 검증

실제 ISO 내부에 autoinstall seed를 삽입하고 QEMU에서 unattended installation을 수행한다.

성공 기준:

```text
UEFI boot
  -> Ubuntu autoinstall
  -> reboot
  -> systemd
  -> SecuAgentOS Foundation
  -> Service Manager
  -> SYSTEM_READY
  -> HEALTH=READY
```

## Bootstrap activation fix

Cloud-init may finish after `multi-user.target` has already been reached. The VM provisioning step therefore uses `systemctl enable --now` so SecuAgentOS bootstrap is both enabled for future boots and started immediately on the current boot.
