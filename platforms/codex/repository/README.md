# 从 Annex 仓库安装 LingMind 应用插件

> **当前个人账号的限制：** 仓库插件与已有云端插件是两个不同安装身份。
> `.app.json` 只复用 App 连接，不合并插件。两边同时安装会在 Codex 显示四个入口。
> 要同时保留云端调用和两个已安装入口，当前应只安装原有两个云端插件；不要再执行下面的仓库安装命令。
> 仓库目录仍可浏览、克隆和版本管理，不能据此声称个人账号已经实现跨端单一安装身份。

在 Codex 插件页选择“添加插件市场”，输入 `https://github.com/lingmind/annex`。
市场 `lingmind-annex` 只提供 **LingMind** 和 **LingMind Operator** 两个插件。

两个 `1.3.0` 包通过 `.app.json` 分别引用已有的 LingMind、LingMind Operator App，
标记为必需应用，包含完整技能、参考资料和品牌资源。它们不再声明本机 MCP 服务器，
也不通过本地脚本修改 Codex 配置。插件详情应显示“应用”；这是与 Notion 相同的依赖形式。
保留企业应用类别、`https://lingmind.cn` 和带 32px 留白的 LingMind Logo。

```bash
codex plugin marketplace add https://github.com/lingmind/annex
codex plugin add lingmind@lingmind-annex
codex plugin add lingmind-operator@lingmind-annex
```

## 连接环境

安装后在 LingMind 应用中关联账号，或运行“设置”并提供环境编码。
Connect 按编码发现环境，引导用户在对应 Phoenix 登录；每个环境独立授权。
没有预置账号或默认环境。只连接一个环境时可作为默认；连接多个环境时按编码选择，
请求未指定编码则先澄清。切换后先验证 `context_get`，再查询业务数据。
Operator 使用同一个已注册运维 App，独立登录，操作前明确目标环境。

## Codex 与云端 dots：连接相同，安装身份仍不同

GitHub 是源码及安装目录，App 是平台托管的连接。两者不能相互代替：

- 本地 Codex 可以从 GitHub 安装这两个包并使用现有 App 的账号连接，但它们是额外的插件安装，
  不会替代账号中的 canonical 云端插件。不要同时启用两套同名插件。
- 云端 dots 使用同两个 App 对应的现有云端插件；更新其技能，不新建同名包装插件。
- 支持工作区 GitHub 同步时，管理员可通过目录条目的 `pluginId` 把现有工作区插件迁移到 GitHub 管理，保留原 ID；
  不能把私人插件 ID 直接用于另一工作区，也不能通过个人 Codex 市场注册自动完成云端导入。
- 当前绑定的是私人 App。仓库公开不代表 App 已向其他用户开放；其他账号必须具有 App 访问权限。
  本次不改变分享范围，也不申请公共目录审核。

这条工作区迁移能力不等于私人 USER App 可以迁移；当前两个 App 均为私人开发模式，尚未验证有对应迁移入口。
详情参见 [身份与验收限制](app-identity-limitations.md)。

不要同时安装 App 的旧同名包装、仓库副本或本机 MCP 版。升级前确认来源，只保留两个已启用入口。
旧版设置助手生成的 `lingmind-<code>` MCP 连接不会因插件升级自动删除；核对后通过宿主
连接管理移除重复连接，保留用户其他服务和已有 App 授权。

## 更新与维护

```bash
codex plugin marketplace upgrade lingmind-annex
make render-repository-plugins PYTHON=/path/to/python3.11
make validate-repository-plugins PYTHON=/path/to/python3.11
```

刷新市场后更新两个插件，按宿主提示重新加载。源码 `plugins/` 拥有版本及技能；
`distributions/codex/plugins/` 是检查入库的派生包。App ID 不随版本更换。
云端 canonical 插件使用 `platforms/codex/canonical-cloud-plugins.json` 保留已有身份，
通过 `scripts/package-cloud-plugins.py --connection-mode account` 更新。
App 自有展示信息与仓库包展示信息由不同入口管理，不能用包字段宣称云端元数据已更新。

官方说明：[App 映射与 GitHub 管理](https://learn.chatgpt.com/docs/enterprise/plugin-management)。
