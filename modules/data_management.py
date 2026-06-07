from __future__ import annotations

from datetime import datetime

import pandas as pd
import streamlit as st

from .admin_dashboard import room_summary
from .data_loader import load_criteria, load_teachers
from .google_sheet import active_log, read_log, soft_delete, update_record
from .utils import thai_buddhist_date


def render_data_management() -> None:
    st.header("จัดการข้อมูล")
    df = active_log()
    if df.empty:
        st.info("ยังไม่มีข้อมูล")
        return

    df["date_dt"] = pd.to_datetime(df["date"], errors="coerce")
    with st.expander("ค้นหาข้อมูล", expanded=True):
        c1, c2, c3 = st.columns(3)
        start = c1.date_input("วันที่เริ่มต้น", value=df["date_dt"].min().date(), key="mgmt_start")
        end = c2.date_input("วันที่สิ้นสุด", value=df["date_dt"].max().date(), key="mgmt_end")
        building = c3.selectbox("อาคาร", ["ทั้งหมด"] + sorted(df["building"].astype(str).unique().tolist()))
        c4, c5, c6 = st.columns(3)
        room = c4.text_input("หมายเลขห้อง")
        teacher = c5.text_input("ครูผู้สอน")
        inspector = c6.text_input("ผู้ตรวจ")

    filtered = df[(df["date_dt"].dt.date >= start) & (df["date_dt"].dt.date <= end)]
    if building != "ทั้งหมด":
        filtered = filtered[filtered["building"].astype(str) == str(building)]
    if room:
        filtered = filtered[filtered["room_number"].astype(str).str.contains(room, case=False, na=False)]
    if teacher:
        filtered = filtered[filtered["teacher_name"].astype(str).str.contains(teacher, case=False, na=False)]
    if inspector:
        filtered = filtered[filtered["inspector"].astype(str).str.contains(inspector, case=False, na=False)]

    summary = room_summary(filtered)
    if summary.empty:
        st.warning("ไม่พบข้อมูลตามเงื่อนไข")
        return

    st.dataframe(
        summary[["record_id", "date", "building", "room_number", "class_level", "period", "teacher_name", "inspector", "mean_score", "note"]],
        use_container_width=True,
    )
    record_id = st.selectbox("เลือก record_id เพื่อดู/แก้ไข", summary["record_id"].tolist())
    record = filtered[filtered["record_id"] == record_id].sort_values("criteria_id")
    if record.empty:
        return

    first = record.iloc[0]
    teachers = load_teachers()
    criteria_df = load_criteria()
    with st.form("edit_record"):
        c1, c2, c3 = st.columns(3)
        new_building = c1.text_input("อาคาร", value=str(first["building"]))
        new_floor = c2.text_input("ชั้น", value=str(first["floor"]))
        new_room = c3.text_input("หมายเลขห้อง", value=str(first["room_number"]))
        c4, c5 = st.columns(2)
        new_class = c4.text_input("ห้อง ม.", value=str(first["class_level"]))
        new_period = c5.selectbox("คาบ", list(range(1, 10)), index=max(0, int(first["period"]) - 1) if str(first["period"]).isdigit() else 0)
        if teachers and str(first["teacher_name"]) in teachers:
            new_teacher = st.selectbox("ครูผู้สอน", teachers, index=teachers.index(str(first["teacher_name"])))
        elif teachers:
            new_teacher = st.selectbox("ครูผู้สอน", [str(first["teacher_name"])] + teachers)
        else:
            new_teacher = st.text_input("ครูผู้สอน", value=str(first["teacher_name"]))

        new_scores = {}
        for _, crit in criteria_df.iterrows():
            crit_id = int(crit["criteria_id"])
            old = record[record["criteria_id"].astype(str) == str(crit_id)]
            old_score = int(old["score"].iloc[0]) if not old.empty and pd.notna(old["score"].iloc[0]) else 2
            new_scores[crit_id] = st.radio(
                str(crit["criteria"]),
                [1, 2, 3],
                index=max(0, min(2, old_score - 1)),
                horizontal=True,
                key=f"edit_score_{crit_id}",
            )
        new_note = st.text_area("หมายเหตุ", value=str(first["note"]))
        save = st.form_submit_button("บันทึกการแก้ไข", type="primary")

    if save:
        now = datetime.now().isoformat(timespec="seconds")
        updated_rows = []
        for _, crit in criteria_df.iterrows():
            updated_rows.append(
                {
                    **first.to_dict(),
                    "building": new_building,
                    "floor": new_floor,
                    "room_number": new_room,
                    "class_level": new_class,
                    "period": str(new_period),
                    "teacher_name": new_teacher,
                    "criteria_id": int(crit["criteria_id"]),
                    "criteria": crit["criteria"],
                    "category": crit["category"],
                    "score": new_scores[int(crit["criteria_id"])],
                    "note": new_note,
                    "is_deleted": False,
                    "updated_at": now,
                    "updated_by": st.session_state.get("username", "admin"),
                }
            )
        update_record(record_id, updated_rows)
        st.success("แก้ไขข้อมูลเรียบร้อย")
        st.rerun()

    st.divider()
    st.subheader("ลบข้อมูล")
    confirm = st.checkbox("ยืนยันการลบข้อมูลชุดนี้")
    if st.button("ลบข้อมูลแบบ soft delete", disabled=not confirm):
        now = datetime.now().isoformat(timespec="seconds")
        soft_delete(record_id, now, st.session_state.get("username", "admin"))
        st.success("ลบข้อมูลเรียบร้อย")
        st.rerun()
