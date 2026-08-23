# LingMind plugin

面向 LingMind 业务用户的标准插件。当前 repo-local 配置是开发 profile，连接 sandbox Phoenix：

```text
https://phoenix.sandbox.lingmind.cn/mcp
```

Phoenix 的版本化 `CapabilityRegistry` 是工具、项目上下文、权限和审计的最终事实源。当前服务端快照
由 [`metadata/lingmind-capability-tool-map.v1.json`](../../metadata/lingmind-capability-tool-map.v1.json) 记录，
并从 Phoenix 源码契约确定性生成。插件只编排服务端实际发布的显式工具，不会扩展用户在 Keycloak、
Radix 和项目授权中的权限；仓库内 profile 仍是 sandbox 开发配置，不代表生产发布条件已满足。

一个标准插件连接只绑定一个独立业务环境及其 Keycloak。需要访问多个环境时，为每个环境安装独立的
租户私有包或配置独立连接；不要把环境 URL 当作工具参数动态切换。这样登录会话、issuer、audience、
项目 ID 和审计记录始终留在同一环境边界内。Operator 使用另一套全局连接，不能复用标准插件 token。

Codex 使用预注册 public client `lingmind-codex`，通过 Authorization Code + PKCE S256 获取短期 token。
开发回调端口是 `1455`；Keycloak 必须精确允许当前客户端生成的 loopback redirect URI，并为 MCP resource
签发 `lingmind.read`、`lingmind.write` 和 `lingmind.execute` scopes。客户端不保存 secret，插件包也不含
用户 token。

## 技能族

- `lingmind-project-context`：在当前业务环境内选择和核验项目。
- `lingmind-business-query`：覆盖所有已发布业务域的有界查询、详情、统计和运行状态读取。
- `lingmind-business-write`：执行带幂等键、字段白名单和版本检查的直接写入。
- `lingmind-async-job`：创建、查询和停止数据处理或导出等异步任务。
- `lingmind-business-planned-action`：对删除、任务/设备控制等高风险动作执行 plan/confirm/execute。
- `lingmind-mission-wayline-operations`：编排任务、轨迹、回放、航线生成/合并/更新与飞行控制。
- `lingmind-media-device-operations`：编排媒体流、录像、PTZ、UAV、NVR、机器人和其他设备操作。

开始操作前阅读 [CapabilityRegistry 规则](references/capability-registry.md) 和
[业务域路由](references/business-domains.md)。直接写入遵循 [安全动作规则](references/safe-actions.md)，
异步任务遵循 [异步任务规则](references/async-jobs.md)。
任何工具调用都必须遵循 [敏感输入边界](references/sensitive-input-boundary.md)。
