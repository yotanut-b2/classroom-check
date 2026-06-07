from __future__ import annotations

import streamlit as st

from modules.admin_dashboard import render_admin_dashboard
from modules.auth import authenticate
from modules.data_loader import load_examiner_data
from modules.data_management import render_data_management
from modules.export_excel import render_excel_download
from modules.observation_form import render_observation_form
from modules.report_generator import render_pdf_report

st.set_page_config(page_title="ระบบสังเกตชั้นเรียน", page_icon="🏫", layout="wide")


def init_state() -> None:
    st.session_state.setdefault("logged_in", False)
    st.session_state.setdefault("username", "")
    st.session_state.setdefault("role", "")
    st.session_state.setdefault("current_day", "")
    st.session_state.setdefault("assignments", [])


def login_page() -> None:
    st.title("ระบบสังเกตชั้นเรียนบนอาคารเรียน")
    st.caption("เข้าสู่ระบบเพื่อบันทึกและติดตามผลการสังเกตชั้นเรียน")
    examiner_df = load_examiner_data()
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login", type="primary")
    if submitted:
        ok, role, assignments, day_name = authenticate(username, password, examiner_df)
        if ok:
            st.session_state["logged_in"] = True
            st.session_state["username"] = username.strip()
            st.session_state["role"] = role
            st.session_state["current_day"] = day_name
            st.session_state["assignments"] = assignments
            st.rerun()
        else:
            st.error("เข้าสู่ระบบไม่สำเร็จ ตรวจสอบชื่อผู้ใช้/รหัสผ่าน หรือไม่มีเวรตรวจในวันนี้")


def logout() -> None:
    for key in ["logged_in", "username", "role", "current_day", "assignments"]:
        st.session_state[key] = False if key == "logged_in" else "" if key != "assignments" else []
    st.rerun()


def main() -> None:
    init_state()
    if not st.session_state["logged_in"]:
        login_page()
        return

    st.sidebar.title("เมนู")
    st.sidebar.write(f"ผู้ใช้: {st.session_state['username']}")
    st.sidebar.write(f"บทบาท: {st.session_state['role']}")

    if st.session_state["role"] == "admin":
        menu = st.sidebar.radio(
            "เลือกหน้า",
            ["บันทึกการสังเกต", "สรุปผลการประเมิน", "จัดการข้อมูล", "ดาวน์โหลดข้อมูล Excel", "พิมพ์รายงาน PDF", "ออกจากระบบ"],
        )
    else:
        menu = st.sidebar.radio("เลือกหน้า", ["บันทึกการสังเกต", "ออกจากระบบ"])

    if menu == "บันทึกการสังเกต":
        render_observation_form()
    elif menu == "สรุปผลการประเมิน":
        render_admin_dashboard()
    elif menu == "จัดการข้อมูล":
        render_data_management()
    elif menu == "ดาวน์โหลดข้อมูล Excel":
        render_excel_download()
    elif menu == "พิมพ์รายงาน PDF":
        render_pdf_report()
    else:
        logout()


if __name__ == "__main__":
    main()
