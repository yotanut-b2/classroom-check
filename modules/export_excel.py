from __future__ import annotations

from io import BytesIO

import pandas as pd
import streamlit as st

from .admin_dashboard import room_summary
from .google_sheet import active_log


def _filtered_log() -> pd.DataFrame:
    df = active_log()
    if df.empty:
        return df
    df = df.copy()
    df["date_dt"] = pd.to_datetime(df["date"], errors="coerce")
    c1, c2 = st.columns(2)
    start = c1.date_input("วันที่เริ่มต้น", value=df["date_dt"].min().date(), key="excel_start")
    end = c2.date_input("วันที่สิ้นสุด", value=df["date_dt"].max().date(), key="excel_end")
    return df[(df["date_dt"].dt.date >= start) & (df["date_dt"].dt.date <= end)].drop(columns=["date_dt"])


def build_excel(df: pd.DataFrame, summary_only: bool = False) -> bytes:
    output = BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df.to_excel(writer, sheet_name="raw_data", index=False)
        overall = pd.DataFrame(
            {
                "metric": ["overall_mean", "evaluated_rooms", "observation_rows", "inspectors"],
                "value": [df["score"].mean(), df["record_id"].nunique(), len(df), df["inspector"].nunique()],
            }
        )
        overall.to_excel(writer, sheet_name="summary_overall", index=False)
        df.groupby("category", as_index=False)["score"].mean().to_excel(writer, sheet_name="summary_by_category", index=False)
        df.groupby("building", as_index=False)["score"].mean().to_excel(writer, sheet_name="summary_by_building", index=False)
        room_summary(df).to_excel(writer, sheet_name="summary_by_room", index=False)
    return output.getvalue()


def render_excel_download() -> None:
    st.header("ดาวน์โหลดข้อมูล Excel")
    df = _filtered_log()
    if df.empty:
        st.info("ยังไม่มีข้อมูลให้ดาวน์โหลด")
        return
    st.download_button(
        "ดาวน์โหลดข้อมูลดิบ Excel",
        data=build_excel(df),
        file_name="classroom_observation_raw.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    st.download_button(
        "ดาวน์โหลดสรุปผล Excel",
        data=build_excel(df, summary_only=True),
        file_name="classroom_observation_summary.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
