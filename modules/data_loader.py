from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

DATA_DIR = Path(__file__).resolve().parents[1] / "data"


def _read_excel(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    return pd.read_excel(path).fillna("")


@st.cache_data(show_spinner=False)
def load_examiner_data() -> pd.DataFrame:
    for name in ("examiner_ssm.xlsx", "examine_ssm.xlsx"):
        df = _read_excel(DATA_DIR / name)
        if not df.empty:
            df.columns = [str(c).strip() for c in df.columns]
            required = {"building", "floor", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday"}
            missing = required.difference(df.columns)
            if missing:
                st.warning(f"ไฟล์เวรตรวจขาดคอลัมน์: {', '.join(sorted(missing))}")
            return df
    st.error("ไม่พบไฟล์ examiner_ssm.xlsx หรือ examine_ssm.xlsx ในโฟลเดอร์ data")
    return pd.DataFrame(columns=["building", "floor", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday"])


@st.cache_data(show_spinner=False)
def load_criteria() -> pd.DataFrame:
    df = _read_excel(DATA_DIR / "criteria_classroom.xlsx")
    if df.empty or "criteria" not in df.columns:
        st.error("ไฟล์ criteria_classroom.xlsx ต้องมีคอลัมน์ criteria")
        return pd.DataFrame(columns=["criteria_id", "criteria", "category"])
    df.columns = [str(c).strip() for c in df.columns]
    if "category" in df.columns:
        category = df["category"]
    elif "dimension" in df.columns:
        category = df["dimension"]
    else:
        category = df["criteria"]
    out = pd.DataFrame(
        {
            "criteria_id": range(1, len(df) + 1),
            "criteria": df["criteria"].astype(str).str.strip(),
            "category": category.astype(str).str.strip(),
        }
    )
    return out[out["criteria"] != ""].reset_index(drop=True)


@st.cache_data(show_spinner=False)
def load_teachers() -> list[str]:
    path = DATA_DIR / "teacher_list.xlsx"
    if not path.exists():
        return []
    df = _read_excel(path)
    if "teacher_name" not in df.columns:
        st.warning("ไฟล์ teacher_list.xlsx ไม่มีคอลัมน์ teacher_name จึงใช้ช่องกรอกเองแทน")
        return []
    return sorted([str(x).strip() for x in df["teacher_name"].dropna().tolist() if str(x).strip()])
