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

```go
client, err := annex.NewClient(annex.Config{
	BaseURL:     "https://gateway.example.com/api/annex/v1",
	Token:       "lm_pat_xxx",
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

通过 Phoenix Annex 入口地址使用 `lm`：

```bash
export LM_BASE_URL=https://gateway.example.com/api/annex/v1
export LM_TOKEN=lm_pat_xxx
export LM_PROJECT_CODE=demo

bin/lm devices list
bin/lm missions get mission_01HZX
bin/lm raw-data list --page-size 20
bin/lm rule-hits list --severity critical --format json
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
