import os
import pandas as pd
from datetime import datetime, timedelta

from config import ENDPOINTS, OUTPUT_DIR, get_headers
from client import fetch_raw
from loader import save_to_db


# ── Helpers ───────────────────────────────────────────────────────────────────

def to_int(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce").astype("Int64")

def to_float(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce")


# ── Parse ─────────────────────────────────────────────────────────────────────

def parse_visits(visit_list: list):
    visits              = []
    person_types        = []
    stocks              = []
    merchandisings      = []
    assortments         = []
    planograms          = []
    planogram_equips    = []
    planogram_products  = []
    shelf_own           = []
    shelf_competitor    = []
    price_tags          = []
    displays            = []
    quizzes             = []
    equipments          = []
    comments            = []

    for block in visit_list:
        note = block.get("note", "")

        # visit_id — birinchi header dan olinadi
        headers = block.get("visit_headers") or []
        vid = headers[0].get("visit_id") if headers else None

        # ── visit_headers ────────────────────────────────────────────────────
        for vh in headers:
            visits.append({
                "visit_id":                  vh.get("visit_id"),
                "filial_code":               vh.get("filial_code"),
                "visit_date":                vh.get("visit_date"),
                "visit_start_time":          vh.get("visit_start_time"),
                "visit_end_time":            vh.get("visit_end_time"),
                "time_at_retail_outlet_sec": vh.get("time_at_retail_outlet_sec"),
                "person_name":               vh.get("person_name"),
                "person_code":               vh.get("person_code"),
                "person_id":                 vh.get("person_id"),
                "room_id":                   vh.get("room_id"),
                "room_name":                 vh.get("room_name"),
                "room_code":                 vh.get("room_code"),
                "supervisor_id":             vh.get("supervisor_id"),
                "sales_manager_id":          vh.get("sales_manager_id"),
                "sales_manager_name":        vh.get("sales_manager_name"),
                "sales_manager_code":        vh.get("sales_manager_code"),
                "visit_start_location":      vh.get("visit_start_location"),
                "visit_end_location":        vh.get("visit_end_location"),
                "is_planned":                vh.get("is_planned"),
                "visit_status":              vh.get("visit_status"),
                "note":                      note,
            })
            for pt in (vh.get("person_types") or []):
                person_types.append({
                    "visit_id":         vh.get("visit_id"),
                    "person_type_id":   pt.get("person_type_id"),
                    "person_type_name": pt.get("person_type_name"),
                })

        # ── stocks ───────────────────────────────────────────────────────────
        for s in (block.get("stocks") or []):
            stocks.append({
                "visit_id":           vid,
                "stock_product_code": s.get("stock_product_code"),
                "stock_quant":        s.get("stock_quant"),
                "stock_expiry_date":  s.get("stock_expiry_date"),
                "stock_card_code":    s.get("stock_card_code"),
            })

        # ── merchandisings ───────────────────────────────────────────────────
        for m in (block.get("merchandisings") or []):
            mid = m.get("merchandising_id")
            merchandisings.append({"visit_id": vid, "merchandising_id": mid})

            for a in (m.get("assortment") or []):
                assortments.append({
                    "visit_id":                       vid,
                    "merchandising_id":               mid,
                    "assortment_product_code":        a.get("assortment_product_code"),
                    "has_assortment":                 a.get("has_assortment"),
                    "assortment_product_quant":       a.get("assortment_product_quant"),
                    "assortment_product_ir_quant":    a.get("assortment_product_ir_quant"),
                    "assortment_unavail_reason_name": a.get("assortment_unavail_reason_name"),
                })

            for pl in (m.get("planograms") or []):
                plid = pl.get("planogram_id")
                planograms.append({
                    "visit_id":             vid,
                    "merchandising_id":     mid,
                    "planogram_id":         plid,
                    "planogram_name":       pl.get("planogram_name"),
                    "planogram_has_photo":  pl.get("planogram_has_photo"),
                    "planogram_photo_sha":  pl.get("planogram_photo_sha"),
                    "planogram_plan_quant": pl.get("planogram_plan_quant"),
                    "planogram_plan_sku":   pl.get("planogram_plan_sku"),
                    "planogram_fact_quant": pl.get("planogram_fact_quant"),
                    "planogram_fact_sku":   pl.get("planogram_fact_sku"),
                })
                for pe in (pl.get("planogram_equipments") or []):
                    planogram_equips.append({
                        "visit_id":                 vid,
                        "planogram_id":             plid,
                        "planogram_equipment_id":   pe.get("planogram_equipment_id"),
                        "planogram_equipment_name": pe.get("planogram_equipment_name"),
                    })
                for pp in (pl.get("planogram_products") or []):
                    planogram_products.append({
                        "visit_id":                        vid,
                        "planogram_id":                    plid,
                        "planogram_product_name":          pp.get("planogram_product_name"),
                        "planogram_sample_unit_id":        pp.get("planogram_sample_unit_id"),
                        "planogram_product_code":          pp.get("planogram_product_code"),
                        "planogram_product_plan_quant":    pp.get("planogram_product_plan_quant"),
                        "planogram_product_fact_quant":    pp.get("planogram_product_fact_quant"),
                        "planogram_match":                 pp.get("planogram_match"),
                        "planogram_match_face_quant":      pp.get("planogram_match_face_quant"),
                        "planogram_not_match_reason_name": pp.get("planogram_not_match_reason_name"),
                    })

            for ss in (m.get("shelf_shares") or []):
                for own in (ss.get("own_shelf_shares") or []):
                    shelf_own.append({
                        "visit_id":                     vid,
                        "merchandising_id":             mid,
                        "own_shelf_share_product_code": own.get("own_shelf_share_product_code"),
                        "own_shelf_share_product_quant":own.get("own_shelf_share_product_quant"),
                    })
                for comp in (ss.get("competitor_inventories") or []):
                    shelf_competitor.append({
                        "visit_id":                           vid,
                        "merchandising_id":                   mid,
                        "competitor_code":                    comp.get("competitor_code"),
                        "competitor_inventory_product_code":  comp.get("competitor_inventory_product_code"),
                        "competitor_inventory_product_quant": comp.get("competitor_inventory_product_quant"),
                    })

            for ptag in (m.get("price_tags") or []):
                price_tags.append({
                    "visit_id":                 vid,
                    "merchandising_id":         mid,
                    "price_tag_product_code":   ptag.get("price_tag_product_code"),
                    "has_price_tag":            ptag.get("has_price_tag"),
                    "price":                    ptag.get("price"),
                    "no_price_tag_reason_name": ptag.get("no_price_tag_reason_name"),
                })

            for d in (m.get("displays") or []):
                displays.append({
                    "visit_id":               vid,
                    "merchandising_id":       mid,
                    "display_id":             d.get("display_id"),
                    "display_name":           d.get("display_name"),
                    "has_display":            d.get("has_display"),
                    "display_photo_sha":      d.get("display_photo_sha"),
                    "no_display_reason_name": d.get("no_display_reason_name"),
                })

        # ── quizzes ──────────────────────────────────────────────────────────
        for q in (block.get("quizzes") or []):
            for qs in (q.get("quiz_sets") or []):
                quizzes.append({
                    "visit_id":       vid,
                    "quiz_name":      qs.get("quiz_name"),
                    "answer":         qs.get("answer"),
                    "has_quiz_photo": qs.get("has_quiz_photo"),
                })

        # ── equipments ───────────────────────────────────────────────────────
        for e in (block.get("equipments") or []):
            equipments.append({
                "visit_id":                vid,
                "equipment_id":            e.get("equipment_id"),
                "equipment_serial_number": e.get("equipment_serial_number"),
                "equipment_status":        e.get("equipment_status"),
            })

        # ── comments ─────────────────────────────────────────────────────────
        for c in (block.get("comments") or []):
            comments.append({
                "visit_id":                vid,
                "comment_name":            c.get("comment_name"),
                "comment_created_by_name": c.get("comment_created_by_name"),
            })

    # ── DataFrame ga o'tkazish ───────────────────────────────────────────────
    def make_df(rows, int_cols=None, float_cols=None):
        if not rows:
            return pd.DataFrame()
        df = pd.DataFrame(rows)
        for c in (int_cols or []):
            if c in df.columns:
                df[c] = to_int(df[c])
        for c in (float_cols or []):
            if c in df.columns:
                df[c] = to_float(df[c])
        return df

    int_base = ["visit_id", "person_id", "room_id", "supervisor_id",
                "sales_manager_id", "merchandising_id", "planogram_id",
                "planogram_equipment_id", "person_type_id", "display_id",
                "equipment_id", "planogram_sample_unit_id"]

    return {
        "visits":                     make_df(visits,            int_base, ["time_at_retail_outlet_sec"]),
        "visit_person_types":         make_df(person_types,      ["visit_id", "person_type_id"]),
        "visit_stocks":               make_df(stocks,            ["visit_id"], ["stock_quant"]),
        "visit_merchandisings":       make_df(merchandisings,    ["visit_id", "merchandising_id"]),
        "visit_assortments":          make_df(assortments,       ["visit_id", "merchandising_id"],
                                              ["assortment_product_quant", "assortment_product_ir_quant"]),
        "visit_planograms":           make_df(planograms,        int_base,
                                              ["planogram_plan_quant", "planogram_plan_sku",
                                               "planogram_fact_quant", "planogram_fact_sku"]),
        "visit_planogram_equipments": make_df(planogram_equips,  ["visit_id", "planogram_id", "planogram_equipment_id"]),
        "visit_planogram_products":   make_df(planogram_products,["visit_id", "planogram_id", "planogram_sample_unit_id"],
                                              ["planogram_product_plan_quant", "planogram_product_fact_quant",
                                               "planogram_match_face_quant"]),
        "visit_shelf_own":            make_df(shelf_own,         ["visit_id", "merchandising_id"],
                                              ["own_shelf_share_product_quant"]),
        "visit_shelf_competitor":     make_df(shelf_competitor,  ["visit_id", "merchandising_id"],
                                              ["competitor_inventory_product_quant"]),
        "visit_price_tags":           make_df(price_tags,        ["visit_id", "merchandising_id"], ["price"]),
        "visit_displays":             make_df(displays,          ["visit_id", "merchandising_id", "display_id"]),
        "visit_quizzes":              make_df(quizzes,           ["visit_id"]),
        "visit_equipments":           make_df(equipments,        ["visit_id", "equipment_id"]),
        "visit_comments":             make_df(comments,          ["visit_id"]),
    }


# ── Run ───────────────────────────────────────────────────────────────────────

def run():
    print("=== Visit pipeline ===")

    # So'nggi 7 kun (API cheklovi: faqat 7 kunlik ma'lumot)
    date_to   = datetime.today().strftime("%Y-%m-%d")
    date_from = (datetime.today() - timedelta(days=7)).strftime("%Y-%m-%d")

    body = {
        "date_from": date_from,
        "date_to":   date_to,
    }

    # 1. Extract
    visit_list = fetch_raw(ENDPOINTS["visit"], get_headers(), key="visit", body=body)
    # visit_list = visit_list.to_dict("records") #shu joyini olib tashlash kerak yoki ozgartirish kk
    if not visit_list:
        print("Ma'lumot kelmadi, pipeline to'xtatildi.")
        return

    # 2. Transform
    tables = parse_visits(visit_list)

    # 3 & 4. Load
    for table_name, df in tables.items():
        if df.empty:
            print(f"[SKIP] '{table_name}' — bo'sh")
            continue
        df.to_excel(os.path.join(OUTPUT_DIR, f"{table_name}.xlsx"), index=False)
        save_to_db(df, table_name)

    print("=== Visit pipeline tugadi ===")