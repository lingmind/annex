# LingMind Operator plugin

面向 LingMind SRE、平台管理员和获授权交付人员的全局运维插件。插件源码内置唯一的
`https://apex.lingmind.cn/mcp/operator` 连接，可直接从 LingMind marketplace 安装；无需运行环境
renderer 或手工填写 MCP 地址。

Operator Plugin 负责环境选择、证据收集、用户确认、结果展示和工作流编排。Apex 负责工具契约、环境
Grant、计划持久化、`Environment.agentConfig` 解析和审计；被分配的共享 VM Apex Agent 负责通过自身
网络或业务平台 VPN 访问目标环境并执行。插件不保存 Agent URL、集群凭据、服务实现、备份格式、部署
schema、角色名称、工具目录或当前可用性清单。

每个目标调用都显式携带环境标识。插件可以保存本地默认环境，但 Apex 会在每次调用重新校验用户 Grant
并读取服务端 Environment 当前分配的 Agent。多个环境可以共享同一个 Agent，Plugin 不假设 Agent 部署在
目标环境中。所有观察和修改操作都必须经过 Apex Agent；Agent 不可用时明确失败，不存在
直接集群客户端、SSH、shell 或其他环境访问 fallback。

修改类操作遵循运行时工具声明的 prepare/confirm/execute 流程。用户确认前展示环境、目标、影响、
前置条件和过期时间；执行后使用运行时状态或证据能力核验结果。具体参数、允许动作、计划规则和结果结构
始终以 Apex MCP `tools/list` 为准。

repo-local `.mcp.json` 固定声明唯一的全局 Apex Operator MCP。OAuth 使用全局控制平台的 Authorization
Code + PKCE S256；
Operator token 不能用于业务环境 Phoenix MCP，标准插件 token 也不能用于 Operator。
当前 Apex 到 Agent 是内部可信网络调用，没有 Agent API token；Plugin 不参与、保存或透传这段内部调用的
认证材料。

## Skills

- `lingmind-operator-environment-context`：发现、选择和核验获授权环境。
- `lingmind-operator-observe`：收集环境、服务、事件和日志证据。
- `lingmind-operator-incident-analysis`：组织故障证据并形成诊断。
- `lingmind-operator-service-maintenance`：编排服务维护与结果验证。
- `lingmind-operator-service-deploy`：编排受控服务安装或升级。
- `lingmind-operator-backup-restore`：编排备份恢复和验证。
- `lingmind-operator-grant-admin`：在服务端授权范围内管理 Grant。
