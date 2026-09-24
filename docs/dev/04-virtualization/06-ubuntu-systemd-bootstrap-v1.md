# Ubuntu systemd Bootstrap v1

## 목적

SecuAgentOS의 Ubuntu x86-64 VM은 cloud-init을 운영체제 lifecycle로 사용하지 않는다. cloud-init은 테스트 이미지에 SecuAgentOS Foundation service를 provisioning하고 enable하는 초기 설정 계층으로만 사용한다. 실제 SecuAgentOS lifecycle은 systemd가 소유한다.

## 문제 분석

기존 Workflow는 180초 동안 VM serial output을 기다린 뒤 `SECUAGENTOS_STATE=INIT_STARTED`를 검사했다. Ubuntu는 정상적으로 `secuagentos login:`까지 부팅했지만 cloud-init의 config 단계가 늦게 진행되어 bootstrap service가 marker를 출력하기 전에 timeout될 수 있었다.

또한 service unit이 `After=cloud-init.target`에 묶여 있어 SecuAgentOS boot lifecycle과 provisioning lifecycle의 경계가 불명확했다.

## 개선 구조

```text
Ubuntu Kernel
  -> systemd
  -> multi-user.target
  -> SecuAgentOS Foundation service
  -> Security / Services / Runtime
  -> SYSTEM_READY
```

cloud-init은 다음 작업만 담당한다.

1. bootstrap executable 설치
2. systemd unit 설치
3. `systemctl daemon-reload`
4. unit enable/start

bootstrap service 자체는 `network-pre.target` 이후 실행되며 cloud-init service ordering에 종속되지 않는다.

## CI 검증

VM boot timeout은 300초로 확대했다. 이것은 근본 해결책이 아니라 Ubuntu cloud image 최초 부팅 및 cloud-init provisioning에 충분한 진단 창을 확보하기 위한 것이다.

성공 조건은 다음 순서의 serial marker다.

`INIT_STARTED -> FOUNDATION_READY -> SECURITY_READY -> SERVICES_READY -> RUNTIME_READY -> SYSTEM_READY -> HEALTH=READY`

## 로그 경로

bootstrap service는 `/run/secuagentos/boot.log`에도 기록하고 `/dev/ttyS0`에도 기록한다. 따라서 CI serial log와 guest runtime state를 동시에 확인할 수 있다.

## 다음 단계

이 Bootstrap v1이 PASS하면 테스트용 marker script를 실제 SecuAgentOS Foundation 구현으로 교체한다. 이후 Service Manager, Security Control Plane, Event Bus, Agent Runtime, Package Manager 순으로 구현한다.
