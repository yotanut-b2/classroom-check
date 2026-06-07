from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from .google_sheet import active_log
from .utils import score_color, score_interpretation


def _filter_by_date(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    df = df.copy()
    df["date_dt"] = pd.to_datetime(df["date"], errors="coerce")
    c1, c2 = st.columns(2)
    start = c1.date_input("วันที่เริ่มต้น", value=df["date_dt"].min().date())
    end = c2.date_input("วันที่สิ้นสุด", value=df["date_dt"].max().date())
    return df[(df["date_dt"].dt.date >= start) & (df["date_dt"].dt.date <= end)]


def room_summary(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()
    group_cols = [
        "record_id",
        "date",
        "building",
        "floor",
        "room_number",
        "class_level",
        "period",
        "teacher_name",
        "inspector",
    ]
    summary = df.groupby(group_cols, dropna=False).agg(mean_score=("score", "mean"), note=("note", "first")).reset_index()
    summary["interpretation"] = summary["mean_score"].apply(score_interpretation)
    return summary


def render_admin_dashboard() -> None:
    st.header("สรุปผลการประเมิน")
    df = _filter_by_date(active_log())
    if df.empty:
        st.info("ยังไม่มีข้อมูลการประเมิน")
        return

    summary = room_summary(df)
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("คะแนนเฉลี่ยรวม", f"{df['score'].mean():.2f}")
    m2.metric("จำนวนห้องที่ประเมิน", f"{summary['record_id'].nunique():,}")
    m3.metric("จำนวนแถวบันทึก", f"{len(df):,}")
    m4.metric("จำนวนผู้ตรวจ", f"{df['inspector'].nunique():,}")

    st.subheader("ห้องที่ประเมินแล้ว")
    for date_value, by_date in summary.groupby("date"):
        with st.expander(f"วันที่ {date_value}"):
            for building, by_building in by_date.groupby("building"):
                rooms = ", ".join(by_building["room_number"].astype(str).tolist())
                st.write(f"อาคาร {building} ตรวจแล้ว {len(by_building)} ห้อง ได้แก่ {rooms}")

    c1, c2 = st.columns(2)
    category_mean = df.groupby("category", as_index=False)["score"].mean()
    building_mean = df.groupby("building", as_index=False)["score"].mean()
    c1.plotly_chart(px.bar(category_mean, x="category", y="score", title="คะแนนเฉลี่ยรายด้าน", text_auto=".2f"), use_container_width=True)
    c2.plotly_chart(px.bar(building_mean, x="building", y="score", title="คะแนนเฉลี่ยรายอาคาร", text_auto=".2f"), use_container_width=True)

    pivot = df.pivot_table(index="building", columns="category", values="score", aggfunc="mean")
    if not pivot.empty:
        st.plotly_chart(px.imshow(pivot, text_auto=".2f", aspect="auto", title="Heatmap อาคาร x ด้านการประเมิน"), use_container_width=True)

    st.subheader("รายละเอียดรายอาคาร")
    building = st.selectbox("เลือกอาคาร", sorted(summary["building"].astype(str).unique()))
    building_summary = summary[summary["building"].astype(str) == str(building)].sort_values(["room_number", "period"])
    display = building_summary[
        ["building", "room_number", "class_level", "period", "teacher_name", "mean_score", "interpretation", "note"]
    ]
    st.dataframe(display.style.applymap(score_color, subset=["mean_score"]), use_container_width=True)

    for _, row in building_summary.iterrows():
        with st.expander(f"ห้อง {row['room_number']} คาบ {row['period']} | {row['teacher_name']}"):
            detail = df[df["record_id"] == row["record_id"]][["criteria_id", "criteria", "category", "score", "note"]]
            st.dataframe(detail, use_container_width=True)
