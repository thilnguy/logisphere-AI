"""
Logistics Command Center — Streamlit Dashboard
================================================
Professional BI dashboard displaying:
  - Pipeline Status Page (trust indicator)
  - KPI Cards (Revenue, OTIF, CO2, Lead Time)
  - OTIF by Carrier (bar chart)
  - Shipping Cost by City (bar chart)
  - CO2 Emissions by Vehicle Type (pie chart)
  - Delivery Map (Folium heatmap)
  - Risk Distribution
"""

import json
import os
import sys
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import folium
from streamlit_folium import st_folium

# --- Paths ---
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

ANALYTICS_CSV = os.path.join(PROJECT_ROOT, "data", "analytics", "Analytics_Summary.csv")
KPI_JSON = os.path.join(PROJECT_ROOT, "data", "analytics", "KPI_Report.json")
OPT_JSON = os.path.join(PROJECT_ROOT, "data", "analytics", "Optimization_Plan.json")
STATUS_JSON = os.path.join(PROJECT_ROOT, "data", "reports", "pipeline_status.json")
VALIDATION_JSON = os.path.join(PROJECT_ROOT, "data", "reports", "validation_report.json")

# =====================================================================
# PAGE CONFIG
# =====================================================================
st.set_page_config(
    page_title="Logistics Command Center",
    page_icon="🚛",
    layout="wide",
    initial_sidebar_state="expanded",
)

