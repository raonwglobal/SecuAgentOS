# Initramfs Boot Contract v1

## 1. 목적

SecuAgentOS는 Linux 위에서 동작하는 일반 애플리케이션이 아니라 향후 하드웨어에서 직접 부팅되는 보안 특화 AgentOS를 목표로 한다. 따라서 PID 1(`/init`)은 일반 사용자 공간의 환경을 전제로 하지 않고, 자신이 실행되는 initramfs 환경을 명시적으로 초기화하고 검증해야 한다.

## 2. 현재 장애의 근본 원인

현재 `system/init/secuagentos-init`은 시작 직후 `mkdir`, `date`, `tee`, `cat`, `sleep` 등의 명령을 사용한다. 그러나 initramfs PID 1에서 사용할 `PATH`와 명령어 availability를 명시하지 않았다. 실제 VM 부트에서는 `mkdir: not found`로 PID 1이 종료되고 Linux가 `Attempted to kill init` kernel panic을 발생시켰다.

QEMU/OVMF/GRUB/kernel/ISO 생성 문제가 아니라 SecuAgentOS init bootstrap contract의 결함이다.

## 3. Boot Contract

PID 1은 다음 순서로 동작해야 한다.

1. Bootstrap environment: `PATH`, 기본 환경, umask
2. Required command verification: 최소 명령어 availability 확인
3. Filesystem bootstrap: `/proc`, `/sys`, `/dev`, `/run`
4. Logging bootstrap
5. Security foundation
6. Service manager
7. Agent runtime
8. `SYSTEM_READY` 및 health 상태 기록

## 4. 최소 실행환경

initramfs의 `/init`은 외부 root filesystem이나 systemd 등에 의존하지 않는다. 기본 명령은 BusyBox 또는 동등한 initramfs 도구로 제공되어야 한다.

최소 검증 대상:

- `/bin/sh`
- `mkdir`
- `cat`
- `date`
- `tee`
- `sleep`
- `printf`
- `/proc/cmdline` 접근

## 5. Build-time 검증

`tools/vm/build.sh`는 initramfs 생성 후 다음을 검사해야 한다.

- `/init` 존재 및 executable
- `/bin/sh` 존재
- 필수 명령 또는 BusyBox applet 존재
- initramfs 내부에 필요한 `/proc`, `/sys`, `/dev` bootstrap 경로가 준비될 수 있는지 확인

빌드 성공은 guest boot 성공을 의미하지 않는다. 따라서 build와 guest boot validation은 독립 단계로 유지한다.

## 6. Runtime 검증

VM workflow는 다음 단계 marker를 순서대로 검증한다.

`INIT_STARTED -> FOUNDATION_READY -> SECURITY_READY -> SERVICES_READY -> RUNTIME_READY -> SYSTEM_READY -> HEALTH=READY`

실패 시 가능한 한 `stage`, `reason`, `command`를 serial log에 남긴다.

## 7. 보안/신뢰 경계

향후 release image에서는 Alpine 등의 외부 artifact를 단순 다운로드하지 않고 pinned version, checksum verification, 필요 시 signature verification을 적용한다. 현재 `ALPINE_VERSION`은 compatibility metadata이며 stable endpoint 선택과 cryptographic pinning은 별개의 문제다.

## 8. 다음 구현

1. `secuagentos-init`에 명시적 PATH 및 bootstrap preflight 추가
2. initramfs 필수 command preflight를 `build.sh`에 추가
3. `INIT_STARTED` marker 추가
4. VM workflow에 stage별 실패 진단 추가
5. Workflow PASS 후 VM Bootstrap v1을 동결하고 Service Manager 구현으로 이동
