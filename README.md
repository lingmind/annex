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

### 在 Codex 中从 GitHub 添加

在插件页面选择“添加插件市场”，粘贴：

```text
https://github.com/lingmind/annex
```

打开 **LingMind** 市场，安装 **LingMind** 和 **LingMind Operator** 两个插件。
开发者为 LingMind，类别为企业应用（`Business & Operations`），网站为 `https://lingmind.cn`；
两者均使用带 32px 留白的 LingMind Logo。

两个包通过已注册 App 连接服务，详情显示“应用”，不再配置本机 MCP 服务器。
业务插件安装后运行“设置”或关联账号，提供环境编码并在对应 Phoenix 登录授权。
添加其他环境时分别授权；新用户没有默认环境。Operator 使用其独立的运维 App 登录。

```bash
codex plugin marketplace add https://github.com/lingmind/annex
codex plugin add lingmind@lingmind-annex
codex plugin add lingmind-operator@lingmind-annex
```

Codex 使用仓库包，云端 dots 使用同两个 App 的现有云端插件；不创建同名云端包装。
个人仓库安装不会自动向云端导入目录，也不会授予其他用户私人 App 的访问权限。
已有旧 MCP 版时先更新来源并核对重复连接，只保留两个插件入口。
安装、更新与源码维护说明见 [`platforms/codex/repository/README.md`](platforms/codex/repository/README.md)。

### 云端连接与高级开发配置

云端 dots 的标准 Agent Plugins 1.0 打包、账户发布与 OAuth 连接步骤见
[`platforms/codex/cloud-plugins.md`](platforms/codex/cloud-plugins.md)。

Annex 维护两个 Agent 插件：

- `plugins/lingmind` 是标准业务插件。每个独立业务环境使用一个 Phoenix MCP 连接和该环境自己的
  Keycloak；一个插件包可包含多个同时启用的具名连接，并按请求指定的环境选择和显式核验。
- `plugins/lingmind-operator` 是全局运维插件。它只连接一套 Apex Operator MCP，并在每次目标调用中
  显式选择有效的 `environmentId`；不在每个业务环境部署 Operator MCP。

插件模板声明 Skills、参考资料和空 MCP 清单，具体环境连接由发布工具注入。标准插件覆盖 Phoenix 当前发布的环境/项目上下文、
完整业务查询、直接写入、异步任务、任务/航线、媒体/流和设备控制；Operator 覆盖 Agent-backed 观察、
维护、服务部署和备份/恢复编排。工具、schema、权限、风险和生命周期始终以运行时 MCP
`tools/list` 为准，Annex 不保存第二份工具目录或业务字段契约。

身份认证使用 Authorization Code、PKCE S256 和目标服务的 OAuth discovery。Codex 使用原生 HTTP
OAuth，WorkBuddy 使用 MCP OAuth discovery/DCR，DeepSeek Harness 通过 Annex 本地 OAuth bridge；bridge
只把 token 存入操作系统 keychain，插件包和平台 profile 中不保存 token，也禁止长效 bearer 配置。平台
profile 见 [`platforms/`](platforms/README.md)。标准业务插件模板不包含具体环境 URL；全局唯一的 Operator
插件直接声明 `https://apex.lingmind.cn/mcp/operator`，安装时无需注入连接。

为 Codex 生成包含一个或多个业务环境的本地 marketplace：

```bash
/Users/shoppon/code/lingmind/.codex-venv/bin/python scripts/render-codex-plugins.py \
  --output .local/codex-marketplace \
  --apex-url https://apex.lingmind.cn \
  --environment-code wf3b \
  --environment-code yf16 \
  --default-environment wf3b
```

本机快速配置并重装标准 LingMind 插件：

```bash
make configure-codex-lingmind \
  PYTHON=/Users/shoppon/code/lingmind/.codex-venv/bin/python
```

