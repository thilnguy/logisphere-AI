"""
Optimization Agent — The Decision Intelligence layer.
===================================================
Analyzing performance gaps and prescribing business actions.
"""

import pandas as pd
import json
import os

INPUT_KPI = "data/analytics/KPI_Report.json"
OUTPUT_RECOMMENDATIONS = "data/analytics/Optimization_Plan.json"

def prescribe():
    base_dir = os.path.dirname(os.path.dirname(__file__))
    input_csv = os.path.join(base_dir, "data", "cleaned", "Logistics_Cleaned.csv")
    input_kpi = os.path.join(base_dir, "data", "analytics", "KPI_Report.json")
    output_file = os.path.join(base_dir, "data", "analytics", "Optimization_Plan.json")

    if not os.path.exists(input_csv) or not os.path.exists(input_kpi):
        return {"error": "Data missing for optimization"}

    with open(input_kpi) as f:
        kpi = json.load(f)
    
    df = pd.read_csv(input_csv)
    global_otif = kpi.get("global_otif_pct", 0)
    recommendations = []

    # 1. Route Bottleneck Analysis (Warehouse -> City)
    # Filter for delayed/risky shipments
    df["is_delayed"] = (df["status"] == "Retardé") | (df["status"] == "En transit") # Approximation for bottleneck
    route_stats = df.groupby(["origin_warehouse", "destination_city"]).agg(
        total=("tracking_id", "count"),
        delayed=("is_delayed", "sum")
    )
    route_stats["delay_rate"] = (route_stats["delayed"] / route_stats["total"] * 100).round(2)
    bottlenecks = route_stats[route_stats["total"] > 5].sort_values("delay_rate", ascending=False).head(2)

    for (warehouse, city), row in bottlenecks.iterrows():
        if row["delay_rate"] > 40:
            recommendations.append({
                "urgency": "HAUTE",
                "issue": f"Nœud critique: {warehouse} ➔ {city}",
                "finding": f"Taux d'anomalie de {row['delay_rate']}% sur cet axe ({int(row['delayed'])} retours/retards).",
                "action": f"Pré-positionner du stock au Hub de {city} ou augmenter la fréquence des départs de {warehouse}.",
                "impact": "Réduction ciblée des délais de 24-48h"
            })

    # 2. Modal Performance Analysis (Vehicle Type)
    vehicle_stats = df.groupby("vehicle_type")["is_delayed"].mean() * 100
    worst_vehicle = vehicle_stats.idxmax()
    worst_rate = vehicle_stats.max()

    if worst_rate > 50:
        recommendations.append({
            "urgency": "STRATÉGIQUE",
            "issue": f"Sous-performance du mode '{worst_vehicle}'",
            "finding": f"Ce type de transport affiche {worst_rate:.1f}% de retards/incidents.",
            "action": f"Lancer un audit de maintenance sur la flotte '{worst_vehicle}' ou basculer vers le Fret Ferroviaire/Gros Camion.",
            "impact": "Stabilisation de la chaîne sur les volumes critiques"
        })

    # 3. Carrier Optimization (Original logic preserved but refined)
    otif_by_carrier = kpi.get("otif_by_carrier", {})
    if otif_by_carrier:
        sorted_carriers = sorted(otif_by_carrier.items(), key=lambda x: x[1]['otif_pct'])
        worst_name, worst_stats = sorted_carriers[0]
        best_name, best_stats = sorted_carriers[-1]
        
        if worst_stats['otif_pct'] < 50:
            recommendations.append({
                "urgency": "LOGISTIQUE",
                "issue": f"Déficit de performance chez {worst_name}",
                "finding": f"OTIF de seulement {worst_stats['otif_pct']}% vs {best_name} ({best_stats['otif_pct']}%).",
                "action": f"Réduire l'allocation de volume chez {worst_name} de 30% au profit de {best_name}.",
                "impact": "Amélioration immédiate de l'OTIF de ~4%"
            })

    plan = {
        "summary": "Plan d'Action IA - Optimisation Multi-dimensionnelle",
        "timestamp": kpi.get("timestamp"),
        "global_kpis": {
            "current_otif": global_otif,
            "target_otif": 90.0,
        },
        "recommendations": recommendations[:4]
    }

    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, "w") as f:
        json.dump(plan, f, indent=2, ensure_ascii=False)
    
    return plan

if __name__ == "__main__":
    prescribe()
