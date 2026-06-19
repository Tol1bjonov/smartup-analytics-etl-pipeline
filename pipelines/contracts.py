import os
import pandas as pd

from config import ENDPOINTS, OUTPUT_DIR, get_headers
from client import fetch
from loader import save_to_db


# ── Transform ────────────────────────────────────────────────────────────────

def build_contracts(raw: pd.DataFrame) -> pd.DataFrame:
    df = raw[raw["state"] == "A"].copy()

    columns = [
        "contract_id",
        "filial_code",
        "code",
        "contract_date",
        "contract_number",
        "name",
        "person_code",
        "currency_code",
        "expiry_date",
        "note",
        "initial_amount",
        "initial_expiry_date",
        "state",
        "is_main",
        "sub_contracts"
    ]

    df = df[[c for c in columns if c in df.columns]]

    df["contract_id"] = pd.to_numeric(
        df["contract_id"],
        errors="coerce"
    ).astype("Int64")

    return (
        df.drop_duplicates(subset=["contract_id"])
          .reset_index(drop=True)
    )


def build_sub_contracts(dim: pd.DataFrame) -> pd.DataFrame:
    rows = []

    for _, row in dim[["contract_id", "sub_contracts"]].iterrows():
        subs = row["sub_contracts"]

        if not isinstance(subs, list):
            continue

        for sub in subs:
            rows.append({
                "contract_id": row["contract_id"],
                "sub_contract_id": sub.get("sub_contract_id"),
                "sub_contract_date": sub.get("sub_contract_date"),
                "sub_contract_number": sub.get("sub_contract_number"),
                "amount": sub.get("amount"),
                "expiry_date": sub.get("expiry_date")
            })

    if not rows:
        return pd.DataFrame(columns=[
            "contract_id",
            "sub_contract_id",
            "sub_contract_date",
            "sub_contract_number",
            "amount",
            "expiry_date"
        ])

    df = pd.DataFrame(rows)

    df["contract_id"] = pd.to_numeric(
        df["contract_id"],
        errors="coerce"
    ).astype("Int64")

    df["sub_contract_id"] = pd.to_numeric(
        df["sub_contract_id"],
        errors="coerce"
    ).astype("Int64")

    return (
        df.drop_duplicates(
            subset=["contract_id", "sub_contract_id"]
        )
        .reset_index(drop=True)
    )


# ── Run ──────────────────────────────────────────────────────────────────────

def run():
    print("=== Contract pipeline ===")

    # Extract
    raw = fetch(
        ENDPOINTS["contract"],
        get_headers(),
        key="contract"
    )

    if raw.empty:
        print("Ma'lumot kelmadi.")
        return

    # Transform
    dim = build_contracts(raw)

    sub_contracts = build_sub_contracts(dim)

    contracts = dim.drop(
        columns=["sub_contracts"],
        errors="ignore"
    )

    # Excel
    contracts.to_excel(
        os.path.join(OUTPUT_DIR, "contracts.xlsx"),
        index=False
    )

    sub_contracts.to_excel(
        os.path.join(OUTPUT_DIR, "sub_contracts.xlsx"),
        index=False
    )

    # PostgreSQL
    save_to_db(contracts, "contracts")
    save_to_db(sub_contracts, "sub_contracts")

    print("=== Contract pipeline tugadi ===")