快速命令默认配置并启用 `beta` 环境。配置其他单一环境时只需设置 `LINGMIND_ENVIRONMENTS=wf3b`，该环境
会自动成为默认环境；配置多个环境时使用空格分隔环境编码，并显式指定 `LINGMIND_DEFAULT_ENVIRONMENT`。若
`codex` 不在当前 shell 的 `PATH` 中，Makefile 会自动使用 Codex 桌面应用内置的 CLI，也可通过
`CODEX=/absolute/path/to/codex` 显式指定。该命令把生成结果写入
`.local/codex-marketplace`，注册 `lingmind-configured` 本地 marketplace（尚未注册时），并从该来源
重装 `lingmind` 插件。完成后需新建 Codex 任务，新的 MCP 连接才会进入 Host 工具目录。

例如同时配置三个可切换环境，并以 `beta` 作为未指定环境时的默认值：

```bash
make configure-codex-lingmind \
  PYTHON=/Users/shoppon/code/lingmind/.codex-venv/bin/python \
  LINGMIND_ENVIRONMENTS="beta sandbox wf3b" \
  LINGMIND_DEFAULT_ENVIRONMENT=beta
```

只配置一个环境时会自动成为默认环境；配置多个环境时必须显式传
`--default-environment`。所有连接始终命名为 `lingmind-<environment-code>`，默认环境以独立指针写入生成
插件的 `references/configured-environments.json`，不会因修改默认值而重绑已有 OAuth token。未提供任何
环境参数且终端可交互时，脚本会提示输入一个环境编码。连接器通过全局 Apex 解析环境编码，只保存返回的
Phoenix MCP 地址；也可用 `--environment` 显式注入连接供发布自动化使用。生成目录包含独立 marketplace
和插件副本；默认连接摘要同时注入生成后的环境选择 Skill，确保 Host 无需读取外部 JSON 也能选择默认
连接。生成的 MCP 配置启用所有稳定连接；未指定环境时选择默认连接，指定或切换环境时按稳定连接名选择并
通过 `context_get` 核验。摘要不包含 URL、issuer 或凭据，环境 URL 也不写回源码。Codex
加载完整动态目录时启用 MCP 2026；旧协议模式应使用 Host 原生 tool allowlist 控制单轮目录规模。

验证 manifest、marketplace 和全部聚合 Skills：

```bash
make validate-plugins PYTHON=/Users/shoppon/code/lingmind/.codex-venv/bin/python
```

为 WorkBuddy 首次安装 LingMind 业务 Skills 和 MCP 连接：

```bash
make configure-workbuddy-lingmind ENV="sandbox"
```

该命令把 `plugins/lingmind` 的 Skills 和参考资料同步到 `~/.workbuddy`，通过 Apex 将每个环境编码解析为
直接 Phoenix MCP 连接，并合并写入 WorkBuddy 的 `mcp.json`。它只替换上次由 LingMind 配置管理的业务环境
连接，保留其他 MCP 连接和 `lingmind-operator`；OAuth token 不写入或复制到这些文件。

已经安装后，直接执行同一命令即可沿用现有环境和 MCP URL 更新 Skills，无需重新解析环境或改变 OAuth
状态：

```bash
make configure-workbuddy-lingmind
```

安装或更新后需重启 WorkBuddy 或新建任务，使新的 Skills 和 MCP 连接进入 Host 工具目录。

为豆包桌面端首次安装“凌析”、LingMind 业务 Skills 和 HTTP MCP 连接信息：

```bash
make configure-doubao-lingmind ENV="sandbox"
```

命令会打印每个连接器的名称和 Phoenix MCP URL；在豆包的“技能 · 连接器 · 伙伴 > 新建 > 新建自定义
连接器”中选择 `HTTP`，填入打印值，自定义 Headers 留空并完成 OAuth 授权。豆包没有公开可写的本地
连接器配置文件，所以首次 UI 注册不会被脚本绕过。

已经安装后，可沿用环境和 OAuth 状态更新 Skills 与启动器：

```bash
make configure-doubao-lingmind
```

安装或更新后需重启豆包或新建工作任务。平台契约和资格验证边界见 `platforms/doubao/README.md`。
“凌析”是本地自定义 Skill；豆包“工作伙伴”是独立的云端上架市场，本地安装不会使它出现在伙伴页。

仓库根目录的 marketplace 提供可直接从 GitHub 安装的完整插件；高级配置命令生成的
`lingmind-configured` 是独立的开发来源，安装时同样应避免启用多个同名来源。

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
