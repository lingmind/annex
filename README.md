# LingMind Annex

LingMind Annex 是 LingMind 的开放集成中心。它通过稳定的 OpenAPI 合约，对外提供 SDK、CLI、Webhook 和标准 HTTP API 接入方式，并统一经 Phoenix 网关访问 LingMind 能力。

## 仓库结构

```text
api/openapi.yaml        Annex 公开 API 合约
cmd/lm/                 CLI 入口
examples/               对外集成示例
pkg/annex/              Go SDK 核心客户端
pkg/webhook/            Go Webhook / 进程模式运行时
sdks/                   OpenAPI SDK 生成配置
scripts/generate-sdks.sh
```

## Go SDK

使用集成客户端凭证获取 token：

```go
authClient, err := annex.NewClient(annex.Config{
	BaseURL: "https://gateway.example.com/api/annex/v1",
})
if err != nil {
	return err
}

token, err := authClient.CreateToken(ctx, annex.AuthTokenRequest{
	GrantType:    annex.GrantTypeClientCredentials,
	ClientID:     "client_xxx",
	ClientSecret: "client_secret_xxx",
	ProjectCode:  "demo",
	Scope:        []string{"device:read", "mission:read"},
})
if err != nil {
	return err
}
```

使用 token 调用资源 API：

```go
client, err := annex.NewClient(annex.Config{
	BaseURL:     "https://gateway.example.com/api/annex/v1",
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

使用客户端凭证登录。默认会把 `baseUrl`、`token`、`refreshToken` 和 `projectCode` 保存到 `~/.lm/config.json`，后续 `lm devices list` 等命令会自动读取。

```bash
bin/lm --base-url https://gateway.example.com/api/annex/v1 \
  auth login \
  --client-id client_xxx \
  --client-secret client_secret_xxx \
  --project demo \
  --scope device:read,mission:read,raw-data:read,rule-hit:read
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
bin/lm --base-url https://gateway.example.com/api/annex/v1 \
  auth login \
  --client-id client_xxx \
  --client-secret client_secret_xxx \
  --format env \
  --save=false
```

### 资源查询

通过 Phoenix Annex 入口地址使用 `lm`：

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
