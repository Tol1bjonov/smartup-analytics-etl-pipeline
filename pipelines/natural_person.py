import os
import pandas as pd

from config import ENDPOINTS, OUTPUT_DIR, get_headers
from client import fetch
from loader import save_to_db


# ── Transform funksiyalari ────────────────────────────────────────────────────

def build_natural_persons(raw: pd.DataFrame) -> pd.DataFrame:
    df = raw[raw["state"] == "A"].copy()

    columns = [
        "person_id", "first_name", "last_name", "middle_name",
        "code", "birthday", "gender",
        "region_name", "region_code", "address", "post_address",
        "is_budgetarian", "state", "legal_person_code",
        "web", "telegram",
        "is_client", "is_supplier",
        "main_phone", "email", "latlng",
        "groups", "rooms",                # nested — keyinroq ajratiladi
    ]
    df = df[[c for c in columns if c in df.columns]]

    df["person_id"] = pd.to_numeric(df["person_id"], errors="coerce").astype("Int64")

    # Boolean ustunlar
    for bool_col in ("is_budgetarian", "is_client", "is_supplier"):
        if bool_col in df.columns:
            df[bool_col] = df[bool_col].map(
                lambda v: True if str(v).strip().upper() in ("1", "TRUE", "T", "YES")
                else (False if str(v).strip().upper() in ("0", "FALSE", "F", "NO")
                      else pd.NA)
            )

    return df.drop_duplicates(subset=["person_id"]).reset_index(drop=True)


def build_person_group(dim: pd.DataFrame) -> pd.DataFrame:
    """person_id + group_code + type_code ko'prik jadvali."""
    rows = []
    for _, row in dim[["person_id", "groups"]].iterrows():
        groups = row["groups"]
        if not isinstance(groups, list):
            continue
        for g in groups:
            gc = g.get("group_code")
            tc = g.get("type_code")
            if gc:
                rows.append({
                    "person_id":  row["person_id"],
                    "group_code": str(gc).strip(),
                    "type_code":  str(tc).strip() if tc else None,
                })

    if not rows:
        return pd.DataFrame(columns=["person_id", "group_code", "type_code"])

    df = pd.DataFrame(rows)
    df["person_id"] = pd.to_numeric(df["person_id"], errors="coerce").astype("Int64")
    df = df.dropna(subset=["person_id"])
    return df.drop_duplicates(subset=["person_id", "group_code"]).reset_index(drop=True)


def build_person_room(dim: pd.DataFrame) -> pd.DataFrame:
    """person_id + room_id + room_code + room_type_code ko'prik jadvali."""
    rows = []
    for _, row in dim[["person_id", "rooms"]].iterrows():
        rooms = row["rooms"]
        if not isinstance(rooms, list):
            continue
        for r in rooms:
            rid = r.get("room_id")
            if rid:
                rows.append({
                    "person_id":      row["person_id"],
                    "room_id":        rid,
                    "room_code":      r.get("room_code"),
                    "room_type_code": r.get("room_type_code"),
                })

    if not rows:
        return pd.DataFrame(columns=["person_id", "room_id", "room_code", "room_type_code"])

    df = pd.DataFrame(rows)
    df["person_id"] = pd.to_numeric(df["person_id"], errors="coerce").astype("Int64")
    df["room_id"]   = pd.to_numeric(df["room_id"],   errors="coerce").astype("Int64")
    df = df.dropna(subset=["person_id", "room_id"])
    return df.drop_duplicates(subset=["person_id", "room_id"]).reset_index(drop=True)


# ── Run ───────────────────────────────────────────────────────────────────────

def run():
    print("=== Natural Persons pipeline ===")

    # 1. Extract
    raw = fetch(ENDPOINTS["natural_person"], get_headers(), key="natural_person")
    if raw.empty:
        print("Ma'lumot kelmadi, pipeline to'xtatildi.")
        return

    # 2. Transform
    dim          = build_natural_persons(raw)
    person_group = build_person_group(dim)
    person_room  = build_person_room(dim)

    # nested ustunlarni DB/Excel uchun olib tashlash
    nested = ["groups", "rooms"]
    persons = dim.drop(columns=[c for c in nested if c in dim.columns])

    # 3. Load — Excel
    persons.to_excel(
        os.path.join(OUTPUT_DIR, "natural_persons.xlsx"), index=False
    )
    person_group.to_excel(
        os.path.join(OUTPUT_DIR, "person_group.xlsx"), index=False
    )
    person_room.to_excel(
        os.path.join(OUTPUT_DIR, "person_room.xlsx"), index=False
    )

    # 4. Load — PostgreSQL
    save_to_db(persons,      "natural_persons")
    save_to_db(person_group, "person_group")
    save_to_db(person_room,  "person_room")

    print("=== Natural Persons pipeline tugadi ===")