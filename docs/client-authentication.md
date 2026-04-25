# 客户端认证使用指南

本文面向需要接入 LingMind Annex 的外部客户端，包括业务系统、自动化脚本、运维终端和集成服务。

Annex SDK 和 CLI 使用 Phoenix 网关根地址作为 `baseUrl`：

```text
https://<phoenix-host>
```

不要配置或调用 `/api/annex/v1`，该路径当前不存在。Annex 客户端内部会调用 Phoenix 的真实接口：

- 认证：`/api/auth/login`、`/api/auth/refresh`、`/api/auth/logout`
- 资源查询：`/proxy/radix/api/devices`、`/proxy/radix/api/missions`、`/proxy/radix/api/raw-data`、`/proxy/radix/api/rule-hits`

客户端不要直接访问 LingMind 内部服务、数据库、对象存储或 Strapi 地址。

## 认证方式

Annex 支持两类凭证：

| 方式 | Header | 适用场景 |
| --- | --- | --- |
| Bearer token | `Authorization: Bearer <token>` | SDK、CLI、服务端集成，推荐使用 |
| API key | `X-LM-API-Key: <key>` | 固定机器到机器调用，需由 LingMind 分配和轮换 |

推荐流程：

1. 客户端使用 LingMind 用户名和密码调用 Phoenix 登录接口。
2. Phoenix 返回 `access_token`、`refresh_token`、有效期和用户上下文。
3. 客户端使用 `access_token` 调用设备、任务、原始数据和规则命中接口。
4. `access_token` 过期前，客户端使用 `refresh_token` 调用 `/api/auth/refresh`。
5. 凭证轮换或退出时，客户端调用 `/api/auth/logout`。

客户端不配置 scope。scope、项目范围和对象权限由 LingMind 管理端分配，客户端只能通过登录响应、JWT 或管理员配置查看最终授权结果。

## 项目上下文

项目上下文通过 Phoenix header 传递：

```text
X-Requested-Project-Code: <project-code>
```

如果凭证只绑定一个项目，项目上下文可以省略；如果凭证覆盖多个项目，建议显式传入项目编码。

## CLI 使用

先构建 CLI：

```bash
make build
```

登录并保存本地配置：

```bash
bin/lm --base-url https://phoenix.example.com \
  auth login \
  --username user@example.com \
  --password 'password' \
  --project demo
```

也可以用环境变量提供敏感字段，避免进入 shell history：

```bash
export LM_USERNAME=user@example.com
export LM_PASSWORD='password'
bin/lm --base-url https://phoenix.example.com auth login --project demo
```

默认配置文件：

```text
~/.lm/config.json
```

配置文件会保存 `baseUrl`、`token`、`refreshToken`、`projectCode` 和 `expiresAt`。后续命令会自动读取配置：

```bash
bin/lm devices list
bin/lm missions get mission_01HZX
bin/lm raw-data list --page-size 20
bin/lm --format json rule-hits list --severity critical
```

刷新 token：

```bash
bin/lm auth refresh
```

查看当前凭证身份：

```bash
bin/lm auth me
```

`auth me` 会在本地解析当前 JWT，不会调用不存在的 `/auth/me` 服务端接口。

退出当前 access token：

```bash
bin/lm auth revoke
```

不保存配置，只输出环境变量：

```bash
bin/lm --base-url https://phoenix.example.com \
  auth login \
  --username user@example.com \
  --password 'password' \
  --project demo \
  --format env \
  --save=false
```

可用环境变量覆盖本地配置：

```bash
export LM_BASE_URL=https://phoenix.example.com
export LM_TOKEN=access_token_xxx
export LM_REFRESH_TOKEN=refresh_token_xxx
export LM_PROJECT_CODE=demo
```

## Go SDK 使用

获取 token：

```go
authClient, err := annex.NewClient(annex.Config{
	BaseURL: "https://phoenix.example.com",
})
if err != nil {
	return err
}

token, err := authClient.CreateToken(ctx, annex.AuthTokenRequest{
	GrantType:   annex.GrantTypePassword,
	Username:    "user@example.com",
	Password:    "password",
	ProjectCode: "demo",
})
if err != nil {
	return err
}
```

