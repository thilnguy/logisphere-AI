# Supply Chain Automation Agents 🚛

> **From Raw Excel to Executive Dashboard — Zero manual intervention.**
> An agentic AI-driven pipeline that automates logistics data cleaning, KPI analytics, EU carbon tracking, and interactive dashboard generation.

---

## Architecture

```
┌──────────────┐    ┌──────────────────┐    ┌────────────────┐    ┌──────────────────┐    ┌────────────────┐
│  Data Source  │───▶│ Data Quality     │───▶│ Cleaner Agent  │───▶│ Analyst Agent    │───▶│ Dashboard      │
│  (ERP / WMS) │    │ Agent (Gate 20%) │    │ (GDPR + Fuzzy) │    │ (OTIF + CO₂)    │    │ (Streamlit)    │
└──────────────┘    └──────────────────┘    └────────────────┘    └──────────────────┘    └────────────────┘
       │                    │                       │                      │                      │
       │              Halts pipeline           Anonymizes PII        Computes KPIs          Status Page
       │              if errors > 20%          Normalizes names      CO₂ Emissions          KPI Cards
       ▼                                       Deduplicates          Risk Flags             Charts + Map
   Logistics_Raw.xlsx                     Logistics_Cleaned.csv   Analytics_Summary.csv    Live Web App
```

## Features

| Feature | Agent | Details |
|---------|-------|---------|
| **Data Validation** | Quality Agent | Halts pipeline if error rate > 20%, sends alerts |
| **GDPR Anonymization** | Cleaner Agent | SHA-256 hashes PII (names, phones) per EU regulation |
| **Fuzzy Matching** | Cleaner Agent | Normalizes carrier/warehouse variants via Source of Truth |
| **OTIF Tracking** | Analyst Agent | On-Time In-Full rate per carrier with 5-day baseline |
| **CO₂ Emissions** | Analyst Agent | EU-standard carbon footprint per shipment |
| **Risk Flagging** | Analyst Agent | HIGH/MEDIUM/LOW risk on delayed shipments |
| **Pipeline Status** | Dashboard | Real-time stage health indicator (trust layer) |
| **Delivery Heatmap** | Dashboard | Folium dark-mode map of shipment distribution |

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Generate mock data & run full pipeline
python pipeline.py --generate

# 3. Launch Dashboard
streamlit run dashboard/app.py
```

## Project Structure

```
supply-chain-automation-agents/
├── agents/
│   ├── data_quality_agent.py    # Validation & exception gating
│   ├── cleaner_agent.py         # GDPR, fuzzy matching, normalization
│   └── analyst_agent.py         # OTIF, lead time, CO₂, risk
├── config/
│   └── master_data.json         # Source of Truth (carriers, warehouses, CO₂ factors)
├── dashboard/
│   └── app.py                   # Streamlit Command Center
├── data/
│   ├── raw/                     # Input files
│   ├── cleaned/                 # Cleaner output
│   ├── analytics/               # Analyst output
│   ├── reports/                 # Validation & pipeline status
│   └── generate_mock_data.py    # Mock data generator
├── pipeline.py                  # Orchestrator
├── requirements.txt
└── README.md
```

## EU Compliance

- **GDPR**: All PII columns are SHA-256 hashed before entering the analytics pipeline
- **Carbon Tracking**: CO₂ emissions calculated using EU reference factors per vehicle type
- **Auditability**: Every pipeline run produces timestamped validation and status reports

---

*Built with Antigravity 🧠 — Agentic AI for Supply Chain Excellence*
