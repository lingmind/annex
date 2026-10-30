# LingMind plugin

面向 LingMind 业务用户的标准 Agent 插件。`skills/`、`references/` 和 `assets/` 是所有宿主的共同来源。
Codex / ChatGPT 通过已注册的 LingMind App 安装，其他 Agent 使用同一发布流程生成的宿主适配包。
接入说明见 [Agent 分发与接入](../../docs/agent-distribution.md)。

插件不预置业务环境。每个连接只绑定一个环境并完成独立授权；调用前核验准确环境编码与 `context_get`。
不同环境的 token、issuer、audience、项目和确认计划不能混用。只有一个已授权连接时可自动选择，
存在多个连接时必须明确环境。

插件负责：

- 环境和项目选择、消歧与当前上下文展示；
- 在登录用户的项目和权限范围内查询用户、角色与有效权限目录；
- 根据运行时 `tools/list` 选择能力；
- 将只读、普通写、异步任务和高风险确认组织成清晰工作流；
- 解释稳定业务概念并向用户展示风险和结果。

插件不维护工具总表、业务 schema、字段路径、权限映射、服务 URL、发布状态或 fallback。Radix、Crux、
Onyx、Vertex 等业务所有者发布工具及公开 DTO；Phoenix 负责认证、项目准入和通用治理。任何能力缺失时，
插件必须明确报告，不能改用 shell、CLI、直接 REST 或猜测的工具。

所有查询继承插件当前登录用户的 token、可访问项目和实时 Access Policy。Phoenix 使用的服务账号只负责
服务间传输，不会赋予登录用户额外权限。

Codex 的 `.app.json` 声明唯一已注册 App；宿主管理连接与 OAuth。
其他 Agent 的安装器只处理必需的本地适配。插件包不保存 client secret 或用户 token。

## Skills

- `lingmind-setup`：通过当前宿主支持的流程连接并授权业务环境。
- `lingmind-operations-expert`：“凌析”运营入口，将请求路由到对应业务 Skill。

- `lingmind-environment-context`：选择、核验和切换业务环境。
- `lingmind-project-context`：选择和核验当前项目。
- `lingmind-business-query`：执行有界业务查询，包括已授权的用户、角色和权限目录查询。
- `lingmind-business-write`：执行普通写操作和安全重试。
- `lingmind-async-job`：提交并跟踪异步任务。
- `lingmind-business-planned-action`：完成 prepare、用户确认、execute 和结果核验。
- `lingmind-mission-wayline-operations`：理解任务与航线概念并编排运行时能力。
- `lingmind-media-device-operations`：理解媒体与设备概念并编排运行时能力。
- `lingmind-daily-report-renderer`：查询已授权业务事实并生成无人机或摄像头日报图片。

通用规则见 [CapabilityRegistry 使用规则](references/capability-registry.md)、
[上下文规则](references/environment-context.md) 和 [安全动作规则](references/safe-actions.md)。
