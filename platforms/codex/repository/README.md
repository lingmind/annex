# 从 Annex 仓库安装 Codex 插件

## 添加仓库

在 Codex 插件页选择“添加插件市场”，输入 `https://github.com/lingmind/annex`。
该仓库根目录的 `.agents/plugins/marketplace.json` 声明市场 `lingmind-annex`，显示名 **LingMind**，
只有 **LingMind** 和 **LingMind Operator** 两个条目。安装时不需要下载 ZIP 或申请公开目录审核。
私有仓库访问权限不是前提：Annex 当前是公开仓库；组织宿主仍可能有自己的安装策略。

CLI 等价操作：

```bash
codex plugin marketplace add https://github.com/lingmind/annex
codex plugin add lingmind@lingmind-annex
codex plugin add lingmind-operator@lingmind-annex
```

源码版本为 `1.2.0`。两个包使用 `Business & Operations`、`https://lingmind.cn` 和 32px 留白 PNG。
插件目录位于 `distributions/codex/plugins/`，由 canonical `plugins/` 源码生成并纳入版本管理。
目录中的包完整包含 Skills、参考资料与图标，不依赖个人创建的私有 App ID。

## 首次连接业务环境

安装 LingMind 后运行“设置”，或输入“连接 beta 环境”。设置 Skill 使用插件内的
`scripts/setup-mcp.py`，需要 Python 3.11+ 和宿主 Codex CLI。助手使用实际安装路径，用户无需克隆仓库。

流程：提供环境编码 → Apex 返回确切 Phoenix MCP 地址 → 写入当前用户的原生 Codex MCP 配置 →
浏览器独立 OAuth 登录 → 新开聊天 → `context_get` 核验环境身份。

没有环境编码就先询问，不默认连接 beta；没有预授权账号。添加 sandbox 等其他环境时重复设置，
保留已有环境并分别完成登录。每个环境命名为 `lingmind-<code>`。仅连接一个环境时可作为默认；
多个环境且请求未指定编码时需要澄清。密码与令牌不写入插件或仓库。

设置助手只新增确切连接，不重绑已有不同端点，也不覆盖用户的其他 MCP 配置。
它使用 `lingmind-codex`、业务 scopes 与 1455 OAuth 回调端口；各环境必须已部署支持该客户端的 Phoenix/Keycloak。
错误码、登录失败或能力缺失应原样作为阻塞报告，不用其他环境替代。

## Operator

Operator 包含一个原生 HTTP MCP：`https://apex.lingmind.cn/mcp/operator`。
使用运维账号独立登录，OAuth 客户端为 `lingmind-operator-codex`、回调端口 1456。
它保留全局运维环境列表；每次目标查询或操作仍须显式选择当前列表中的环境。
安装成功不等于账号有运维权限，重要操作仍遵守服务端确认流程。

## 更新与来源选择

```bash
codex plugin marketplace upgrade lingmind-annex
```

刷新仓库市场后，在插件详情更新到新版本，再按宿主要求重新加载。
已有其他来源的同名插件时先决定保留的来源，避免同时启用多个副本。
不要为了安装源码版删除服务端 App、清除 OAuth 授权或改动其他用户的连接。

这是本地 Codex 仓库安装路径。它不会把本机原生 MCP 配置同步成云端 dots 授权；
工作区管理员的 GitHub 市场导入是另一条工作区流程，需单独配置连接和策略，不能据本地安装结果声称云端可用。

## 维护者

```bash
make render-repository-plugins PYTHON=/path/to/python3.11
make validate-repository-plugins PYTHON=/path/to/python3.11
```

修改 `plugins/`、设置 Skill、脚本或 Logo 后重新生成派生包，并提交源码及生成结果。
发布新仓库版本时更新 `scripts/render-repository-plugins.py` 的版本；`--check` 会检查生成结果是否漂移。
此生成器不更新或发布现有私有 App。

官方格式与分发说明：[Package your plugin](https://developers.openai.com/plugins/build/plugins)。
