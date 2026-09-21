# VM Build Reliability v1

## 목적
SecuAgentOS x86-64 VM Bootstrap이 외부 Alpine artifact 변경에 의해 반복적으로 깨지지 않도록 build 경계를 정의한다.

## 현재 장애 원인
GitHub Actions run 28에서 dependency 설치와 static smoke는 성공했지만 `Build UEFI VM artifact` 단계가 Alpine asset 다운로드에서 HTTP 404로 종료되었다. 당시 build script는 versioned `netboot-3.24.2` 디렉터리의 개별 `vmlinuz-lts`와 `initramfs-lts`를 직접 요청했다.

## 변경 원칙
1. VM bootstrap의 기본 endpoint는 Alpine의 유지되는 `latest-stable/releases/x86_64/netboot`로 사용한다.
2. `ALPINE_NETBOOT_BASE` 환경변수로 테스트/운영 환경에서 endpoint를 명시적으로 고정할 수 있다.
3. 다운로드 전에 HTTP HEAD preflight를 수행한다.
4. curl retry를 적용한다.
5. 다운로드된 kernel/initramfs가 비어 있으면 즉시 실패한다.
6. 생성된 VM ISO의 SHA256을 계속 생성한다.
7. CI는 build와 boot 로그를 artifact로 보존한다.

## 재현성 정책
현재 v1은 부트스트랩 안정성을 위해 stable endpoint를 기본값으로 사용한다. 향후 release-grade image pipeline에서는 다음 순서로 강화한다.

`pinned Alpine release → published checksum verification → optional signature verification → reproducible image build`

따라서 현재 `ALPINE_VERSION=3.24.2`는 compatibility target/문서값이며, cryptographic pinning을 의미하지 않는다.

## CI 진단
Workflow는 다음을 별도 단계로 검증한다.

`checkout → dependencies → static smoke → VM build → QEMU boot → state/health assertions`

Build 단계의 stdout/stderr는 `vm-build.log`, QEMU serial output은 `vm-boot.log`, 생성 ISO checksum은 diagnostics artifact에 보존한다.

## 보안 고려
외부 artifact를 신뢰한 상태로 OS image에 포함시키지 않는다. release-grade pipeline에서는 checksum 이상의 publisher/signature verification을 추가하고, artifact source 변경은 ADR 및 release manifest에 기록한다.
