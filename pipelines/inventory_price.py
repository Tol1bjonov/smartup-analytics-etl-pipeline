import os
import pandas as pd

from config import ENDPOINTS, OUTPUT_DIR, get_headers
from client import fetch
from loader import save_to_db


# ── Transform funksiyalari ────────────────────────────────────────────────────

def build_inventory_prices(raw: pd.DataFrame) -> pd.DataFrame:
    columns = [
        "inventory_code", "inventory_barcode",
        "price_type",   # nested — keyinroq ajratiladi
    ]
    df = raw[[c for c in columns if c in raw.columns]].copy()

    return df.drop_duplicates(subset=["inventory_code"]).reset_index(drop=True)


def build_inventory_price_detail(dim: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, row in dim[["inventory_code", "price_type"]].iterrows():
        price_types = row["price_type"]
        if not isinstance(price_types, list):
            continue
        for pt in price_types:
            ptc = pt.get("price_type_code")
            if ptc:
                rows.append({
                    "inventory_code":  row["inventory_code"],
                    "price_type_code": str(ptc).strip(),
                    "card_code":       pt.get("card_code"),
                    "price":           pt.get("price"),
                })

    if not rows:
        return pd.DataFrame(columns=[
            "inventory_code", "price_type_code", "card_code", "price"
        ])

    df = pd.DataFrame(rows)
    df["price"] = pd.to_numeric(df["price"], errors="coerce")
    df = df.dropna(subset=["inventory_code", "price_type_code"])
    return df.drop_duplicates(
        subset=["inventory_code", "price_type_code", "card_code"]
    ).reset_index(drop=True)


# ── Run ───────────────────────────────────────────────────────────────────────

def run():
    print("=== Inventory Price pipeline ===")

    # 1. Extract
    raw = fetch(ENDPOINTS["inventory_price"], get_headers(), key="inventory")
    if raw.empty:
        print("Ma'lumot kelmadi, pipeline to'xtatildi.")
        return

    # 2. Transform
    dim                    = build_inventory_prices(raw)
    inventory_price_detail = build_inventory_price_detail(dim)

    # nested ustunni olib tashlash
    inventory_prices = dim.drop(columns=["price_type"], errors="ignore")

    # 3. Load — Excel
    inventory_prices.to_excel(
        os.path.join(OUTPUT_DIR, "inventory_prices.xlsx"), index=False
    )
    inventory_price_detail.to_excel(
        os.path.join(OUTPUT_DIR, "inventory_price_detail.xlsx"), index=False
    )

    # 4. Load — PostgreSQL
    save_to_db(inventory_prices,       "inventory_prices")
    save_to_db(inventory_price_detail, "inventory_price_detail")

    print("=== Inventory Price pipeline tugadi ===")