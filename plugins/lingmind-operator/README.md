# LingMind Operator plugin

面向 LingMind SRE、平台管理员和获授权交付人员的 Codex 插件。当前 repo-local marketplace profile
连接 sandbox 的一套全局 Apex Operator MCP：

```text
https://apex.sandbox.lingmind.cn/mcp/operator
```

`operator_capabilities_list` 和 `environments_list` 用于发现；选择环境后的所有目标观察和修改调用都
显式携带 `environmentId`。能力由 Apex grant、目标 Agent capability、allowlist 和目标环境权限共同
决定。修改动作必须先生成服务端 plan，再由用户确认后执行。

当前版本只发布环境列举、环境详情、capability discovery、工作负载/Pod/事件/有界日志/rollout 观察，
以及 restart/scale 的 plan、execute 和 operation 查询。服务安装、镜像维护、备份和恢复仍是
[后续发布目标](references/planned-capabilities.md)，当前不会被插件自动发现。

Codex 使用预注册 public client `lingmind-operator-codex` 和固定本地回调端口 `1456`，执行
Authorization Code + PKCE S256；客户端不保存 secret。该 client 和 Operator scopes 只能由
全局控制平台 Keycloak 签发，redirect URI 为
`http://127.0.0.1:1456/callback/TAAMC9YbNs4C`，不能复用业务环境的标准插件 token。
当前只申请 `openid`、`apex.environments.read`、`apex.operator.observe` 和
`apex.operator.maintain`；服务端不使用 `profile` 或 `email` claims。

这是 sandbox 预演配置，不表示每个业务环境都部署 Operator MCP。正式发布仍只在生产全局控制平台
部署一套 `https://apex.lingmind.cn/mcp/operator`，切换 URL 时必须同步使用该 URL 对应的 Codex
callback hash 和 Keycloak 精确 redirect allowlist。

## Skills

- `lingmind-operator-observe`：环境、工作负载、事件和日志观察。
- `lingmind-operator-incident-analysis`：跨证据诊断故障。
- `lingmind-operator-service-maintenance`：重启和扩缩容维护。
