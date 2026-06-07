from __future__ import annotations

import pandas as pd

from .utils import current_day_name, normalize_text


def _cell_has_name(cell, username: str) -> bool:
    names = [part.strip() for part in str(cell).replace(";", ",").split(",")]
    return username in names or username == str(cell).strip()


def assignments_for_user(examiner_df: pd.DataFrame, username: str, day_name: str) -> list[dict]:
    if examiner_df.empty or day_name not in examiner_df.columns:
        return []
    username = normalize_text(username)
    rows = examiner_df[examiner_df[day_name].apply(lambda value: _cell_has_name(value, username))]
    return [
        {"building": str(row["building"]), "floor": str(row["floor"])}
        for _, row in rows.iterrows()
    ]


def admin_assignments_for_user(examiner_df: pd.DataFrame, username: str) -> list[dict]:
    if examiner_df.empty or "Admin" not in examiner_df.columns:
        return []
    username = normalize_text(username)
    rows = examiner_df[examiner_df["Admin"].apply(lambda value: _cell_has_name(value, username))]
    return [
        {"building": str(row["building"]), "floor": str(row["floor"])}
        for _, row in rows.iterrows()
    ]


def authenticate(username: str, password: str, examiner_df: pd.DataFrame) -> tuple[bool, str, list[dict], str]:
    username = normalize_text(username)
    password = normalize_text(password)
    day_name = current_day_name()

    if username == "admin" and password == "654321":
        all_assignments = [
            {"building": str(row["building"]), "floor": str(row["floor"])}
            for _, row in examiner_df.iterrows()
        ]
        return True, "admin", all_assignments, day_name

    admin_assignments = admin_assignments_for_user(examiner_df, username)
    if admin_assignments and password == "654321":
        return True, "admin", admin_assignments, day_name

    if password != "123456":
        return False, "", [], day_name

    assignments = assignments_for_user(examiner_df, username, day_name)
    if not assignments:
        return False, "", [], day_name
    return True, "inspector", assignments, day_name
