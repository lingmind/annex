# LingMind Annex

LingMind Annex 是 LingMind 的开放集成中心。它对外提供 SDK、CLI 和 Webhook/进程模式，统一经 Phoenix 网关访问 LingMind 能力，并在客户端侧屏蔽 Phoenix 认证、Radix 代理路径和数据模型差异。

## 仓库结构

```text
api/openapi.yaml        Annex 公开 API 合约
cmd/lm/                 CLI 入口
docs/                   对外使用文档
examples/               对外集成示例
pkg/annex/              Go SDK 核心客户端
pkg/webhook/            Go Webhook / 进程模式运行时
sdks/                   OpenAPI SDK 生成配置
scripts/generate-sdks.sh
plugins/                LingMind 与 LingMind Operator 插件源码
platforms/              Codex、WorkBuddy、DeepSeek Harness 连接 profile
.agents/plugins/        Annex 仓库内的 Codex marketplace
```

## Agent 插件

Annex 维护两个 Agent 插件：

- `plugins/lingmind` 是标准业务插件。每个独立业务环境使用一个 Phoenix MCP 连接和该环境自己的
  Keycloak；一个插件包可包含多个具名连接，并在请求开始时显式核验和切换环境。
- `plugins/lingmind-operator` 是全局运维插件。它只连接一套 Apex Operator MCP，并在每次目标调用中
  显式选择获授权的 `environmentId`；不在每个业务环境部署 Operator MCP。

插件模板声明 Skills、参考资料和空 MCP 清单，具体环境连接由发布工具注入。标准插件覆盖 Phoenix 当前发布的环境/项目上下文、
完整业务查询、直接写入、异步任务、任务/航线、媒体/流和设备控制；Operator 覆盖 Agent-backed 观察、
Grant 管理、维护、服务部署和备份/恢复编排。工具、schema、权限、风险和生命周期始终以运行时 MCP
`tools/list` 为准，Annex 不保存第二份工具目录或业务字段契约。

身份认证使用 Authorization Code、PKCE S256 和目标服务的 OAuth discovery。Codex 使用原生 HTTP
OAuth，WorkBuddy 使用 MCP OAuth discovery/DCR，DeepSeek Harness 通过 Annex 本地 OAuth bridge；bridge
只把 token 存入操作系统 keychain，插件包和平台 profile 中不保存 token，也禁止长效 bearer 配置。平台
profile 见 [`platforms/`](platforms/README.md)。仓库模板不包含具体环境 URL，也不表示生产就绪。

为 Codex 生成包含一个或多个业务环境的本地 marketplace：

```bash
/Users/shoppon/code/lingmind/.codex-venv/bin/python scripts/render-codex-plugins.py \
  --output .local/codex-marketplace \
  --apex-url https://apex.lingmind.cn \
  --environment-code wf3b \
  --environment-code yf16 \
  --default-environment wf3b \
  --operator https://apex.example/mcp/operator lingmind-operator-codex 1456
```

只配置一个环境时会自动成为默认环境；配置多个环境时必须显式传
`--default-environment`。所有连接始终命名为 `lingmind-<environment-code>`，默认环境以独立指针写入生成
插件的 `references/configured-environments.json`，不会因修改默认值而重绑已有 OAuth token。未提供任何
环境参数且终端可交互时，脚本会提示输入一个环境编码。连接器通过全局 Apex 解析环境编码，只保存返回的
Phoenix MCP 地址；也可用 `--environment` 显式注入连接供发布自动化使用。生成目录包含独立 marketplace
和插件副本；默认连接摘要同时注入生成后的环境选择 Skill，确保 Host 无需读取外部 JSON 也能选择默认
连接。摘要不包含 URL、issuer 或凭据，环境 URL 也不写回源码。

验证 manifest、marketplace 和全部聚合 Skills：

```bash
make validate-plugins PYTHON=/Users/shoppon/code/lingmind/.codex-venv/bin/python
```

本目录的 marketplace 用于仓库内开发和团队测试，不会创建或修改用户目录下的 marketplace。

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
	ProjectCode: "demo",
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

使用 Phoenix 用户名密码登录。默认会把 `baseUrl`、`token`、`refreshToken` 和 `projectCode` 保存到 `~/.lm/config.json`，后续 `lm devices list` 等命令会自动读取。

```bash
bin/lm --base-url https://phoenix.example.com \
  auth login \
  --username user@example.com \
  --password 'password' \
  --project demo
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

执行脚本前需要确保 `openapi-generator-cli` 已在 `PATH` 中。

## 开发

```bash
make fmt
make test
make lint
```
