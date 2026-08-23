# LingMind plugin

面向 LingMind 业务用户的 Codex 插件。当前开发配置固定连接 sandbox：

```text
https://phoenix.sandbox.lingmind.cn/mcp
```

Phoenix 是业务工具、项目上下文、权限和审计的最终事实源。插件中的 Skills 只编排显式工具，
不会扩展用户在 LingMind 中已有的权限。

当前版本是 sandbox 垂直切片，只发布：

- `projects_list`
- `devices_list`
- `raw_notes_create`

该切片不是完整业务能力，也不满足正式发布门禁。完整任务、规则命中、流媒体和其他业务工具保留为
[后续发布目标](references/planned-capabilities.md)，在服务端工具存在前不会被插件自动发现。

Codex 使用预注册 public client `lingmind-codex` 和固定本地回调端口 `1455`，执行
Authorization Code + PKCE S256。sandbox Keycloak 必须允许
`http://127.0.0.1:1455/callback/QU-iJP6Kee5-`，并为 access token 签发标准 MCP resource audience 与
`lingmind.read`、`lingmind.write` scopes。当前服务端不使用 `profile` 或 `email` claims，因此插件不申请
这两个 scope；当前 catalog 也没有 execute 工具，因此不申请 `lingmind.execute`。

## Skills

- `lingmind-project-context`：选择和核验项目上下文。
- `lingmind-business-query`：列出项目设备，或在明确请求时创建原始数据备注。

OAuth、工具契约和风险约束由 `.mcp.json` 及 `references/` 中的资料说明。
