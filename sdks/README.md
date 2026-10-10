# SDK 使用说明

Annex 使用 `api/openapi.yaml` 生成 TypeScript、Python 和 Java 客户端。生成结果位于
`generated/`，默认不提交到 Git。

## 生成与本地安装

先生成 SDK：

```bash
make generate-sdks
```

该命令要求官方生成器已在 `PATH` 中，可通过 `npm install -g @openapitools/openapi-generator-cli` 安装。
生成的客户端包含 Auth、Devices、Missions、RawData、RuleHits、Incidents、ClosedLoopActions 和 Messages。
Messages API 提供个人消息查询、单条已读和全部已读；不包含通知投递或通知规则接口。
目标包及本地安装方式：

| 语言 | 包 | 本地安装或构建 |
| --- | --- | --- |
| TypeScript | `@lingmind/annex` | `npm install ./generated/typescript` |
| Python | `lingmind-annex` | `python -m pip install ./generated/python` |
| Java | `com.lingmind:annex:0.2.0` | `mvn -f generated/java/pom.xml install` |

生成脚本在三个生成器全部成功后替换 SDK 目录，旧目录备份到 `.local/sdk-backups/`，避免旧模型残留。
本次新增接口已使用 OpenAPI Generator 7.25.0 验证。生成后可运行构建及离线请求测试：

```bash
npm --prefix generated/typescript install --ignore-scripts
../.codex-venv/bin/pip install ./generated/python
make test-generated-sdks PYTHON=../.codex-venv/bin/python
```

测试覆盖新增接口的路径、认证、项目 Header、筛选参数、处置请求体和个人消息响应，
并编译 Java SDK；不调用真实环境。Java 构建需要 JDK 11 或更高版本。

发布后应改用团队制品仓库中的固定版本，不要在生产项目中引用本地 `generated/` 目录。

## 调用前准备

样例从环境变量读取连接信息，避免把令牌或项目标识写入源码：

```bash
export LM_BASE_URL=https://phoenix.example.com
export LM_ACCESS_TOKEN=access_token_xxx
export LM_PROJECT_ID=project_document_id
```

- `LM_BASE_URL` 是 Phoenix HTTPS 根地址，不含接口路径，建议不要以 `/` 结尾。
- `LM_ACCESS_TOKEN` 可通过 `AuthApi` 的用户名密码登录、短信登录或刷新接口获得。
- `LM_PROJECT_ID` 是本次请求使用的项目 `documentId`。SDK 会将它放入
  `X-Requested-Project` Header；该项目必须在当前用户的数据权限范围内。
- 外部对象引用使用 `documentId`，不要依赖数值 `id`。
- 关系数据必须显式选择。下面的样例只展开 `project`；不要使用通配展开。

## TypeScript

完整样例：[examples/typescript/devices.ts](examples/typescript/devices.ts)

```ts
import { Configuration, DevicesApi, ResponseError } from '@lingmind/annex';

const api = new DevicesApi(new Configuration({
  basePath: process.env.LM_BASE_URL,
  accessToken: process.env.LM_ACCESS_TOKEN,
}));

const result = await api.listDevices({
  xRequestedProject: process.env.LM_PROJECT_ID,
  populate: 'project',
  paginationPageSize: 20,
});
```

运行：

```bash
npx tsx sdks/examples/typescript/devices.ts
```

查询 RuleHit 的 `evidences[].observation.detections[]`：

```bash
export LM_RULE_HIT_ID=rule_hit_document_id
npx tsx sdks/examples/typescript/rule-hit-detections.ts
```

完整样例见 [examples/typescript/rule-hit-detections.ts](examples/typescript/rule-hit-detections.ts)。
生成版 SDK 的 `populate` 字符串参数只适用于单个根字段；该样例通过 SDK 的
`withPreMiddleware` 将 `populate[evidences][populate][observation][populate][0]=detections`
作为独立查询参数添加到 `getRuleHit` 请求。返回值沿
`response.data.evidences[].observation.detections[]` 读取。若还要展开 Observation
中的其他组件，可在同一 middleware 里用 `[1]`、`[2]` 追加字段。

## Python

完整样例：[examples/python/devices.py](examples/python/devices.py)

```python
configuration = lingmind_annex.Configuration(
    host=os.environ["LM_BASE_URL"],
    access_token=os.environ["LM_ACCESS_TOKEN"],
)

async with lingmind_annex.ApiClient(configuration) as client:
    result = await DevicesApi(client).list_devices(
        x_requested_project=os.environ["LM_PROJECT_ID"],
        populate="project",
        pagination_page_size=20,
    )
```

运行：

```bash
python sdks/examples/python/devices.py
```

## Java

完整样例：[examples/java/DevicesExample.java](examples/java/DevicesExample.java)

Java `native` 客户端通过请求拦截器添加 Bearer Header：

```java
ApiClient client = new ApiClient();
client.updateBaseUri(System.getenv("LM_BASE_URL"));
client.setRequestInterceptor(builder -> builder.header(
    "Authorization", "Bearer " + System.getenv("LM_ACCESS_TOKEN")));

DevicesApi api = new DevicesApi(client);
DeviceListResponse result = api.listDevices(
    System.getenv("LM_PROJECT_ID"), "project", 1, 20,
    null, null, null, null);
```

将示例加入使用 `com.lingmind:annex:0.2.0` 的 Java 项目后运行即可。

## 分页、筛选与错误处理

- 列表默认页大小为 25，最大为 100；生产调用应显式处理 `meta.pagination` 并逐页读取。
- 筛选参数已按各语言命名规则生成，例如 TypeScript 的 `filtersState$eq`、Python 的
  `filters_state_eq`，以及 Java `listDevices` 的对应参数。
- `401` 通常表示 access token 无效或过期；刷新令牌后重试一次，不要无限重试。
- `403` 表示用户或项目权限不足；不要改用其他项目绕过权限。
- `404` 应按目标 `documentId` 不存在或不可见处理。
- 记录错误时可保留 HTTP 状态码、响应体和请求 ID，但不要输出 access token。
