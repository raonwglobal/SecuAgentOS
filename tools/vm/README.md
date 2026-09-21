# VM Development Tools

This directory will contain reproducible developer tooling for the x86-64 QEMU/KVM target.

Required lifecycle:

build → create → boot → health-check → test → snapshot → rollback → logs

Host-specific virtualization details must remain here or below the VM implementation boundary and must not leak into the SecuAgentOS runtime APIs.
