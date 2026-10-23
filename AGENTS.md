# SecuAgentOS Engineering Guidance

- Treat `README.md` and `docs/dev/` as the project overview and authoritative design/progress records.
- SecuAgentOS is the OS/platform; `raonwglobal/SecuAgent` is a separate future installable application/package target.
- Keep development-support tools and chat-specific skills outside the SecuAgentOS product repository and runtime.
- Before changing security-sensitive code, inspect the relevant design document, tests, and latest GitHub Actions run.
- Distinguish unit-test success, VM boot success, installer success, Proxmox validation, and physical hardware validation. Never claim a later stage from an earlier stage's result.
- Fail closed on missing/invalid security authority. Do not log credentials or secrets.
- Record major decisions, implementation status, test evidence, known gaps, and next steps under `docs/dev/`.
