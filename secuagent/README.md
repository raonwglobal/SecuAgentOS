# SecuAgentOS - Security-Focused Agent Operating System

보안 특화 AI Agent를 안전하게 실행하고, 외부 보안 솔루션을 패키지/라이브러리 형태로 연결할 수 있도록 설계된 Python 기반 AgentOS Core입니다.

> `SecuAgentOS`의 핵심은 특정 EDR/SIEM/Firewall 또는 특정 Agent Framework에 종속되지 않는 **Security Kernel + Runtime + Extension SPI**입니다.

## Architecture

```text
                     SecuAgentOS
                  Security Kernel
                         |
          +--------------+--------------+
          |              |              |
      AgentRuntime   SecurityPolicy   ToolGateway
          |              |              |
     AgentRegistry  Capability/Risk   ToolRegistry
          |              |              |
          +--------------+--------------+
                         |
                 Security Agents
                         |
          +--------------+--------------+
          |              |              |
       Sentinel       Defender       Threat Intel
                         |
                    External Tools
              EDR / SIEM / IAM / Firewall
```

### Core responsibilities

- **Agent Runtime**: Agent lifecycle, task execution, result normalization
- **Agent Registry**: Built-in 및 third-party Agent package discovery
- **Security Policy**: RBAC와 분리된 capability/policy 기반 실행 제어
- **Tool Gateway**: 외부 보안 솔루션 호출의 단일 보안 경계
- **Security Context / Events / Audit**: 실행 주체, 세션, 보안 이벤트 및 감사 추적
- **Extension SPI**: EDR, SIEM, SOAR, IAM, Firewall, Cloud 및 전문 Agent를 패키지로 확장

## External package model

외부 Agent는 Python package로 배포하고 `secuagentos.agents` entry point를 통해 등록할 수 있습니다.

```toml
[project.entry-points."secuagentos.agents"]
my_agent = "my_security_agent.provider:get_agent_spec"
```

Provider는 `AgentSpec`을 반환합니다.

```python
from secuagent.core.registry import AgentSpec


def get_agent_spec():
    return AgentSpec(
        name="malware-agent",
        version="1.0.0",
        agent_class=MalwareAgent,
        capabilities=("malware.detect", "malware.analyze"),
    )
```

Runtime에서 설치된 Agent package를 검색할 수 있습니다.

```python
from secuagent import AgentRegistry, AgentRuntime

registry = AgentRegistry()
registry.load_installed_packages()
runtime = AgentRuntime(registry=registry)
```

## External security-tool model

외부 보안 제품은 `SecurityTool` adapter로 연결합니다. Agent가 제품 SDK/API를 직접 호출하지 않고 Tool Gateway를 통과하도록 하는 것이 기본 원칙입니다.

```python
from secuagent import SecurityTool, ToolGateway, ToolRegistry

class EDRTool(SecurityTool):
    name = "edr"

    def capabilities(self):
        return {"endpoint.isolate", "endpoint.release"}

    async def execute(self, action, **kwargs):
        ...
```

실제 실행 흐름은 다음과 같습니다.

```text
Agent -> Task -> Policy -> Capability -> ToolGateway -> Adapter -> Security Product
```

## Execution policy

기본 정책은 **deny-by-default**입니다. Agent에 capability를 명시적으로 부여해야 실행할 수 있습니다.

```python
from secuagent import SecurityPolicy

policy = SecurityPolicy()
policy.grant("defender", "endpoint.isolate")
policy.set_approval_required({"endpoint.isolate"})
```

향후 정책 엔진은 위험도, 대상 범위, tenant, 시간, 승인자, resource quota 등의 조건을 추가할 수 있도록 확장합니다.

## Installation

```bash
pip install secuagentos
```

개발 환경:

```bash
pip install -e .[dev]
```

## Package layout

```text
secuagent/
├── secuagent/
│   ├── core/           # runtime, registry, task, context, events
│   ├── security/       # authentication, authorization, policy, crypto, audit
│   ├── agents/         # built-in security agents
│   ├── tools/          # external security-tool SPI and gateway
│   └── utils/
├── examples/
├── tests/
└── pyproject.toml
```

## Design principles

1. **Security Kernel first** — 보안 정책과 실행 통제를 Agent보다 우선한다.
2. **Deny by default** — 명시적으로 허용되지 않은 Agent/Action/Tool은 실행하지 않는다.
3. **Framework agnostic** — LangGraph 등 특정 Agent Framework는 Core가 아니라 integration layer로 취급한다.
4. **Tool isolation** — 외부 보안 제품은 Tool Gateway/Adapter 뒤에 격리한다.
5. **Package extensibility** — 외부 Agent와 Tool을 Python package로 설치할 수 있도록 한다.
6. **Auditability** — 모든 중요한 실행은 SecurityEvent/Audit으로 추적할 수 있어야 한다.

## Scope note

Repository의 `.agents/skills/luna-chat-coder`는 SecuAgentOS runtime에 포함되는 기능이 아닙니다. 이는 프로젝트 개발을 위한 별도의 개발 지원 skill이며 AgentOS 배포 package에 포함되지 않는 **development-time tooling**으로 취급합니다.

## License

MIT License
