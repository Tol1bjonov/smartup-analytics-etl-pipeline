import os
import pandas as pd

from config import ENDPOINTS, OUTPUT_DIR, get_headers
from client import fetch
from loader import save_to_db


# ── Transform funksiyalari ────────────────────────────────────────────────────

def build_orders(raw: pd.DataFrame) -> pd.DataFrame:
    nested = [
        "order_products", "order_gifts",
        "order_actions", "order_consignments",
    ]
    columns = [
        "filial_code", "external_id", "deal_id", "invoice_external_id",
        "subfilial_code", "deal_time", "delivery_number", "delivery_date",
        "booked_date", "total_amount", "room_id", "room_code", "room_name",
        "robot_code", "lap_code",
        "sales_manager_id", "sales_manager_code", "sales_manager_name",
        "expeditor_id", "expeditor_code", "expeditor_name",
        "person_id", "person_code", "person_name", "person_local_code",
        "person_latitude", "person_longitude", "person_tin",
        "currency_code", "owner_person_code", "manager_code", "van_code",
        "contract_code", "contract_number", "invoice_number",
        "payment_type_code", "deal_margin_kind", "deal_margin_value",
        "visit_payment_type_code", "note", "deal_note", "status",
        "with_marking", "self_shipment",
        "delivery_address_short", "delivery_address_full",
        "marking_attaching_method", "visit_id",
        "total_weight_netto", "total_weight_brutto", "total_litre",
        *nested,
    ]
    df = raw[[c for c in columns if c in raw.columns]].copy()

    # Numeric castlar
    for col in ("deal_id", "room_id", "sales_manager_id",
                "expeditor_id", "person_id", "visit_id"):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").astype("Int64")

    for col in ("total_amount", "deal_margin_value",
                "total_weight_netto", "total_weight_brutto", "total_litre"):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Boolean
    for col in ("with_marking", "self_shipment"):
        if col in df.columns:
            df[col] = df[col].map(
                lambda v: True if str(v).strip().upper() in ("1", "TRUE", "T", "YES")
                else (False if str(v).strip().upper() in ("0", "FALSE", "F", "NO")
                      else pd.NA)
            )

    return df.drop_duplicates(subset=["deal_id"]).reset_index(drop=True)


def build_order_products(dim: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, row in dim[["deal_id", "order_products"]].iterrows():
        products = row["order_products"]
        if not isinstance(products, list):
            continue
        for p in products:
            rows.append({
                "deal_id":           row["deal_id"],
                "external_id":       p.get("external_id"),
                "product_unit_id":   p.get("product_unit_id"),
                "product_code":      p.get("product_code"),
                "product_local_code":p.get("product_local_code"),
                "product_name":      p.get("product_name"),
                "serial_number":     p.get("serial_number"),
                "expiry_date":       p.get("expiry_date"),
                "order_quant":       p.get("order_quant"),
                "sold_quant":        p.get("sold_quant"),
                "return_quant":      p.get("return_quant"),
                "inventory_kind":    p.get("inventory_kind"),
                "on_balance":        p.get("on_balance"),
                "card_code":         p.get("card_code"),
                "warehouse_code":    p.get("warehouse_code"),
                "product_price":     p.get("product_price"),
                "margin_amount":     p.get("margin_amount"),
                "margin_value":      p.get("margin_value"),
                "margin_kind":       p.get("margin_kind"),
                "vat_amount":        p.get("vat_amount"),
                "vat_percent":       p.get("vat_percent"),
                "sold_amount":       p.get("sold_amount"),
                "price_type_code":   p.get("price_type_code"),
                "price_type_id":     p.get("price_type_id"),
                # details & action_margins — alohida jadvalda
                "_details":          p.get("details", []),
                "_action_margins":   p.get("action_margins", []),
            })

    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows)
    df["deal_id"]         = pd.to_numeric(df["deal_id"],         errors="coerce").astype("Int64")
    df["product_unit_id"] = pd.to_numeric(df["product_unit_id"], errors="coerce").astype("Int64")
    df["price_type_id"]   = pd.to_numeric(df["price_type_id"],   errors="coerce").astype("Int64")

    for col in ("order_quant", "sold_quant", "return_quant",
                "product_price", "margin_amount", "margin_value",
                "vat_amount", "vat_percent", "sold_amount"):
        df[col] = pd.to_numeric(df[col], errors="coerce")

    return df.drop_duplicates(
        subset=["deal_id", "product_unit_id", "external_id"]
    ).reset_index(drop=True)


