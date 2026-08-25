# Camera Report Input Schema

Use this schema for a camera operations daily report.

## Required fields

```json
{
  "report_type": "camera",
  "report_date": "2026-03-10",
  "window_start": "2026-03-09 00:00:00",
  "window_end": "2026-03-10 00:00:00",
  "report_title": "摄像头每日运维报告",
  "departments": [
    {
      "name": "区域A",
      "status": "success"
    },
    {
      "name": "区域B",
      "status": "partial",
      "incidents": [
        {
          "name": "摄像头A",
          "offline_start": "2026-03-09 08:12:00",
          "offline_end": "2026-03-09 09:36:00",
          "reason": "临时断电，配电恢复后上线。"
        },
        {
          "name": "摄像头B",
          "offline_start": "2026-03-09 13:30:00",
          "offline_end": "2026-03-09 15:05:00",
          "reason": "交换机端口异常，重启后恢复。"
        }
      ]
    },
    {
      "name": "区域C",
      "status": "success"
    },
    {
      "name": "区域D",
      "status": "success"
    }
  ],
  "past_day_offline_cameras": [
    {
      "title": "设备离线：掌子面",
      "department": "一分部",
      "trigger_time": "2026-03-09 21:10:00",
      "resolved_time": "2026-03-09 21:35:00",
      "status": "已解决"
    }
  ]
}
```

## Input rules

- Department order defaults to the input order.
- Camera status supports `success` / `partial` / `failed`.
- The renderer also accepts user-facing wording such as `正常`、`部分离线`、`离线`.
- Prefer filling top-level `window_start` and `window_end` to represent the statistics window (for example `3月17日 00:00:00` to `3月18日 00:00:00`).
- For abnormal departments, prefer using `incidents` with per-camera details:
  - `name`
  - `offline_start`
  - `offline_end`
  - `reason`
- The original/current report section renders `offline_start`, `offline_end`, and `reason` inside each department card.
- For the separate past-day/近 24 小时 offline camera list, put `设备离线` rows into top-level `past_day_offline_cameras` or `past_day_alert_records`:
  - `title` / `alert_title` / `alarm_title`: examples `设备离线：掌子面`, `设备离线：洗砂洗石机`.
  - `department` / `section` / `branch`: optional; when present, the record is grouped under that department in the bottom list.
  - `trigger_time` / `triggered_at` / `created_at`: accepted for normalization/metadata, but not displayed in the bottom list.
  - `resolved_time` / `recovered_at` / `handled_at`: optional recovery or handled time.
  - `offline_duration_seconds`: optional cumulative offline duration for this camera; live builder fills this automatically.
  - `status`: optional metadata; it is not displayed in the bottom list.
- Use `lingmind-business-query` with the selected environment and project context for live LingMind
  facts. Keep current/unrecovered offline alerts in `departments[].incidents` and write collapsed
  past-day unique cameras to `past_day_offline_cameras`.
- Collapse repeated past-day offline alerts by stable camera identity. One camera that was offline
  multiple times in the window appears once, under its branch/department, with clipped durations summed.
- The bottom past-day list only includes cameras whose cumulative offline duration is greater than 10 minutes. Durations of 10 minutes or less are filtered out.
- Legacy `alert_records` still merge into the original department cards for compatibility. Do not use `alert_records` for the bottom past-day list.
- Legacy fields (`offline_items`, `offline_cameras`, `detail`) are still accepted.
- If a camera offline item has no owner-returned or user-provided reason, use `待补充`.

## User shorthand

These user messages map naturally into the schema:

- `区域A摄像头正常`
- `区域B：摄像头A 08:12-09:36 离线，原因断电`
- `区域D：K12+300监控杆离线`
- `过去一天离线过的摄像头（右侧日期：6月4日）：一分部 掌子面 累计离线23分钟，二分部 洞口 累计离线1小时`

## Output

The renderer writes to:

`~/Desktop/`

Files:

- `camera-daily-report.png`
- `report_input.json`

The workflow ends with the local image path. Do not generate an `scp` command.
