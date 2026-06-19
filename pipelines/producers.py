import os
import pandas as pd

from config import ENDPOINTS, OUTPUT_DIR, get_headers
from client import fetch
from loader import save_to_db


# ── Transform ─────────────────────────────────────────────────────────────────

def build_producers(raw: pd.DataFrame) -> pd.DataFrame:
    df = raw[raw["state"] == "A"].copy()

    columns = ["code", "person_code", "state", "order_no"]
    df = df[[c for c in columns if c in df.columns]]

    df["order_no"] = pd.to_numeric(df["order_no"], errors="coerce")

    return df.drop_duplicates(subset=["code"]).reset_index(drop=True)


# ── Run ───────────────────────────────────────────────────────────────────────

def run():
    print("=== Producers pipeline ===")

    # 1. Extract
    raw = fetch(ENDPOINTS["producer"], get_headers(), key="producer")
    if raw.empty:
        print("Ma'lumot kelmadi, pipeline to'xtatildi.")
        return

    # 2. Transform
    producers = build_producers(raw)

    # 3. Load — Excel
    producers.to_excel(
        os.path.join(OUTPUT_DIR, "producers.xlsx"), index=False
    )

    # 4. Load — PostgreSQL
    save_to_db(producers, "producers")

    print("=== Producers pipeline tugadi ===")