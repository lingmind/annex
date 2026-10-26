#!/usr/bin/env python3

import argparse
import json
import os
import re
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
from zoneinfo import ZoneInfo

from PIL import Image, ImageDraw, ImageFont


SKILL_ROOT = Path(__file__).resolve().parent.parent
ASSETS_DIR = SKILL_ROOT / "assets"

CANVAS_WIDTH = 1080
MIN_UAV_HEIGHT = 1500
MIN_CAMERA_HEIGHT = 1920
PADDING = 44
CARD_GAP = 24
DEFAULT_OUTPUT_DIR = Path.home() / "Desktop"
DEFAULT_META_DIR = Path("/tmp/ops-daily-report-renderer/meta")
DEFAULT_CUSTOMER_LOGO_PATH = ASSETS_DIR / "customer-logo.png"
DEFAULT_CAMERA_CUSTOMER_LOGO_PATH = ASSETS_DIR / "camera-customer-logo.png"
DEFAULT_REPORT_TITLE = "无人机每日运维报告"
DEFAULT_CAMERA_REPORT_TITLE = "摄像头每日运维报告"
FINAL_REPORT_FILENAME = "uav-daily-report.png"
CAMERA_REPORT_FILENAME = "camera-daily-report.png"
CHINA_TZ = ZoneInfo("Asia/Shanghai")
DEFAULT_CAMERA_DEPARTMENT_ORDER = ["一分部", "二分部", "三分部", "临近营业线"]
DEFAULT_CAMERA_OFFLINE_REASON = "待补充"
MIN_PAST_DAY_OFFLINE_SECONDS = 10 * 60

FONT_REGULAR_CANDIDATES = [
    "/System/Library/Fonts/STHeiti Light.ttc",
    "/System/Library/Fonts/Hiragino Sans GB.ttc",
    "/System/Library/Fonts/Supplemental/Songti.ttc",
    "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
    "/Library/Fonts/Arial Unicode.ttf",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
]
FONT_BOLD_CANDIDATES = [
    "/System/Library/Fonts/STHeiti Medium.ttc",
    "/System/Library/Fonts/Hiragino Sans GB.ttc",
    "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
    "/Library/Fonts/Arial Unicode.ttf",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
]

STATUS_META = {
    "success": {"label": "正常", "bg": "#DCFCE7", "fg": "#166534", "accent": "#16A34A"},
    "failed": {"label": "失败", "bg": "#FEE2E2", "fg": "#991B1B", "accent": "#DC2626"},
    "partial": {"label": "部分成功", "bg": "#FEF3C7", "fg": "#92400E", "accent": "#F59E0B"},
    "pending": {"label": "待确认", "bg": "#E0F2FE", "fg": "#075985", "accent": "#0284C7"},
    "not_scheduled": {"label": "未排班", "bg": "#E5E7EB", "fg": "#374151", "accent": "#6B7280"},
    "unknown": {"label": "未知", "bg": "#E5E7EB", "fg": "#374151", "accent": "#6B7280"},
}

STATUS_ALIASES = {
    "ok": "success",
    "successful": "success",
    "completed": "success",
    "normal": "success",
    "success": "success",
    "fail": "failed",
    "failed": "failed",
    "error": "failed",
    "partial": "partial",
    "partially_failed": "partial",
    "pending": "pending",
    "waiting": "pending",
    "unknown": "unknown",
    "not_scheduled": "not_scheduled",
    "not-scheduled": "not_scheduled",
    "skipped": "not_scheduled",
}

CAMERA_STATUS_META = {
    "success": {"label": "正常", "bg": "#DCFCE7", "fg": "#166534", "accent": "#16A34A"},
    "partial": {"label": "部分离线", "bg": "#FEF3C7", "fg": "#92400E", "accent": "#F59E0B"},
    "failed": {"label": "离线", "bg": "#FEE2E2", "fg": "#991B1B", "accent": "#DC2626"},
}

CAMERA_STATUS_ALIASES = {
    "success": "success",
    "normal": "success",
    "ok": "success",
    "正常": "success",
    "partial": "partial",
    "partially_failed": "partial",
    "部分离线": "partial",
    "failed": "failed",
    "fail": "failed",
    "offline": "failed",
    "离线": "failed",
}

