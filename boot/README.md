# SecuAgentOS Boot

This directory defines the SecuAgentOS boot/image boundary.

The initial prototype uses a Linux-based foundation. Boot artifacts must eventually provide:
- x86-64 UEFI boot
- serial console
- persistent system identity
- explicit SecuAgentOS startup state
- recovery entry point

Application packages such as SecuAgent are not embedded in the base boot artifact.
