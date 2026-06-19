import os
import pandas as pd

from config import ENDPOINTS, OUTPUT_DIR, get_headers
from client import fetch
from loader import save_to_db


def build_purchases(raw: pd.DataFrame) -> pd.DataFrame:
    columns = [
        "filial_code", "external_id", "purchase_id", "purchase_time",
        "purchase_number", "input_date", "supplier_code", "invoice_number",
        "invoice_date", "order_id", "currency_code", "contract_code",
        "total_margin_kind", "total_margin_value", "warehouse_code",
        "status_code", "note", "posted",
        "purchase_items",
    ]
    df = raw[[c for c in columns if c in raw.columns]].copy()
    for col in ("purchase_id", "order_id"):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").astype("Int64")
    df["total_margin_value"] = pd.to_numeric(df.get("total_margin_value"), errors="coerce")
    return df.drop_duplicates(subset=["purchase_id"]).reset_index(drop=True)


def build_purchase_items(dim: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, row in dim[["purchase_id", "purchase_items"]].iterrows():
        items = row["purchase_items"]
        if not isinstance(items, list):
            continue
        for item in items:
            # marking_codes — alohida jadval
            rows.append({
                "purchase_id":      row["purchase_id"],
                "external_id":      item.get("external_id"),
                "purchase_item_id": item.get("purchase_item_id"),
                "product_code":     item.get("product_code"),
                "inventory_kind":   item.get("inventory_kind"),
                "order_item_id":    item.get("order_item_id"),
                "on_balance":       item.get("on_balance"),
                "serial_number":    item.get("serial_number"),
                "card_code":        item.get("card_code"),
                "expiry_date":      item.get("expiry_date"),
                "base_price":       item.get("base_price"),
                "quantity":         item.get("quantity"),
                "price":            item.get("price"),
                "margin_kind":      item.get("margin_kind"),
                "margin_value":     item.get("margin_value"),
                "vat_percent":      item.get("vat_percent"),
                "vat_amount":       item.get("vat_amount"),
                "_marking_codes":   item.get("marking_codes", []),
            })
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows)
    df["purchase_id"]      = pd.to_numeric(df["purchase_id"],      errors="coerce").astype("Int64")
    df["purchase_item_id"] = pd.to_numeric(df["purchase_item_id"], errors="coerce").astype("Int64")
    df["order_item_id"]    = pd.to_numeric(df["order_item_id"],    errors="coerce").astype("Int64")
    for col in ("base_price", "quantity", "price", "margin_value", "vat_percent", "vat_amount"):
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df.drop_duplicates(subset=["purchase_id", "purchase_item_id"]).reset_index(drop=True)


def build_purchase_marking_codes(items_df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, row in items_df[["purchase_id", "purchase_item_id", "_marking_codes"]].iterrows():
        codes = row["_marking_codes"]
        if not isinstance(codes, list):
            continue
        for mc in codes:
            code = mc.get("marking_code")
            if code:
                rows.append({
                    "purchase_id":      row["purchase_id"],
                    "purchase_item_id": row["purchase_item_id"],
                    "marking_code":     str(code).strip(),
                })
    if not rows:
        return pd.DataFrame(columns=["purchase_id", "purchase_item_id", "marking_code"])
    df = pd.DataFrame(rows)
    df["purchase_id"]      = pd.to_numeric(df["purchase_id"],      errors="coerce").astype("Int64")
    df["purchase_item_id"] = pd.to_numeric(df["purchase_item_id"], errors="coerce").astype("Int64")
    return df.drop_duplicates().reset_index(drop=True)


def run():
    print("=== Purchase pipeline ===")
    raw = fetch(ENDPOINTS["purchase"], get_headers(), key="purchase")
    if raw.empty:
        print("Ma'lumot kelmadi, pipeline to'xtatildi.")
        return

    dim              = build_purchases(raw)
    items_full       = build_purchase_items(dim)
    marking_codes    = build_purchase_marking_codes(items_full)
    purchases        = dim.drop(columns=["purchase_items"], errors="ignore")
    purchase_items   = items_full.drop(columns=["_marking_codes"], errors="ignore")

    purchases.to_excel(      os.path.join(OUTPUT_DIR, "purchases.xlsx"),               index=False)
    purchase_items.to_excel( os.path.join(OUTPUT_DIR, "purchase_items.xlsx"),          index=False)
    marking_codes.to_excel(  os.path.join(OUTPUT_DIR, "purchase_marking_codes.xlsx"),  index=False)
    save_to_db(purchases,       "purchases")
    save_to_db(purchase_items,  "purchase_items")
    save_to_db(marking_codes,   "purchase_marking_codes")
    print("=== Purchase pipeline tugadi ===")