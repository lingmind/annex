# LingMind plugin

面向 LingMind 业务用户的标准 Agent 插件。插件源码不绑定 sandbox 或任何其他业务环境；安装或发布时使用
[`render-codex-plugins.py`](../../scripts/render-codex-plugins.py) 注入用户获准访问的 Phoenix MCP 连接。

每个连接只绑定一个业务环境和该环境独立的 Keycloak，并始终使用稳定名称
`lingmind-<environment-code>`。默认环境是安装侧偏好，记录在生成的
`references/configured-environments.json` 中，不通过重命名连接表达。切换环境就是切换 MCP resource；不同
环境的 token、issuer、audience、项目和确认计划不能混用。只有一个环境时可自动设为默认，多个环境时由
用户选择默认环境。

插件负责：

- 环境和项目选择、消歧与当前上下文展示；
- 根据运行时 `tools/list` 选择能力；
- 将只读、普通写、异步任务和高风险确认组织成清晰工作流；
- 解释稳定业务概念并向用户展示风险和结果。

插件不维护工具总表、业务 schema、字段路径、权限映射、服务 URL、发布状态或 fallback。Radix、Crux、
Onyx、Vertex 等业务所有者发布工具及公开 DTO；Phoenix 负责认证、项目准入和通用治理。任何能力缺失时，
插件必须明确报告，不能改用 shell、CLI、直接 REST 或猜测的工具。

repo-local `.mcp.json` 是空的环境无关模板，不能直接访问业务数据。OAuth 使用 Authorization Code + PKCE
S256 和目标 MCP resource discovery；插件包不包含 client secret 或用户 token。

## Skills

- `lingmind-environment-context`：选择、核验和切换业务环境。
- `lingmind-project-context`：选择和核验当前项目。
- `lingmind-business-query`：执行有界业务查询。
- `lingmind-business-write`：执行普通写操作和安全重试。
- `lingmind-async-job`：提交并跟踪异步任务。
- `lingmind-business-planned-action`：完成 prepare、用户确认、execute 和结果核验。
- `lingmind-mission-wayline-operations`：理解任务与航线概念并编排运行时能力。
- `lingmind-media-device-operations`：理解媒体与设备概念并编排运行时能力。

通用规则见 [CapabilityRegistry 使用规则](references/capability-registry.md)、
[上下文规则](references/environment-context.md) 和 [安全动作规则](references/safe-actions.md)。
