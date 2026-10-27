# 从 GitHub 安装 LingMind 插件

当前发行版为 **1.4.0，GitHub-only**。在 Codex「插件 → 添加插件市场」输入：

```
https://github.com/lingmind/annex
```

进入 LingMind 市场，只安装 **LingMind** 和 **LingMind Operator**。
两个包使用原生 MCP，不包含 `.app.json`，不引用平台 App，不需要 OpenAI 发布后台或公开审核。
详情显示“MCP 服务器”属于预期行为；这是用户选择的本地连接方式。
开发者 LingMind、类别 Business & Operations、官网 https://lingmind.cn 和 32px 留白 Logo 均随仓库包分发。

```bash
codex plugin marketplace add https://github.com/lingmind/annex
codex plugin marketplace upgrade lingmind-annex
codex plugin add lingmind@lingmind-annex
codex plugin add lingmind-operator@lingmind-annex
```

## 连接业务环境

运行 LingMind 的“设置”或说“连接 beta 环境”。设置助手使用插件内的
`scripts/setup-mcp.py`，通过 Apex 按用户提供的环境编码发现确切 Phoenix，
为当前用户保存 `lingmind-<code>` 原生 MCP 连接，并启动该环境独立的 OAuth 登录。
需要 Python 3.11+ 和 Codex CLI；助手必须使用实际安装路径，不能猜路径。

没有预置业务环境，没有默认账号。新用户先提供环境编码；新增 sandbox 等环境需重复独立登录。
只连接一个环境时可默认使用它；多个环境且请求未指定编码时先询问。
每次切换均先调用该连接的 `context_get`，核验 code/resourceUrl，再使用该环境的项目和能力。
密码与令牌不写入插件或仓库。助手保留其他配置，拒绝静默修改已有不同端点或 OAuth 回调。

Operator 通过 `https://apex.lingmind.cn/mcp/operator` 独立授权，
使用已注册的 `lingmind-operator-codex` OAuth 客户端和本机 1456 回调端口。
它不提供构建代码能力；查询或操作前明确目标环境，敏感操作仍需服务端计划与确认。

## 安装身份与使用范围

- GitHub 市场中只有两个插件。业务的 beta、sandbox MCP 连接不是额外插件。
- 迁移前先卸载账号中的两个同名云端插件和其他旧来源的副本，再安装仓库版，避免侧栏四个入口。
- 卸载可使用宿主支持的插件管理；不需要删除平台创建记录，也不要触碰其他插件或用户的环境授权。
- 当前版本仅支持运行原生 MCP 的 Codex 桌面端及 CLI。它不在云端 dots 注册服务，
  不会同步本机 OAuth 或保证 dots 可调用。用户已明确选择此范围，正式公开发布已取消。
- 先前 App-backed 1.3.0 与云端插件同装会重复；
  [当时的身份调查](app-identity-limitations.md) 保留为历史，不能作为当前发行版安装步骤。

## 更新与维护

刷新 `lingmind-annex` 市场后更新两个已安装插件，按宿主提示重新加载或新开聊天。
不要通过新建同名市场、平台 App 或包装插件来更新。

```bash
make render-repository-plugins PYTHON=/path/to/python3.11
make validate-repository-plugins PYTHON=/path/to/python3.11
```

`plugins/` 的 canonical 私人 App 源码保留为历史与其他分发的实现来源，本次不发布或更新它。
`scripts/render-repository-plugins.py` 生成原生 MCP 包并使用独立版本号；
`distributions/codex/plugins/` 纳入版本管理。修改技能、资源或连接配置后重新生成并检查漂移。

官方格式说明：[Package your plugin](https://developers.openai.com/plugins/build/plugins)。

## ZIP 下载与实测

两个完整 ZIP 与校验文件已发布到
[GitHub Releases](https://github.com/lingmind/annex/releases/tag/codex-plugins-v1.4.0)。

```bash
python3 scripts/package-repository-plugins.py --output dist/repository-plugins
```

[1.4.0 ZIP 实测报告](zip-acceptance-1.4.0.md)：Codex 原生调用成功，类别和官网正确；
上传后的 Logo 字段缺失，云端 dots 实际调用失败。因此该 Release 为预发布验收包，
不能视为完整跨端可用版本。当前机器保留的是两个已上传 ZIP 身份，而非 Git 市场副本；
不要再叠加安装仓库版本。
