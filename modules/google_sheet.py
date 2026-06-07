from __future__ import annotations

import json
import os
from pathlib import Path
from urllib import request

import pandas as pd
import streamlit as st

LOG_COLUMNS = [
    "record_id",
    "timestamp",
    "date",
    "buddhist_date",
    "day_name",
    "inspector",
    "role",
    "building",
    "floor",
    "room_number",
    "class_level",
    "period",
    "teacher_name",
    "criteria_id",
    "criteria",
    "category",
    "score",
    "note",
    "is_deleted",
    "updated_at",
    "updated_by",
]

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
CSV_PATH = DATA_DIR / "data_classroom_log.csv"


def _apps_script_config() -> tuple[str, str]:
    url = os.getenv("APPS_SCRIPT_URL", "")
    token = os.getenv("APPS_SCRIPT_TOKEN", "")
    try:
        url = st.secrets.get("apps_script", {}).get("url", url)
        token = st.secrets.get("apps_script", {}).get("token", token)
    except Exception:
        pass
    return str(url).strip(), str(token).strip()


def _append_rows_to_apps_script(rows: list[dict]) -> tuple[bool, str]:
    url, token = _apps_script_config()
    if not url or not token:
        return False, "ยังไม่ได้ตั้งค่า Apps Script URL/TOKEN"

    payload = json.dumps({"token": token, "rows": rows}, ensure_ascii=False).encode("utf-8")
    req = request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with request.urlopen(req, timeout=20) as response:
            body = response.read().decode("utf-8")
        result = json.loads(body)
        if result.get("ok"):
            return True, f"บันทึกลง Google Sheet แล้ว {result.get('inserted', len(rows))} แถว"
        return False, result.get("error", body)
    except Exception as exc:
        return False, str(exc)


def ensure_csv() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not CSV_PATH.exists():
        pd.DataFrame(columns=LOG_COLUMNS).to_csv(CSV_PATH, index=False, encoding="utf-8-sig")


def read_log() -> pd.DataFrame:
    ensure_csv()
    try:
        df = pd.read_csv(CSV_PATH, dtype=str, encoding="utf-8-sig").fillna("")
    except Exception as exc:
        st.error(f"อ่านไฟล์บันทึกไม่สำเร็จ: {exc}")
        return pd.DataFrame(columns=LOG_COLUMNS)
    for col in LOG_COLUMNS:
        if col not in df.columns:
            df[col] = ""
    df["score"] = pd.to_numeric(df["score"], errors="coerce")
    df["is_deleted"] = df["is_deleted"].astype(str).str.lower().isin(["true", "1", "yes"])
    return df[LOG_COLUMNS]


def write_log(df: pd.DataFrame) -> None:
    ensure_csv()
    out = df.copy()
    for col in LOG_COLUMNS:
        if col not in out.columns:
            out[col] = ""
    out[LOG_COLUMNS].to_csv(CSV_PATH, index=False, encoding="utf-8-sig")


def append_rows(rows: list[dict]) -> None:
    current = read_log()
    incoming = pd.DataFrame(rows)
    write_log(pd.concat([current, incoming], ignore_index=True))
    ok, message = _append_rows_to_apps_script(rows)
    if ok:
        st.toast(message)
    else:
        st.warning(f"บันทึกสำรองในเครื่องแล้ว แต่ส่งไป Google Sheet ไม่สำเร็จ: {message}")


def active_log() -> pd.DataFrame:
    df = read_log()
    return df[~df["is_deleted"].astype(bool)].copy()


def duplicate_exists(date_value: str, building: str, room_number: str, period: str, teacher_name: str) -> bool:
    df = active_log()
    if df.empty:
        return False
    mask = (
        (df["date"].astype(str) == str(date_value))
        & (df["building"].astype(str) == str(building))
        & (df["room_number"].astype(str) == str(room_number))
        & (df["period"].astype(str) == str(period))
        & (df["teacher_name"].astype(str) == str(teacher_name))
    )
    return bool(mask.any())


def update_record(record_id: str, updated_rows: list[dict]) -> None:
    df = read_log()
    keep = df["record_id"].astype(str) != str(record_id)
    write_log(pd.concat([df[keep], pd.DataFrame(updated_rows)], ignore_index=True))


def soft_delete(record_id: str, updated_at: str, updated_by: str) -> None:
    df = read_log()
    mask = df["record_id"].astype(str) == str(record_id)
    df.loc[mask, "is_deleted"] = True
    df.loc[mask, "updated_at"] = updated_at
    df.loc[mask, "updated_by"] = updated_by
    write_log(df)
