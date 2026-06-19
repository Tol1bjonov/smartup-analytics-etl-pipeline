import os
import pandas as pd

from config import ENDPOINTS, OUTPUT_DIR, get_headers
from client import fetch
from loader import save_to_db


# ── Transform: Cross Movements ───────────────────────────────────────────────

def build_cross_movements(raw: pd.DataFrame) -> pd.DataFrame:
    columns = [
        "from_filial_code",
        "external_id",
        "movement_id",
        "subfilial_code",
        "to_subfilial_code",
        "from_room_code",
        "from_robot_code",
        "from_robot_person_code",
        "from_warehouse_code",
        "from_time",
        "to_filial_code",
        "to_warehouse_code",
        "to_time",
        "currency_code",
        "price_type_code",
        "payment_type_code",
        "to_payment_type_code",
        "request_id",
        "reason_id",
        "note",
        "barcode",
        "amount",
        "amount_base",
        "delivery_number",
        "contract_code",
        "status",
        "movement_items",
    ]

    df = raw[[c for c in columns if c in raw.columns]].copy()

    # Integer fields
    for col in ("movement_id", "request_id", "reason_id"):
        if col in df.columns:
            df[col] = pd.to_numeric(
                df[col],
                errors="coerce"
            ).astype("Int64")

    # Numeric fields
    for col in ("amount", "amount_base"):
        if col in df.columns:
            df[col] = pd.to_numeric(
                df[col],
                errors="coerce"
            )

    return (
        df.drop_duplicates(subset=["external_id"])
          .reset_index(drop=True)
    )


# ── Transform: Movement Items ────────────────────────────────────────────────

def build_cross_movement_items(dim: pd.DataFrame) -> pd.DataFrame:
    rows = []

    for _, row in dim[["movement_id", "external_id", "movement_items"]].iterrows():

        items = row["movement_items"]

        if not isinstance(items, list):
            continue

        for item in items:
            rows.append({
                "movement_id": row["movement_id"],
                "external_id": row["external_id"],
                "movement_unit_id": item.get("movement_unit_id"),
                "request_item_id": item.get("request_item_id"),
                "from_inventory_kind": item.get("from_inventory_kind"),
                "on_balance": item.get("on_balance"),
                "to_inventory_kind": item.get("to_inventory_kind"),
                "product_code": item.get("product_code"),
                "card_code": item.get("card_code"),
                "expiry_date": item.get("expiry_date"),
                "serial_number": item.get("serial_number"),
                "quantity": item.get("quantity"),
                "price": item.get("price"),
                "amount": item.get("amount"),
                "amount_base": item.get("amount_base"),
                "margin_kind": item.get("margin_kind"),
                "margin_value": item.get("margin_value"),
                "margin_amount": item.get("margin_amount"),
                "vat_percent": item.get("vat_percent"),
                "vat_amount": item.get("vat_amount"),
                "load_id": item.get("load_id"),
            })

    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows)

    # Integer fields
    for col in (
        "movement_id",
        "movement_unit_id",
        "request_item_id",
    ):
        if col in df.columns:
            df[col] = pd.to_numeric(
                df[col],
                errors="coerce"
            ).astype("Int64")

    # Numeric fields
    for col in (
        "quantity",
        "price",
        "amount",
        "amount_base",
        "margin_value",
        "margin_amount",
        "vat_percent",
        "vat_amount",
    ):
        if col in df.columns:
            df[col] = pd.to_numeric(
                df[col],
                errors="coerce"
            )

    return (
        df.drop_duplicates(
            subset=["movement_id", "movement_unit_id"]
        )
        .reset_index(drop=True)
    )


# ── Run ──────────────────────────────────────────────────────────────────────

def run():
    print("=== Cross Movement pipeline ===")

    raw = fetch(
        ENDPOINTS["cross_movement"],
        get_headers(),
        key="movement"
    )

    if raw.empty:
        print("Ma'lumot kelmadi, pipeline to'xtatildi.")
        return

    # Transform
    dim = build_cross_movements(raw)

    items = build_cross_movement_items(dim)

    movements = dim.drop(
        columns=["movement_items"],
        errors="ignore"
    )

    # Excel
    movements.to_excel(
        os.path.join(
            OUTPUT_DIR,
            "cross_movements.xlsx"
        ),
        index=False
    )

    items.to_excel(
        os.path.join(
            OUTPUT_DIR,
            "cross_movement_items.xlsx"
        ),
        index=False
    )

    # PostgreSQL
    save_to_db(
        movements,
        "cross_movements"
    )

    save_to_db(
        items,
        "cross_movement_items"
    )

    print("=== Cross Movement pipeline tugadi ===")