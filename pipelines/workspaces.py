import os
import pandas as pd

from config import ENDPOINTS, OUTPUT_DIR, get_headers
from client import fetch
from loader import save_to_db


# ── Transform ────────────────────────────────────────────────────────────────

def build_workspaces(raw: pd.DataFrame) -> pd.DataFrame:
    df = raw[raw["state"] == "A"].copy()

    columns = [
        "room_id",
        "room_code",
        "filial_code",
        "room_name",
        "room_type_code",
        "state",
        "order_no"
    ]

    df = df[[c for c in columns if c in df.columns]]

    df["room_id"] = pd.to_numeric(
        df["room_id"],
        errors="coerce"
    ).astype("Int64")

    df["order_no"] = pd.to_numeric(
        df["order_no"],
        errors="coerce"
    )

    return (
        df.drop_duplicates(subset=["room_id"])
          .reset_index(drop=True)
    )


# ── Run ──────────────────────────────────────────────────────────────────────

def run():
    print("=== Workspace pipeline ===")

    # Extract
    raw = fetch(
        ENDPOINTS["workspace"],
        get_headers(),
        key="room"
    )

    if raw.empty:
        print("Ma'lumot kelmadi.")
        return

    # Transform
    workspaces = build_workspaces(raw)

    # Excel
    workspaces.to_excel(
        os.path.join(OUTPUT_DIR, "workspaces.xlsx"),
        index=False
    )

    # PostgreSQL
    save_to_db(
        workspaces,
        "workspaces"
    )

    print("=== Workspace pipeline tugadi ===")