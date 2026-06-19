import os
import pandas as pd

from config import ENDPOINTS, OUTPUT_DIR, get_headers
from client import fetch
from loader import save_to_db


# ── Transform funksiyalari ────────────────────────────────────────────────────

def build_services(raw: pd.DataFrame) -> pd.DataFrame:
    df = raw[raw["state"] == "A"].copy()

    columns = [
        "service_id", "code", "name", "short_name",
        "measure_code", "state", "order_no",
        "groups",   # nested — keyinroq ajratiladi
    ]
    df = df[[c for c in columns if c in df.columns]]

    df["service_id"] = pd.to_numeric(df["service_id"], errors="coerce").astype("Int64")
    df["order_no"]   = pd.to_numeric(df["order_no"],   errors="coerce")

    return df.drop_duplicates(subset=["service_id"]).reset_index(drop=True)


def build_service_group(dim: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, row in dim[["service_id", "groups"]].iterrows():
        groups = row["groups"]
        if not isinstance(groups, list):
            continue
        for g in groups:
            gc = g.get("group_code")
            if gc:
                rows.append({
                    "service_id": row["service_id"],
                    "group_code": str(gc).strip(),
                    "type_code":  str(g.get("type_code", "")).strip() or None,
                })

    if not rows:
        return pd.DataFrame(columns=["service_id", "group_code", "type_code"])

    df = pd.DataFrame(rows)
    df["service_id"] = pd.to_numeric(df["service_id"], errors="coerce").astype("Int64")
    df = df.dropna(subset=["service_id"])
    return df.drop_duplicates(subset=["service_id", "group_code"]).reset_index(drop=True)


# ── Run ───────────────────────────────────────────────────────────────────────

def run():
    print("=== Service pipeline ===")

    # 1. Extract
    raw = fetch(ENDPOINTS["service"], get_headers(), key="service")
    if raw.empty:
        print("Ma'lumot kelmadi, pipeline to'xtatildi.")
        return

    # 2. Transform
    dim           = build_services(raw)
    service_group = build_service_group(dim)

    # nested ustunni olib tashlash
    services = dim.drop(columns=["groups"], errors="ignore")

    # 3. Load — Excel
    services.to_excel(
        os.path.join(OUTPUT_DIR, "services.xlsx"), index=False
    )
    service_group.to_excel(
        os.path.join(OUTPUT_DIR, "service_group.xlsx"), index=False
    )

    # 4. Load — PostgreSQL
    save_to_db(services,      "services")
    save_to_db(service_group, "service_group")

    print("=== Service pipeline tugadi ===")