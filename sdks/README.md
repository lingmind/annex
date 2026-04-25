# SDK 生成

Annex 使用 `api/openapi.yaml` 作为非 Go SDK 的协议源。

在发布流水线准备好之前，生成结果默认不提交到 git。目标包名如下：

- TypeScript: `@lingmind/annex`
- Python: `lingmind-annex`
- Java: `com.lingmind.annex`

执行：

```bash
make generate-sdks
```

该命令要求 `openapi-generator-cli` 已在 `PATH` 中。
