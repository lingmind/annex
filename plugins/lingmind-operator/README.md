# LingMind Operator plugin

面向 LingMind SRE、平台管理员和获授权交付人员的 Codex 插件。当前 repo-local marketplace profile
连接 sandbox 的一套全局 Apex Operator MCP：

```text
https://apex.sandbox.lingmind.cn/mcp/operator
```

`operator_capabilities_list` 和 `environments_list` 用于发现；选择环境后的所有目标观察和修改调用都
显式携带 `environmentId`。能力由 Apex grant、目标 Agent capability、namespace/resource/service allowlist
和目标环境 Agent 权限共同决定。环境访问只经过 Apex Agent；插件不持有目标集群凭据，也不提供备用
集群访问路径。

当前服务端工具覆盖环境与 capability discovery、Grant 创建/更新/列表/详情/撤销/历史、工作负载/Pod/事件/有界
日志/rollout、资源检查、服务状态和诊断、备份目标与安全部署配置 discovery，以及 restart/scale、服务升级/受审安装、Matrix 备份的持久化
plan、cancel、execute、status 和结果证明；Matrix 恢复从已完成且 checksum-bound 的备份 operation 派生，
同样只通过 Agent 执行。运行时 `operator_capabilities_list` 与 tool catalog 仍是最终事实源；当前不可用项
见 [能力边界](references/unavailable-capabilities.md)。

Codex 使用预注册 public client `lingmind-operator-codex` 和固定本地回调端口 `1456`，执行
Authorization Code + PKCE S256；客户端不保存 secret。该 client 和 Operator scopes 只能由
全局控制平台 Keycloak 签发，redirect URI 为
`http://127.0.0.1:1456/callback/TAAMC9YbNs4C`，不能复用业务环境的标准插件 token。
当前按工具申请 `openid`、环境读取、观察、维护、服务部署、备份操作和 Grant 管理 scopes。Grant 管理
仍由服务端同时核验 `apex.grants.manage` 与配置的 Keycloak `apex-operator-admin` realm role；普通 Operator
用户即使能申请可选 scope 或看到技能说明也不能越权调用。服务端不使用
`profile` 或 `email` claims。

这是 sandbox 开发 profile，不表示生产就绪，也不表示每个业务环境都部署 Operator MCP。Operator 始终
只有一套全局控制平台连接；切换到非 sandbox 入口时，必须同步使用该入口的 issuer、resource audience、
Codex callback hash 和 Keycloak 精确 redirect allowlist。

## Skills

- `lingmind-operator-environment-context`：发现获授权环境并显式切换 `environmentId`。
- `lingmind-operator-observe`：环境、工作负载、事件和日志观察。
- `lingmind-operator-incident-analysis`：跨证据诊断故障。
- `lingmind-operator-service-maintenance`：重启/扩缩容 plan、取消、执行和 rollout 证明。
- `lingmind-operator-service-deploy`：服务升级和内置受审服务安装。
- `lingmind-operator-backup-restore`：checksum-bound Matrix 备份与恢复流程。
- `lingmind-operator-grant-admin`：在管理员 scope 与 Keycloak 管理角色双重授权下管理 Grant。
