import json
import base64
import os

# ── API ───────────────────────────────────────────────────────────────────────
PROJECT_CODE = "trade"
FILIAL_ID    = "86401"
TIMEOUT      = 150

ENDPOINTS = {
    "inventory":       "https://smartup.online/b/anor/mxsx/mr/inventory$export",
    "natural_person":  "https://smartup.online/b/anor/mxsx/mr/natural_person$export",
    "service":         "https://smartup.online/b/anor/mxsx/mr/service$export",  # ← qo'sh,
    "product_group": "https://smartup.online/b/anor/mxsx/mr/product_group$export",
    "price_type" : "https://smartup.online/b/anor/api/v2/mkr/price_type$export",
    "inventory_price": "https://smartup.online/b/anor/api/v2/mkf/product_price$export",
    "producer": "https://smartup.online/b/anor/mxsx/mr/producer$export",
    "legal_entity": "https://smartup.online/b/anor/mxsx/mr/legal_person$export",
    "person_group": "https://smartup.online/b/anor/mxsx/mr/person_group$export",
    "workspace": "https://smartup.online/b/anor/mxsx/mrf/room$export",
    "contract": "https://smartup.online/b/anor/mxsx/mkf/contract$export",
    "return_reason": "https://smartup.online/b/anor/mxsx/mdeal/return_reason$export",
    "order": "https://smartup.online/b/trade/txs/tdeal/order$export",
    "return": "https://smartup.online/b/anor/mxsx/mdeal/return$export",
    "visit": "https://smartup.online/b/trade/txs/tvt/visit$export",
    "cross_movement": "https://smartup.online/b/anor/mxsx/mfm/movement$export",
    "internal_movement": "https://smartup.online/b/anor/mxsx/mkw/movement$export",
    "stocktaking":       "https://smartup.online/b/anor/mxsx/mkw/stocktaking$export",
    "writeoff":          "https://smartup.online/b/anor/mxsx/mkw/writeoff$export",
    "warehouse_input":   "https://smartup.online/b/anor/mxsx/mkw/input$export",
    "purchase":          "https://smartup.online/b/anor/mxsx/mkw/purchase$export",
    "logistics":         "https://smartup.online/b/trade/txs/tdeal/logistics$export"
}

# ── Database ──────────────────────────────────────────────────────────────────
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_URL = f"postgresql://postgres:postgres@{DB_HOST}:5432/smartup"
# ── Output ────────────────────────────────────────────────────────────────────
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "CleanedData")
os.makedirs(OUTPUT_DIR, exist_ok=True)


# Fayl tepasida (import os allaqachon bor)
AUTH_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "auth.json")

def get_headers() -> dict:
    with open(AUTH_PATH) as f:
        auth = json.load(f)

    token = base64.b64encode(
        f"{auth['username']}:{auth['password']}".encode()
    ).decode()

    return {
        "Authorization": f"Basic {token}",
        "project_code":  PROJECT_CODE,
        "filial_id":     FILIAL_ID,
    }