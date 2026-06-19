import os
import pandas as pd

from config import ENDPOINTS, OUTPUT_DIR, get_headers
from client import fetch
from loader import save_to_db


def build_logistics(raw: pd.DataFrame) -> pd.DataFrame:
    columns = [
        "logistics_id", "external_id", "delivery_date",
        "expeditor_code", "expeditor_name",
        "van_code", "van_name", "lap",
        "begin_location", "end_location",
        "cash_register_id", "cash_register_name",
        "deals",
    ]
    df = raw[[c for c in columns if c in raw.columns]].copy()
    for col in ("logistics_id", "cash_register_id"):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").astype("Int64")
    return df.drop_duplicates(subset=["logistics_id"]).reset_index(drop=True)


def build_logistics_deals(dim: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, row in dim[["logistics_id", "deals"]].iterrows():
        deals = row["deals"]
        if not isinstance(deals, list):
            continue
        for d in deals:
            rows.append({
                "logistics_id": row["logistics_id"],
                "deal_id":      d.get("deal_id"),
                "status":       d.get("status"),
                "external_id":  d.get("external_id"),
            })
    if not rows:
        return pd.DataFrame(columns=["logistics_id", "deal_id", "status", "external_id"])
    df = pd.DataFrame(rows)
    df["logistics_id"] = pd.to_numeric(df["logistics_id"], errors="coerce").astype("Int64")
    df["deal_id"]      = pd.to_numeric(df["deal_id"],      errors="coerce").astype("Int64")
    return df.drop_duplicates(subset=["logistics_id", "deal_id"]).reset_index(drop=True)


def run():
    print("=== Logistics pipeline ===")
    raw = fetch(ENDPOINTS["logistics"], get_headers(), key="logistics")
    if raw.empty:
        print("Ma'lumot kelmadi, pipeline to'xtatildi.")
        return

    dim              = build_logistics(raw)
    logistics_deals  = build_logistics_deals(dim)
    logistics        = dim.drop(columns=["deals"], errors="ignore")

    logistics.to_excel(       os.path.join(OUTPUT_DIR, "logistics.xlsx"),        index=False)
    logistics_deals.to_excel( os.path.join(OUTPUT_DIR, "logistics_deals.xlsx"),  index=False)
    save_to_db(logistics,       "logistics")
    save_to_db(logistics_deals, "logistics_deals")
    print("=== Logistics pipeline tugadi ===")