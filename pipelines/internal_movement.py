import os
import pandas as pd

from config import ENDPOINTS, OUTPUT_DIR, get_headers
from client import fetch
from loader import save_to_db


def build_internal_movements(raw: pd.DataFrame) -> pd.DataFrame:
    columns = [
        "filial_code", "external_id", "movement_id", "movement_number",
        "from_movement_date", "to_movement_date", "request_id", "status",
        "from_warehouse_code", "to_warehouse_code", "reason_code", "note",
        "barcode", "movement_items",
    ]
    df = raw[[c for c in columns if c in raw.columns]].copy()
    for col in ("movement_id", "request_id"):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").astype("Int64")
    return df.drop_duplicates(subset=["movement_id"]).reset_index(drop=True)


def build_internal_movement_items(dim: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, row in dim[["movement_id", "movement_items"]].iterrows():
        items = row["movement_items"]
        if not isinstance(items, list):
            continue
        for item in items:
            rows.append({
                "movement_id":      row["movement_id"],
                "external_id":      item.get("external_id"),
                "movement_item_id": item.get("movement_item_id"),
                "request_item_id":  item.get("request_item_id"),
                "product_code":     item.get("product_code"),
                "serial_number":    item.get("serial_number"),
                "inventory_kind":   item.get("inventory_kind"),
                "on_balance":       item.get("on_balance"),
                "card_code":        item.get("card_code"),
                "expiry_date":      item.get("expiry_date"),
                "quantity":         item.get("quantity"),
                "batch_number":     item.get("batch_number"),
            })
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows)
    df["movement_id"]      = pd.to_numeric(df["movement_id"],      errors="coerce").astype("Int64")
    df["movement_item_id"] = pd.to_numeric(df["movement_item_id"], errors="coerce").astype("Int64")
    df["quantity"]         = pd.to_numeric(df["quantity"],         errors="coerce")
    return df.drop_duplicates(subset=["movement_id", "movement_item_id"]).reset_index(drop=True)


def run():
    print("=== Internal Movement pipeline ===")
    raw = fetch(ENDPOINTS["internal_movement"], get_headers(), key="movement")
    if raw.empty:
        print("Ma'lumot kelmadi, pipeline to'xtatildi.")
        return

    dim   = build_internal_movements(raw)
    items = build_internal_movement_items(dim)
    movements = dim.drop(columns=["movement_items"], errors="ignore")

    movements.to_excel(os.path.join(OUTPUT_DIR, "internal_movements.xlsx"),      index=False)
    items.to_excel(    os.path.join(OUTPUT_DIR, "internal_movement_items.xlsx"), index=False)
    save_to_db(movements, "internal_movements")
    save_to_db(items,     "internal_movement_items")
    print("=== Internal Movement pipeline tugadi ===")