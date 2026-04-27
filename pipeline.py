"""
Pipeline Orchestrator
=====================
Runs the full agent pipeline end-to-end:
  1. (Optional) Generate mock data
  2. Data Quality Agent   → Validate
  3. Cleaner Agent        → Clean & anonymize
  4. Analyst Agent        → Compute KPIs
  5. Return pipeline status for Dashboard

Usage:
  python pipeline.py              # Run full pipeline
  python pipeline.py --generate   # Generate mock data first, then run
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)

from agents.data_quality_agent import validate
from agents.cleaner_agent import clean
from agents.analyst_agent import analyze
from agents.optimization_agent import prescribe

RAW_DIR = os.path.join(PROJECT_ROOT, "data", "raw")
STATUS_FILE = os.path.join(PROJECT_ROOT, "data", "reports", "pipeline_status.json")


def run_pipeline(input_file: str = None, generate_data: bool = False) -> dict:
    """
    Execute the full logistics automation pipeline.
    Returns a status dict for the Dashboard Status Page.
    """
    status = {
        "pipeline_run": datetime.now(timezone.utc).isoformat(),
        "stages": {},
        "overall": "UNKNOWN",
    }

    # --- Stage 0: Generate mock data (optional) ---
    if generate_data:
        print("\n" + "=" * 60)
        print("🔧 STAGE 0: Generating Mock Data")
        print("=" * 60)
        try:
            from data.generate_mock_data import generate
            input_file = generate()
            status["stages"]["data_generation"] = {"status": "OK", "file": input_file}
        except Exception as e:
            status["stages"]["data_generation"] = {"status": "ERROR", "error": str(e)}
            status["overall"] = "FAILED"
            _save_status(status)
            return status

    if not input_file:
        # Default: pick latest file in raw dir
        input_file = _find_latest_raw()
        if not input_file:
            status["overall"] = "FAILED"
            status["stages"]["data_extraction"] = {"status": "ERROR", "error": "No raw files found in data/raw/"}
            _save_status(status)
            return status

    status["stages"]["data_extraction"] = {"status": "OK", "file": input_file}

    # --- Stage 1: Data Quality Validation ---
    print("\n" + "=" * 60)
    print("🔍 STAGE 1: Data Quality Validation")
    print("=" * 60)
    try:
        validation_report = validate(input_file)
        status["stages"]["validation"] = {
            "status": validation_report["status"],
            "error_rate_pct": validation_report["error_rate_pct"],
            "issues_count": len(validation_report["issues"]),
        }
        if validation_report["status"] == "FAIL":
            status["overall"] = "HALTED"
            print("\n🚨 Pipeline HALTED by Data Quality Agent. Fix data source and retry.")
            _save_status(status)
            return status
    except Exception as e:
        status["stages"]["validation"] = {"status": "ERROR", "error": str(e)}
        status["overall"] = "FAILED"
        _save_status(status)
        return status

    # --- Stage 2: Data Cleaning ---
    print("\n" + "=" * 60)
    print("🧹 STAGE 2: Data Cleaning & GDPR Compliance")
    print("=" * 60)
    try:
        cleaned_path = clean(input_file)
        status["stages"]["cleaning"] = {"status": "PASS", "output": cleaned_path}
    except Exception as e:
        status["stages"]["cleaning"] = {"status": "ERROR", "error": str(e)}
        status["overall"] = "FAILED"
        _save_status(status)
        return status

    # --- Stage 3: Analytics & KPI ---
    print("\n" + "=" * 60)
    print("📊 STAGE 3: Analytics & CO2 Tracking")
    print("=" * 60)
    try:
        kpi = analyze(cleaned_path)
        status["stages"]["analytics"] = {
            "status": "SUCCESS",
            "global_otif_pct": kpi.get("global_otif_pct"),
            "total_co2_kg": kpi.get("total_co2_kg"),
            "total_revenue_eur": kpi.get("total_revenue_eur"),
        }
    except Exception as e:
        status["stages"]["analytics"] = {"status": "ERROR", "error": str(e)}
        status["overall"] = "FAILED"
        _save_status(status)
        return status

    # --- Stage 4: Optimization & Strategy ---
    print("\n" + "=" * 60)
    print("🤖 STAGE 4: AI Optimization & Prescriptive Strategy")
    print("=" * 60)
    try:
        opt_plan = prescribe()
        status["stages"]["optimization"] = {"status": "READY", "recommendations": len(opt_plan.get("recommendations", []))}
        for rec in opt_plan.get("recommendations", []):
            print(f"   💡 Suggestion: {rec['action']}")
            print(f"      - Issue: {rec['issue']}")
            print(f"      - Likely Impact: {rec['impact']}")
    except Exception as e:
        status["stages"]["optimization"] = {"status": "ERROR", "error": str(e)}

    # --- All stages passed ---
    status["overall"] = "SUCCESS"
    _save_status(status)

    print("\n" + "=" * 60)
    print("🎉 PIPELINE COMPLETE — All stages passed!")
    print("=" * 60)
    print(f"   Run `streamlit run dashboard/app.py` to view Dashboard")

    return status


def _find_latest_raw() -> str | None:
    """Find the most recently modified file in data/raw/."""
    if not os.path.exists(RAW_DIR):
        return None
    files = [os.path.join(RAW_DIR, f) for f in os.listdir(RAW_DIR)
             if f.endswith((".xlsx", ".xls", ".csv"))]
    if not files:
        return None
    return max(files, key=os.path.getmtime)


def _save_status(status: dict):
    """Persist pipeline status for the Dashboard Status Page."""
    os.makedirs(os.path.dirname(STATUS_FILE), exist_ok=True)
    with open(STATUS_FILE, "w") as f:
        json.dump(status, f, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Supply Chain Automation Pipeline")
    parser.add_argument("--generate", action="store_true", help="Generate mock data before running")
    parser.add_argument("--input", type=str, help="Path to raw input file", default=None)
    args = parser.parse_args()

    run_pipeline(input_file=args.input, generate_data=args.generate)
