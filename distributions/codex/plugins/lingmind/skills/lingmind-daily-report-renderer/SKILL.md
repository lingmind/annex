---
name: lingmind-daily-report-renderer
description: Query authorized LingMind business facts and render a UAV or camera daily operations report image on the local desktop.
---

# LingMind daily report renderer

Use this business skill for a daily UAV execution/upload summary or camera status/offline summary.
The business plugin supplies the authorized facts; the bundled renderer only turns reviewed facts
into an image.

## Context and data

1. Verify the business environment with `lingmind-environment-context`.
2. Resolve one project or an explicitly requested all-project read set with `lingmind-project-context`.
3. Use `lingmind-business-query` and runtime capability discovery for the required report facts.
4. Keep the query window, project identity, pagination completeness, and returned timestamps with the
   report input. If a required statistic or alert capability is absent, report the contract gap and
   stop; do not use a local API helper, direct REST, shell, database, or Operator tool to reconstruct it.

For UAV reports, collect the requested day's mission execution state, upload/delivery state, counts,
and owner-returned failure details. For camera reports, collect persisted device identity, the declared
status/statistics result, and bounded device-offline alert evidence. Do not infer live state from a
persisted record or invent an outage reason.

## Build the input

Write a temporary JSON document matching the report type:

- UAV: [UAV input schema](references/report-input.md)
- Camera: [camera input schema](references/camera-report-input.md)

For camera reports:

- keep the current/report-window incident cards separate from the previous-24-hour list;
- collapse repeated past-day alerts by stable camera identity;
- clip each occurrence to the requested window before summing duration;
- include a camera in the past-day list only when cumulative offline duration is greater than ten minutes;
- preserve department/project labels returned by the business tools;
- use `待补充` when the owner and user provide no reason.

Do not include tokens, credentials, signed URLs, hidden fields, or raw unbounded responses in the JSON.

## Render and verify

Run the bundled renderer from this skill directory:

```bash
python3 scripts/render_daily_report.py /tmp/lingmind-daily-report.json --out-dir "$HOME/Desktop"
```

It writes one of:

- `~/Desktop/uav-daily-report.png`
- `~/Desktop/camera-daily-report.png`

Inspect the generated image before delivery. Verify title/date, report window, counts, abnormal items,
department grouping, offline durations, reason wording, and legibility. Return the exact local image path.

The renderer may overwrite the previous image for the same report type. It must not modify LingMind
business records or trigger a device, mission, media, or runtime action.
