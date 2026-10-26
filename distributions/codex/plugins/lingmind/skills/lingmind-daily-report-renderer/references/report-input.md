# UAV Input Schema

Use this schema for a UAV operations daily report.

## Required fields

```json
{
  "report_type": "uav",
  "report_date": "2026-03-09",
  "line_name": "无人机项目",
  "sites": [
    {
      "name": "站点A",
      "mission_status": "success",
      "upload_status": "success",
      "mission_count": 2,
      "uploaded_batches": 2,
      "failure_reason": "",
      "notes": ""
    },
    {
      "name": "站点B",
      "mission_status": "failed",
      "upload_status": "partial",
      "mission_count": 2,
      "uploaded_batches": 1,
      "failure_reason": "任务执行失败，现场风速超限。",
      "notes": "已通知现场等待补飞窗口。"
    }
  ],
  "overall_notes": "当日两站点均有自动任务安排。"
}
```

## Status values

- `mission_status`: prefer `success` or `failed`
- `upload_status`: prefer `success` or `failed`

The renderer also accepts aliases such as `正常`, `失败`, `ok`, `completed`, `error`.

## Wording rules

- Do not invent failure reasons. If a mission failed and the user did not provide a reason, write `待补充`.
- Keep the report factual and concise. Avoid marketing language.
- If the station is normal, prefer short wording such as `无异常，任务与上传状态正常。`
- If the user provides a custom `suggestion`, use it as-is. Otherwise the renderer derives a generic recommendation from the failure reason.

## Output

The renderer writes to:

`~/Desktop/`

Before each render, the renderer only replaces the existing `uav-daily-report.png` file if it already exists.

Files:

- `uav-daily-report.png`
- `report_input.json`

The workflow ends with the local image path. Do not generate an `scp` command.
