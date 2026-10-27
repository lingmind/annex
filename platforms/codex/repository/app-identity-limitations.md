# App 连接复用不等于插件身份合并

## 2026-10-27 更正

1.3.0 的 Git 包可以被 Codex 解析为一个 App 依赖、零个本机 MCP 服务器，
但这只验证了包的组件，不代表界面只会显示两个插件。
本机已安装的 `lingmind@lingmind-annex`、`lingmind-operator@lingmind-annex` 与账号的两个
`plugin_asdk_app_...` canonical 插件同时启用时，Codex 会显示四个入口。
只统计本地市场的 `plugin/installed` 结果漏掉了账号侧入口；此前的“只有两个”验收不完整。

本次处理移除了两个仓库安装副本，保留原有两个云端 App、技能及独立环境连接。
没有新建 App，没有删除授权，也没有恢复废弃记录。

## 两个不同的配置所有者

| 内容 | 所有者 | 当前结果 |
| --- | --- | --- |
| Git 包显示名称、Logo、类别、网站 | 仓库 manifest 和 assets | LingMind / Business & Operations / lingmind.cn / 32px 留白 Logo |
| 云端开发 App 显示信息 | 平台 App 记录 | 开发者为账号名、类别 Other、网站不可用；Logo 使用原 App 资产 |
| 业务和 Operator 工具 | 同两个已注册 App | 复用原 App ID；云端自然语言任务查询与 Pod 查询已成功 |
| 插件安装身份 | 宿主和账号目录 | 仓库安装与云端 canonical 安装没有合并 |

已读取当前云端源文件和 App 管理页：技能更新支持修改版本、技能和引导入口；
App 自有绑定、展示信息与连接需保留。管理页当前只显示名称和描述编辑，
没有图标、类别或网站编辑控件。不能把仓库 manifest 的正确字段当成云端 App 元数据已经更新。

## 已知受支持的身份保留路径

官方文档描述了**工作区**管理员将现有插件迁移到 GitHub 管理：目录条目指定原有 `pluginId`，
保留 ID、分享和策略；插件必须属于同一工作区。当前两个 App 为 USER / PRIVATE / DEVELOPMENT，
不能把它们的 ID 填到其他工作区，也不能假定个人 Codex 市场支持此迁移。

在个人账号的单一身份迁移、App 自有元数据编辑入口得到证实前，不再创建新的包装来模拟同一身份，
不通过反复上传、重装或清缓存宣称此限制已解决。公开审核、迁移工作区或向平台发送支持请求均未在本次执行。

后续验收必须同时核对真实桌面侧栏、账号云端安装、仓库安装和 App 关联；
再分别验证工具调用与 App 自有元数据，不能用其中一个结果替代其他项目。

官方依据：[GitHub 管理与现有插件迁移](https://learn.chatgpt.com/docs/enterprise/plugin-management)。
