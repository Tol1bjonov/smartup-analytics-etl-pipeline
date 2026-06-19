import os
import pandas as pd

from config import ENDPOINTS, OUTPUT_DIR, get_headers
from client import fetch
from loader import save_to_db


# ── Transform funksiyalari ────────────────────────────────────────────────────

def build_legal_entities(raw: pd.DataFrame) -> pd.DataFrame:
    df = raw[raw["state"] == "A"].copy()

    columns = [
        "person_id", "name", "code", "short_name",
        "region_code", "is_budgetarian", "tin", "state",
        "primary_person_code", "parent_person_code",
        "barcode", "vat_code", "cea",
        "main_phone", "email", "web",
        "address", "address_guide", "zip_code", "latlng",
        "is_client", "is_supplier",
        "groups", "bank_accounts", "rooms",  # nested — keyinroq ajratiladi
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


def build_legal_entity_group(dim: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, row in dim[["person_id", "groups"]].iterrows():
        groups = row["groups"]
        if not isinstance(groups, list):
            continue
        for g in groups:
            gc = g.get("group_code")
            if gc:
                rows.append({
                    "person_id":  row["person_id"],
                    "group_code": str(gc).strip(),
                    "type_code":  str(g.get("type_code", "")).strip() or None,
                })

    if not rows:
        return pd.DataFrame(columns=["person_id", "group_code", "type_code"])

    df = pd.DataFrame(rows)
    df["person_id"] = pd.to_numeric(df["person_id"], errors="coerce").astype("Int64")
    df = df.dropna(subset=["person_id"])
    return df.drop_duplicates(subset=["person_id", "group_code"]).reset_index(drop=True)


def build_legal_entity_bank_account(dim: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, row in dim[["person_id", "bank_accounts"]].iterrows():
        accounts = row["bank_accounts"]
        if not isinstance(accounts, list):
            continue
        for a in accounts:
            if a.get("state") == "A" or a.get("state") == "":
                ba_id = a.get("bank_account_id")
                if ba_id:
                    rows.append({
                        "person_id":        row["person_id"],
                        "bank_account_id":  ba_id,
                        "bank_account_code":a.get("bank_account_code"),
                        "bank_account_name":a.get("bank_account_name"),
                        "is_main":          a.get("is_main"),
                        "currency_code":    a.get("currency_code"),
                        "state":            a.get("state"),
                        "note":             a.get("note"),
                        "mfo":              a.get("mfo"),
                        "bank_name":        a.get("bank_name"),
                    })

    if not rows:
        return pd.DataFrame(columns=[
            "person_id", "bank_account_id", "bank_account_code",
            "bank_account_name", "is_main", "currency_code",
            "state", "note", "mfo", "bank_name"
        ])

    df = pd.DataFrame(rows)
    df["person_id"]       = pd.to_numeric(df["person_id"],       errors="coerce").astype("Int64")
    df["bank_account_id"] = pd.to_numeric(df["bank_account_id"], errors="coerce").astype("Int64")
    df["is_main"] = df["is_main"].map(
        lambda v: True if str(v).strip().upper() in ("1", "TRUE", "T", "YES")
        else (False if str(v).strip().upper() in ("0", "FALSE", "F", "NO")
              else pd.NA)
    )
    df = df.dropna(subset=["person_id", "bank_account_id"])
    return df.drop_duplicates(subset=["person_id", "bank_account_id"]).reset_index(drop=True)


def build_legal_entity_room(dim: pd.DataFrame) -> pd.DataFrame:
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
    print("=== Legal Entity pipeline ===")

    # 1. Extract
    raw = fetch(ENDPOINTS["legal_entity"], get_headers(), key="legal_person")
    if raw.empty:
        print("Ma'lumot kelmadi, pipeline to'xtatildi.")
        return

    # 2. Transform
    dim                      = build_legal_entities(raw)
    legal_entity_group       = build_legal_entity_group(dim)
    legal_entity_bank_account= build_legal_entity_bank_account(dim)
    legal_entity_room        = build_legal_entity_room(dim)

    # nested ustunlarni olib tashlash
    nested = ["groups", "bank_accounts", "rooms"]
    legal_entities = dim.drop(columns=[c for c in nested if c in dim.columns])

    # 3. Load — Excel
    legal_entities.to_excel(
        os.path.join(OUTPUT_DIR, "legal_entities.xlsx"), index=False
    )
    legal_entity_group.to_excel(
        os.path.join(OUTPUT_DIR, "legal_entity_group.xlsx"), index=False
    )
    legal_entity_bank_account.to_excel(
        os.path.join(OUTPUT_DIR, "legal_entity_bank_account.xlsx"), index=False
    )
    legal_entity_room.to_excel(
        os.path.join(OUTPUT_DIR, "legal_entity_room.xlsx"), index=False
    )

    # 4. Load — PostgreSQL
    save_to_db(legal_entities,            "legal_entities")
    save_to_db(legal_entity_group,        "legal_entity_group")
    save_to_db(legal_entity_bank_account, "legal_entity_bank_account")
    save_to_db(legal_entity_room,         "legal_entity_room")

    print("=== Legal Entity pipeline tugadi ===")