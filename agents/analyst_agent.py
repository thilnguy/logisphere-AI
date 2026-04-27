"""
Analyst Agent (Agent 3 / 4)
===========================
Computes logistics KPIs and EU-mandated CO2 emissions from cleaned data.

Responsibilities:
  - OTIF (On-Time In-Full) per carrier
  - Average Lead Time per carrier & per warehouse
  - CO2 Emissions Tracking per shipment (EU reference factors)
  - Risk Level flagging for delayed / at-risk shipments
  - Summary statistics export
"""

import json
import os
from datetime import datetime, timezone
import pandas as pd
import numpy as np

CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config", "master_data.json")
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "analytics")
OUTPUT_SUMMARY = os.path.join(OUTPUT_DIR, "Analytics_Summary.csv")
OUTPUT_KPI = os.path.join(OUTPUT_DIR, "KPI_Report.json")


def _load_config() -> dict:
    with open(CONFIG_PATH, "r") as f:
        return json.load(f)


def analyze(input_path: str) -> dict:
    """
    Analyze cleaned logistics data. Returns KPI summary dict.
    """
    config = _load_config()
    co2_factors = config["co2_emission_factors"]

    df = pd.read_csv(input_path)
    print(f"📊 Analyst Agent: Loaded {len(df)} rows from {os.path.basename(input_path)}")

    # --- Parse dates ---
    df["order_date"] = pd.to_datetime(df["order_date"], errors="coerce")
    df["delivery_date"] = pd.to_datetime(df["delivery_date"], errors="coerce")

    # --- Lead Time (days) ---
    df["lead_time_days"] = (df["delivery_date"] - df["order_date"]).dt.days

    # --- OTIF: Delivered within <= 5 days baseline ---
    OTIF_BASELINE_DAYS = 5
    delivered = df[df["status"] == "Livré"].copy()
    delivered["on_time"] = delivered["lead_time_days"] <= OTIF_BASELINE_DAYS

    otif_by_carrier = delivered.groupby("carrier").agg(
        total_delivered=("on_time", "count"),
        on_time_count=("on_time", "sum"),
    )
    otif_by_carrier["otif_pct"] = round(
        otif_by_carrier["on_time_count"] / otif_by_carrier["total_delivered"] * 100, 2
    )

    # --- Average Lead Time per carrier ---
    lead_time_carrier = df.groupby("carrier")["lead_time_days"].mean().round(2)

    # --- Average Lead Time per warehouse ---
    lead_time_warehouse = df.groupby("origin_warehouse")["lead_time_days"].mean().round(2)

    # --- CO2 Emissions Tracking ---
    def calc_co2(row):
        factor = co2_factors.get(str(row.get("vehicle_type", "petit_camion")), 0.120)
        weight_tons = row.get("weight_kg", 0)
        if pd.isna(weight_tons):
            weight_tons = 0
        weight_tons = float(weight_tons) / 1000.0
        distance = float(row.get("distance_km", 0)) if pd.notna(row.get("distance_km")) else 0
        return round(factor * distance * weight_tons, 4)

    df["co2_kg"] = df.apply(calc_co2, axis=1)
    total_co2 = round(df["co2_kg"].sum(), 2)
    co2_by_carrier = df.groupby("carrier")["co2_kg"].sum().round(2)
    co2_by_vehicle = df.groupby("vehicle_type")["co2_kg"].sum().round(2)

    # --- Risk Level ---
    def flag_risk(row):
        if row["status"] == "Retardé":
            return "ÉLEVÉ"
        if row["status"] == "En transit" and pd.notna(row["lead_time_days"]) and row["lead_time_days"] > OTIF_BASELINE_DAYS:
            return "ÉLEVÉ"
        if row["status"] == "En transit":
            return "MOYEN"
        if row["status"] == "Livré" and pd.notna(row["lead_time_days"]) and row["lead_time_days"] > OTIF_BASELINE_DAYS:
            return "FAIBLE"
        return "AUCUN"

    df["risk_level"] = df.apply(flag_risk, axis=1)

    # --- Revenue / Cost summary ---
    total_revenue = round(df["shipping_cost_eur"].sum(), 2) if "shipping_cost_eur" in df.columns else 0
    cost_by_region = df.groupby("destination_city")["shipping_cost_eur"].sum().round(2) if "shipping_cost_eur" in df.columns else {}

    # --- KPI Report ---
    kpi = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "total_shipments": int(len(df)),
        "total_delivered": int(len(delivered)),
        "global_otif_pct": round(delivered["on_time"].mean() * 100, 2) if len(delivered) > 0 else 0,
        "avg_lead_time_days": round(df["lead_time_days"].mean(), 2) if df["lead_time_days"].notna().any() else None,
        "total_co2_kg": total_co2,
        "total_revenue_eur": total_revenue,
        "risk_distribution": df["risk_level"].value_counts().to_dict(),
        "otif_by_carrier": otif_by_carrier.to_dict("index"),
        "lead_time_by_carrier": lead_time_carrier.to_dict(),
        "lead_time_by_warehouse": lead_time_warehouse.to_dict(),
        "co2_by_carrier": co2_by_carrier.to_dict(),
        "co2_by_vehicle_type": co2_by_vehicle.to_dict(),
        "cost_by_city": cost_by_region.to_dict() if isinstance(cost_by_region, pd.Series) else {},
    }

    # --- Save outputs ---
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    df.to_csv(OUTPUT_SUMMARY, index=False)
    with open(OUTPUT_KPI, "w") as f:
        json.dump(kpi, f, indent=2, ensure_ascii=False, default=str)

    print(f"   📈 OTIF Global: {kpi['global_otif_pct']}%")
    print(f"   ⏱️  Avg Lead Time: {kpi['avg_lead_time_days']} days")
    print(f"   🌿 Total CO2: {total_co2} kg")
    print(f"   💰 Total Revenue: €{total_revenue}")
    print(f"   ⚠️  Risk: {df['risk_level'].value_counts().to_dict()}")
    print(f"✅ Analyst Agent: Output → {OUTPUT_SUMMARY}")

    return kpi


if __name__ == "__main__":
    cleaned_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "cleaned", "Logistics_Cleaned.csv")
    analyze(cleaned_path)