使用 token 调用 API：

```go
client, err := annex.NewClient(annex.Config{
	BaseURL:     "https://phoenix.example.com",
	Token:       token.AccessToken,
	ProjectCode: token.ProjectCode,
})
if err != nil {
	return err
}

devices, err := client.ListDevices(ctx, annex.ListDevicesParams{
	ListParams: annex.ListParams{PageSize: 50},
	State:      "online",
})
if err != nil {
	return err
}
```

刷新 token：

```go
next, err := authClient.RefreshToken(ctx, annex.AuthRefreshRequest{
	RefreshToken: token.RefreshToken,
	ProjectCode:  token.ProjectCode,
})
if err != nil {
	return err
}
```

查询当前凭证：

```go
subject, err := client.AuthMe(ctx)
if err != nil {
	return err
}
```

退出 token：

```go
err = client.RevokeToken(ctx, annex.AuthRevokeRequest{
	Token: token.AccessToken,
})
```

## HTTP API 使用

直接 HTTP 调用应使用 Phoenix 真实路径。SDK/CLI 会隐藏这些细节，优先推荐使用 SDK/CLI。

登录：

```bash
curl -sS https://phoenix.example.com/api/auth/login \
  -H 'Content-Type: application/json' \
  -d '{
    "username": "user@example.com",
    "password": "password"
  }'
```

响应示例：

```json
{
  "access_token": "access_token_xxx",
  "refresh_token": "refresh_token_xxx",
  "token_type": "Bearer",
  "expires_in": 300,
  "issued_at": "2026-04-25T10:00:00Z"
}
```

调用资源接口：

```bash
curl -sS 'https://phoenix.example.com/proxy/radix/api/devices?pagination[pageSize]=20&filters[state][$eq]=online' \
  -H 'Authorization: Bearer access_token_xxx' \
  -H 'X-Requested-Project-Code: demo'
```

不要默认追加 `populate=*`。如果确实需要关系数据，应按业务场景显式指定最小关系；Annex SDK 默认不使用 `populate=*`。

刷新 token：

```bash
curl -sS https://phoenix.example.com/api/auth/refresh \
  -H 'Content-Type: application/json' \
  -d '{
    "refresh_token": "refresh_token_xxx"
  }'
```

退出：

```bash
curl -sS -X POST https://phoenix.example.com/api/auth/logout \
  -H 'Authorization: Bearer access_token_xxx'
```

## Token 刷新策略

客户端建议：

- 在 `accessToken` 过期前 5 分钟刷新。
- 多进程或多实例部署时避免同时刷新同一个 token。
- 刷新成功后立即替换旧 `accessToken`。
- 如果刷新失败且错误为 `unauthenticated`，重新执行登录。
- 不要把密码、token 或 API key 写入代码仓库、日志、前端页面或移动端包。

## 常见问题

### 返回 `unauthenticated`

常见原因：

- `Authorization` header 缺失。
- token 已过期或已退出。
- 使用了错误环境的 `baseUrl`。
- API key 已轮换。

处理方式：

```bash
bin/lm auth refresh
bin/lm auth me
```

### 返回 `permission_denied`

常见原因：

- 当前 token 缺少所需权限。
- 项目编码不在授权范围内。
- 设备、任务、原始数据或规则命中不在对象权限范围内。

处理方式：

- 使用 `bin/lm auth me` 查看当前 JWT 身份信息。
- 联系 LingMind 管理员调整项目、角色、权限或 API key。

### CLI 没有读取到配置

检查配置文件路径：

```bash
ls -l ~/.lm/config.json
```

也可以显式指定：

```bash
export LM_CONFIG=/path/to/config.json
```

## 安全建议

- 优先在服务端、CI secret 或密钥管理系统中保存密码和 token。
- 不要在浏览器前端或移动端应用内置长期凭证。
- 对自动化集成分配最小项目和最小权限。
- 生产环境启用 token 轮换和调用审计。
