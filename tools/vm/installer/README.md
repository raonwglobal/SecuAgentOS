# SecuAgentOS Installer v2

Installer contract for x86-64 Ubuntu Server installation media.

The autoinstall configuration establishes the SecuAgentOS filesystem boundary and base packages. Credentials must be replaced by the deployment pipeline; no default production password is permitted.

Next integration point: customize Ubuntu Server ISO and inject `autoinstall/user-data`, `meta-data`, and SecuAgentOS Foundation packages into the boot media.
