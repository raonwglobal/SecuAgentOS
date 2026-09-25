# VM Disk Layout v1

## 목적

Ubuntu 24.04 cloud image를 SecuAgentOS x86-64 VM 기준 이미지로 사용한다. Host에서 GPT를 직접 재작성하지 않고 Ubuntu guest의 growpart/cloud-init 경로를 사용하여 확장 가능한 디스크를 유지한다.

## 기준

- Base image: Ubuntu Server 24.04 cloud image
- Architecture: x86-64 / amd64
- CI disk size: 8 GiB
- Image integrity: SHA256 검증
- Partition/filesystem expansion: guest-side growpart/cloud-init

## 원칙

1. Host build는 image artifact와 seed ISO를 생성한다.
2. Host build는 guest partition table을 직접 수정하지 않는다.
3. Guest가 첫 부팅 시 자신의 GPT/partition/filesystem 확장을 담당한다.
4. SecuAgentOS lifecycle은 cloud-init이 아니라 systemd가 담당한다.
5. 이후 production image에서는 persistent state와 OS/application 경계를 별도 partition/layout contract로 확장한다.

## 다음 단계

VM Bootstrap v1 PASS 후 production-oriented disk layout을 정의한다.