CAMERA_DATETIME_FORMATS = [
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%d %H:%M",
    "%Y/%m/%d %H:%M:%S",
    "%Y/%m/%d %H:%M",
    "%m-%d %H:%M:%S",
    "%m-%d %H:%M",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Render Chengdu S11 UAV daily report images.")
    parser.add_argument("input_json", help="Path to the input JSON file.")
    parser.add_argument(
        "--out-dir",
        help="Output directory. Defaults to ~/Desktop/",
    )
    parser.add_argument(
        "--desktop-path",
        help="Legacy alias for output directory. Defaults to ~/Desktop/.",
    )
    return parser.parse_args()


def load_json(path: str) -> Dict:
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def normalize_status(value: str) -> str:
    raw = str(value or "").strip().lower().replace(" ", "_")
    return STATUS_ALIASES.get(raw, "unknown")


def safe_int(value) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def normalize_site(site: Dict) -> Dict:
    mission_status = normalize_status(site.get("mission_status"))
    upload_status = normalize_status(site.get("upload_status"))
    failure_reason = str(site.get("failure_reason") or "").strip()
    if not failure_reason and (mission_status == "failed" or upload_status == "failed"):
        failure_reason = "待补充"
    return {
        "name": str(site.get("name") or "未命名站点").strip(),
        "mission_status": mission_status,
        "upload_status": upload_status,
        "mission_count": safe_int(site.get("mission_count")),
        "uploaded_batches": safe_int(site.get("uploaded_batches")),
        "failure_reason": failure_reason,
        "notes": str(site.get("notes") or "").strip(),
        "suggestion": str(site.get("suggestion") or "").strip(),
        "task_name": str(site.get("task_name") or site.get("mission_name") or "").strip(),
        "task_schedule": str(site.get("task_schedule") or site.get("schedule") or "").strip(),
    }


def normalize_camera_status(value: str) -> str:
    raw = str(value or "").strip().lower().replace(" ", "_")
    return CAMERA_STATUS_ALIASES.get(raw, "failed" if raw else "success")


def parse_camera_datetime(value: str, report_date: str) -> Optional[datetime]:
    text = str(value or "").strip()
    if not text:
        return None

    report_year = datetime.now(CHINA_TZ).year
    try:
        report_year = datetime.strptime(report_date, "%Y-%m-%d").year
    except ValueError:
        pass

    for fmt in CAMERA_DATETIME_FORMATS:
        try:
            parsed = datetime.strptime(text, fmt)
            if fmt.startswith("%m-"):
                parsed = parsed.replace(year=report_year)
            return parsed
        except ValueError:
            continue
    return None


def format_duration(delta: timedelta) -> str:
    total_minutes = max(0, int(delta.total_seconds() // 60))
    days, rem_minutes = divmod(total_minutes, 1440)
    hours, minutes = divmod(rem_minutes, 60)
    parts: List[str] = []
    if days:
        parts.append(f"{days}天")
    if hours:
        parts.append(f"{hours}小时")
    if minutes or not parts:
        parts.append(f"{minutes}分钟")
    return "".join(parts)


def display_camera_datetime(value: Optional[datetime], fallback: str = "待补充") -> str:
    if value is None:
        return fallback
    return f"{value.month}-{value.day} {value.strftime('%H:%M')}"


def display_camera_time_value(raw_value: str, parsed_value: Optional[datetime], fallback: str = "待补充") -> str:
    if parsed_value is not None:
        return display_camera_datetime(parsed_value)
    raw_text = str(raw_value or "").strip()
    return raw_text or fallback


def format_camera_incident_window(incident: Dict, report_date: str) -> str:
    start_raw = incident.get("offline_start")
    end_raw = incident.get("offline_end")
    start_at = parse_camera_datetime(start_raw, report_date)
    end_at = parse_camera_datetime(end_raw, report_date)

    if start_at and end_at:
        if end_at >= start_at:
            return f"时段：{display_camera_datetime(start_at)} ~ {display_camera_datetime(end_at)}（{format_duration(end_at - start_at)}）"
        return f"时段：{display_camera_datetime(start_at)} ~ {display_camera_datetime(end_at)}"
    if start_at or str(start_raw or "").strip():
        return f"时段：{display_camera_time_value(start_raw, start_at)} ~ {display_camera_time_value(end_raw, end_at)}"
    if end_at or str(end_raw or "").strip():
        return f"时段：待补充 ~ {display_camera_time_value(end_raw, end_at)}"
    return "时段：待补充"


def format_camera_incident_names(incidents: List[Dict]) -> str:
    names = [str(incident.get("name") or "").strip() for incident in incidents]
    names = [name for name in names if name]
    if not names:
        return "无"
    return "、".join(f"{index}. {name}" for index, name in enumerate(names, start=1))


def past_day_offline_camera_date_label(report_date: str) -> str:
    try:
        previous_day = datetime.strptime(str(report_date or "").strip(), "%Y-%m-%d") - timedelta(days=1)
    except ValueError:
        return ""
    return f"{previous_day.month}月{previous_day.day}日"


def past_day_offline_camera_title(count: int) -> str:
    return f"过去一天离线过的摄像头（{count}台）"


def safe_float(value) -> float:
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0


def format_offline_duration_seconds(value) -> str:
    seconds = max(0, int(safe_float(value)))
    return format_duration(timedelta(seconds=seconds))


def is_significant_past_day_offline(record: Dict) -> bool:
    return safe_float(record.get("offline_duration_seconds") or record.get("duration_seconds") or record.get("offlineDurationSeconds")) > MIN_PAST_DAY_OFFLINE_SECONDS


def normalize_past_day_offline_camera(record) -> Dict:
    if isinstance(record, dict):
        if "incident" in record and isinstance(record["incident"], dict):
            incident = normalize_camera_incident(record["incident"])
            department = str(record.get("department") or record.get("department_name") or "未分配工点").strip()
        else:
            normalized = normalize_camera_alert_record(record)
            incident = normalized["incident"]
            department = normalized["department"]
        return {
            "department": department or "未分配工点",
            "name": incident["name"],
            "offline_duration_seconds": safe_float(record.get("offline_duration_seconds") or record.get("duration_seconds") or record.get("offlineDurationSeconds")),
        }

    text = str(record or "").strip()
    return {"department": "未分配工点", "name": text or "待补充", "offline_duration_seconds": 0}


def normalize_past_day_offline_cameras(raw: Dict) -> List[Dict]:
    records = (
        raw.get("past_day_offline_cameras")
        or raw.get("last_day_offline_cameras")
        or raw.get("past_day_alert_records")
        or raw.get("last_day_alert_records")
        or []
    )
    if isinstance(records, dict):
        records = [records]

    normalized: List[Dict] = []
    seen = set()
    for record in records:
        if isinstance(record, dict) and isinstance(record.get("cameras"), list):
            department = str(record.get("department") or record.get("name") or "未分配工点").strip()
            for camera in record["cameras"]:
                item = normalize_past_day_offline_camera({"department": department, **(camera if isinstance(camera, dict) else {"name": camera})})
                if not is_significant_past_day_offline(item):
                    continue
                key = (item["department"], item["name"])
                if key not in seen:
                    seen.add(key)
                    normalized.append(item)
            continue

        item = normalize_past_day_offline_camera(record)
        if not is_significant_past_day_offline(item):
            continue
        key = (item["department"], item["name"])
        if key in seen:
            continue
        seen.add(key)
        normalized.append(item)
    return normalized


def format_past_day_offline_camera_lines(records: List[Dict]) -> List[str]:
    if not records:
        return ["无"]

    groups: Dict[str, List[Dict]] = {}
    order: List[str] = []
    for record in records:
        department = str(record.get("department") or "未分配工点").strip()
        name = str(record.get("name") or "待补充").strip()
        if department not in groups:
            groups[department] = []
            order.append(department)
        if not any(str(item.get("name") or "") == name for item in groups[department]):
            groups[department].append({"name": name, "offline_duration_seconds": record.get("offline_duration_seconds")})

    lines: List[str] = []
    ordered_departments = [department for department in DEFAULT_CAMERA_DEPARTMENT_ORDER if department in groups]
    ordered_departments.extend(department for department in order if department not in DEFAULT_CAMERA_DEPARTMENT_ORDER)
    for department in ordered_departments:
        lines.append(department)
        for index, item in enumerate(groups[department], start=1):
            duration = format_offline_duration_seconds(item.get("offline_duration_seconds"))
            lines.append(f"{index}. {item['name']}（累计离线：{duration}）")
    return lines


def pick_first_text(item: Dict, keys: List[str]) -> str:
    for key in keys:
        value = item.get(key)
        if value is None:
            continue
        text = str(value).strip()
        if text:
            return text
    return ""


def infer_camera_alert_name(record: Dict) -> str:
    direct = pick_first_text(record, ["name", "camera_name", "camera", "device_name", "worksite", "site", "point"])
    if direct:
        return direct

    title = pick_first_text(record, ["title", "alert_title", "alarm_title", "message", "content"])
    if not title:
        return "待补充"

    cleaned = re.sub(r"^\s*(设备|摄像头|相机)?\s*离线\s*[:：]\s*", "", title).strip()
    return cleaned or title


def infer_camera_alert_department(record: Dict, incident_name: str) -> str:
    department = pick_first_text(record, ["department", "department_name", "section", "branch", "branch_name", "division"])
    if department:
        return department
    return pick_first_text(record, ["worksite_group", "group"]) or incident_name or "未分配工点"


def normalize_camera_alert_record(record) -> Dict:
    if not isinstance(record, dict):
        return {
            "department": str(record or "").strip() or "未分配工点",
            "incident": normalize_camera_incident(record),
        }

    incident_name = infer_camera_alert_name(record)
    start_at = pick_first_text(
        record,
        ["offline_start", "trigger_time", "triggered_at", "created_at", "start", "start_time", "time"],
    )
    end_at = pick_first_text(
        record,
        ["offline_end", "resolved_time", "recovered_at", "handled_at", "end", "end_time"],
    )
    status = pick_first_text(record, ["status", "state", "resolution"])
    reason = pick_first_text(record, ["reason", "failure_reason", "cause"])
    if not reason:
        reason = DEFAULT_CAMERA_OFFLINE_REASON

    return {
        "department": infer_camera_alert_department(record, incident_name),
        "incident": normalize_camera_incident(
            {
                "name": incident_name,
                "offline_start": start_at,
                "offline_end": end_at,
                "reason": reason,
            }
        ),
    }


def normalize_camera_incident(item) -> Dict:
    if isinstance(item, dict):
        name = str(item.get("name") or item.get("camera_name") or item.get("camera") or "待补充").strip()
        start_at = str(item.get("offline_start") or item.get("start") or item.get("start_time") or "").strip()
        end_at = str(item.get("offline_end") or item.get("end") or item.get("end_time") or "").strip()
        reason = str(item.get("reason") or item.get("failure_reason") or item.get("cause") or "").strip()
    else:
        name = str(item or "").strip() or "待补充"
        start_at = ""
        end_at = ""
        reason = ""

    return {
        "name": name,
        "offline_start": start_at,
        "offline_end": end_at,
        "reason": reason or DEFAULT_CAMERA_OFFLINE_REASON,
    }


def normalize_camera_department(department: Dict) -> Dict:
    incidents_raw = department.get("incidents") or department.get("offline_events") or department.get("offline_details")
    incidents: List[Dict] = []
    if incidents_raw:
        if isinstance(incidents_raw, list):
            incidents = [normalize_camera_incident(item) for item in incidents_raw]
        else:
            incidents = [normalize_camera_incident(incidents_raw)]
    else:
        offline_raw = department.get("offline_cameras") or department.get("offline_items") or department.get("detail") or ""
        if isinstance(offline_raw, list):
            incidents = [normalize_camera_incident(item) for item in offline_raw if str(item).strip()]
        elif str(offline_raw or "").strip():
            incidents = [normalize_camera_incident(offline_raw)]

    status = normalize_camera_status(department.get("status"))
    if not department.get("status"):
        status = "partial" if incidents else "success"
    if status in {"failed", "partial"} and not incidents:
        incidents = [normalize_camera_incident({"name": "待补充"})]

    offline_detail = "、".join(incident["name"] for incident in incidents if incident["name"]) or "无"

    return {
        "name": str(department.get("name") or "未命名分部").strip(),
        "status": status,
        "offline_detail": offline_detail,
        "offline_count": len(incidents),
        "incidents": incidents,
    }


def add_incident_to_department(departments: List[Dict], department_name: str, incident: Dict) -> None:
    normalized_name = str(department_name or "").strip() or "未分配工点"
    for department in departments:
        if department["name"] == normalized_name:
            department["incidents"].append(incident)
            break
    else:
        departments.append(
            {
                "name": normalized_name,
                "status": "partial",
                "offline_detail": "无",
                "offline_count": 0,
                "incidents": [incident],
            }
        )


def finalize_camera_department(department: Dict) -> Dict:
    incidents = department["incidents"]
    if incidents and department["status"] == "success":
        department["status"] = "partial"
    department["offline_detail"] = "、".join(incident["name"] for incident in incidents if incident["name"]) or "无"
    department["offline_count"] = len(incidents)
    return department


def normalize_camera_departments(raw: Dict) -> List[Dict]:
    departments = [normalize_camera_department(department) for department in raw.get("departments", raw.get("sites", []))]
    alert_records = raw.get("alert_records") or raw.get("alarm_records") or raw.get("alerts") or []
    if isinstance(alert_records, dict):
        alert_records = [alert_records]

    for record in alert_records:
        normalized = normalize_camera_alert_record(record)
        add_incident_to_department(departments, normalized["department"], normalized["incident"])

    return [finalize_camera_department(department) for department in departments]


def order_sites(sites: List[Dict]) -> List[Dict]:
    return sites


def order_departments(departments: List[Dict]) -> List[Dict]:
    return departments


def detect_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    candidates = FONT_BOLD_CANDIDATES if bold else FONT_REGULAR_CANDIDATES
    for font_path in candidates:
        if os.path.exists(font_path):
            return ImageFont.truetype(font_path, size=size)
    return ImageFont.load_default()


def draw_text(draw: ImageDraw.ImageDraw, xy, text: str, font, fill: str, anchor: str = "la") -> None:
    draw.text(xy, text, font=font, fill=fill, anchor=anchor)


def wrap_text(draw: ImageDraw.ImageDraw, text: str, font, max_width: int, max_lines: int) -> List[str]:
    if not text:
        return []

    lines: List[str] = []
    current = ""
    for char in text:
        candidate = current + char
        if draw.textlength(candidate, font=font) <= max_width:
            current = candidate
            continue
        if current:
            lines.append(current)
        current = char
        if len(lines) == max_lines:
            break

    if current and len(lines) < max_lines:
        lines.append(current)

    if len(lines) > max_lines:
        lines = lines[:max_lines]

    if lines and len(lines) == max_lines and sum(len(line) for line in lines) < len(text):
        trimmed = lines[-1]
        while trimmed and draw.textlength(trimmed + "…", font=font) > max_width:
            trimmed = trimmed[:-1]
        lines[-1] = (trimmed or lines[-1][: max(1, len(lines[-1]) - 1)]) + "…"
    return lines


def draw_wrapped_text(
    draw: ImageDraw.ImageDraw,
    x: int,
    y: int,
    text: str,
    font,
    fill: str,
    max_width: int,
    max_lines: int,
    line_gap: int = 8,
) -> int:
    lines = wrap_text(draw, text, font, max_width, max_lines)
    if not lines:
        return y

    line_height = font.size + line_gap
    current_y = y
    for line in lines:
        draw.text((x, current_y), line, font=font, fill=fill)
        current_y += line_height
    return current_y - line_gap


def rounded_box(draw: ImageDraw.ImageDraw, box, fill: str, outline: str = "", radius: int = 24, width: int = 1) -> None:
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline or None, width=width)


def draw_chip(draw: ImageDraw.ImageDraw, x: int, y: int, label: str, status_key: str, font) -> int:
    meta = STATUS_META[status_key]
    return draw_chip_with_meta(draw, x, y, label, meta, font)


def draw_chip_with_meta(draw: ImageDraw.ImageDraw, x: int, y: int, label: str, meta: Dict, font) -> int:
    text_width = draw.textlength(label, font=font)
    chip_width = int(text_width) + 28
    chip_height = font.size + 14
    rounded_box(draw, (x, y, x + chip_width, y + chip_height), fill=meta["bg"], radius=chip_height // 2)
    draw.text((x + chip_width / 2, y + chip_height / 2), label, font=font, fill=meta["fg"], anchor="mm")
    return chip_width


def draw_status_row(
    draw: ImageDraw.ImageDraw,
    x: int,
    center_y: int,
    label: str,
    status_key: str,
    label_font,
    chip_font,
    gap: int = 20,
) -> None:
    label_width = int(draw.textlength(label, font=label_font))
    chip_height = chip_font.size + 14
    draw_text(draw, (x, center_y), label, label_font, "#64748B", anchor="lm")
    chip_x = x + label_width + gap
    chip_y = center_y - chip_height // 2
    draw_chip(draw, chip_x, chip_y, status_label(status_key), status_key, chip_font)


def draw_status_row_with_meta(
    draw: ImageDraw.ImageDraw,
    x: int,
    center_y: int,
    label: str,
    meta: Dict,
    label_font,
    chip_font,
    gap: int = 20,
) -> None:
    label_width = int(draw.textlength(label, font=label_font))
    chip_height = chip_font.size + 14
    draw_text(draw, (x, center_y), label, label_font, "#64748B", anchor="lm")
    chip_x = x + label_width + gap
    chip_y = center_y - chip_height // 2
    draw_chip_with_meta(draw, chip_x, chip_y, meta["label"], meta, chip_font)


def draw_inline_row(
    draw: ImageDraw.ImageDraw,
    x: int,
    center_y: int,
    text: str,
    font,
    fill: str = "#64748B",
) -> None:
    draw_text(draw, (x, center_y), text, font, fill, anchor="lm")


def site_row_centers(card_top: int, card_height: int) -> List[int]:
    content_top = card_top + 30
    content_bottom = card_top + card_height - 28
    step = (content_bottom - content_top) / 3
    return [round(content_top + step * index) for index in range(4)]


def three_row_centers(card_top: int, card_height: int) -> List[int]:
    content_top = card_top + 30
    content_bottom = card_top + card_height - 28
    step = (content_bottom - content_top) / 2
    return [round(content_top + step * index) for index in range(3)]


def status_label(status_key: str) -> str:
    return STATUS_META[status_key]["label"]


def derive_overall_status(sites: List[Dict]) -> str:
    if any(site["mission_status"] == "failed" or site["upload_status"] == "failed" for site in sites):
        return "failed"
    if any(site["mission_status"] == "partial" or site["upload_status"] == "partial" for site in sites):
        return "partial"
    if all(site["mission_status"] == "success" and site["upload_status"] == "success" for site in sites):
        return "success"
    return "pending"


def derive_site_overall_status(site: Dict) -> str:
    mission_status = site["mission_status"]
    upload_status = site["upload_status"]
    if mission_status == "failed" or upload_status == "failed":
        return "failed"
    if mission_status in {"partial", "pending", "unknown", "not_scheduled"} or upload_status in {"partial", "pending", "unknown", "not_scheduled"}:
        return "partial"
    if mission_status == "success" and upload_status == "success":
        return "success"
    return "pending"


def mission_result_label(status_key: str) -> str:
    if status_key == "success":
        return "工人正常施工"
    if status_key == "failed":
        return "无人机巡检异常"
    if status_key == "partial":
        return "无人机巡检部分异常"
    if status_key == "not_scheduled":
        return "无人机巡检未执行"
    return "无人机巡检待确认"


def derive_suggestion(site: Dict) -> str:
    if site["suggestion"]:
        return site["suggestion"]

    reason = site["failure_reason"]
    if not reason:
        return "保持现有自动任务编排，继续观察次日任务与上传稳定性。"
    lowered = reason.lower()
    if "天气" in reason or "wind" in lowered or "rain" in lowered:
        return "关注天气窗口，必要时调整起飞时段并补飞缺失任务。"
    if "电" in reason or "battery" in lowered:
        return "复核电池健康度、起飞前电量阈值和备电准备情况。"
    if "网络" in reason or "上传" in reason or "link" in lowered:
        return "核查链路连通性、上传队列和边缘侧存储余量。"
    if "权限" in reason or "审批" in reason:
        return "补齐飞行审批和作业前置条件，恢复后补执行当日任务。"
    return "复盘飞行日志和任务编排配置，完成原因定位后安排补飞。"


def create_canvas(height: int) -> Image.Image:
    image = Image.new("RGB", (CANVAS_WIDTH, height), "#F5F7FB")
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 0, CANVAS_WIDTH, 220), fill="#EAF2FF")
    draw.rounded_rectangle((CANVAS_WIDTH - 320, -120, CANVAS_WIDTH + 120, 220), radius=140, fill="#D6E7FF")
    draw.rounded_rectangle((-140, height - 260, 320, height + 80), radius=180, fill="#E7F8F0")
    return image


def resize_logo(logo_path: Path, max_width: int, max_height: int) -> Optional[Image.Image]:
    if not logo_path.exists():
        return None

    logo = Image.open(logo_path).convert("RGBA")
    scale = min(1.0, max_width / logo.width, max_height / logo.height)
    resized = logo.resize((int(logo.width * scale), int(logo.height * scale)), Image.LANCZOS)
    return resized


def add_top_customer_logo(
    image: Image.Image,
    customer_logo_path: Path = DEFAULT_CUSTOMER_LOGO_PATH,
    align_center_y: int = 80,
) -> None:
    customer_logo = resize_logo(customer_logo_path, max_width=220, max_height=88)
    if customer_logo is None:
        return

    logo_y = round(align_center_y - customer_logo.height / 2)
    image.paste(customer_logo, (PADDING, logo_y), customer_logo)


def extract_logo_wordmark(logo_path: Path) -> Optional[Image.Image]:
    if not logo_path.exists():
        return None

    logo = Image.open(logo_path).convert("RGBA")
    crop_top = int(logo.height * 0.60)
    wordmark = logo.crop((0, crop_top, logo.width, logo.height))
    bbox = wordmark.getbbox()
    if bbox is None:
        return None
    return wordmark.crop(bbox)


def add_top_brand_wordmark(image: Image.Image, logo_path: Path) -> None:
    wordmark = extract_logo_wordmark(logo_path)
    if wordmark is None:
        return

    scale = min(1.0, 200 / wordmark.width, 54 / wordmark.height)
    resized = wordmark.resize((int(wordmark.width * scale), int(wordmark.height * scale)), Image.LANCZOS)
    x = CANVAS_WIDTH - PADDING - resized.width
    y = 28 + max(0, (54 - resized.height) // 2)
    image.paste(resized, (x, y), resized)


def draw_header(draw: ImageDraw.ImageDraw, report: Dict, title_font, subtitle_font, page_subtitle: str) -> None:
    draw_text(draw, (CANVAS_WIDTH / 2, 64), report["report_title"], title_font, "#0F172A", anchor="ma")
    if page_subtitle:
        draw_text(draw, (CANVAS_WIDTH / 2, 130), page_subtitle, subtitle_font, "#475569", anchor="ma")


def draw_header_title(draw: ImageDraw.ImageDraw, report_title: str, title_font, subtitle_font, page_subtitle: str) -> None:
    draw_text(draw, (CANVAS_WIDTH / 2, 64), report_title, title_font, "#0F172A", anchor="ma")
    if page_subtitle:
        draw_text(draw, (CANVAS_WIDTH / 2, 130), page_subtitle, subtitle_font, "#475569", anchor="ma")


def draw_header_with_token(draw: ImageDraw.ImageDraw, report_title: str, token: str, title_font, subtitle_font, page_subtitle: str) -> None:
    if token not in report_title:
        draw_header_title(draw, report_title, title_font, subtitle_font, page_subtitle)
        return

    prefix, suffix = report_title.split(token, 1)
    prefix_width = draw.textlength(prefix, font=title_font)
    token_width = draw.textlength(token, font=title_font)
    suffix_width = draw.textlength(suffix, font=title_font)
    total_width = prefix_width + token_width + suffix_width
    start_x = (CANVAS_WIDTH - total_width) / 2

    draw_text(draw, (start_x, 64), prefix, title_font, "#0F172A", anchor="la")
    draw_text(draw, (start_x + prefix_width, 67), token, title_font, "#0F172A", anchor="la")
    draw_text(draw, (start_x + prefix_width + token_width, 64), suffix, title_font, "#0F172A", anchor="la")

    if page_subtitle:
        draw_text(draw, (CANVAS_WIDTH / 2, 130), page_subtitle, subtitle_font, "#475569", anchor="ma")


def get_title_center_y(draw: ImageDraw.ImageDraw, report_title: str, title_font, token: Optional[str] = None) -> int:
    if not token or token not in report_title:
        left, top, right, bottom = draw.textbbox((CANVAS_WIDTH / 2, 64), report_title, font=title_font, anchor="ma")
        return round((top + bottom) / 2)

    prefix, suffix = report_title.split(token, 1)
    prefix_width = draw.textlength(prefix, font=title_font)
    token_width = draw.textlength(token, font=title_font)
    suffix_width = draw.textlength(suffix, font=title_font)
    total_width = prefix_width + token_width + suffix_width
    start_x = (CANVAS_WIDTH - total_width) / 2

    boxes = [
        draw.textbbox((start_x, 64), prefix, font=title_font, anchor="la"),
        draw.textbbox((start_x + prefix_width, 67), token, font=title_font, anchor="la"),
        draw.textbbox((start_x + prefix_width + token_width, 64), suffix, font=title_font, anchor="la"),
    ]
    top = min(box[1] for box in boxes)
    bottom = max(box[3] for box in boxes)
    return round((top + bottom) / 2)


def draw_uav_header(draw: ImageDraw.ImageDraw, report_title: str, title_font, subtitle_font, page_subtitle: str) -> None:
    draw_header_with_token(draw, report_title, "S11", title_font, subtitle_font, page_subtitle)


def draw_camera_header(draw: ImageDraw.ImageDraw, report_title: str, title_font, subtitle_font, page_subtitle: str) -> None:
    draw_header_with_token(draw, report_title, "16", title_font, subtitle_font, page_subtitle)


def clear_previous_images(out_dir: Path, final_filename: str) -> None:
    target_path = out_dir / final_filename
    if target_path.exists():
        target_path.unlink()


def resolve_output_dir(raw_path: Optional[str]) -> Path:
    candidate = str(raw_path or "").strip().strip("'\"")
    if not candidate:
        return DEFAULT_OUTPUT_DIR
    if ":\\" in candidate or candidate.startswith("C:/") or candidate.startswith("D:/"):
        return DEFAULT_OUTPUT_DIR
    return Path(candidate).expanduser()


def display_report_date(report_date: str) -> str:
    try:
        parsed = datetime.strptime(report_date, "%Y-%m-%d")
        return f"{parsed.year}-{parsed.month}-{parsed.day}"
    except ValueError:
        return report_date


def display_report_datetime(report_datetime: str) -> str:
    try:
        parsed = datetime.strptime(report_datetime, "%Y-%m-%d %H:%M:%S")
        return f"{parsed.year}-{parsed.month}-{parsed.day} {parsed.strftime('%H:%M:%S')}"
    except ValueError:
        return report_datetime


def render_uav_report(report: Dict) -> Image.Image:
    sites = report["sites"]
    card_heights = [460 for _ in sites]
    cards_top = 456
    footer_margin = 136
    canvas_height = max(MIN_UAV_HEIGHT, cards_top + sum(card_heights) + max(0, len(card_heights) - 1) * CARD_GAP + footer_margin)

    image = create_canvas(canvas_height)
    draw = ImageDraw.Draw(image)

    title_font = detect_font(54, bold=True)
    subtitle_font = detect_font(28)
    label_font = detect_font(32)
    body_font = detect_font(40)
    chip_font = detect_font(30, bold=True)
    small_font = detect_font(28)
    detail_font = detect_font(26)
    add_top_customer_logo(image, DEFAULT_CUSTOMER_LOGO_PATH, align_center_y=get_title_center_y(draw, report["report_title"], title_font, token="S11"))

    header_datetime = str(report.get("generated_at") or "").strip()
    window_start = str(report.get("window_start") or "").strip()
    window_end = str(report.get("window_end") or "").strip()
    if window_start or window_end:
        start_text = display_report_datetime(window_start) if window_start else "待补充"
        end_text = display_report_datetime(window_end) if window_end else "待补充"
        page_subtitle = f"统计窗口：{start_text} 至 {end_text}"
    else:
        page_subtitle = f"日期：{display_report_datetime(header_datetime)}"
    draw_uav_header(draw, report["report_title"], title_font, subtitle_font, page_subtitle)

    rounded_box(draw, (PADDING, 214, CANVAS_WIDTH - PADDING, 410), fill="#FFFFFF", radius=28)
    draw_text(draw, (PADDING + 30, 246), "当日概览", body_font, "#0F172A")

    mission_abnormal_count = sum(1 for site in sites if site["mission_status"] != "success")
    if mission_abnormal_count == 0:
        summary_text = "统计窗口内各站点自动任务执行正常。"
    else:
        summary_text = f"任务异常站点 {mission_abnormal_count} / {len(sites)}"
    draw_wrapped_text(draw, PADDING + 30, 320, summary_text, subtitle_font, "#334155", CANVAS_WIDTH - PADDING * 2 - 60, 2, line_gap=10)

    current_top = cards_top
    for index, site in enumerate(sites):
        left = PADDING
        top = current_top
        card_height = card_heights[index]
        right = CANVAS_WIDTH - PADDING
        site_status = derive_site_overall_status(site)
        accent = STATUS_META[site_status]["accent"]
        rounded_box(draw, (left, top, right, top + card_height), fill="#FFFFFF", radius=28)
        draw.rounded_rectangle((left, top, left + 10, top + card_height), radius=12, fill=accent)

        draw_text(draw, (left + 32, top + 66), site["name"], body_font, "#0F172A", anchor="lm")
        draw_status_row_with_meta(draw, left + 32, top + 158, "站点无人机状态", STATUS_META[site_status], label_font, chip_font)
        draw_text(draw, (left + 32, top + 232), "自动任务", small_font, "#64748B")

        task_name = site["task_name"] or "待补充"
        task_schedule = site["task_schedule"] or "待补充"
        mission_result = mission_result_label(site["mission_status"])
        detail_width = right - left - 64
        task_cursor_y = top + 272
        task_cursor_y = draw_wrapped_text(
            draw,
            left + 32,
            task_cursor_y,
            f"任务名称：{task_name}",
            detail_font,
            "#334155",
            detail_width,
            2,
            line_gap=6,
        ) + 10
        task_cursor_y = draw_wrapped_text(
            draw,
            left + 32,
            task_cursor_y,
            f"执行时间：{task_schedule}",
            detail_font,
            "#334155",
            detail_width,
            2,
            line_gap=6,
        ) + 10
        draw_wrapped_text(
            draw,
            left + 32,
            task_cursor_y,
            f"今日无人机巡检结果：{mission_result}",
            detail_font,
            "#334155",
            detail_width,
            2,
            line_gap=6,
        )

        draw_text(draw, (left + 32, top + 388), "无人机异常原因", small_font, "#64748B")
        draw_wrapped_text(
            draw,
            left + 32,
            top + 428,
            site["failure_reason"] or "无",
            detail_font,
            "#334155",
            detail_width,
            2,
            line_gap=6,
        )
        current_top += card_height + CARD_GAP

    draw_text(
        draw,
        (CANVAS_WIDTH / 2, canvas_height - 46),
        f"运维报告日期：{display_report_datetime(report['generated_at'])}",
        small_font,
        "#64748B",
        anchor="ma",
    )

    return image


def render_camera_report(report: Dict) -> Image.Image:
    departments = report["departments"]
    past_day_cameras = report.get("past_day_offline_cameras") or []
    past_day_lines = format_past_day_offline_camera_lines(past_day_cameras) if past_day_cameras else []
    card_heights = [max(320, 290 + department["offline_count"] * 138) for department in departments]
    cards_top = 456
    footer_margin = 136
    title_font = detect_font(54, bold=True)
    subtitle_font = detect_font(28)
    label_font = detect_font(32)
    body_font = detect_font(40)
    chip_font = detect_font(30, bold=True)
    small_font = detect_font(28)
    detail_font = detect_font(26)
    past_day_font = detect_font(24)
    max_detail_width = CANVAS_WIDTH - PADDING * 2 - 64
    temp_draw = ImageDraw.Draw(Image.new("RGB", (CANVAS_WIDTH, 120), "#FFFFFF"))
    past_day_text_height = 0
    for line in past_day_lines:
        wrapped_line_count = max(1, len(wrap_text(temp_draw, line, past_day_font, max_detail_width, 3)))
        past_day_text_height += wrapped_line_count * (past_day_font.size + 8) + 18
    past_day_section_height = 0
    if past_day_lines:
        past_day_section_height = max(260, 132 + past_day_text_height)

    canvas_height = max(
        MIN_CAMERA_HEIGHT,
        cards_top
        + sum(card_heights)
        + max(0, len(card_heights) - 1) * CARD_GAP
        + (CARD_GAP + past_day_section_height if past_day_section_height else 0)
        + footer_margin,
    )

    image = create_canvas(canvas_height)
    draw = ImageDraw.Draw(image)
    add_top_customer_logo(image, DEFAULT_CAMERA_CUSTOMER_LOGO_PATH, align_center_y=get_title_center_y(draw, report["report_title"], title_font, token="16"))

    header_datetime = str(report.get("generated_at") or "").strip()
    window_start = str(report.get("window_start") or "").strip()
    window_end = str(report.get("window_end") or "").strip()
    if window_start or window_end:
        start_text = display_report_datetime(window_start) if window_start else "待补充"
        end_text = display_report_datetime(window_end) if window_end else "待补充"
        page_subtitle = f"统计窗口：{start_text} 至 {end_text}"
    else:
        page_subtitle = f"日期：{display_report_datetime(header_datetime)}"
    draw_camera_header(draw, report["report_title"], title_font, subtitle_font, page_subtitle)

    rounded_box(draw, (PADDING, 214, CANVAS_WIDTH - PADDING, 410), fill="#FFFFFF", radius=28)
    draw_text(draw, (PADDING + 30, 246), "当日概览", body_font, "#0F172A")

    affected_department_count = sum(1 for department in departments if department["offline_count"] > 0)
    offline_camera_count = sum(department["offline_count"] for department in departments)
    if offline_camera_count == 0:
        summary_text = "统计窗口内未发现摄像头离线。"
    else:
        summary_text = f"离线摄像头 {offline_camera_count} 台 · 受影响分部 {affected_department_count} / {len(departments)}"
    draw_wrapped_text(draw, PADDING + 30, 320, summary_text, subtitle_font, "#334155", CANVAS_WIDTH - PADDING * 2 - 60, 2, line_gap=10)

    current_top = cards_top
    for index, department in enumerate(departments):
        left = PADDING
        top = current_top
        card_height = card_heights[index]
        right = CANVAS_WIDTH - PADDING
        meta = CAMERA_STATUS_META[department["status"]]
        rounded_box(draw, (left, top, right, top + card_height), fill="#FFFFFF", radius=28)
        draw.rounded_rectangle((left, top, left + 10, top + card_height), radius=12, fill=meta["accent"])
        draw_text(draw, (left + 32, top + 66), department["name"], body_font, "#0F172A", anchor="lm")
        draw_status_row_with_meta(draw, left + 32, top + 158, "分部状态", meta, label_font, chip_font)
        draw_text(draw, (left + 32, top + 232), "离线明细", small_font, "#64748B")

        incidents = department["incidents"]
        cursor_y = top + 272
        max_width = right - left - 64
        if not incidents:
            draw_text(draw, (left + 32, cursor_y), "无", detail_font, "#334155")
        else:
            for event_index, incident in enumerate(incidents):
                incident_title = f"{event_index + 1}. {incident['name']}"
                cursor_y = draw_wrapped_text(draw, left + 32, cursor_y, incident_title, detail_font, "#1F2937", max_width, 2, line_gap=6) + 10
                cursor_y = draw_wrapped_text(
                    draw,
                    left + 32,
                    cursor_y,
                    format_camera_incident_window(incident, report["report_date"]),
                    detail_font,
                    "#334155",
                    max_width,
                    2,
                    line_gap=6,
                ) + 10
                cursor_y = draw_wrapped_text(
                    draw,
                    left + 32,
                    cursor_y,
                    f"原因：{incident.get('reason') or DEFAULT_CAMERA_OFFLINE_REASON}",
                    detail_font,
                    "#334155",
                    max_width,
                    2,
                    line_gap=6,
                ) + 16
        current_top += card_height + CARD_GAP

    if past_day_lines:
        left = PADDING
        top = current_top
        right = CANVAS_WIDTH - PADDING
        rounded_box(draw, (left, top, right, top + past_day_section_height), fill="#FFFFFF", radius=28)
        draw.rounded_rectangle((left, top, left + 10, top + past_day_section_height), radius=12, fill="#0284C7")
        draw_text(draw, (left + 32, top + 58), past_day_offline_camera_title(len(past_day_cameras)), body_font, "#0F172A", anchor="lm")
        date_label = past_day_offline_camera_date_label(str(report.get("report_date") or ""))
        if date_label:
            draw_text(draw, (right - 32, top + 58), date_label, small_font, "#64748B", anchor="rm")
        cursor_y = top + 112
        for line in past_day_lines:
            cursor_y = draw_wrapped_text(
                draw,
                left + 32,
                cursor_y,
                line,
                past_day_font,
                "#334155",
                max_detail_width,
                3,
                line_gap=8,
            ) + 18

    draw_text(
        draw,
        (CANVAS_WIDTH / 2, canvas_height - 52),
        f"运维报告日期：{display_report_datetime(report['generated_at'])}",
        small_font,
        "#64748B",
        anchor="ma",
    )

    return image


def save_final_report(summary_image: Image.Image, out_path: Path) -> None:
    summary_image.save(out_path)


def main() -> None:
    args = parse_args()
    raw = load_json(args.input_json)

    report_type = str(raw.get("report_type") or "uav").strip().lower()
    report_date = str(raw.get("report_date") or datetime.now().strftime("%Y-%m-%d"))
    out_dir = resolve_output_dir(args.out_dir or raw.get("out_dir") or args.desktop_path or raw.get("desktop_path"))
    if report_type == "camera":
        meta_dir = DEFAULT_META_DIR / "camera" / report_date
        final_filename = CAMERA_REPORT_FILENAME
    else:
        meta_dir = DEFAULT_META_DIR / report_date
        final_filename = FINAL_REPORT_FILENAME
    out_dir.mkdir(parents=True, exist_ok=True)
    meta_dir.mkdir(parents=True, exist_ok=True)
    clear_previous_images(out_dir, final_filename)
    generated_at = datetime.now(CHINA_TZ).strftime("%Y-%m-%d %H:%M:%S")

    report = {
        "report_type": report_type,
        "report_date": report_date,
        "output_dir": out_dir.as_posix(),
        "generated_at": generated_at,
        "generated_date": datetime.now(CHINA_TZ).strftime("%Y-%m-%d"),
    }

    if report_type == "camera":
        departments = normalize_camera_departments(raw)
        past_day_offline_cameras = normalize_past_day_offline_cameras(raw)
        if not departments:
            raise SystemExit("camera report input_json must include at least one item in `departments` or `alert_records`.")
        report.update(
            {
                "line_name": str(raw.get("line_name") or "摄像头项目").strip(),
                "report_title": str(raw.get("report_title") or DEFAULT_CAMERA_REPORT_TITLE).strip(),
                "window_start": str(raw.get("window_start") or raw.get("start_time") or raw.get("report_window_start") or "").strip(),
                "window_end": str(raw.get("window_end") or raw.get("end_time") or raw.get("report_window_end") or "").strip(),
                "departments": order_departments(departments),
                "past_day_offline_cameras": past_day_offline_cameras,
            }
        )
        summary_image = render_camera_report(report)
    else:
        sites = [normalize_site(site) for site in raw.get("sites", [])]
        if not sites:
            raise SystemExit("uav report input_json must include at least one site in `sites`.")
        report.update(
            {
                "line_name": str(raw.get("line_name") or "无人机项目").strip(),
                "report_title": str(raw.get("report_title") or DEFAULT_REPORT_TITLE).strip(),
                "window_start": str(raw.get("window_start") or raw.get("start_time") or raw.get("report_window_start") or "").strip(),
                "window_end": str(raw.get("window_end") or raw.get("end_time") or raw.get("report_window_end") or "").strip(),
                "overall_notes": str(raw.get("overall_notes") or "").strip(),
                "sites": order_sites(sites),
            }
        )
        summary_image = render_uav_report(report)

    normalized_input_path = meta_dir / "report_input.json"
    normalized_input_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    final_report_path = out_dir / final_filename
    save_final_report(summary_image, final_report_path)

    result = {
        "report_date": report_date,
        "out_dir": out_dir.as_posix(),
        "output_file": final_report_path.as_posix(),
        "files": [
            final_report_path.as_posix(),
            normalized_input_path.as_posix(),
        ],
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
