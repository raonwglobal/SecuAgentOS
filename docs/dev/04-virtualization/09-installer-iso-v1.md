# SecuAgentOS Installer ISO v1

- Architecture: x86-64
- Base installer: Ubuntu Server 24.04
- Artifact: `secuagentos-x86_64-installer.iso`
- Target: physical x86-64 hardware, Proxmox VM, QEMU/Hypervisor VM

Build:

```sh
tools/vm/build-installer-iso.sh
```

The current v1 produces bootable Ubuntu Server installation media. The next installer phase will add Ubuntu autoinstall configuration, SecuAgentOS Foundation installation, systemd services, and first-boot readiness validation.
