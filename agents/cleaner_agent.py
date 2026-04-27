"""
Cleaner Agent (Agent 2 / 4)
===========================
Transforms raw logistics data into a clean, GDPR-compliant,
standardized dataset ready for analytics.

Responsibilities:
  - GDPR Anonymization (hash PII columns)
  - Master Data Fuzzy Matching (carrier & warehouse name normalization)
  - Date format standardization (→ YYYY-MM-DD)
  - Duplicate tracking ID removal
  - Fill missing values
"""

import hashlib
import json
import os
import pandas as pd
import numpy as np
from thefuzz import fuzz, process

CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config", "master_data.json")
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "cleaned")
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "Logistics_Cleaned.csv")


def _load_config() -> dict:
    with open(CONFIG_PATH, "r") as f:
        return json.load(f)


def _anonymize_pii(df: pd.DataFrame, pii_columns: list) -> pd.DataFrame:
    """SHA-256 hash PII columns for GDPR compliance."""
    df = df.copy()
    for col in pii_columns:
        if col in df.columns:
            df[col] = df[col].apply(
                lambda x: hashlib.sha256(str(x).encode()).hexdigest()[:16] if pd.notna(x) else None
            )
    return df


def _fuzzy_map(value: str, canonical_map: dict, threshold: int) -> str:
    """Map a messy string to its canonical name using fuzzy matching."""
    if pd.isna(value) or str(value).strip() == "":
        return "Unknown"

    value_str = str(value).strip()

    # Direct match first (fast path)
    for canonical, variants in canonical_map.items():
        if value_str in variants:
            return canonical

    # Fuzzy match (slow path)
    all_variants = []
    variant_to_canonical = {}
    for canonical, variants in canonical_map.items():
        for v in variants:
            all_variants.append(v)
            variant_to_canonical[v] = canonical

    match, score = process.extractOne(value_str, all_variants, scorer=fuzz.ratio)
    if score >= threshold:
        return variant_to_canonical[match]

    return value_str  # Keep original if no match


def clean(input_path: str) -> str:
    """
    Clean & standardize raw logistics data.
    Returns path to the cleaned CSV file.
    """
    config = _load_config()

    # --- Read raw data ---
    ext = os.path.splitext(input_path)[1].lower()
    if ext in (".xlsx", ".xls"):
        df = pd.read_excel(input_path, engine="openpyxl")
    else:
        df = pd.read_csv(input_path)

    initial_rows = len(df)
    print(f"📥 Cleaner Agent: Loaded {initial_rows} rows from {os.path.basename(input_path)}")

    # 1. GDPR Anonymization
    pii_cols = config.get("pii_columns", [])
    df = _anonymize_pii(df, pii_cols)
    print(f"   🔒 GDPR: Anonymized {len([c for c in pii_cols if c in df.columns])} PII columns")

    # 2. Fuzzy Matching - Carriers
    carrier_config = config["carriers"]
    carrier_map = carrier_config["canonical_names"]
    carrier_threshold = carrier_config["fuzzy_threshold"]
    df["carrier"] = df["carrier"].apply(lambda x: _fuzzy_map(x, carrier_map, carrier_threshold))
    print(f"   🔗 Master Data: Carriers normalized to {df['carrier'].nunique()} canonical names")

    # 3. Fuzzy Matching - Warehouses
    wh_config = config["warehouses"]
    wh_map = wh_config["canonical_names"]
    wh_threshold = wh_config["fuzzy_threshold"]
    df["origin_warehouse"] = df["origin_warehouse"].apply(lambda x: _fuzzy_map(x, wh_map, wh_threshold))
    print(f"   🔗 Master Data: Warehouses normalized to {df['origin_warehouse'].nunique()} canonical names")

    # 4. Standardize dates → YYYY-MM-DD
    for col in ["order_date", "delivery_date"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce", dayfirst=True, format="mixed")
    
    # --- Chronology Fix: Ensure order_date <= delivery_date ---
    bad_dates_mask = (df["order_date"].notna()) & (df["delivery_date"].notna()) & (df["order_date"] > df["delivery_date"])
    bad_count = bad_dates_mask.sum()
    if bad_count > 0:
        # Heuristic fix: Swap dates if delivery is before order (often a swap/parsing error)
        temp = df.loc[bad_dates_mask, "order_date"].copy()
        df.loc[bad_dates_mask, "order_date"] = df.loc[bad_dates_mask, "delivery_date"]
        df.loc[bad_dates_mask, "delivery_date"] = temp
        print(f"   📅 Chronology: Fixed {bad_count} rows with inverted delivery/order dates")

    # Final string formatting
    for col in ["order_date", "delivery_date"]:
        if col in df.columns:
             df[col] = df[col].dt.strftime("%Y-%m-%d")
    
    print(f"   📅 Dates standardized to YYYY-MM-DD")

    # 5. Fix numeric columns
    if "weight_kg" in df.columns:
        df["weight_kg"] = pd.to_numeric(df["weight_kg"], errors="coerce")

    # 6. Remove duplicates
    before_dedup = len(df)
    df = df.drop_duplicates(subset=["tracking_id"], keep="last")
    deduped = before_dedup - len(df)
    print(f"   🧹 Removed {deduped} duplicate tracking IDs")

    # 7. Fill missing values
    df["carrier"] = df["carrier"].fillna("Unknown")
    df["status"] = df["status"].fillna("Unknown")
    df["vehicle_type"] = df["vehicle_type"].fillna("truck_small")

    # --- Save ---
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    df.to_csv(OUTPUT_FILE, index=False)
    print(f"✅ Cleaner Agent: Output {len(df)} clean rows → {OUTPUT_FILE}")

    return OUTPUT_FILE


if __name__ == "__main__":
    raw_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "raw", "Logistics_Raw_July.xlsx")
    clean(raw_path)
