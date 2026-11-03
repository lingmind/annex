# 在 DSH 中快速安装 LingMind

本指南使用已发布的 [LingMind Agent 1.5.2](https://github.com/lingmind/annex/releases/tag/v1.5.2)。桌面版可直接在插件界面安装；一次安装包含 **LingMind** 和 **LingMind Operator** 两个组件。

| 组件 | 用途 | 首次授权 |
| --- | --- | --- |
| LingMind | 查询与处理自己有权限访问的项目、设备、任务等业务数据 | 输入环境编码，在该环境的登录页完成授权 |
| LingMind Operator | 查看环境与服务状态，处理获授权的运维工作 | 使用具备运维权限的账号独立授权，调用时再选择目标环境 |

只使用业务功能时，可以关闭 LingMind Operator 组件。业务环境登录权限不等于运维权限。

## 安装前准备

- 已安装并能正常使用 DSH。`1.5.2` 声明兼容 `>=0.2.1-rc.5 <0.3.0`，已在桌面版 `0.2.1-rc.5` 验收。
- 电脑已安装 Python 3.11 或更高版本，并有可用的系统钥匙串。插件自动准备自己的 Python 依赖，无需手动安装 `keyring` 等包。
- 知道管理员提供的业务环境编码，并有该环境的登录账号。需要运维功能时，另备获授权的 Operator 账号。
- 安装时能访问 GitHub、npm registry 和 Python 包源；授权时能访问 LingMind 登录服务。

桌面版使用其内置 Node.js 运行时。命令行用户还需 Node.js 22 或更高版本。可在终端用 `python3 --version` 检查 Python；Windows 通常使用 `python --version`。

## 三步完成桌面安装

### 1. 添加插件

打开 DSH 左侧的 **插件** → **添加插件**，在包名或来源输入框粘贴：

```text
github:lingmind/annex#v1.5.2
```

按安装向导确认安装并启用。这个输入框只需要上面的包标识，不要粘贴整条终端命令。无需克隆仓库、下载 ZIP 或手工添加 MCP 服务器。[DSH 官方插件管理说明](https://github.com/deepseek-ai/deepseek-harness/blob/dsh-v0.2.1-rc.5/packages/client/ui-plugin-manager/README.zh.md)

安装列表中会出现一个 **LingMind** 安装项。打开它，在 **包含的组件** 中可以看到 **LingMind** 和 **LingMind Operator**，并分别开关。

### 2. 完成浏览器授权

首次启用时，插件会打开浏览器。两个组件分别授权，页面出现的先后顺序不影响使用。

**LingMind 业务授权：**输入管理员提供的环境编码 → 核对确认页的环境 → 点击“继续登录” → 在该环境的登录页完成登录和授权。

**LingMind Operator 授权：**在独立的运维登录页完成授权。这里不需要输入业务环境编码；进入 DSH 后再指定需要查看的环境。

授权成功后，浏览器会显示 `LingMind authorization received. Return to your Agent.`。返回 DSH，等待已启用的组件显示 **运行中**。若界面没有更新，点击插件页的“刷新”；仍未加载时重启 DSH。

凭据保存在本机系统钥匙串。后续启动会复用或刷新各自的授权，不需要每次登录。不要把密码、token 或浏览器回调地址粘贴到对话中。

### 3. 在新会话中验证

先用只读请求确认业务连接，例如：

```text
使用 LingMind 核对当前连接的环境编码，并列出我可以访问的项目。只查询，不创建或修改数据。
```

返回的环境编码应与自己授权的环境一致，项目范围以当前登录账号的权限为准。组件“运行中”和实际业务查询成功是两项检查。

启用了 Operator 时，再验证：

```text
使用 LingMind Operator 列出我有权运维的环境。只查询，不执行重启、升级或其他修改。
```

## 已有 dsh 命令时的安装方式

使用桌面应用对应的 `dsh` 命令，在终端执行：

```bash
dsh --version
dsh plugin --profile desktop add github:lingmind/annex#v1.5.2
```

然后回到桌面插件页刷新并完成上述授权。如果提示 `dsh: command not found`，直接使用前面的界面安装方式。

如果使用的是命令行启动的 Web 界面，将 `desktop` 换成该会话实际使用的 profile；例如已有的 `web` profile：

```bash
dsh plugin --profile web add github:lingmind/annex#v1.5.2
```

插件只对安装目标 profile 生效。不要把桌面版装到另一个 profile 后，再到桌面窗口寻找插件。[DSH 官方 profile 安装机制](https://github.com/deepseek-ai/deepseek-harness/blob/dsh-v0.2.1-rc.5/docs/user/develop/basic/publish.md)

## 多环境连接（按需配置）

首次安装使用本机账户名 `lingmind`。这个名称只是本地标签，实际环境由浏览器授权决定。一个业务账户只绑定一个环境；新增环境需要新增账户并独立授权。

`1.5.2` 没有提供 `connections` 的图形化配置页。需要连接多个环境时，使用 DSH 支持的 profile 用户配置：

1. 退出 DSH，备份该 profile 的 `cordis.patch.yml`。桌面版默认路径为 `~/.dsh/profiles/desktop/cordis.patch.yml`；Windows 为用户目录下的 `.dsh\profiles\desktop\cordis.patch.yml`。设置过 `DSH_HOME` 或使用其他 profile 时，以实际位置为准。
2. 将下面的条目合并到文件的顶层 YAML 列表。保留其他配置；如果已有 `id: lingmind`，修改原条目，不要重复添加。
3. 重新启动 DSH，为新增账户完成浏览器授权。已有账户继续使用自己的授权。

```yaml
- id: lingmind
  config:
    connections:
      - lingmind
      - sandbox
```

上例保留默认账户，新增一个名为 `sandbox` 的本机账户。`sandbox` 仅为示例标签，授权时应输入你实际要连接的环境编码。如果原账户已命名为 `beta` 等其他名称，保留原名称，不要为了照抄示例而替换它。

账户名使用 1–23 个小写字母、数字、连字符或下划线，并以字母或数字开头。默认账户对应 `lingmind` MCP 命名空间，其他账户对应 `lingmind-<账户名>`。每个账户的凭据与刷新锁相互隔离。

连接多个环境后，在请求中明确环境编码；插件应先核对所选连接的 `connection_profile_get` 和 `context_get`。传入其他环境的 `envCode` 会被拒绝，不能用它切换已有凭据。Operator 仍使用独立的全局授权，不需要为每个业务账户重复安装。

## 重新授权与撤销

先关闭相应组件或退出 DSH，再执行授权维护命令，避免与正在进行的授权流程争用回调端口。以下业务命令使用默认账户 `lingmind`；若配置了其他账户名，将 `--connection` 后的值改成对应名称。

重新授权一个业务账户：

```bash
npx --yes --package="github:lingmind/annex#v1.5.2" lingmind-agent --agent dsh --product lingmind --connection lingmind --login
```

重新授权 Operator：

```bash
npx --yes --package="github:lingmind/annex#v1.5.2" lingmind-agent --agent dsh --product lingmind-operator --login
```

完成后重新启用组件。重新授权应连接原账户对应的环境；连接新环境时使用新的账户名。

撤销业务账户授权：

```bash
npx --yes --package="github:lingmind/annex#v1.5.2" lingmind-agent --agent dsh --product lingmind --connection lingmind --logout
```

撤销 Operator 授权：

```bash
npx --yes --package="github:lingmind/annex#v1.5.2" lingmind-agent --agent dsh --product lingmind-operator --logout
```

不再使用的业务账户应从 `connections` 移除；不再使用的组件保持关闭。重新启用一个没有授权的账户会再次打开浏览器。卸载插件可在 DSH 插件详情页操作，但卸载本身不会自动撤销钥匙串中的授权。

## 常见问题

| 现象 | 处理方法 |
| --- | --- |
| 插件市场搜不到 LingMind | 使用“添加插件”粘贴本指南的 GitHub 包标识。GitHub 安装不依赖市场索引上架。 |
| 安装提示 DSH 版本不兼容 | 核对宿主版本和包标识是否为 `v1.5.2`。不要通过版本风险豁免强行安装其他版本。 |
| 组件一直“加载中” | 首次启动需要准备 Python 依赖并完成浏览器授权。检查 Python 版本、包源连通性和未完成的授权页；不需要运维功能时关闭 Operator。 |
| 授权超时、旧回调页打不开 | 重新发起授权并使用新打开的页面，不重复提交旧回调。若持续失败，检查是否有其他授权流程占用本机回调端口。 |
| 提示系统钥匙串不可用 | 确保系统钥匙串可用并已解锁；Linux 需要可用的 Secret Service 后端。插件不使用明文文件保存 token。 |
| Operator 提示“客户端未找到”或授权后仍被拒绝 | 请管理员检查 Keycloak 的 Operator DSH 客户端、scope 绑定及 Apex 客户端白名单。普通业务用户也可以关闭 Operator，单独使用 LingMind。 |
| 业务授权页面返回 `invalid_request` | 请管理员确认 Connect 已登记 DSH 客户端，并对齐服务端配置与版本。 |
| 查询提示环境不匹配或没有项目权限 | 核对实际授权环境、所选账户与登录账号的权限；不要更换到其他环境来代替本次请求。 |

管理员的配套部署要求见 [Agent 分发与接入：服务端发布依赖](agent-distribution.md#服务端发布依赖)。普通用户无需修改服务端配置。
