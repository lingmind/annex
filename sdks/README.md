# SDK 使用说明

Annex 使用 `api/openapi.yaml` 生成 TypeScript、Python 和 Java 客户端。生成结果位于
`generated/`，默认不提交到 Git。

## 生成与本地安装

先生成 SDK：

```bash
make generate-sdks
```

该命令要求 `openapi-generator-cli` 已在 `PATH` 中。目标包及本地安装方式：

| 语言 | 包 | 本地安装或构建 |
| --- | --- | --- |
| TypeScript | `@lingmind/annex` | `npm install ./generated/typescript` |
| Python | `lingmind-annex` | `python -m pip install ./generated/python` |
| Java | `com.lingmind:annex:0.2.0` | `mvn -f generated/java/pom.xml install` |

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
