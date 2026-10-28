# 从 GitHub 安装 LingMind 插件

在 Codex 插件市场添加 `https://github.com/lingmind/annex`，安装 LingMind 和 LingMind Operator。
仓库市场使用 `distributions/codex/plugins/` 中的原生 MCP 包，不依赖平台 App。

```bash
codex plugin marketplace add https://github.com/lingmind/annex
codex plugin add lingmind@lingmind-annex
codex plugin add lingmind-operator@lingmind-annex
```

## 连接与使用

通过 LingMind 设置助手提供自己的环境代码。助手使用包内 `scripts/setup-mcp.py` 经 Apex 发现确切 Phoenix，
创建 `lingmind-<code>` 连接并启动独立 OAuth。需要 Python 3.11+ 和 Codex CLI。
没有预置业务账号或环境。新增连接需独立授权；切换时核验 `context_get`，保留其他连接配置。

Operator 通过 `https://apex.lingmind.cn/mcp/operator` 独立授权，使用 `lingmind-operator-codex` 客户端及本机回调。
操作前选择目标环境，修改操作使用服务端计划及确认。密码、令牌和验证结果不得写入仓库。

原生 MCP 依赖运行它的本机宿主，不会把本机 OAuth 自动同步给云端宿主。
App 分发见[分发指南](../distribution-guide.md)。选择一种来源，避免同时安装同名副本。

## 构建与维护

```bash
make render-repository-plugins PYTHON=python3
make validate-repository-plugins PYTHON=python3
python3 scripts/package-repository-plugins.py --output dist/repository-plugins
```

`plugins/` 是技能、资源和品牌素材的规范来源，生成器输出原生 MCP 包及连接声明。
修改后重新生成并检查漂移；打包成功与运行验证分别记录，运行证据保存在私有工作区。
