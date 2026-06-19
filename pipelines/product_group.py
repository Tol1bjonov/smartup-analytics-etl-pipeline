import os
import pandas as pd

from config import ENDPOINTS, OUTPUT_DIR, get_headers
from client import fetch
from loader import save_to_db


# ── Transform funksiyalari ────────────────────────────────────────────────────

def build_product_groups(raw: pd.DataFrame) -> pd.DataFrame:
    df = raw[raw["state"] == "A"].copy()

    columns = [
        "product_group_id", "code", "name",
        "product_kind", "state",
        "product_group_types",  # nested — keyinroq ajratiladi
    ]
    df = df[[c for c in columns if c in df.columns]]

    df["product_group_id"] = pd.to_numeric(df["product_group_id"], errors="coerce").astype("Int64")

    return df.drop_duplicates(subset=["product_group_id"]).reset_index(drop=True)


def build_product_group_types(dim: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, row in dim[["product_group_id", "product_group_types"]].iterrows():
        types = row["product_group_types"]
        if not isinstance(types, list):
            continue
        for t in types:
            if t.get("state") != "A":
                continue
            rows.append({
                "product_group_id": row["product_group_id"],
                "code":             t.get("code"),
                "name":             t.get("name"),
                "order_no":         t.get("order_no"),
            })

    if not rows:
        return pd.DataFrame(columns=["product_group_id", "code", "name", "order_no"])

    df = pd.DataFrame(rows)
    df["product_group_id"] = pd.to_numeric(df["product_group_id"], errors="coerce").astype("Int64")
    df["order_no"]         = pd.to_numeric(df["order_no"],         errors="coerce")
    df = df.dropna(subset=["product_group_id", "code"])
    return df.drop_duplicates(subset=["product_group_id", "code"]).reset_index(drop=True)


# ── Run ───────────────────────────────────────────────────────────────────────

def run():
    print("=== Product Group pipeline ===")

    # 1. Extract
    raw = fetch(ENDPOINTS["product_group"], get_headers(), key="product_group")
    if raw.empty:
        print("Ma'lumot kelmadi, pipeline to'xtatildi.")
        return

    # 2. Transform
    dim                 = build_product_groups(raw)
    product_group_types = build_product_group_types(dim)

    # nested ustunni olib tashlash
    product_groups = dim.drop(columns=["product_group_types"], errors="ignore")

    # 3. Load — Excel
    product_groups.to_excel(
        os.path.join(OUTPUT_DIR, "product_groups.xlsx"), index=False
    )
    product_group_types.to_excel(
        os.path.join(OUTPUT_DIR, "product_group_types.xlsx"), index=False
    )

    # 4. Load — PostgreSQL
    save_to_db(product_groups,      "product_groups")
    save_to_db(product_group_types, "product_group_types")

    print("=== Product Group pipeline tugadi ===")
    