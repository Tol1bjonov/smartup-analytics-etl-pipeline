import os
import pandas as pd

from config import ENDPOINTS, OUTPUT_DIR, get_headers
from client import fetch
from loader import save_to_db


def build_inputs(raw: pd.DataFrame) -> pd.DataFrame:
    columns = [
        "filial_code", "external_id", "input_id", "input_number",
        "input_time", "status", "warehouse_code", "note",
        "input_items",
    ]
    df = raw[[c for c in columns if c in raw.columns]].copy()
    df["input_id"] = pd.to_numeric(df["input_id"], errors="coerce").astype("Int64")
    return df.drop_duplicates(subset=["input_id"]).reset_index(drop=True)


def build_input_items(dim: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, row in dim[["input_id", "input_items"]].iterrows():
        items = row["input_items"]
        if not isinstance(items, list):
            continue
        for item in items:
            rows.append({
                "input_id":        row["input_id"],
                "external_id":     item.get("external_id"),
                "input_item_id":   item.get("input_item_id"),
                "purchase_id":     item.get("purchase_id"),
                "purchase_item_id":item.get("purchase_item_id"),
                "product_code":    item.get("product_code"),
                "inventory_kind":  item.get("inventory_kind"),
                "card_code":       item.get("card_code"),
                "expiry_date":     item.get("expiry_date"),
                "quantity":        item.get("quantity"),
                "price":           item.get("price"),
                "margin_kind":     item.get("margin_kind"),
                "margin_value":    item.get("margin_value"),
                "vat_percent":     item.get("vat_percent"),
                "vat_amount":      item.get("vat_amount"),
            })
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows)
    df["input_id"]        = pd.to_numeric(df["input_id"],        errors="coerce").astype("Int64")
    df["input_item_id"]   = pd.to_numeric(df["input_item_id"],   errors="coerce").astype("Int64")
    df["purchase_id"]     = pd.to_numeric(df["purchase_id"],     errors="coerce").astype("Int64")
    df["purchase_item_id"]= pd.to_numeric(df["purchase_item_id"],errors="coerce").astype("Int64")
    for col in ("quantity", "price", "margin_value", "vat_percent", "vat_amount"):
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df.drop_duplicates(subset=["input_id", "input_item_id"]).reset_index(drop=True)


def run():
    print("=== Warehouse Input pipeline ===")
    raw = fetch(ENDPOINTS["warehouse_input"], get_headers(), key="input")
    if raw.empty:
        print("Ma'lumot kelmadi, pipeline to'xtatildi.")
        return

    dim   = build_inputs(raw)
    items = build_input_items(dim)
    inputs = dim.drop(columns=["input_items"], errors="ignore")

    inputs.to_excel(os.path.join(OUTPUT_DIR, "warehouse_inputs.xlsx"),      index=False)
    items.to_excel( os.path.join(OUTPUT_DIR, "warehouse_input_items.xlsx"), index=False)
    save_to_db(inputs, "warehouse_inputs")
    save_to_db(items,  "warehouse_input_items")
    print("=== Warehouse Input pipeline tugadi ===")