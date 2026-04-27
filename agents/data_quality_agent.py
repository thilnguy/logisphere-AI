"""
Data Quality Agent (Agent 1 / 4)
================================
Scans raw input data for structural anomalies BEFORE cleaning.
If the error rate exceeds the configured threshold (default 20%),
the pipeline is halted and an alert is generated.

Responsibilities:
  - Validate required columns exist
  - Check data types per column (numeric columns must be numeric)
  - Measure overall error rate
  - Generate a validation report (JSON)
"""

import json
import os
import pandas as pd
import numpy as np
from datetime import datetime

CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config", "master_data.json")
REPORT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "reports")


def _load_config() -> dict:
    with open(CONFIG_PATH, "r") as f:
        return json.load(f)


def validate(input_path: str) -> dict:
    """
    Validate a raw logistics file.

    Returns a report dict:
      {
        "status": "PASS" | "FAIL",
        "timestamp": ...,
        "input_file": ...,
        "total_rows": ...,
        "error_rows": ...,
        "error_rate_pct": ...,
        "issues": [...]
      }
    """
    config = _load_config()
    dq = config["data_quality"]
    required_cols = dq["required_columns"]
    max_error_pct = dq["max_error_rate_pct"]

    # --- Read file ---
    ext = os.path.splitext(input_path)[1].lower()
    if ext in (".xlsx", ".xls"):
        df = pd.read_excel(input_path, engine="openpyxl")
    else:
        df = pd.read_csv(input_path)

    issues = []
    error_row_flags = pd.Series(False, index=df.index)

    # 1. Check required columns
    missing_cols = [c for c in required_cols if c not in df.columns]
    if missing_cols:
        issues.append({
            "type": "MISSING_COLUMNS",
            "severity": "CRITICAL",
            "detail": f"Missing columns: {missing_cols}"
        })

    # 2. Check numeric columns contain valid numbers
    numeric_cols = ["weight_kg", "distance_km", "shipping_cost_eur"]
    for col in numeric_cols:
        if col not in df.columns:
            continue
        converted = pd.to_numeric(df[col], errors="coerce")
        bad_mask = converted.isna() & df[col].notna()
        n_bad = bad_mask.sum()
        if n_bad > 0:
            error_row_flags |= bad_mask
            issues.append({
                "type": "INVALID_NUMERIC",
                "severity": "HIGH",
                "column": col,
                "bad_count": int(n_bad),
                "detail": f"Column '{col}' contains {n_bad} non-numeric values"
            })

    # 3. Check date columns are parseable (try multiple strategies)
    date_cols = ["order_date", "delivery_date"]
    for col in date_cols:
        if col not in df.columns:
            continue
        non_null = df[col].dropna()
        # Try both parsing strategies — mixed formats are expected
        parsed_a = pd.to_datetime(non_null, errors="coerce", dayfirst=True, format="mixed")
        parsed_b = pd.to_datetime(non_null, errors="coerce", dayfirst=False, format="mixed")
        # A date is truly bad only if BOTH strategies fail
        combined_good = parsed_a.notna() | parsed_b.notna()
        truly_bad = ~combined_good
        bad_mask_full = pd.Series(False, index=df.index)
        if truly_bad.sum() > 0:
            bad_mask_full.loc[truly_bad.index[truly_bad]] = True
            error_row_flags |= bad_mask_full
            issues.append({
                "type": "INVALID_DATE",
                "severity": "MEDIUM",
                "column": col,
                "bad_count": int(truly_bad.sum()),
                "detail": f"Column '{col}' has {truly_bad.sum()} unparseable dates"
            })

    # 4. Check tracking_id blanks
    if "tracking_id" in df.columns:
        blank_tracking = df["tracking_id"].isna() | (df["tracking_id"].astype(str).str.strip() == "")
        n_blank = blank_tracking.sum()
        if n_blank > 0:
            error_row_flags |= blank_tracking
            issues.append({
                "type": "BLANK_TRACKING_ID",
                "severity": "HIGH",
                "bad_count": int(n_blank),
                "detail": f"{n_blank} rows have blank tracking IDs"
            })

    # 5. Check carrier blanks
    if "carrier" in df.columns:
        blank_carrier = df["carrier"].isna() | (df["carrier"].astype(str).str.strip() == "")
        n_blank = blank_carrier.sum()
        if n_blank > 0:
            issues.append({
                "type": "BLANK_CARRIER",
                "severity": "LOW",
                "bad_count": int(n_blank),
                "detail": f"{n_blank} rows have blank carrier (will be filled by Cleaner Agent)"
            })

    # --- Compute error rate ---
    total_rows = len(df)
    error_rows = int(error_row_flags.sum())
    error_rate = round((error_rows / total_rows) * 100, 2) if total_rows > 0 else 0

    status = "FAIL" if error_rate > max_error_pct else "PASS"

    report = {
        "status": status,
        "timestamp": datetime.utcnow().isoformat(),
        "input_file": input_path,
        "total_rows": total_rows,
        "error_rows": error_rows,
        "error_rate_pct": error_rate,
        "threshold_pct": max_error_pct,
        "issues": issues,
    }

    # Save report
    os.makedirs(REPORT_DIR, exist_ok=True)
    report_path = os.path.join(REPORT_DIR, "validation_report.json")
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    # Console summary
    icon = "✅" if status == "PASS" else "🚨"
    print(f"{icon} Data Quality Agent: {status} | Errors: {error_rows}/{total_rows} ({error_rate}%) | Issues: {len(issues)}")
    if status == "FAIL":
        print(f"   ⛔ PIPELINE HALTED: Error rate {error_rate}% exceeds threshold {max_error_pct}%")
        print(f"   → Alerte : 'Les données téléchargées présentent une anomalie > {max_error_pct}%, veuillez vérifier la source d'extraction'")

    return report


if __name__ == "__main__":
    raw_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "raw", "Logistics_Raw_July.xlsx")
    validate(raw_path)
