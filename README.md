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
bin/lm --format json rule-hits list --severity critical
```

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
