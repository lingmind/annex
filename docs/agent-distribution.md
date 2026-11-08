# Agent 分发与接入

DSH 普通用户请先阅读 [快速安装 LingMind 与 LingMind Operator](dsh-quick-start.md)。本文保留跨宿主分发机制、发布与管理员部署说明。

Annex 维护一份共享插件内容、一个版本来源和一个发布入口。普通用户通过 App、GitHub 安装命令或宿主市场安装，
不再下载 ZIP、手工拷贝 Skills 或编辑 MCP 配置文件。首次账户授权仍由用户在浏览器完成。

## 分发渠道与完成边界

| 平台 | 目标入口 | 当前源码提供的能力 | 尚未完成 |
| --- | --- | --- | --- |
| Codex / ChatGPT | 已有 LingMind / LingMind Operator App | 保持已有 App 身份，生成平台更新包 | 新版本上传、平台审核与本地/云端验收 |
| DSH | GitHub 原生 bundle；可选自定义市场索引 | 根 `package.json` 声明 `dsh.bundle`；一次安装加载两个独立插件，分别挂载 Skills、准备 OAuth 运行时并引导登录 | 市场索引静态托管；其他 DSH 版本仍需对应宿主验收 |
| WorkBuddy | GitHub 安装命令；后续 SkillHub + 连接器市场 | npm/GitHub 包提供安装命令，自动合并 Skills 与 MCP 配置 | 宿主验收；原生市场上架与连接器资格 |
| 豆包 | GitHub 安装命令；最终使用工作伙伴/连接器市场 | 自动安装共享 Skills，输出需要的连接信息 | 尚无已核验的连接器自动注册接口，首次 UI 注册仍是缺口；不能宣称一键完成 |

WorkBuddy 的技能市场和连接器是独立入口，上架 Skill 不代表自动取得服务连接。
豆包本地 Skills 也不等于云端工作伙伴上架。不能通过猜测私有协议或修改宿主内部数据库规避注册。

## GitHub 安装

以下命令使用不可变版本标签。升级时替换为已发布的新版本标签。

DSH 支持 `>=0.2.1-rc.5 <0.3.0`（包含 `0.2.1` 稳定版）。
使用其原生插件管理器安装；桌面版的 profile 为 `desktop`，命令行 Web 版为 `web`：

```bash
dsh plugin --profile desktop add github:lingmind/annex#v1.5.3
```

包内是可直接执行的 JavaScript，没有 prepare/build/install 生命周期脚本。
启动该 profile 时，插件自动准备本机 Python OAuth 依赖，首次打开浏览器输入环境编码并独立授权，
再加载共享 Skills 和 MCP 工具。已有授权会复用并按需刷新，不要求重复登录。
需要 Node 22+、Python 3.11+ 和受支持的系统钥匙串。

WorkBuddy 使用同一个 GitHub 包中的安装命令：

```bash
npx --yes --package=github:lingmind/annex#v1.5.3 lingmind-agent --agent workbuddy --environment-code <code>
```

安装器自动合并 `~/.workbuddy/mcp.json`，保留其他 MCP 连接，由 WorkBuddy 完成 OAuth。
省略环境参数可更新已安装配置。安装后重启宿主或创建新会话。

豆包可用同一命令安装 Skills：

```bash
npx --yes --package=github:lingmind/annex#v1.5.3 lingmind-agent --agent doubao --environment-code <code>
```

目前仍需通过豆包支持的 UI 注册 HTTP 连接器，所以这条命令尚不满足完整一键接入。
要消除该步骤，应发布平台认可的 LingMind 工作伙伴/连接器，并验证安装后的登录卡片流程。

## 维护与自动发布

- `plugins/release.json`：两个产品与唯一版本。
- `plugins/<product>/`：产品定义、App 身份、共享 Skills、参考资料和素材。
- 根 `package.json`、`cordis.patch.yml`：同源 GitHub/npm 交付与 DSH 原生 bundle 声明。
- `scripts/agent-cli.mjs`：GitHub 安装命令入口，调用共享安装逻辑。
- `scripts/release-agent-plugins.py`：唯一打包入口。

```bash
make render-agent-plugins
make validate-plugins
make release-agent-plugins
```

本地生成两个 Codex App 更新包，以及一个供 GitHub/npm/DSH 共用的 `lingmind-annex-<version>.tgz`。
App 更新包是维护者交付文件，不要求用户下载。已删除面向用户的 WorkBuddy、豆包和 DSH ZIP 分发包。
`release.json` 与 `SHA256SUMS` 记录版本、产物及校验值。

`.github/workflows/agent-release.yml` 在推送匹配版本的 `v*` 标签时验证并创建 GitHub Release **草稿**，
不会自动提交 App 市场审核或将草稿公开。GitHub 安装使用原标签源码，无需下载草稿附件。
发布先提交源码和推送版本标签，流水线产出草稿后由维护者公开发布。各宿主的真实验收与发行包分开记录。

## DSH 自定义市场索引

发布脚本在显式给定当前干净提交的完整 SHA 和发布时间时，额外生成 `dsh-index.json`：

```bash
python3 scripts/release-agent-plugins.py --source-commit <full-sha> --published-at <unix-seconds>
```

