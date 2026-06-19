import os
import pandas as pd

from config import ENDPOINTS, OUTPUT_DIR, get_headers
from client import fetch
from loader import save_to_db


def build_writeoffs(raw: pd.DataFrame) -> pd.DataFrame:
    columns = [
        "filial_code", "external_id", "writeoff_id", "writeoff_number",
        "writeoff_date", "status", "currency_code", "barcode",
        "warehouse_code", "reason_code", "note",
        "c_amount", "c_amount_base",
        "writeoff_items",
    ]
    df = raw[[c for c in columns if c in raw.columns]].copy()
    df["writeoff_id"] = pd.to_numeric(df["writeoff_id"], errors="coerce").astype("Int64")
    for col in ("c_amount", "c_amount_base"):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df.drop_duplicates(subset=["writeoff_id"]).reset_index(drop=True)


def build_writeoff_items(dim: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, row in dim[["writeoff_id", "writeoff_items"]].iterrows():
        items = row["writeoff_items"]
        if not isinstance(items, list):
            continue
        for item in items:
            rows.append({
                "writeoff_id":      row["writeoff_id"],
                "external_id":      item.get("external_id"),
                "writeoff_item_id": item.get("writeoff_item_id"),
                "inventory_kind":   item.get("inventory_kind"),
                "product_code":     item.get("product_code"),
                "serial_number":    item.get("serial_number"),
                "card_code":        item.get("card_code"),
                "expiry_date":      item.get("expiry_date"),
                "quantity":         item.get("quantity"),
                "batch_number":     item.get("batch_number"),
            })
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows)
    df["writeoff_id"]      = pd.to_numeric(df["writeoff_id"],      errors="coerce").astype("Int64")
    df["writeoff_item_id"] = pd.to_numeric(df["writeoff_item_id"], errors="coerce").astype("Int64")
    df["quantity"]         = pd.to_numeric(df["quantity"],         errors="coerce")
    return df.drop_duplicates(subset=["writeoff_id", "writeoff_item_id"]).reset_index(drop=True)


def run():
    print("=== Writeoff pipeline ===")
    raw = fetch(ENDPOINTS["writeoff"], get_headers(), key="writeoff")
    if raw.empty:
        print("Ma'lumot kelmadi, pipeline to'xtatildi.")
        return

    dim   = build_writeoffs(raw)
    items = build_writeoff_items(dim)
    writeoffs = dim.drop(columns=["writeoff_items"], errors="ignore")

    writeoffs.to_excel(os.path.join(OUTPUT_DIR, "writeoffs.xlsx"),      index=False)
    items.to_excel(    os.path.join(OUTPUT_DIR, "writeoff_items.xlsx"), index=False)
    save_to_db(writeoffs, "writeoffs")
    save_to_db(items,     "writeoff_items")
    print("=== Writeoff pipeline tugadi ===")