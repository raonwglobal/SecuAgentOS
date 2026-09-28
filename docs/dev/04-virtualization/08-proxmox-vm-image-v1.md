# Proxmox VM Image v1

## 목적

SecuAgentOS x86-64 Ubuntu VM 이미지를 Proxmox VE에서 테스트할 수 있도록 qcow2 export 경로를 제공한다.

## Image

- Base: Ubuntu 24.04 SecuAgentOS VM image
- Format: qcow2
- Firmware: OVMF/UEFI 권장
- Machine: q35 권장
- CPU: host, 2 cores 권장
- RAM: 4 GiB 권장
- Network: VirtIO

## Build

```sh
tools/vm/build.sh
tools/vm/build-proxmox.sh
```

결과:

```text
.build/vm/proxmox/secuagentos-x86_64-ubuntu24.04.qcow2
```

## Proxmox import

```sh
qm create 9000 --name secuagentos --memory 4096 --cores 2 --machine q35 --bios ovmf --net0 virtio,bridge=vmbr0
qm importdisk 9000 secuagentos-x86_64-ubuntu24.04.qcow2 local-lvm
qm set 9000 --scsihw virtio-scsi-single --scsi0 local-lvm:vm-9000-disk-0
qm set 9000 --boot order=scsi0
qm start 9000
```

EFI disk가 필요한 환경에서는 Proxmox UI 또는 `qm set`으로 EFI disk를 추가한다.

## 검증

VM 부팅 후 다음을 확인한다.

```sh
systemctl status secuagentos-bootstrap.service
systemctl status secuagentos-service-manager.service
cat /run/secuagentos/state
cat /run/secuagentos/health
```

최종 기준:

```text
SYSTEM_READY
status=READY
```

> 현재 export는 테스트용 VM 이미지다. 향후 production/hardware 배포 전에는 persistent partition layout과 cloud-init 제거/초기화 정책을 별도로 확정한다.
