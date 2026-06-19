import os
import pandas as pd

from config import ENDPOINTS, OUTPUT_DIR, get_headers
from client import fetch
from loader import save_to_db


# ── Transform ─────────────────────────────────────────────────────────────────

def build_price_types(raw: pd.DataFrame) -> pd.DataFrame:
    df = raw[raw["state"] == "A"].copy()

    columns = [
        "code", "name", "short_name",
        "with_card", "state",
        "price_type_kind", "currency_code",
    ]
    df = df[[c for c in columns if c in df.columns]]

    # with_card boolean ga
    if "with_card" in df.columns:
        df["with_card"] = df["with_card"].map(
            lambda v: True if str(v).strip().upper() in ("1", "TRUE", "T", "YES")
            else (False if str(v).strip().upper() in ("0", "FALSE", "F", "NO")
                  else pd.NA)
        )

    return df.drop_duplicates(subset=["code"]).reset_index(drop=True)


# ── Run ───────────────────────────────────────────────────────────────────────

def run():
    print("=== Price Type pipeline ===")

    # 1. Extract
    # Bu endpoint "data" key ostida array qaytaradi
    raw = fetch(ENDPOINTS["price_type"], get_headers(), key="data")
    if raw.empty:
        print("Ma'lumot kelmadi, pipeline to'xtatildi.")
        return

    # 2. Transform
    price_types = build_price_types(raw)

    # 3. Load — Excel
    price_types.to_excel(
        os.path.join(OUTPUT_DIR, "price_types.xlsx"), index=False
    )

    # 4. Load — PostgreSQL
    save_to_db(price_types, "price_types")

    print("=== Price Type pipeline tugadi ===")