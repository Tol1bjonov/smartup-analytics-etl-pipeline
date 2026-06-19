import os
import pandas as pd

from config import ENDPOINTS, OUTPUT_DIR, get_headers
from client import fetch
from loader import save_to_db


def build_stocktakings(raw: pd.DataFrame) -> pd.DataFrame:
    columns = [
        "filial_code", "external_id", "stocktaking_id", "stocktaking_number",
        "stocktaking_date", "status", "warehouse_code", "currency_code",
        "reason_code", "note", "barcode", "income_batch_number",
        "c_income_amount", "c_income_amount_base",
        "c_expense_amount", "c_expense_amount_base",
        "stocktaking_items",
    ]
    df = raw[[c for c in columns if c in raw.columns]].copy()
    df["stocktaking_id"] = pd.to_numeric(df["stocktaking_id"], errors="coerce").astype("Int64")
    for col in ("c_income_amount", "c_income_amount_base", "c_expense_amount", "c_expense_amount_base"):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df.drop_duplicates(subset=["stocktaking_id"]).reset_index(drop=True)


def build_stocktaking_items(dim: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, row in dim[["stocktaking_id", "stocktaking_items"]].iterrows():
        items = row["stocktaking_items"]
        if not isinstance(items, list):
            continue
        for item in items:
            rows.append({
                "stocktaking_id":      row["stocktaking_id"],
                "external_id":         item.get("external_id"),
                "stocktaking_item_id": item.get("stocktaking_item_id"),
                "product_code":        item.get("product_code"),
                "inventory_kind":      item.get("inventory_kind"),
                "card_code":           item.get("card_code"),
                "serial_number":       item.get("serial_number"),
                "expiry_date":         item.get("expiry_date"),
                "balance_quantity":    item.get("balance_quantity"),
                "quantity":            item.get("quantity"),
                "batch_number":        item.get("batch_number"),
                "income_price":        item.get("income_price"),
                "income_amount":       item.get("income_amount"),
            })
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows)
    df["stocktaking_id"]      = pd.to_numeric(df["stocktaking_id"],      errors="coerce").astype("Int64")
    df["stocktaking_item_id"] = pd.to_numeric(df["stocktaking_item_id"], errors="coerce").astype("Int64")
    for col in ("balance_quantity", "quantity", "income_price", "income_amount"):
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df.drop_duplicates(subset=["stocktaking_id", "stocktaking_item_id"]).reset_index(drop=True)


def run():
    print("=== Stocktaking pipeline ===")
    raw = fetch(ENDPOINTS["stocktaking"], get_headers(), key="stocktaking")
    if raw.empty:
        print("Ma'lumot kelmadi, pipeline to'xtatildi.")
        return

    dim   = build_stocktakings(raw)
    items = build_stocktaking_items(dim)
    stocktakings = dim.drop(columns=["stocktaking_items"], errors="ignore")

    stocktakings.to_excel(os.path.join(OUTPUT_DIR, "stocktakings.xlsx"),      index=False)
    items.to_excel(       os.path.join(OUTPUT_DIR, "stocktaking_items.xlsx"), index=False)
    save_to_db(stocktakings, "stocktakings")
    save_to_db(items,        "stocktaking_items")
    print("=== Stocktaking pipeline tugadi ===")