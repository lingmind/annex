# ZIP 1.4.0 实际安装验收（2026-10-27）

## 结论

ZIP 分发已发布并实际测试，**不是完整的跨端通过版本**。
Codex 原生 MCP 调用成功；云端 dots 无法调用；导入后 Logo 元数据缺失，两个端的 Logo 验收不通过。
企业应用类别和官网链接已保留。

发布页：https://github.com/lingmind/annex/releases/tag/codex-plugins-v1.4.0

| 项目 | Codex 原生宿主 | 云端 dots / 插件页 |
| --- | --- | --- |
| ZIP 导入、安装 | 两个已安装、启用的 ZIP 插件；无 App 依赖 | ZIP 创建成功，当前账号只保留这两个新 ZIP 插件 |
| 类别 | Business & Operations | Business & Operations |
| 官网 | https://lingmind.cn | https://lingmind.cn |
| Logo | 安装后的宿主详情中 logo/composerIcon 为 null；未通过 | 页面实见通用图标；未通过 |
| 业务调用 | beta → sandbox → beta 身份核验通过；sandbox 全部 8 条任务读取成功 | 无身份、上下文或任务查询工具，未读取数据 |
| Operator | 38 个原生工具；beta 全部 25 个命名空间、48 个 Pod 查询成功 | 页面只有“使用桌面应用打开”；dots 未取得环境或 Pod 工具 |
| 平台 App 引用 | 0 | 0 |

## Artifact provenance

- Source tag: `codex-plugins-v1.4.0`, source commit `f5e4b859d5a2de28fb8625de7cf66be2e1116e90`.
- `lingmind-1.4.0.zip`: SHA-256 `357ad239e801ac4e5c73a4b11ac4a2b12cc90430dc13cca13de8467361c823c2`.
- `lingmind-operator-1.4.0.zip`: SHA-256 `6843a3c1945e1438e9519af06caf129cfeb8dc7d304df6fd05ec7c459d36b31a`.
- Archives contain the exact generated repository packages, including hidden compatibility manifests, MCP files,
  all 10/6 skills, references, setup helper and PNG assets. No archive wrapper or `.app.json`.
- Downloaded both release assets again and verified `SHA256SUMS` before extraction and native checks.
- The source PNGs are valid 256×256 RGBA files, 8,031 bytes, alpha bounds `(32, 38, 224, 218)`.
  File presence does not establish successful ingestion of cloud icon metadata. The cause of that loss is not established.

## Runtime evidence and scope

The exact ZIPs were imported through Plugin Creator, then installed in Codex using those returned remote plugin IDs.
The native host reported the two `created-by-me-remote` identities, version 1.4.0, enabled and installed.
There were no extra `lingmind-annex` installations. Remote plugin lookup requires its backend ID, not its display name;
this was an internal test detail and was not included in user-facing prompts.

The installed ZIP business setup helper independently resolved beta and sandbox, preserving their native OAuth
configuration. This run reused the existing native OAuth grants; it did not test a completely new user's login.
Both environments published 19 tools, with no tool load error. All environment identity checks matched exactly.
Sandbox's latest five returned records were `state=ok`, `synthetic=true`, `noFlight=true`; they are not real flights.
Sandbox Vertex was unavailable, and device control was not tested.

Operator beta inspection ran at **10:16:16–10:16:23 Beijing time**: 25 namespaces, 48 Pods, 45 Running and ready,
3 normally Succeeded, zero current abnormal Pods, no pagination or access gaps. This is a read-only snapshot,
not a guarantee of future health. No business records or workloads were modified.

The cloud dots request used ordinary language asking for sandbox's latest five missions and beta's abnormal Pods.
At **10:14 Beijing time**, dots reported no callable business context/mission or Operator environment/Pod tools.
Its plugin search returned an empty result. It did not read data or use a local/REST fallback. This proves this
attempt did not execute the requested cloud reads; it does not prove an OAuth or service outage.

The web business page exposed ten skills and no business MCP connection. The Operator page exposed one native MCP
and a desktop-open link. Import success therefore must not be reported as cloud execution acceptance.

## Installation state retained

Keep only the two uploaded ZIP plugin identities installed. The old App plugins and Git marketplace installations
remain uninstalled. Do not install the Git marketplace copies alongside the ZIP identities. Created-but-uninstalled
historical records may remain in the directory; they are not active installations and have not been permanently deleted.

Release remains a **prerelease** with these limitations. No OpenAI public-directory submission or new App was created.
