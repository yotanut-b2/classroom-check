from __future__ import annotations

from datetime import datetime
from io import BytesIO
from pathlib import Path

import pandas as pd
import streamlit as st
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from .admin_dashboard import room_summary
from .data_loader import load_criteria
from .google_sheet import active_log
from .utils import score_interpretation


def _register_thai_font() -> str:
    candidates = [
        r"C:\Windows\Fonts\THSarabunNew.ttf",
        r"C:\Windows\Fonts\tahoma.ttf",
        r"C:\Windows\Fonts\arial.ttf",
    ]
    for path in candidates:
        if Path(path).exists():
            font_name = Path(path).stem
            try:
                pdfmetrics.registerFont(TTFont(font_name, path))
                return font_name
            except Exception:
                continue
    return "Helvetica"


def build_pdf(df: pd.DataFrame, title: str) -> bytes:
    font = _register_thai_font()
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4), rightMargin=1 * cm, leftMargin=1 * cm, topMargin=1 * cm, bottomMargin=1 * cm)
    styles = getSampleStyleSheet()
    for style in styles.byName.values():
        style.fontName = font

    story = [Paragraph(title, styles["Title"]), Spacer(1, 0.25 * cm)]
    summary = room_summary(df)
    metrics = [
        ["จำนวนห้องที่ประเมิน", summary["record_id"].nunique()],
        ["จำนวนรายการบันทึก", len(df)],
        ["จำนวนผู้ตรวจ", df["inspector"].nunique()],
        ["คะแนนเฉลี่ยรวม", f"{df['score'].mean():.2f} ({score_interpretation(df['score'].mean())})"],
    ]
    story.append(Table(metrics, style=[("FONTNAME", (0, 0), (-1, -1), font), ("GRID", (0, 0), (-1, -1), 0.25, colors.grey)]))
    story.append(Spacer(1, 0.35 * cm))

    for heading, grouped in [
        ("คะแนนเฉลี่ยรายด้าน", df.groupby("category", as_index=False)["score"].mean()),
        ("คะแนนเฉลี่ยรายอาคาร", df.groupby("building", as_index=False)["score"].mean()),
    ]:
        story.append(Paragraph(heading, styles["Heading2"]))
        table_data = [grouped.columns.tolist()] + grouped.round(2).astype(str).values.tolist()
        story.append(Table(table_data, style=[("FONTNAME", (0, 0), (-1, -1), font), ("GRID", (0, 0), (-1, -1), 0.25, colors.grey), ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey)]))
        story.append(Spacer(1, 0.3 * cm))

    criteria = load_criteria()
    detail_df = df.copy()
    detail_df["criteria_id"] = pd.to_numeric(detail_df["criteria_id"], errors="coerce").astype("Int64").astype(str)
    pivot = detail_df.pivot_table(
        index=["record_id", "building", "room_number", "class_level", "period", "teacher_name", "note"],
        columns="criteria_id",
        values="score",
        aggfunc="first",
    ).reset_index()
    criteria_ids = [str(int(value)) for value in criteria["criteria_id"].tolist()]
    for criteria_id in criteria_ids:
        if criteria_id not in pivot.columns:
            pivot[criteria_id] = pd.NA
    pivot["mean_score"] = pivot[criteria_ids].apply(pd.to_numeric, errors="coerce").mean(axis=1)
    pivot["interpretation"] = pivot["mean_score"].apply(score_interpretation)
    rename = {criteria_id: f"C{criteria_id}" for criteria_id in criteria_ids}
    pivot = pivot.rename(columns=rename).sort_values(["building", "room_number", "period"])
    cols = ["building", "room_number", "class_level", "period", "teacher_name"] + list(rename.values()) + ["mean_score", "interpretation", "note"]
    detail_data = [cols] + pivot[cols].round(2).astype(str).values.tolist()
    story.append(Paragraph("รายละเอียดรายห้อง", styles["Heading2"]))
    story.append(Table(detail_data, repeatRows=1, style=[("FONTNAME", (0, 0), (-1, -1), font), ("FONTSIZE", (0, 0), (-1, -1), 8), ("GRID", (0, 0), (-1, -1), 0.25, colors.grey), ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey)]))
    story.append(Spacer(1, 0.35 * cm))
    story.append(Paragraph("คำอธิบายรหัสเกณฑ์", styles["Heading2"]))
    legend = [[f"C{int(row.criteria_id)}", row.criteria] for row in criteria.itertuples()]
    story.append(Table([["รหัส", "เกณฑ์"]] + legend, style=[("FONTNAME", (0, 0), (-1, -1), font), ("GRID", (0, 0), (-1, -1), 0.25, colors.grey)]))
    doc.build(story)
    return buffer.getvalue()


def render_pdf_report() -> None:
    st.header("พิมพ์รายงาน PDF")
    df = active_log()
    if df.empty:
        st.info("ยังไม่มีข้อมูลสำหรับรายงาน")
        return
    df["date_dt"] = pd.to_datetime(df["date"], errors="coerce")
    c1, c2 = st.columns(2)
    start = c1.date_input("วันที่เริ่มต้น", value=df["date_dt"].min().date(), key="pdf_start")
    end = c2.date_input("วันที่สิ้นสุด", value=df["date_dt"].max().date(), key="pdf_end")
    filtered = df[(df["date_dt"].dt.date >= start) & (df["date_dt"].dt.date <= end)].drop(columns=["date_dt"])
    if filtered.empty:
        st.warning("ไม่พบข้อมูลในช่วงวันที่ที่เลือก")
        return
    title = f"รายงานผลการสังเกตชั้นเรียน ({start} ถึง {end})"
    pdf = build_pdf(filtered, title)
    st.download_button("ดาวน์โหลดรายงาน PDF", data=pdf, file_name=f"classroom_report_{datetime.now():%Y%m%d}.pdf", mime="application/pdf")
