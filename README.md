# LingMind Annex

LingMind Annex 是 LingMind 的开放集成中心，维护 SDK、CLI 与 Agent 插件。

## 在 Agent 中连接 LingMind

统一入口：选择 Agent → 安装 LingMind → 输入环境编码 → 浏览器授权 → 验证环境 → 开始使用。

- **Codex / ChatGPT 本地与云端**：在插件页安装已有的 **LingMind** App 插件；运维人员另行安装 **LingMind Operator**。
- **WorkBuddy**：安装同源 Skills 和远程 MCP 配置，由宿主管理 OAuth。
- **豆包桌面端**：安装同源 Skills，按指引注册 HTTP 连接器并完成 OAuth。
- **DeepSeek Harness（DSH）**：安装同源 Skills 和 Cordis 配置，通过 Annex stdio 连接助手完成 OAuth；凭据仅存于系统钥匙串。

DSH alpha `0.2.2-alpha.2` 或兼容版本使用原生 GitHub bundle 安装（DSH 宿主待验收）：

```bash
dsh plugin --profile web add github:lingmind/annex#v1.5.0
```

WorkBuddy 使用同源 GitHub 安装命令，自动配置共享 Skills 与 MCP：

```bash
npx --yes --package=github:lingmind/annex#v1.5.0 lingmind-agent --agent workbuddy --environment-code <code>
```

上述命令按固定 GitHub 版本安装。豆包的 Skills 安装也可自动化，
但首次连接器 UI 注册仍待平台市场接入解决，不能宣称完整一键安装。
渠道状态、更新与授权说明见 [Agent 分发与接入](docs/agent-distribution.md)。

## 维护与发布

`plugins/` 是共享内容唯一来源，`plugins/release.json` 是所有 manifest 的版本来源。
根 npm 包同时提供 GitHub 安装命令和 DSH 原生 bundle，复用相同 Skills 和 OAuth 助手。

```bash
make render-agent-plugins
make validate-plugins
make release-agent-plugins
```

发布流程输出两个 App 更新包和一个共享 npm 归档，不再向用户分发各宿主 ZIP。
推送版本标签后，GitHub Actions 创建带校验和及 DSH 索引的 Release 草稿；市场上架与真实宿主验收另行完成。

## 仓库结构

```text
api/openapi.yaml   公开 API 合约
cmd/lm/           CLI
pkg/              Go SDK 与 Webhook
sdks/             SDK 生成配置
plugins/          Agent 插件唯一源码及发布版本
scripts/          统一安装、渲染、打包与验证
```

## Go SDK

完整认证流程见 [客户端认证使用指南](docs/client-authentication.md)。

通过 Phoenix 用户名密码登录获取 token。`BaseURL` 使用 Phoenix 根地址，不带 `/api/annex/v1`：

```go
authClient, err := annex.NewClient(annex.Config{
	BaseURL: "https://phoenix.example.com",
})
if err != nil {
	return err
}

token, err := authClient.CreateToken(ctx, annex.AuthTokenRequest{
	GrantType:   annex.GrantTypePassword,
	Username:    "user@example.com",
	Password:    "password",
	ProjectCode: "demo",
})
if err != nil {
	return err
}
```

使用 token 调用资源 API：

```go
client, err := annex.NewClient(annex.Config{
	BaseURL:     "https://phoenix.example.com",
	Token:       token.AccessToken,
	ProjectID:   token.ProjectID,
	ProjectCode: token.ProjectCode,
})
if err != nil {
	return err
}

devices, err := client.ListDevices(ctx, annex.ListDevicesParams{
	State: "online",
})
```

## CLI

构建 CLI：

```bash
make build
```

### 认证

完整认证流程见 [客户端认证使用指南](docs/client-authentication.md)。

使用 Phoenix 用户名密码登录。默认会把 `baseUrl`、`token`、`refreshToken`、`projectId` 和 `projectCode` 保存到 `~/.lm/config.json`，后续 `lm devices list` 等命令会自动读取。

```bash
bin/lm --base-url https://phoenix.example.com \
  auth login \
  --username user@example.com \
  --password 'password' \
  --project-id project-document-id \
  --project-code demo
```

刷新 token：

```bash
bin/lm auth refresh
```

查看当前凭证身份和授权范围：

```bash
bin/lm auth me
```

吊销当前 access token：

```bash
bin/lm auth revoke
```

如果不想保存本地配置，可以使用 `--save=false`，并用 `--format env` 输出环境变量：

```bash
bin/lm --base-url https://phoenix.example.com \
  auth login \
  --username user@example.com \
  --password 'password' \
  --format env \
  --save=false
```

### 资源查询

通过保存的 Phoenix 根地址使用 `lm`。CLI/SDK 内部会调用 `/api/auth/*` 和 `/proxy/radix/api/*`，不会访问不存在的 `/api/annex/v1`：

```bash
bin/lm devices list
bin/lm missions get mission_01HZX
bin/lm raw-data list --page-size 20
bin/lm rule-hits list --severity critical
bin/lm devices list --format table
```

CLI 默认输出 JSON。需要带边框表格时传 `--format table`。

## Webhook 进程模式

启动本地进程，用于接收 LingMind 主动上报的事件：

```bash
export LM_WEBHOOK_SECRET=whsec_xxx
bin/lm serve --addr :8080 --path /lingmind/webhook
```

入站请求必须包含以下 header：

- `X-LM-Event`
- `X-LM-Delivery`
- `X-LM-Timestamp`
- `X-LM-Signature: sha256=<hex hmac>`

## SDK 生成

TypeScript、Python 和 Java SDK 从 `api/openapi.yaml` 生成：

```bash
make generate-sdks
```

生成器产出 Auth、Devices、Missions、RawData、RuleHits、Incidents、ClosedLoopActions 和 Messages 客户端 API；`webhooks`
是 Annex 向集成方投递事件的接收契约，不会生成反向调用客户端，其事件模型仍会包含在 SDK 中。

执行脚本前需要确保官方生成器已在 `PATH` 中：`npm install -g @openapitools/openapi-generator-cli`。
不要安装同名的 `openapi-generator-cli` 占位包；脚本会验证生成器版本并拒绝无效工具。

安装、认证、项目上下文和 TypeScript/Python/Java 调用样例见
[`sdks/README.md`](sdks/README.md)。

## 开发

```bash
make fmt
make test
make lint
```
