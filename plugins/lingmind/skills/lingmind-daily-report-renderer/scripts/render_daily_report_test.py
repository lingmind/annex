#!/usr/bin/env python3

import importlib.util
import unittest
from pathlib import Path


SCRIPT_PATH = Path(__file__).with_name("render_daily_report.py")
SPEC = importlib.util.spec_from_file_location("render_daily_report", SCRIPT_PATH)
renderer = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(renderer)


class CameraReportRendererTest(unittest.TestCase):
    def test_alert_records_merge_without_inventing_a_reason(self):
        raw = {
            "report_type": "camera",
            "report_date": "2026-06-05",
            "departments": [{"name": "一分部", "status": "正常"}],
            "alert_records": [
                {
                    "title": "设备离线：掌子面",
                    "department": "一分部",
                    "trigger_time": "2026-06-04 21:10:00",
                    "resolved_time": "2026-06-04 21:35:00",
                    "status": "已解决",
                }
            ],
        }

        departments = renderer.normalize_camera_departments(raw)
        incident = departments[0]["incidents"][0]

        self.assertEqual(departments[0]["status"], "partial")
        self.assertEqual(incident["name"], "掌子面")
        self.assertEqual(incident["reason"], "待补充")

    def test_past_day_section_collapses_to_display_rows(self):
        report = {
            "report_type": "camera",
            "report_title": "摄像头每日运维报告",
            "report_date": "2026-06-05",
            "departments": [{"name": "一分部", "status": "success", "incidents": []}],
            "past_day_offline_cameras": [
                {"department": "一分部", "name": "洞口", "offline_duration_seconds": 61 * 60},
                {"department": "二分部", "name": "短时抖动", "offline_duration_seconds": 10 * 60},
            ],
        }

        past_day = renderer.normalize_past_day_offline_cameras(report)
        lines = renderer.format_past_day_offline_camera_lines(past_day)

        self.assertEqual(len(past_day), 1)
        self.assertEqual(lines, ["一分部", "1. 洞口（累计离线：1小时1分钟）"])
        self.assertEqual(renderer.past_day_offline_camera_title(1), "过去一天离线过的摄像头（1台）")
        self.assertEqual(renderer.past_day_offline_camera_date_label("2026-06-05"), "6月4日")

    def test_camera_report_renders(self):
        report = {
            "report_type": "camera",
            "report_title": "摄像头每日运维报告",
            "report_date": "2026-06-05",
            "generated_at": "2026-06-05 10:04:54",
            "window_start": "2026-06-05 00:00:00",
            "window_end": "2026-06-05 10:04:02",
            "departments": [
                {
                    "name": "一分部",
                    "status": "partial",
                    "offline_count": 1,
                    "incidents": [{"name": "洞口", "reason": "待补充"}],
                }
            ],
        }

        image = renderer.render_camera_report(report)

        self.assertGreaterEqual(image.size[1], renderer.MIN_CAMERA_HEIGHT)


if __name__ == "__main__":
    unittest.main()