def build_order_product_details(order_products: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, row in order_products[["deal_id", "product_unit_id", "_details"]].iterrows():
        details = row["_details"]
        if not isinstance(details, list):
            continue
        for d in details:
            rows.append({
                "deal_id":        row["deal_id"],
                "product_unit_id":row["product_unit_id"],
                "expiry_date":    d.get("expiry_date"),
                "card_code":      d.get("card_code"),
                "batch_number":   d.get("batch_number"),
                "sold_quant":     d.get("sold_quant"),
            })

    if not rows:
        return pd.DataFrame(columns=[
            "deal_id", "product_unit_id", "expiry_date",
            "card_code", "batch_number", "sold_quant"
        ])

    df = pd.DataFrame(rows)
    df["deal_id"]         = pd.to_numeric(df["deal_id"],         errors="coerce").astype("Int64")
    df["product_unit_id"] = pd.to_numeric(df["product_unit_id"], errors="coerce").astype("Int64")
    df["sold_quant"]      = pd.to_numeric(df["sold_quant"],      errors="coerce")
    return df.reset_index(drop=True)


def build_order_product_action_margins(order_products: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, row in order_products[["deal_id", "product_unit_id", "_action_margins"]].iterrows():
        margins = row["_action_margins"]
        if not isinstance(margins, list):
            continue
        for m in margins:
            rows.append({
                "deal_id":          row["deal_id"],
                "product_unit_id":  row["product_unit_id"],
                "bonus_calc_level": m.get("bonus_calc_level"),
                "bonus_id":         m.get("bonus_id"),
                "margin_value":     m.get("margin_value"),
                "margin_kind":      m.get("margin_kind"),
                "action_name":      m.get("action_name"),
            })

    if not rows:
        return pd.DataFrame(columns=[
            "deal_id", "product_unit_id", "bonus_calc_level",
            "bonus_id", "margin_value", "margin_kind", "action_name"
        ])

    df = pd.DataFrame(rows)
    df["deal_id"]         = pd.to_numeric(df["deal_id"],         errors="coerce").astype("Int64")
    df["product_unit_id"] = pd.to_numeric(df["product_unit_id"], errors="coerce").astype("Int64")
    df["bonus_id"]        = pd.to_numeric(df["bonus_id"],        errors="coerce").astype("Int64")
    df["margin_value"]    = pd.to_numeric(df["margin_value"],    errors="coerce")
    return df.reset_index(drop=True)


def _build_order_line_items(dim: pd.DataFrame, col: str, extra_fields: list) -> pd.DataFrame:
    """order_gifts va order_actions uchun umumiy helper."""
    rows = []
    for _, row in dim[["deal_id", col]].iterrows():
        items = row[col]
        if not isinstance(items, list):
            continue
        for item in items:
            entry = {"deal_id": row["deal_id"]}
            for f in extra_fields:
                entry[f] = item.get(f)
            rows.append(entry)

    if not rows:
        return pd.DataFrame(columns=["deal_id"] + extra_fields)

    df = pd.DataFrame(rows)
    df["deal_id"] = pd.to_numeric(df["deal_id"], errors="coerce").astype("Int64")
    if "product_unit_id" in df.columns:
        df["product_unit_id"] = pd.to_numeric(df["product_unit_id"], errors="coerce").astype("Int64")
    for qcol in ("order_quant", "sold_quant", "return_quant"):
        if qcol in df.columns:
            df[qcol] = pd.to_numeric(df[qcol], errors="coerce")
    return df.reset_index(drop=True)


def build_order_gifts(dim: pd.DataFrame) -> pd.DataFrame:
    fields = [
        "external_id", "product_unit_id", "product_code", "product_local_code",
        "product_name", "serial_number", "expiry_date",
        "order_quant", "sold_quant", "return_quant",
        "inventory_kind", "on_balance", "card_code", "warehouse_code",
    ]
    return _build_order_line_items(dim, "order_gifts", fields)


def build_order_actions(dim: pd.DataFrame) -> pd.DataFrame:
    fields = [
        "external_id", "product_unit_id", "product_code", "product_local_code",
        "product_name", "serial_number", "expiry_date",
        "order_quant", "sold_quant", "return_quant",
        "inventory_kind", "on_balance", "card_code", "warehouse_code",
        "bonus_id", "action_name",
    ]
    return _build_order_line_items(dim, "order_actions", fields)


def build_order_consignments(dim: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, row in dim[["deal_id", "order_consignments"]].iterrows():
        items = row["order_consignments"]
        if not isinstance(items, list):
            continue
        for c in items:
            rows.append({
                "deal_id":            row["deal_id"],
                "external_id":        c.get("external_id"),
                "consignment_unit_id":c.get("consignment_unit_id"),
                "consignment_date":   c.get("consignment_date"),
                "consignment_amount": c.get("consignment_amount"),
            })

    if not rows:
        return pd.DataFrame(columns=[
            "deal_id", "external_id", "consignment_unit_id",
            "consignment_date", "consignment_amount"
        ])

    df = pd.DataFrame(rows)
    df["deal_id"]             = pd.to_numeric(df["deal_id"],             errors="coerce").astype("Int64")
    df["consignment_unit_id"] = pd.to_numeric(df["consignment_unit_id"], errors="coerce").astype("Int64")
    df["consignment_amount"]  = pd.to_numeric(df["consignment_amount"],  errors="coerce")
    return df.reset_index(drop=True)


# ── Run ───────────────────────────────────────────────────────────────────────

def run():
    print("=== Orders pipeline ===")

    # 1. Extract
    raw = fetch(ENDPOINTS["order"], get_headers(), key="order")
    if raw.empty:
        print("Ma'lumot kelmadi, pipeline to'xtatildi.")
        return

    # 2. Transform
    dim              = build_orders(raw)
    op_full          = build_order_products(dim)           # nested saqlanadi (_details, _action_margins)
    op_details       = build_order_product_details(op_full)
    op_margins       = build_order_product_action_margins(op_full)
    order_gifts      = build_order_gifts(dim)
    order_actions    = build_order_actions(dim)
    order_consign    = build_order_consignments(dim)

    # nested ustunlarni olib tashlash
    nested_order = ["order_products", "order_gifts", "order_actions", "order_consignments"]
    orders = dim.drop(columns=[c for c in nested_order if c in dim.columns])

    order_products = op_full.drop(columns=["_details", "_action_margins"], errors="ignore")

    # 3. Load — Excel
    orders.to_excel(            os.path.join(OUTPUT_DIR, "orders.xlsx"),                        index=False)
    order_products.to_excel(    os.path.join(OUTPUT_DIR, "order_products.xlsx"),                index=False)
    op_details.to_excel(        os.path.join(OUTPUT_DIR, "order_product_details.xlsx"),         index=False)
    op_margins.to_excel(        os.path.join(OUTPUT_DIR, "order_product_action_margins.xlsx"),  index=False)
    order_gifts.to_excel(       os.path.join(OUTPUT_DIR, "order_gifts.xlsx"),                   index=False)
    order_actions.to_excel(     os.path.join(OUTPUT_DIR, "order_actions.xlsx"),                 index=False)
    order_consign.to_excel(     os.path.join(OUTPUT_DIR, "order_consignments.xlsx"),            index=False)

    # 4. Load — PostgreSQL
    save_to_db(orders,          "orders")
    save_to_db(order_products,  "order_products")
    save_to_db(op_details,      "order_product_details")
    save_to_db(op_margins,      "order_product_action_margins")
    save_to_db(order_gifts,     "order_gifts")
    save_to_db(order_actions,   "order_actions")
    save_to_db(order_consign,   "order_consignments")

    print("=== Orders pipeline tugadi ===")