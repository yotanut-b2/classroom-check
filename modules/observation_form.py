from __future__ import annotations

from datetime import date, datetime

import streamlit as st

from .data_loader import load_criteria, load_examiner_data, load_teachers
from .google_sheet import append_rows, duplicate_exists
from .utils import current_day_name, make_record_id, thai_buddhist_date


def _building_floor_from_room(room_number: str, fallback_assignments: list[dict]) -> tuple[str, str]:
    digits = "".join(ch for ch in str(room_number) if ch.isdigit())
    if digits.startswith("10") and len(digits) >= 3:
        return "10", digits[2]
    if len(digits) >= 2:
        return digits[0], digits[1]
    if fallback_assignments:
        first = fallback_assignments[0]
        return str(first.get("building", "")), str(first.get("floor", ""))
    return "", ""


def _teacher_input(teachers: list[str]) -> str:
    if not teachers:
        st.warning("ไม่พบไฟล์รายชื่อครู จึงให้กรอกชื่อเอง")
        return st.text_input("ครูผู้สอน")
    return st.selectbox(
        "ครูผู้สอน",
        [""] + teachers,
        index=0,
        placeholder="พิมพ์เพื่อค้นหาหรือเลือกชื่อครู",
    )


def render_observation_form() -> None:
    st.header("บันทึกการสังเกตชั้นเรียน")
    criteria_df = load_criteria()
    examiner_df = load_examiner_data()
    teachers = load_teachers()
    assignments = st.session_state.get("assignments", [])
    role = st.session_state.get("role", "")
    username = st.session_state.get("username", "")
    today = date.today()

    st.info(
        f"วันที่ {thai_buddhist_date(today)} | ผู้ตรวจ: {username} | บทบาท: {role} | "
        f"วันตรวจ: {current_day_name(today)}"
    )

    if role == "inspector" and not assignments:
        st.warning("ไม่พบอาคาร/ชั้นที่รับผิดชอบในวันนี้")
        return

    if assignments:
        assigned_text = ", ".join([f"อาคาร {a['building']} ชั้น {a['floor']}" for a in assignments])
        st.caption(f"สิทธิ์พื้นที่รับผิดชอบ: {assigned_text}")

    with st.form("observation_form"):
        c1, c2, c3 = st.columns(3)
        room_number = c1.text_input("หมายเลขห้อง เช่น 921")
        class_level = c2.text_input("ห้อง ม. เช่น ม.3/1")
        period = c3.selectbox("คาบ", list(range(1, 10)))
        teacher_name = _teacher_input(teachers)

        st.subheader("ประเมินตามเกณฑ์")
        scores = {}
        for _, row in criteria_df.iterrows():
            key = f"criteria_{int(row['criteria_id'])}"
            scores[int(row["criteria_id"])] = st.radio(
                str(row["criteria"]),
                options=[1, 2, 3],
                format_func=lambda x: {1: "1 = น้อย", 2: "2 = ปานกลาง", 3: "3 = มาก"}[x],
                horizontal=True,
                key=key,
            )
        note = st.text_area("หมายเหตุ")
        submitted = st.form_submit_button("บันทึกผลการสังเกต", type="primary")

    if not submitted:
        return

    missing = []
    for label, value in {
        "หมายเลขห้อง": room_number,
        "ห้อง ม.": class_level,
        "ครูผู้สอน": teacher_name,
    }.items():
        if not str(value or "").strip():
            missing.append(label)
    if missing:
        st.error("กรุณากรอกข้อมูลให้ครบ: " + ", ".join(missing))
        return

    building, floor = _building_floor_from_room(room_number, assignments)
    if not building or not floor:
        st.error("กรุณากรอกหมายเลขห้องอย่างน้อย 2 หลัก เพื่อให้ระบบอ่านอาคารและชั้นได้ เช่น 921")
        return

    date_value = today.isoformat()
    if duplicate_exists(date_value, building, room_number, str(period), teacher_name):
        st.warning("พบข้อมูลห้องนี้ในวัน/คาบ/ครูเดียวกันแล้ว จึงไม่บันทึกซ้ำ")
        return

    now = datetime.now().isoformat(timespec="seconds")
    record_id = make_record_id()
    rows = []
    for _, row in criteria_df.iterrows():
        criteria_id = int(row["criteria_id"])
        rows.append(
            {
                "record_id": record_id,
                "timestamp": now,
                "date": date_value,
                "buddhist_date": thai_buddhist_date(today),
                "day_name": current_day_name(today),
                "inspector": username,
                "role": role,
                "building": str(building),
                "floor": str(floor),
                "room_number": str(room_number).strip(),
                "class_level": str(class_level).strip(),
                "period": str(period),
                "teacher_name": str(teacher_name).strip(),
                "criteria_id": criteria_id,
                "criteria": row["criteria"],
                "category": row["category"],
                "score": scores[criteria_id],
                "note": note,
                "is_deleted": False,
                "updated_at": now,
                "updated_by": username,
            }
        )
    append_rows(rows)
    st.success("บันทึกข้อมูลสำเร็จ")
