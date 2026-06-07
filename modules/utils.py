from __future__ import annotations

from datetime import date, datetime
from uuid import uuid4

THAI_MONTHS = [
    "",
    "มกราคม",
    "กุมภาพันธ์",
    "มีนาคม",
    "เมษายน",
    "พฤษภาคม",
    "มิถุนายน",
    "กรกฎาคม",
    "สิงหาคม",
    "กันยายน",
    "ตุลาคม",
    "พฤศจิกายน",
    "ธันวาคม",
]

DAY_NAMES = {
    0: "Monday",
    1: "Tuesday",
    2: "Wednesday",
    3: "Thursday",
    4: "Friday",
    5: "Saturday",
    6: "Sunday",
}


def current_day_name(today: date | None = None) -> str:
    today = today or date.today()
    return DAY_NAMES[today.weekday()]


def thai_buddhist_date(value: date | datetime | str | None = None) -> str:
    if value is None:
        value = date.today()
    if isinstance(value, str):
        value = datetime.fromisoformat(value).date()
    if isinstance(value, datetime):
        value = value.date()
    return f"{value.day} {THAI_MONTHS[value.month]} {value.year + 543}"


def make_record_id() -> str:
    return f"OBS-{datetime.now():%Y%m%d%H%M%S}-{uuid4().hex[:6].upper()}"


def normalize_text(value) -> str:
    if value is None:
        return ""
    return str(value).strip()


def score_interpretation(score: float | int | None) -> str:
    if score is None:
        return "-"
    score = float(score)
    if score <= 1.66:
        return "น้อย"
    if score <= 2.33:
        return "ปานกลาง"
    return "มาก"


def score_color(score: float | int | None) -> str:
    label = score_interpretation(score)
    return {
        "น้อย": "background-color: #fde2e2",
        "ปานกลาง": "background-color: #fff4bf",
        "มาก": "background-color: #d9f5df",
    }.get(label, "")


def truthy(value) -> bool:
    return str(value).strip().lower() in {"true", "1", "yes", "y"}