# =====================================================================
# CUSTOM CSS
# =====================================================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    * { font-family: 'Inter', sans-serif; }

    .main .block-container {
        padding-top: 1.5rem;
        max-width: 1400px;
    }

    /* KPI Cards */
    .kpi-card {
        background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
        border-radius: 16px;
        padding: 24px;
        text-align: center;
        border: 1px solid rgba(255,255,255,0.08);
        box-shadow: 0 8px 32px rgba(0,0,0,0.3);
        transition: transform 0.2s ease;
    }
    .kpi-card:hover { transform: translateY(-4px); }
    .kpi-label {
        font-size: 13px;
        font-weight: 600;
        color: #94a3b8;
        text-transform: uppercase;
        letter-spacing: 1.2px;
        margin-bottom: 8px;
    }
    .kpi-value {
        font-size: 36px;
        font-weight: 800;
        background: linear-gradient(135deg, #38bdf8, #818cf8);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .kpi-sub {
        font-size: 12px;
        color: #64748b;
        margin-top: 4px;
    }

    /* Pipeline Status */
    .status-badge {
        display: inline-block;
        padding: 4px 14px;
        border-radius: 20px;
        font-size: 13px;
        font-weight: 700;
        letter-spacing: 0.5px;
    }
    .status-ok { background: #065f46; color: #6ee7b7; }
    .status-warn { background: #78350f; color: #fbbf24; }
    .status-fail { background: #7f1d1d; color: #fca5a5; }

    /* Section headers */
    .section-header {
        font-size: 20px;
        font-weight: 700;
        color: #e2e8f0;
        margin-bottom: 16px;
        padding-bottom: 8px;
        border-bottom: 2px solid #334155;
    }

    /* Actionable Insight Cards */
    .rec-card {
        background: #0f172a;
        border-right: 4px solid #334155;
        border-left: 4px solid #334155;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 20px;
        border: 1px solid rgba(255,255,255,0.05);
        box-shadow: 0 4px 20px rgba(0,0,0,0.2);
    }
    .rec-badge {
        display: inline-block;
        padding: 2px 10px;
        border-radius: 4px;
        font-size: 10px;
        font-weight: 800;
        margin-bottom: 10px;
        text-transform: uppercase;
    }
    .urgency-critical { background: #ef4444; color: white; border-right: 4px solid #b91c1c; }
    .urgency-strategic { background: #3b82f6; color: white; border-right: 4px solid #1d4ed8; }
    .urgency-efficiency { background: #10b981; color: white; border-right: 4px solid #047857; }

    .rec-action { color: #f8fafc; font-weight: 700; font-size: 17px; margin-bottom: 8px; }
    .rec-finding { color: #94a3b8; font-size: 14px; margin-bottom: 12px; font-style: italic; }
    .rec-impact { font-weight: 600; font-size: 13px; color: #38bdf8; }
</style>
""", unsafe_allow_html=True)


# =====================================================================
# DATA LOADING
# =====================================================================
@st.cache_data(ttl=60)
def load_data():
    kpi = {}
    df = pd.DataFrame()
    pipeline_status = {}
    validation = {}
    opt_plan = {}

    if os.path.exists(KPI_JSON):
        with open(KPI_JSON) as f:
            kpi = json.load(f)
    if os.path.exists(ANALYTICS_CSV):
        df = pd.read_csv(ANALYTICS_CSV)
    if os.path.exists(STATUS_JSON):
        with open(STATUS_JSON) as f:
            pipeline_status = json.load(f)
    if os.path.exists(VALIDATION_JSON):
        with open(VALIDATION_JSON) as f:
            validation = json.load(f)
    if os.path.exists(OPT_JSON):
        with open(OPT_JSON) as f:
            opt_plan = json.load(f)

    return kpi, df, pipeline_status, validation, opt_plan


kpi, df, pipeline_status, validation, opt_plan = load_data()

# =====================================================================
# SIDEBAR - AIDE & GUIDE KPI
# =====================================================================
with st.sidebar:
    st.markdown("### 💡 Aide & Guide KPI")
    
    with st.expander("📖 Guide d'Utilisation", expanded=False):
        st.markdown("""
        1. **Pipeline** : Vérifiez que tous les agents sont verts (PASS/OK).
        2. **KPIs** : Suivez l'OTIF (performance) et les CO2 (écologie).
        3. **Optimisation** : Appliquez les conseils de l'IA situés en bas.
        4. **Prévisions** : Anticipez les flux sur les 6 prochains mois.
        """)

    with st.expander("🔍 Légende des Risques", expanded=True):
        st.markdown("""
        *   🟢 **AUCUN** : Livraison à l'heure.
        *   🔵 **FAIBLE** : Livraison effectuée mais en retard.
        *   🟠 **MOYEN** : En cours de route (dans les délais).
        *   🔴 **ÉLEVÉ** : Retard critique ou blocage.
        """)
    
    st.divider()
    st.markdown("🔒 **Sécurité :** RGPD Anonymisé")
    st.markdown("🌿 **Carbone :** Normes UE 2024")

    st.divider()
    from pipeline import run_pipeline
    
    # --- New Phase 13.1: Config Email Alert ---
    with st.sidebar.expander("📧 Configuration Alertes Email"):
        st.write("Configura các tham số SMTP để nhận báo cáo chủ động.")
        smtp_user = st.text_input("User Email", value="", help="Email used to send alerts")
        smtp_pass = st.text_input("App Password", type="password", help="Gmail App Password")
        st.info("💡 **Gmail**: Bật 2FA > App Passwords. Tạo mã 16 ký tự.")

    gen_data = st.sidebar.checkbox("Générer de nouvelles données au lancement", value=False)
    
    if st.sidebar.button("🚀 Lancer le Pipeline Complet", use_container_width=True):
        with st.spinner("Pipeline en cours d'exécution..."):
            status = run_pipeline(generate_data=gen_data, smtp_user=smtp_user, smtp_pass=smtp_pass)
            st.success("✅ Pipeline terminé !")
            st.toast("Rapport d'alerte généré !")
            st.rerun()

# =====================================================================
# HEADER
# =====================================================================
st.markdown("""
<div style="text-align: center; padding: 20px 0 10px 0;">
    <h1 style="font-size: 32px; font-weight: 800; margin-bottom: 4px;
               background: linear-gradient(135deg, #38bdf8, #818cf8, #c084fc);
               -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
        🚛 Centre de Commande Logistique
    </h1>
    <p style="color: #64748b; font-size: 14px;">
        Intelligence Logistique · Conforme RGPD · Suivi Carbone UE
    </p>
</div>
""", unsafe_allow_html=True)

# =====================================================================
# PIPELINE STATUS BAR
# =====================================================================
st.markdown('<div class="section-header">⚡ Statut du Pipeline</div>', unsafe_allow_html=True)

if pipeline_status:
    stages = pipeline_status.get("stages", {})
    cols = st.columns(len(stages) + 1)

    # Overall status
    overall = pipeline_status.get("overall", "UNKNOWN")
    badge_class = "status-ok" if overall == "SUCCESS" else ("status-warn" if overall == "HALTED" else "status-fail")
    cols[0].markdown(f"""
        <div style="text-align:center;">
            <div style="font-size:11px; color:#94a3b8; font-weight:600;">GÉNÉRAL</div>
            <span class="status-badge {badge_class}">{overall}</span>
        </div>
    """, unsafe_allow_html=True)

    for i, (stage_name, stage_info) in enumerate(stages.items(), 1):
        s = stage_info.get("status", "?")
        bc = "status-ok" if s in ("OK", "PASS", "SUCCESS") else ("status-warn" if s == "WARNING" else "status-fail")
        cols[i].markdown(f"""
            <div style="text-align:center;">
                <div style="font-size:11px; color:#94a3b8; font-weight:600;">{stage_name.upper()}</div>
                <span class="status-badge {bc}">{s}</span>
            </div>
        """, unsafe_allow_html=True)

    st.markdown(f'<p style="font-size:11px; color:#475569; text-align:right;">Dernière exécution : {pipeline_status.get("pipeline_run", "N/A")}</p>', unsafe_allow_html=True)
else:
    st.info("No pipeline status available. Run `python pipeline.py --generate` first.")

st.divider()

# =====================================================================
# KPI CARDS
# =====================================================================
if kpi:
    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">Total des Expéditions</div>
            <div class="kpi-value">{kpi.get('total_shipments', 0):,}</div>
            <div class="kpi-sub">{kpi.get('total_delivered', 0):,} livrés</div>
        </div>
        """, unsafe_allow_html=True)

    with c2:
        otif = kpi.get('global_otif_pct', 0)
        otif_color = "#6ee7b7" if otif >= 85 else ("#fbbf24" if otif >= 70 else "#fca5a5")
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">Taux OTIF</div>
            <div class="kpi-value" style="background: {otif_color}; -webkit-background-clip: text;">{otif}%</div>
            <div class="kpi-sub">À l'heure, En complet</div>
        </div>
        """, unsafe_allow_html=True)

    with c3:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">Coût Total de Livraison</div>
            <div class="kpi-value">€{kpi.get('total_revenue_eur', 0):,.0f}</div>
            <div class="kpi-sub">Somme des frais</div>
        </div>
        """, unsafe_allow_html=True)

    with c4:
        co2 = kpi.get('total_co2_kg', 0)
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">Émissions de CO₂</div>
            <div class="kpi-value">{co2:,.0f} kg</div>
            <div class="kpi-sub">Empreinte Carbone UE</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    sc1, sc2 = st.columns(2)
    with sc1:
        st.metric("⏱️ Délai de Livraison Moyen", f"{kpi.get('avg_lead_time_days', 'N/A')} jours")
    with sc2:
        risk = kpi.get("risk_distribution", {})
        high_risk = risk.get("ÉLEVÉ", 0)
        st.metric("⚠️ Expéditions à Haut Risque", high_risk)

    st.markdown("<br>", unsafe_allow_html=True)
    
    # --- AI STRATEGY SECTION ---
    if opt_plan:
        st.markdown('<div class="section-header">🧠 Plan d\'Action Stratégique IA</div>', unsafe_allow_html=True)
        
        for rec in opt_plan.get("recommendations", []):
            urgency = rec.get("urgency", "STRATÉGIQUE")
            badge_class = f"urgency-{urgency.lower()}"
            
            # Map specific French urgency to correct CSS class names for styling, e.g. CRITIQUE -> critical
            if urgency == "CRITIQUE": css_class = "urgency-critical"
            elif urgency == "EFFICACITÉ": css_class = "urgency-efficiency"
            else: css_class = "urgency-strategic"

            st.markdown(f"""
            <div class="rec-card">
                <span class="rec-badge {css_class}">{urgency}</span>
                <div class="rec-action">💡 {rec['action']}</div>
                <div class="rec-finding"><b>Analyse :</b> {rec['finding']}</div>
                <div class="rec-impact">🎯 Impact Attendu : {rec['impact']}</div>
            </div>
            """, unsafe_allow_html=True)

st.divider()

# =====================================================================
# CHARTS
# =====================================================================
if not df.empty:
    chart_col1, chart_col2 = st.columns(2)

    # --- OTIF by Carrier ---
    with chart_col1:
        st.markdown('<div class="section-header">📊 OTIF par Transporteur</div>', unsafe_allow_html=True)
        otif_data = kpi.get("otif_by_carrier", {})
        if otif_data:
            otif_df = pd.DataFrame(otif_data).T.reset_index().rename(columns={"index": "Carrier"})
            fig = px.bar(
                otif_df, x="Carrier", y="otif_pct",
                color="otif_pct",
                color_continuous_scale=["#ef4444", "#fbbf24", "#22c55e"],
                range_color=[0, 100],
                labels={"otif_pct": "OTIF %"},
                text="otif_pct",
            )
            fig.update_layout(
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                font_color="#94a3b8",
                showlegend=False,
                height=400,
                xaxis=dict(tickangle=-45),
            )
            fig.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
            st.plotly_chart(fig, use_container_width=True)

    # --- Cost by City ---
    with chart_col2:
        st.markdown('<div class="section-header">💰 Coût d\'Expédition par Ville</div>', unsafe_allow_html=True)
        cost_data = kpi.get("cost_by_city", {})
        if cost_data:
            cost_df = pd.DataFrame(list(cost_data.items()), columns=["City", "Cost_EUR"])
            cost_df = cost_df.sort_values("Cost_EUR", ascending=True)
            fig = px.bar(
                cost_df, x="Cost_EUR", y="City", orientation="h",
                color="Cost_EUR",
                color_continuous_scale="Blues",
                labels={"Cost_EUR": "€"},
                text="Cost_EUR",
            )
            fig.update_layout(
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                font_color="#94a3b8",
                showlegend=False,
                height=400,
            )
            fig.update_traces(texttemplate='€%{text:,.0f}', textposition='outside')
            st.plotly_chart(fig, use_container_width=True)

    # --- Row 2 ---
    chart_col3, chart_col4 = st.columns(2)

    # --- CO2 by Vehicle Type ---
    with chart_col3:
        st.markdown('<div class="section-header">🌿 CO₂ par Type de Véhicule</div>', unsafe_allow_html=True)
        co2_vt = kpi.get("co2_by_vehicle_type", {})
        if co2_vt:
            co2_df = pd.DataFrame(list(co2_vt.items()), columns=["Véhicule", "CO2_kg"])
            fig = px.pie(
                co2_df, values="CO2_kg", names="Véhicule",
                color_discrete_sequence=px.colors.qualitative.Set3,
                hole=0.45,
            )
            fig.update_layout(
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                font_color="#94a3b8",
                height=400,
            )
            fig.update_traces(textinfo="percent+label", textfont_size=12)
            st.plotly_chart(fig, use_container_width=True)

    # --- Risk Distribution ---
    with chart_col4:
        st.markdown('<div class="section-header">⚠️ Distribution des Risques</div>', unsafe_allow_html=True)
        if "risk_level" in df.columns:
            risk_counts = df[["risk_level"]].copy()
            RISK_ORDER = ["AUCUN", "FAIBLE", "MOYEN", "ÉLEVÉ"]
            risk_counts["risk_level"] = pd.Categorical(risk_counts["risk_level"], categories=RISK_ORDER, ordered=True)
            risk_counts = risk_counts["risk_level"].value_counts().reindex(RISK_ORDER, fill_value=0).reset_index()
            risk_counts.columns = ["Niveau de Risque", "Count"]
            color_map = {"AUCUN": "#22c55e", "FAIBLE": "#3b82f6", "MOYEN": "#f59e0b", "ÉLEVÉ": "#ef4444"}
            fig = px.bar(
                risk_counts, x="Niveau de Risque", y="Count",
                color="Niveau de Risque",
                color_discrete_map=color_map,
                text="Count",
            )
            fig.update_layout(
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                font_color="#94a3b8",
                showlegend=False,
                height=400,
            )
            fig.update_traces(textposition='outside')
            st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # =====================================================================
    # RISK DRILL DOWN (TABLE)
    # =====================================================================
    st.markdown('<div class="section-header">🔍 Exploration des Opérations (Drill-down)</div>', unsafe_allow_html=True)
    
    risk_to_drill = st.selectbox("Sélectionnez le niveau de risque à analyser :", ["ÉLEVÉ", "MOYEN"], index=0)
    drill_df = df[df["risk_level"] == risk_to_drill].copy()
    
    if not drill_df.empty:
        if risk_to_drill == "ÉLEVÉ":
            st.warning(f"🚨 {len(drill_df)} expéditions à HAUT RISQUE détectées. Action immédiate requise !")
        else:
            st.info(f"⚠️ {len(drill_df)} expéditions à RISQUE MOYEN détectées. À surveiller.")
        
        # Select key columns for display
        cols_to_show = [
            "tracking_id", "status", "carrier", "vehicle_type",
            "weight_kg", "origin_warehouse", "destination_city",
            "lead_time_days", "shipping_cost_eur"
        ]
        display_df = drill_df[[c for c in cols_to_show if c in drill_df.columns]].sort_values("lead_time_days", ascending=False)
        
        with st.expander(f"👉 Cliquez pour voir la liste détaillée ({risk_to_drill})", expanded=(risk_to_drill == "ÉLEVÉ")):
            st.dataframe(
                display_df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "tracking_id": "Tracking ID",
                    "status": "Statut",
                    "carrier": "Transporteur",
                    "vehicle_type": "Véhicule",
                    "weight_kg": st.column_config.NumberColumn("Poids", format="%.1f kg"),
                    "origin_warehouse": "Origine",
                    "destination_city": "Destination",
                    "lead_time_days": st.column_config.NumberColumn("Délai", format="%d j"),
                    "shipping_cost_eur": st.column_config.NumberColumn("Coût", format="€%.2f")
                }
            )
            
            # Action button mock-up
            st.button(f"📥 Exporter la liste des risques {risk_to_drill} en CSV", key=f"btn_{risk_to_drill}", 
                      on_click=lambda: display_df.to_csv(f"{risk_to_drill.lower()}_risk_alert.csv", index=False))
    else:
        st.success(f"Aucune expédition à risque {risk_to_drill} détectée ! Tous les systèmes sont normaux.")

    st.divider()

    # =====================================================================
    # MAP — Delivery Heatmap
    # =====================================================================
    st.markdown('<div class="section-header">🗺️ Carte de Distribution des Livraisons</div>', unsafe_allow_html=True)

    if "lat" in df.columns and "lon" in df.columns:
        map_df = df.dropna(subset=["lat", "lon"])
        if not map_df.empty:
            center_lat = map_df["lat"].mean()
            center_lon = map_df["lon"].mean()

            m = folium.Map(location=[center_lat, center_lon], zoom_start=6,
                           tiles="CartoDB dark_matter")

            from folium.plugins import HeatMap
            heat_data = map_df[["lat", "lon"]].values.tolist()
            HeatMap(heat_data, radius=8, blur=5, max_zoom=10,
                    gradient={0.2: '#3b82f6', 0.5: '#8b5cf6', 0.8: '#f59e0b', 1: '#ef4444'}).add_to(m)

            st_folium(m, width=None, height=500, use_container_width=True)
        else:
            st.warning("Aucune coordonnée GPS disponible pour la carte.")
    else:
        st.info("La carte nécessite les colonnes 'lat' et 'lon' dans les données d'analyse.")

    st.divider()

    # =====================================================================
    # FORECASTING (PROPHET)
    # =====================================================================
    st.markdown('<div class="section-header">📈 Prévisions de Volume (Tactique - 6 mois)</div>', unsafe_allow_html=True)
    forecast_path = os.path.join(PROJECT_ROOT, "data", "analytics", "Forecast_Prophet.csv")
    
    if os.path.exists(forecast_path):
        forecast_df = pd.read_csv(forecast_path)
        forecast_df["ds"] = pd.to_datetime(forecast_df["ds"])

        # Filter: Show 30 days of history + the full forecast
        today_dt = pd.Timestamp.now().normalize()
        history_limit = today_dt - pd.Timedelta(days=30)
        display_df = forecast_df[forecast_df["ds"] >= history_limit].copy()

        import plotly.graph_objects as go
        fig = go.Figure()

        # Lower bound
        fig.add_trace(go.Scatter(
            x=display_df['ds'], y=display_df['yhat_lower'],
            mode='lines',
            line=dict(width=0),
            showlegend=False
        ))

        # Upper bound
        fig.add_trace(go.Scatter(
            x=display_df['ds'], y=display_df['yhat_upper'],
            mode='lines',
            line=dict(width=0),
            fill='tonexty',
            fillcolor='rgba(59, 130, 246, 0.2)',
            showlegend=True,
            name='Intervalle (95%)'
        ))

        # Main Prediction
        fig.add_trace(go.Scatter(
            x=display_df['ds'], y=display_df['yhat'],
            mode='lines',
            line=dict(color='#3b82f6', width=3),
            name='Prévision',
            hovertemplate="<b>Date</b>: %{x}<br><b>Volume</b>: %{y:.0f} colis<extra></extra>"
        ))

        fig.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font_color="#94a3b8",
            height=500,
            margin=dict(l=60, r=40, t=40, b=80),
            hovermode="x unified",
            hoverlabel=dict(
                bgcolor="#1e293b",
                font_size=12,
                font_family="Inter",
                namelength=-1  # FORCE FULL NAME DISPLAY
            ),
            xaxis=dict(title="Timeline de Livraison (12 mois)", showgrid=False, automargin=True),
            yaxis=dict(title="Volume (Nombre de colis)", showgrid=True, gridcolor="#1e293b", automargin=True),
            legend=dict(
                orientation="v", 
                yanchor="top", 
                y=0.98, 
                xanchor="left", 
                x=0.02,
                bgcolor="rgba(15, 23, 42, 0.5)"
            )
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Module de prévision inactif. Exécutez le pipeline avec Facebook Prophet configuré.")

else:
    st.warning("⚠️ Aucune donnée d'analyse trouvée. Exécutez `python pipeline.py --generate` en premier.")

# =====================================================================
# FOOTER
# =====================================================================
st.markdown("""
<div style="text-align:center; padding: 30px 0 10px 0; border-top: 1px solid #1e293b;">
    <p style="color:#475569; font-size:12px;">
        Agents d'Automatisation Supply Chain · Développé par Thi Lan Anh NGUYEN · Conforme RGPD & Bilan Carbone UE
    </p>
</div>
""", unsafe_allow_html=True)
