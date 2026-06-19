import os
import pandas as pd

from config import ENDPOINTS, OUTPUT_DIR, get_headers
from client import fetch
from loader import save_to_db


# ── Transform funksiyalari ────────────────────────────────────────────────────

def build_person_groups(raw: pd.DataFrame) -> pd.DataFrame:
    df = raw[raw["state"] == "A"].copy()

    columns = [
        "person_group_id", "code", "name",
        "person_kind", "state",
        "person_group_types",  # nested — keyinroq ajratiladi
    ]
    df = df[[c for c in columns if c in df.columns]]

    df["person_group_id"] = pd.to_numeric(df["person_group_id"], errors="coerce").astype("Int64")

    return df.drop_duplicates(subset=["person_group_id"]).reset_index(drop=True)


def build_person_group_types(dim: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, row in dim[["person_group_id", "person_group_types"]].iterrows():
        types = row["person_group_types"]
        if not isinstance(types, list):
            continue
        for t in types:
            if t.get("state") != "A":
                continue
            rows.append({
                "person_group_id": row["person_group_id"],
                "code":            t.get("code"),
                "name":            t.get("name"),
                "order_no":        t.get("order_no"),
            })

    if not rows:
        return pd.DataFrame(columns=["person_group_id", "code", "name", "order_no"])

    df = pd.DataFrame(rows)
    df["person_group_id"] = pd.to_numeric(df["person_group_id"], errors="coerce").astype("Int64")
    df["order_no"]        = pd.to_numeric(df["order_no"],        errors="coerce")
    df = df.dropna(subset=["person_group_id", "code"])
    return df.drop_duplicates(subset=["person_group_id", "code"]).reset_index(drop=True)


# ── Run ───────────────────────────────────────────────────────────────────────

def run():
    print("=== Person Group pipeline ===")

    # 1. Extract
    raw = fetch(ENDPOINTS["person_group"], get_headers(), key="person_group")
    if raw.empty:
        print("Ma'lumot kelmadi, pipeline to'xtatildi.")
        return

    # 2. Transform
    dim               = build_person_groups(raw)
    person_group_types = build_person_group_types(dim)

    # nested ustunni olib tashlash
    person_groups = dim.drop(columns=["person_group_types"], errors="ignore")

    # 3. Load — Excel
    person_groups.to_excel(
        os.path.join(OUTPUT_DIR, "person_groups.xlsx"), index=False
    )
    person_group_types.to_excel(
        os.path.join(OUTPUT_DIR, "person_group_types.xlsx"), index=False
    )

    # 4. Load — PostgreSQL
    save_to_db(person_groups,      "person_groups")
    save_to_db(person_group_types, "person_group_types")

    print("=== Person Group pipeline tugadi ===")