索引绑定不可变 Git commit。工作区有未提交/未跟踪源文件时拒绝生成，避免市场索引指向不存在的实现。
索引须部署到能直接返回 2xx、无重定向的 HTTPS 静态站点，例如经配置的 GitHub Pages。
GitHub Release 的 latest/download 地址存在重定向，不能直接当作 DSH 的索引源。
当前尚未设置或验证公开索引 URL；不得把本地产物声称为已上线市场。

## 授权与运行时

业务通过 Connect 或当前宿主的直接 Phoenix MCP 独立授权，每条连接只绑定一个环境。
Operator 经全局 Apex MCP 选择 `environmentId`，不与业务授权混用。
DSH 依赖运行时位于用户目录 `.lingmind/runtime/`，凭据仅存系统钥匙串。
业务 OAuth 回调临时监听 `127.0.0.1:17641/callback`，Operator 为 `127.0.0.1:17642/callback`，服务错误不会自动重放工具调用。
业务复用 `lingmind-dsh` Connect client；Operator 使用独立的 `lingmind-operator-dsh` Keycloak public client、S256 PKCE 和 Apex audience。
两者的授权、系统钥匙串条目和刷新锁相互隔离，业务已有钥匙串条目保持不变。
Operator client 必须随 Apex Keycloak 配置部署后才能完成真实授权，不复用 Codex client 或业务凭据。

各宿主分别验收首次安装、新会话、真实授权读取、刷新、撤销、升级和错误环境拒绝。
配置生成、npm 打包和模拟挂载测试不能代替实际 DSH 或各宿主验收。
环境隔离详见 [环境连接契约](agent-connections.md)。

依据：[DSH GitHub bundle 安装](https://github.com/deepseek-ai/deepseek-harness/blob/master/docs/user/develop/basic/publish.md)、
[DSH 市场索引](https://github.com/deepseek-ai/deepseek-harness/blob/master/docs/user/guide/plugin-market.md)、
[WorkBuddy 技能市场](https://www.codebuddy.cn/docs/workbuddy/From-Beginner-to-Expert-Guide/Function-Description/Skills-Market)、
[WorkBuddy 连接器](https://www.codebuddy.cn/docs/workbuddy/From-Beginner-to-Expert-Guide/Function-Description/Connector)。

## DSH 0.2.1 兼容验证

`make validate-plugins` 覆盖双插件挂载、发布归档完整性、独立授权发现、回调与凭据隔离。
可指定真实宿主依赖执行集成验证，测试使用本地 MCP 协议服务，不访问业务数据、不进行账户授权：

```bash
DSH_NODE_MODULES=<DSH-runtime>/node_modules node scripts/test-dsh-runtime.mjs
```

macOS 桌面版的依赖位于 ASAR 内时，使用该应用的 Electron Node 模式执行此脚本。
测试覆盖真实 Cordis、Skills registry、Skills filesystem 和 MCP client 的加载与工具发现。
通过测试不等于完成线上 OAuth、新会话或真实工具调用验收。

版本 `1.5.3` 已在 DSH `0.2.2-rc.1` 完成双插件激活、撤销后重新授权和只读调用验收；`1.5.2` 在 `0.2.1-rc.5` 的验收记录仍然有效。具体环境与账户记录保留私有。
维护者可先运行 `npm pack --ignore-scripts`，再用 `dsh plugin --profile desktop add /absolute/path/lingmind-annex-1.5.3.tgz` 安装本地构建验收。

### DSH 多环境连接

LingMind 组件的 `connections` 是本机账户名称列表，默认 `["lingmind"]`。每个账户分别完成浏览器环境授权，
钥匙串凭据、刷新锁和 MCP 命名空间均相互隔离；本机账户名只是标签，不是环境授权或身份依据。
`1.5.3` 没有提供该字段的图形化配置页，需要在目标 profile 的 `cordis.patch.yml` 中合并 `id: lingmind` 配置条目。
保留已有账户，再为新环境添加账户名；首次授权顺序执行，同一业务回调端口不并发占用。
具体路径和可复制示例见[快速安装指南：多环境连接](dsh-quick-start.md#多环境连接按需配置)。

默认账户保留 `lingmind` 工具命名空间；其他账户使用 `lingmind-<账户名>`。
每次选择连接后先调用 `connection_profile_get` 和 `context_get`，以返回的实际环境代码为准。
环境参数与授权不匹配时必须拒绝，不能复用另一个账户的凭据或回退到默认连接。
Operator 是独立的全局运维授权，仍通过显式 `environmentId` 选择环境。

安装列表和组件详情通过 DSH 官方 locale metadata 显示 **LingMind** 和 **LingMind Operator**，
内部 npm 包名不作为产品显示名。

### 服务端发布依赖

DSH 授权需要同时完成：

- Keycloak：`lingmind-operator-dsh` public client、精确本机回调、S256 PKCE 和 Operator audience/scopes。
- Apex gateway：在现有 `components.gateway.operator.allowedClientIds` 中加入 `lingmind-operator-dsh`，保留已有客户端。
- Connect：`clients` 同时保留 `lingmind-cloud` 与 `lingmind-dsh`，后者回调为 `http://127.0.0.1:17641/callback`。
- Apex gateway 与执行安装的 apex-agent 必须都包含新版 Connect 模板。只更新 gateway 会导致旧 Agent 继续渲染旧格式。
- Connect 二进制必须与新 `clients` 配置格式匹配；升级须保留原 vault PVC 和加密密钥。

验证客户端登录页、浏览器回调、实际 MCP 握手和只读工具调用后，才可认定授权可用。
