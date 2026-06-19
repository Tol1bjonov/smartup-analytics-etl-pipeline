import os
import pandas as pd

from config import ENDPOINTS, OUTPUT_DIR, get_headers
from client import fetch
from loader import save_to_db


# ── Transform ────────────────────────────────────────────────────────────────

def build_return_reasons(raw: pd.DataFrame) -> pd.DataFrame:
    df = raw[raw["state"] == "A"].copy()

    columns = [
        "return_reason_id",
        "code",
        "name",
        "state",
        "order_no"
    ]

    df = df[[c for c in columns if c in df.columns]]

    df["return_reason_id"] = pd.to_numeric(
        df["return_reason_id"],
        errors="coerce"
    ).astype("Int64")

    df["order_no"] = pd.to_numeric(
        df["order_no"],
        errors="coerce"
    )

    return (
        df.drop_duplicates(subset=["return_reason_id"])
          .reset_index(drop=True)
    )


# ── Run ──────────────────────────────────────────────────────────────────────

def run():
    print("=== Return Reason pipeline ===")

    # Extract
    raw = fetch(
        ENDPOINTS["return_reason"],
        get_headers(),
        key="return_reason"
    )

    if raw.empty:
        print("Ma'lumot kelmadi.")
        return

    # Transform
    return_reasons = build_return_reasons(raw)

    # Excel
    return_reasons.to_excel(
        os.path.join(OUTPUT_DIR, "return_reasons.xlsx"),
        index=False
    )

    # PostgreSQL
    save_to_db(
        return_reasons,
        "return_reasons"
    )

    print("=== Return Reason pipeline tugadi ===")