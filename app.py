"""
AP-WRIMS Early Warning System — Streamlit Dashboard
Run: streamlit run app.py
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import folium
from streamlit_folium import st_folium

from utils.data_loader import load_all_dates
from utils.risk_engine import compute_all_risks

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="AP-WRIMS Early Warning System | APSDMA",
    page_icon="🚨",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ---------------------------------------------------------------------------
# Global CSS — World-Class Clean Light Government Portal Theme
# ---------------------------------------------------------------------------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');

    /* ── Base ─────────────────────────────────────────────────────────────── */
    html, body, .stApp {
        background-color: #EBF2FB !important;
        color: #0F172A !important;
        font-family: 'Inter', sans-serif !important;
    }

    /* Kill Streamlit chrome */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stDeployButton {display:none;}
    [data-testid="stToolbar"] {display:none;}
    [data-testid="stDecoration"] {display:none;}
    [data-testid="stStatusWidget"] {display:none;}
    .viewerBadge_container__1QSob {display:none;}
    section[data-testid="stSidebar"] {display:none;}

    /* Remove default padding */
    .block-container {
        padding: 0 !important;
        max-width: 100% !important;
    }
    .main > div { padding: 0 !important; }

    /* ── Top Navbar — white with navy brand bar ─────────────────────────── */
    .ews-navbar {
        background: #FFFFFF;
        border-bottom: 3px solid #1B4F91;
        padding: 0 32px;
        height: 68px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        position: sticky;
        top: 0;
        z-index: 999;
        box-shadow: 0 2px 12px rgba(0,0,0,0.08);
    }
    .ews-navbar-left { display:flex; align-items:center; gap:14px; }
    .ews-gov-seal {
        width: 44px; height: 44px;
        background: #EBF2FB;
        border: 2px solid #1B4F91;
        border-radius: 50%;
        display: flex; align-items: center; justify-content: center;
        font-size: 22px;
    }
    .ews-navbar-title { font-size:13px; font-weight:700; color:#0F172A; line-height:1.3; }
    .ews-navbar-subtitle { font-size:10px; color:#64748B; font-weight:500; letter-spacing:0.8px; text-transform:uppercase; }
    .ews-navbar-center { text-align:center; flex:1; }
    .ews-system-name {
        font-size: 19px; font-weight: 900; color: #1B4F91;
        letter-spacing: 1.5px; text-transform: uppercase;
    }
    .ews-system-sub { font-size:10px; color:#94A3B8; letter-spacing:1.5px; text-transform:uppercase; }
    .ews-navbar-right { display:flex; align-items:center; gap:10px; }
    .ews-badge {
        background: #F1F5F9; border: 1px solid #CBD5E1; border-radius:4px;
        padding:5px 11px; font-size:10px; color:#475569; font-weight:600; letter-spacing:0.3px;
    }
    .ews-badge-live {
        background: #DCFCE7; border: 1px solid #16A34A; border-radius:4px;
        padding:5px 11px; font-size:10px; color:#15803D; font-weight:700; letter-spacing:1px;
        animation: blink-live 2s infinite;
    }
    @keyframes blink-live { 0%,100%{opacity:1} 50%{opacity:0.55} }
    .ews-timestamp { font-size:10px; color:#64748B; font-family:'Courier New',monospace; }

    /* ── Page content padding ─────────────────────────────────────────────── */
    .ews-content { padding: 24px 28px 0 28px; }

    /* ── Section label bar ────────────────────────────────────────────────── */
    .ews-section-label {
        font-size: 10px; font-weight: 800; letter-spacing: 2px;
        text-transform: uppercase; color: #1B4F91;
        border-left: 4px solid #1B4F91; padding-left: 10px;
        margin-bottom: 14px; margin-top: 18px;
    }

    /* ── Metric Cards — white card, navy top accent ───────────────────────── */
    .ews-metric-card {
        background: #FFFFFF; border: 1px solid #E2E8F0;
        border-top: 3px solid #1B4F91; border-radius: 8px;
        padding: 16px 18px; margin-bottom: 4px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    }
    .ews-metric-label {
        font-size: 10px; font-weight: 700; letter-spacing: 1.5px;
        text-transform: uppercase; color: #94A3B8; margin-bottom: 6px;
    }
    .ews-metric-value {
        font-size: 28px; font-weight: 900; color: #0F172A;
        line-height: 1; font-family: 'Inter', monospace;
    }
    .ews-metric-sub { font-size: 11px; color: #94A3B8; margin-top: 4px; }
    .ews-metric-delta-bad  { color: #DC2626; font-size: 11px; font-weight: 600; margin-top: 4px; }
    .ews-metric-delta-good { color: #16A34A; font-size: 11px; font-weight: 600; margin-top: 4px; }

    /* ── CRITICAL Alert — vivid red on white, pulsing left border ─────────── */
    .critical-alert {
        background: #FFF5F5;
        border: 1px solid #FECACA;
        border-left: 6px solid #DC2626;
        color: #7F1D1D;
        padding: 18px 24px;
        border-radius: 8px;
        font-size: 15px;
        font-weight: 700;
        margin: 16px 0;
        animation: critical-pulse 1.8s infinite;
        box-shadow: 0 4px 20px rgba(220,38,38,0.12);
        letter-spacing: 0.2px;
    }
    @keyframes critical-pulse {
        0%,100% { border-left-color: #DC2626; box-shadow: 0 4px 20px rgba(220,38,38,0.12); }
        50%      { border-left-color: #EF4444; box-shadow: 0 4px 28px rgba(220,38,38,0.28); }
    }

    /* ── Risk Status Banner ───────────────────────────────────────────────── */
    .ews-risk-banner {
        border-radius: 8px; padding: 14px 20px; margin-bottom: 16px;
        border-left: 6px solid; display: flex; align-items: center;
        justify-content: space-between; flex-wrap: wrap; gap: 8px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    }

    /* ── Tabs — white tab bar, navy underline ────────────────────────────── */
    .stTabs [data-baseweb="tab-list"] {
        background: #FFFFFF;
        border-bottom: 2px solid #E2E8F0;
        border-radius: 0; padding: 0 28px; gap: 0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04);
    }
    .stTabs [data-baseweb="tab"] {
        font-family: 'Inter', sans-serif; font-weight: 500; font-size: 13px;
        color: #64748B; padding: 14px 22px; border-radius: 0;
        border-bottom: 3px solid transparent; background: transparent; letter-spacing: 0.2px;
    }
    .stTabs [aria-selected="true"] {
        color: #1B4F91 !important;
        border-bottom: 3px solid #1B4F91 !important;
        background: transparent !important;
        font-weight: 700 !important;
    }
    .stTabs [data-baseweb="tab"]:hover {
        color: #1B4F91 !important;
        background: #F1F5F9 !important;
    }
    [data-baseweb="tab-panel"] {
        background: #EBF2FB;
        padding: 0 !important;
    }

    /* ── Tables — clean white ─────────────────────────────────────────────── */
    .stDataFrame, .dataframe {
        border-radius: 8px; overflow: hidden;
        border: 1px solid #E2E8F0 !important;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    }
    [data-testid="stDataFrame"] > div { background: #FFFFFF !important; }
    thead th {
        background: #1B4F91 !important;
        color: #FFFFFF !important;
        font-size: 11px !important; letter-spacing: 1px !important;
        text-transform: uppercase !important; font-weight: 700 !important;
        border-bottom: none !important;
    }
    tbody td {
        background: #FFFFFF !important; color: #1E293B !important;
        font-size: 13px !important; border-bottom: 1px solid #F1F5F9 !important;
    }
    tbody tr:hover td { background: #F8FAFC !important; }

    /* ── Streamlit native metrics — white card ────────────────────────────── */
    [data-testid="stMetric"] {
        background: #FFFFFF; border: 1px solid #E2E8F0;
        border-top: 3px solid #1B4F91; border-radius: 8px;
        padding: 16px 18px; box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    }
    [data-testid="stMetricLabel"] p {
        font-size: 10px !important; font-weight: 700 !important;
        letter-spacing: 1.5px !important; text-transform: uppercase !important;
        color: #94A3B8 !important;
    }
    [data-testid="stMetricValue"] {
        font-size: 26px !important; font-weight: 900 !important;
        color: #0F172A !important;
    }
    [data-testid="stMetricDelta"] { font-size: 11px !important; }

    /* ── Buttons ──────────────────────────────────────────────────────────── */
    .stButton > button {
        background: #FFFFFF; border: 1px solid #CBD5E1; color: #334155;
        font-family: 'Inter', sans-serif; font-size: 12px;
        font-weight: 600; letter-spacing: 0.3px; border-radius: 6px;
        padding: 8px 18px; transition: all 0.18s;
        box-shadow: 0 1px 3px rgba(0,0,0,0.07);
    }
    .stButton > button:hover {
        background: #EBF2FB; border-color: #1B4F91; color: #1B4F91;
    }
    .stButton[data-testid] > button[kind="primary"] {
        background: #1B4F91; border: 1px solid #1B4F91; color: #FFFFFF;
        box-shadow: 0 2px 8px rgba(27,79,145,0.3);
    }
    .stButton[data-testid] > button[kind="primary"]:hover {
        background: #1A3F76; border-color: #1A3F76;
    }

    /* ── Headings  ───────────────────────────────────────────────────────── */
    h1, h2, h3, h4 { font-family: 'Inter', sans-serif !important; color: #0F172A !important; }
    h3 {
        font-size: 15px !important; font-weight: 700 !important;
        letter-spacing: 0.3px !important;
        border-bottom: 2px solid #E2E8F0 !important;
        padding-bottom: 10px !important; margin-bottom: 18px !important;
        color: #1E293B !important;
    }
    h4 {
        font-size: 11px !important; font-weight: 800 !important;
        letter-spacing: 1.2px !important; text-transform: uppercase !important;
        color: #64748B !important; margin-bottom: 12px !important;
    }
    p, li, span, td { color: #1E293B !important; }

    /* ── SMS box — dark terminal on light page ────────────────────────────── */
    .sms-box {
        background: #0F172A;
        color: #4ADE80;
        font-family: 'Courier New','Lucida Console',monospace;
        padding: 22px; border-radius: 8px;
        border: 1px solid #166534;
        font-size: 13px; line-height: 1.9;
        box-shadow: 0 4px 16px rgba(0,0,0,0.15);
    }

    /* ── Option/Action cards — white with accent top border ──────────────── */
    .ews-card {
        background: #FFFFFF; border: 1px solid #E2E8F0;
        border-radius: 8px; padding: 20px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.06);
    }
    .ews-card-green { border-top: 4px solid #16A34A; }
    .ews-card-amber { border-top: 4px solid #D97706; }
    .ews-card-red   { border-top: 4px solid #DC2626; }

    /* ── Info box  ───────────────────────────────────────────────────────── */
    .ews-info-box {
        background: #EFF6FF; border-left: 4px solid #1B4F91;
        border-radius: 0 8px 8px 0; padding: 18px 22px;
        color: #1E3A5F; font-size: 14px; line-height: 1.8;
        margin-bottom: 20px;
    }

    /* ── Footer bar ──────────────────────────────────────────────────────── */
    .ews-footer {
        background: #FFFFFF; border-top: 2px solid #E2E8F0;
        padding: 12px 32px; font-size: 11px; color: #94A3B8;
        letter-spacing: 0.3px; margin-top: 40px;
        display: flex; justify-content: space-between;
        box-shadow: 0 -2px 8px rgba(0,0,0,0.03);
    }

    /* ── Comparison cards ────────────────────────────────────────────────── */
    .ews-cmp-bad  { background:#FFF5F5; border:1px solid #FECACA; border-radius:8px; padding:20px; }
    .ews-cmp-good { background:#F0FDF4; border:2px solid #16A34A; border-radius:8px; padding:20px; box-shadow:0 4px 16px rgba(22,163,74,0.1); }
    .ews-cmp-neutral { background:#FFFFFF; border:1px solid #E2E8F0; border-radius:8px; padding:20px; }

    /* ── Scrollbar ────────────────────────────────────────────────────────── */
    ::-webkit-scrollbar { width: 5px; height: 5px; }
    ::-webkit-scrollbar-track { background: #F1F5F9; }
    ::-webkit-scrollbar-thumb { background: #CBD5E1; border-radius: 3px; }
    ::-webkit-scrollbar-thumb:hover { background: #94A3B8; }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Data (cached)
# ---------------------------------------------------------------------------
@st.cache_data(show_spinner="Loading data…")
def get_data():
    all_data = load_all_dates()
    risks = compute_all_risks(all_data)
    return all_data, risks


all_data, risks = get_data()

# ---------------------------------------------------------------------------
# Colour helpers  — EOC dark palette
# ---------------------------------------------------------------------------
LEVEL_COLORS = {
    "LOW":      "#16A34A",
    "MEDIUM":   "#D97706",
    "HIGH":     "#EA580C",
    "CRITICAL": "#DC2626",
}
_LEVEL_RGB = {
    "LOW":      "rgb(22, 163, 74)",
    "MEDIUM":   "rgb(217, 119, 6)",
    "HIGH":     "rgb(234, 88, 12)",
    "CRITICAL": "rgb(220, 38, 38)",
}

DATE_LABELS = {
    "Nov17":   "17 Nov 2021",
    "Nov18":   "18 Nov 2021",
    "Nov19":   "19 Nov 2021",
    "Nov20":   "20 Nov 2021",
    "Current": "Current (2026)",
}

# Approximate centre coords for Kadapa / Annamayya districts
DISTRICT_COORDS = {
    "Y.S.R Kadapa":                      (14.4674, 78.8241),
    "Annamayya":                          (13.9700, 78.7200),
    "Pincha Reservoir":                   (13.8900, 78.8500),
    "Annamayya (Cheyyeru) Reservoir":     (14.4200, 78.6500),
}


# ---------------------------------------------------------------------------
# Helper: Gauge chart  — aircraft altimeter / EOC dark style
# ---------------------------------------------------------------------------
def make_gauge(score: float, level: str, title: str = "RISK SCORE") -> go.Figure:
    hex_color = LEVEL_COLORS[level]
    rgb_color = _LEVEL_RGB[level]

    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=score,
            title={
                # Level label sits ABOVE the number — no overlap
                "text": f"<b style='color:{hex_color}'>{level}</b><br><span style='font-size:11px;color:#94A3B8'>{title}</span>",
                "font": {"size": 15, "color": hex_color, "family": "Inter"},
            },
            number={
                "font": {"size": 48, "color": rgb_color, "family": "Inter"},
                "suffix": "",
            },
            gauge={
                "axis": {
                    "range": [0, 100],
                    "tickwidth": 1,
                    "tickcolor": "#CBD5E1",
                    "tickfont": {"color": "#94A3B8", "size": 10},
                    "dtick": 25,
                },
                "bar": {"color": rgb_color, "thickness": 0.06},
                "bgcolor": "rgb(248, 250, 252)",
                "borderwidth": 1,
                "bordercolor": "rgb(226, 232, 240)",
                "steps": [
                    {"range": [0, 40],   "color": "rgba(22, 163, 74, 0.10)"},
                    {"range": [40, 70],  "color": "rgba(217, 119, 6, 0.10)"},
                    {"range": [70, 100], "color": "rgba(220, 38, 38, 0.10)"},
                ],
                "threshold": {
                    "line": {"color": rgb_color, "width": 4},
                    "thickness": 0.85,
                    "value": score,
                },
            },
        )
    )
    fig.update_layout(
        height=300,
        margin=dict(t=60, b=20, l=30, r=30),
        paper_bgcolor="rgb(255, 255, 255)",
        plot_bgcolor="rgb(255, 255, 255)",
        font={"family": "Inter", "color": "#1E293B"},
        # No annotations — label is already in title, avoids all overlap
    )
    return fig



# ---------------------------------------------------------------------------
# Helper: Folium map  — dark terrain, glowing markers
# ---------------------------------------------------------------------------
def make_map(risk_result: dict, date_key: str) -> folium.Map:
    m = folium.Map(
        location=[14.2833, 79.1167],   # Annamayya Dam — centred
        zoom_start=11,
        tiles="CartoDB dark_matter",
        prefer_canvas=True,
    )

    level = risk_result["level"]
    score = risk_result["score"]
    folium_color = LEVEL_COLORS[level]

    # Risk radius circle around Annamayya dam
    folium.Circle(
        location=[14.2833, 79.1167],
        radius=8000,
        color="#FF3B3B",
        fill=True,
        fill_color="#FF3B3B",
        fill_opacity=0.07,
        weight=1.5,
        dash_array="6 4",
        tooltip="Risk Radius — 8 km",
    ).add_to(m)

    # District risk circles
    for loc_key, radius, label in [
        ("Y.S.R Kadapa",  28000, "Y.S.R Kadapa"),
        ("Annamayya",     22000, "Annamayya"),
    ]:
        folium.CircleMarker(
            location=DISTRICT_COORDS[loc_key],
            radius=28,
            color=folium_color,
            fill=True,
            fill_color=folium_color,
            fill_opacity=0.25,
            weight=2,
            popup=folium.Popup(
                f"<div style='font-family:Arial;font-size:13px'><b>{label}</b><br>"
                f"Risk: <b>{level}</b><br>Score: <b>{score:.0f}/100</b></div>",
                max_width=200,
            ),
            tooltip=f"▸ {label} — {level}",
        ).add_to(m)

    # Reservoir markers
    data = all_data.get(date_key, {})
    sensor_dead = data.get("annamayya_sensor_dead", False)

    for name, coords in [
        ("Pincha Reservoir", DISTRICT_COORDS["Pincha Reservoir"]),
        ("Annamayya (Cheyyeru) Reservoir", DISTRICT_COORDS["Annamayya (Cheyyeru) Reservoir"]),
    ]:
        is_cheyyeru = "Cheyyeru" in name
        marker_color = "red" if (is_cheyyeru and sensor_dead) else "blue"
        inflow  = data.get("annamayya_inflow"  if is_cheyyeru else "pincha_inflow",  0)
        outflow = data.get("annamayya_outflow" if is_cheyyeru else "pincha_outflow", 0)
        dead_note = " ⚠️ SENSOR DEAD" if (is_cheyyeru and sensor_dead) else ""
        folium.Marker(
            location=coords,
            popup=folium.Popup(
                f"<div style='font-family:Arial;font-size:13px'><b>{name}</b>{dead_note}<br>"
                f"Inflow: <b>{inflow:,.0f}</b> cusecs<br>"
                f"Outflow: <b>{outflow:,.0f}</b> cusecs</div>",
                max_width=250,
            ),
            tooltip=name,
            icon=folium.Icon(color=marker_color, icon="tint", prefix="fa"),
        ).add_to(m)

    # Annamayya Dam — glowing red pulsing marker
    folium.Marker(
        location=[14.2833, 79.1167],
        popup=folium.Popup(
            "<div style='font-family:Arial;font-size:13px;color:#c0392b'>"
            "<b>🔴 ANNAMAYYA DAM</b><br>"
            "Status: Breached — Nov 19, 2021<br>"
            "District: Kadapa / Annamayya</div>",
            max_width=260,
        ),
        tooltip="⚠ ANNAMAYYA DAM — CRITICAL",
        icon=folium.Icon(color="red", icon="exclamation-sign", prefix="glyphicon"),
    ).add_to(m)
    # Pulse ring
    folium.Circle(
        location=[14.2833, 79.1167],
        radius=1200,
        color="#FF3B3B",
        fill=True,
        fill_color="#FF3B3B",
        fill_opacity=0.3,
        weight=2,
    ).add_to(m)

    # Pincha Dam — orange marker
    folium.Marker(
        location=[14.3800, 79.0500],
        popup=folium.Popup(
            "<div style='font-family:Arial;font-size:13px;color:#e67e22'>"
            "<b>⚠ PINCHA DAM</b><br>Role: Upstream Trigger</div>",
            max_width=220,
        ),
        tooltip="⚠ PINCHA DAM — Upstream",
        icon=folium.Icon(color="orange", icon="tint", prefix="fa"),
    ).add_to(m)

    # Affected villages — blue markers
    for village_name, village_coords, label in [
        ("Mandapalli",  [14.2400, 79.1600], "🏘 Mandapalli — 12 deaths"),
        ("Togurupeta",  [14.2500, 79.1500], "🏘 Togurupeta — 500 displaced"),
        ("Pulapathur",  [14.2300, 79.1700], "🏘 Pulapathur"),
        ("Gundlur",     [14.2200, 79.1800], "🏘 Gundlur"),
    ]:
        folium.Marker(
            location=village_coords,
            popup=folium.Popup(
                f"<div style='font-family:Arial;font-size:13px'><b>{label}</b></div>",
                max_width=220,
            ),
            tooltip=village_name,
            icon=folium.Icon(color="blue", icon="home", prefix="glyphicon"),
        ).add_to(m)

    return m


# ---------------------------------------------------------------------------
# Helper: Factor bar chart  — dark analytics dashboard style
# ---------------------------------------------------------------------------
def make_factor_chart(top_factors: list) -> go.Figure:
    names  = [f[0] for f in top_factors]
    values = [f[1] for f in top_factors]
    max_vals = {
        "Soil Moisture (100cm)": 25,
        "Inflow Surge Rate":     25,
        "Discharge Imbalance":   20,
        "Rainfall Anomaly":      20,
        "Sensor Dead Penalty":   10,
    }
    colors = [
        "#DC2626" if v > 0.7 * max_vals.get(n, 25) else
        "#D97706" if v > 0.4 * max_vals.get(n, 25) else
        "#16A34A"
        for n, v in zip(names, values)
    ]

    fig = go.Figure(go.Bar(
        x=values, y=names, orientation="h",
        marker=dict(color=colors, line=dict(width=0)),
        text=[f"{v:.1f}" for v in values],
        textposition="outside",
        textfont={"color": "#64748B", "size": 11, "family": "Inter"},
    ))
    fig.update_layout(
        height=260,
        margin=dict(t=10, b=10, l=10, r=55),
        paper_bgcolor="rgb(255, 255, 255)",
        plot_bgcolor="rgb(255, 255, 255)",
        font={"color": "#64748B", "family": "Inter"},
        xaxis=dict(
            range=[0, 28], showgrid=True,
            gridcolor="#F1F5F9", gridwidth=1, zeroline=False,
            tickfont={"color": "#94A3B8", "size": 10},
            ticksuffix=" pts",
        ),
        yaxis=dict(
            showgrid=False,
            tickfont={"color": "#334155", "size": 11},
        ),
    )
    return fig


# ---------------------------------------------------------------------------
# Helper: Metrics row  — dark EOC cards
# ---------------------------------------------------------------------------
def show_metrics(data: dict, risk: dict):
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("MI TANK FILL",         f"{data['mi_tank_fill_pct']:.1f}%")
    c2.metric("SOIL MOISTURE 100cm",  f"{data['soil_moisture_100cm']:.1f}%")
    c3.metric("PINCHA INFLOW",        f"{data['pincha_inflow']:,.0f} cs")
    c4.metric(
        "ANNAMAYYA INFLOW",
        f"{data['annamayya_inflow']:,.0f} cs",
        delta="⚠ SENSOR DEAD" if data["annamayya_sensor_dead"] else None,
        delta_color="inverse" if data["annamayya_sensor_dead"] else "normal",
    )
    c5.metric("RAINFALL ACTUAL", f"{data['rainfall_actual']:.1f} mm",
              delta=f"{data['rainfall_anomaly_pct']:+.1f}%")


# ---------------------------------------------------------------------------
# Helper: Risk status banner  — dark EOC style
# ---------------------------------------------------------------------------
def risk_banner(level: str, score: float, risk: dict):
    palette = {
        "LOW":      ("#16A34A", "#F0FDF4", "#DCFCE7"),
        "MEDIUM":   ("#D97706", "#FFFBEB", "#FEF3C7"),
        "HIGH":     ("#EA580C", "#FFF7ED", "#FFEDD5"),
        "CRITICAL": ("#DC2626", "#FFF5F5", "#FEE2E2"),
    }
    color, bg, border_bg = palette.get(level, ("#64748B", "#F8FAFC", "#F1F5F9"))
    ttf  = risk.get('time_to_failure', 'N/A')
    conf = risk.get('confidence', 0)
    st.markdown(
        f"""<div style='background:{bg};border-left:5px solid {color};
        border:1px solid {border_bg};border-left:5px solid {color};
        padding:14px 22px;border-radius:8px;margin-bottom:18px;
        display:flex;align-items:center;justify-content:space-between;
        flex-wrap:wrap;gap:8px;box-shadow:0 2px 8px rgba(0,0,0,0.06)'>
        <div>
          <span style='font-size:10px;font-weight:800;letter-spacing:2px;
          text-transform:uppercase;color:{color}'>● RISK STATUS</span>
          <span style='font-size:22px;font-weight:900;color:{color};
          margin-left:14px;letter-spacing:0.5px'>{level}</span>
          <span style='font-size:13px;color:#64748B;margin-left:10px'>
          — Score: <b style='color:#0F172A'>{score:.0f}</b>/100</span>
        </div>
        <div style='display:flex;gap:28px;font-size:12px;color:#64748B'>
          <span>⏱ Time to Failure: <b style='color:#0F172A'>{ttf}</b></span>
          <span>📊 Confidence: <b style='color:#0F172A'>{conf:.0f}%</b></span>
        </div>
        </div>""",
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Global Navbar — clean white government portal
# ---------------------------------------------------------------------------
import datetime as _dt
_now = _dt.datetime.now().strftime("%d %b %Y  %H:%M IST")

st.markdown(f"""
<div class="ews-navbar">
  <div class="ews-navbar-left">
    <div class="ews-gov-seal">🏛</div>
    <div>
      <div class="ews-navbar-title">Government of Andhra Pradesh</div>
      <div class="ews-navbar-subtitle">APSDMA · APWRIMS · Disaster Management Authority</div>
    </div>
  </div>
  <div class="ews-navbar-center">
    <div class="ews-system-name">AP-WRIMS Early Warning System</div>
    <div class="ews-system-sub">Annamayya Dam · Cheyyeru River · Kadapa District, AP</div>
  </div>
  <div class="ews-navbar-right">
    <div style="text-align:right">
      <div class="ews-timestamp">🕐 {_now}</div>
      <div class="ews-timestamp" style="margin-top:2px">📡 APWRIMS + Sentinel-1 SAR</div>
    </div>
    <div class="ews-badge-live">● LIVE</div>
    <div class="ews-badge">HierachAI</div>
    <div class="ews-badge">DPIIT ✓</div>
  </div>
</div>
<div style="height:4px;background:linear-gradient(90deg,#1B4F91 0%,#2563EB 50%,#1B4F91 100%);"></div>
<div style="padding: 24px 28px 0 28px">""",
unsafe_allow_html=True)



# ---------------------------------------------------------------------------
# Tab 1 — Overview
# ---------------------------------------------------------------------------
def tab_overview():
    st.markdown("### 🗺️ Overview — Real-Time Risk Status")

    current_risk = risks.get("Current", {})
    current_data = all_data.get("Current", {})
    level = current_risk.get("level", "LOW")
    score = current_risk.get("score", 0)

    risk_banner(level, score, current_risk)

    col_map, col_gauge = st.columns([3, 2])
    with col_map:
        st.subheader("District Map")
        m = make_map(current_risk, "Current")
        st_folium(m, width=620, height=400, returned_objects=[])

    with col_gauge:
        st.subheader("Risk Gauge")
        st.plotly_chart(make_gauge(score, level), use_container_width=True,
                        key="chart_overview_gauge")
        st.subheader("Contributing Factors")
        st.plotly_chart(
            make_factor_chart(current_risk.get("top_factors", [])),
            use_container_width=True,
            key="chart_overview_factors",
        )

    st.subheader("Current Snapshot")
    show_metrics(current_data, current_risk)


# ---------------------------------------------------------------------------
# Tab 2 — Historical Replay
# ---------------------------------------------------------------------------
def tab_historical():
    st.markdown("### 📅 Historical Replay — November 2021 Flood Event")

    btn_cols = st.columns(4)
    date_keys = ["Nov17", "Nov18", "Nov19", "Nov20"]
    if "selected_date" not in st.session_state:
        st.session_state.selected_date = "Nov17"

    for col, dk in zip(btn_cols, date_keys):
        risk  = risks.get(dk, {})
        level = risk.get("level", "LOW")
        color = LEVEL_COLORS[level]
        if col.button(
            f"📅 {DATE_LABELS[dk]}\n**{level}** — {risk.get('score', 0):.0f}/100",
            use_container_width=True,
            key=f"btn_{dk}",
        ):
            st.session_state.selected_date = dk

    dk    = st.session_state.selected_date
    data  = all_data.get(dk, {})
    risk  = risks.get(dk, {})
    level = risk.get("level", "LOW")
    score = risk.get("score", 0)

    st.markdown(f"### {DATE_LABELS[dk]}")

    # CRITICAL alert for Nov 18
    if dk == "Nov18":
        st.markdown("""
<div class="critical-alert">
    🚨 CRITICAL ALERT — November 18, 2021 08:00 AM<br>
    <span style="font-size:14px; font-weight:normal;">
    High probability of bund failure within 6–12 hours |
    Evacuate: Mandapalli · Togurupeta · Pulapathur · Gundlur
    </span>
</div>
""", unsafe_allow_html=True)

    col_map, col_right = st.columns([3, 2])
    with col_map:
        m = make_map(risk, dk)
        st_folium(m, width=620, height=360, returned_objects=[], key=f"map_{dk}")

    with col_right:
        st.plotly_chart(
            make_gauge(score, level, title=f"Risk — {DATE_LABELS[dk]}"),
            use_container_width=True, key="chart_replay_gauge",
        )
        st.markdown(f"**Time to Failure:** `{risk.get('time_to_failure','N/A')}`")
        st.markdown(f"**Confidence:** `{risk.get('confidence',0):.0f}%`")

    st.subheader("Data Snapshot")
    show_metrics(data, risk)

    st.subheader("Factor Breakdown")
    st.plotly_chart(
        make_factor_chart(risk.get("top_factors", [])),
        use_container_width=True, key="chart_replay_factors",
    )

    # Trend table with level-based row highlighting
    st.subheader("Trend Across Nov 2021")
    rows = []
    for k in date_keys:
        r = risks.get(k, {})
        d = all_data.get(k, {})
        rows.append({
            "Date":                   DATE_LABELS[k],
            "Score":                  r.get("score", 0),
            "Level":                  r.get("level", "—"),
            "Pincha Inflow (cs)":     d.get("pincha_inflow", 0),
            "Annamayya Inflow (cs)":  d.get("annamayya_inflow", 0),
            "Soil 100cm %":           d.get("soil_moisture_100cm", 0),
            "Sensor Dead":            "⚠️ YES" if d.get("annamayya_sensor_dead") else "OK",
        })

    df_trend = pd.DataFrame(rows)

    # Format numeric columns cleanly before display
    df_trend["Score"]                = df_trend["Score"].round(1)
    df_trend["Pincha Inflow (cs)"]   = df_trend["Pincha Inflow (cs)"].apply(lambda x: f"{x:,.0f}")
    df_trend["Annamayya Inflow (cs)"] = df_trend["Annamayya Inflow (cs)"].apply(lambda x: f"{x:,.0f}")
    df_trend["Soil 100cm %"]         = df_trend["Soil 100cm %"].round(1)

    def highlight_risk(row):
        level_val = row.get("Level", "")
        if level_val == "CRITICAL":
            return ["background-color:#FEE2E2;color:#7F1D1D"] * len(row)
        elif level_val == "HIGH":
            return ["background-color:#FFEDD5;color:#7C2D12"] * len(row)
        elif level_val == "MEDIUM":
            return ["background-color:#FEF3C7;color:#78350F"] * len(row)
        return ["background-color:#F8FAFC;color:#1E293B"] * len(row)

    st.dataframe(
        df_trend.style.apply(highlight_risk, axis=1),
        hide_index=True,
        use_container_width=True,
    )


# ---------------------------------------------------------------------------
# Tab 3 — Live 2026
# ---------------------------------------------------------------------------
def tab_live():
    st.markdown("### 📡 Live Data — Current (2026)")

    current_data = all_data.get("Current", {})
    current_risk = risks.get("Current", {})
    level = current_risk.get("level", "LOW")
    score = current_risk.get("score", 0)

    risk_banner(level, score, current_risk)

    col1, col2 = st.columns([2, 3])
    with col1:
        st.plotly_chart(
            make_gauge(score, level, "Live Risk Score"),
            use_container_width=True, key="chart_live_gauge",
        )

    with col2:
        st.subheader("Live Sensor Readings")
        show_metrics(current_data, current_risk)
        st.subheader("Factor Breakdown")
        st.plotly_chart(
            make_factor_chart(current_risk.get("top_factors", [])),
            use_container_width=True, key="chart_live_factors",
        )

    st.subheader("Live Map")
    m = make_map(current_risk, "Current")
    st_folium(m, width=900, height=420, returned_objects=[], key="map_live")

    st.subheader("Comparison: Nov 2021 vs Now")
    compare_rows = []
    for dk in ["Nov19", "Nov20", "Current"]:
        r = risks.get(dk, {})
        d = all_data.get(dk, {})
        compare_rows.append({
            "Period":          DATE_LABELS[dk],
            "Risk Score":      r.get("score", 0),
            "Level":           r.get("level", "—"),
            "Pincha Inflow":   d.get("pincha_inflow", 0),
            "MI Tank Fill %":  d.get("mi_tank_fill_pct", 0),
            "Soil 100cm %":    d.get("soil_moisture_100cm", 0),
            "Rainfall (mm)":   d.get("rainfall_actual", 0),
        })

    df_compare = pd.DataFrame(compare_rows)

    def highlight_risk(row):
        level_val = row.get("Level", "")
        if level_val == "CRITICAL":
            return ["background-color: #FEE2E2"] * len(row)
        elif level_val == "HIGH":
            return ["background-color: #FEF2F2"] * len(row)
        elif level_val == "MEDIUM":
            return ["background-color: #FFFBEB"] * len(row)
        return ["background-color: #FFFFFF"] * len(row)

    st.dataframe(
        df_compare.style.apply(highlight_risk, axis=1),
        hide_index=True,
        use_container_width=True,
    )


# ---------------------------------------------------------------------------
# Tab 4 — How It Works
# ---------------------------------------------------------------------------
def tab_how_it_works():
    st.markdown("### ℹ️ How the Risk Engine Works")

    st.markdown("""
## Hybrid Risk Scoring Formula

The Early Warning System computes a **0–100 risk score** using five weighted components:

```
Score = (soil_moisture_100cm / 100 × 25)
      + (inflow_surge_rate × 25)
      + (discharge_imbalance × 20)
      + (rainfall_anomaly × 20)
      + (sensor_penalty × 10)
```

---

### Component Details

| # | Component | Max Pts | Formula |
|---|-----------|---------|-|
| 1 | **Soil Moisture (100 cm)** | 25 | `soil_moisture_100cm / 100 × 25` |
| 2 | **Inflow Surge Rate** | 25 | `(cur_inflow − prev_inflow) / prev_inflow`, capped 0–1 |
| 3 | **Discharge Imbalance** | 20 | `1 − (outflow / inflow)` when inflow > outflow, else 0 |
| 4 | **Rainfall Anomaly** | 20 | `min(actual / normal, 5) / 5` |
| 5 | **Sensor Dead Penalty** | 10 | `1` if Annamayya sensor is dead, else `0` |

---

### Risk Levels

| Level | Score Range | Interpretation |
|-------|-------------|----------------|
| 🟢 LOW | 0 – 30 | No immediate threat; monitor normally |
| 🟡 MEDIUM | 30 – 55 | Elevated watch; prepare response teams |
| 🟠 HIGH | 55 – 75 | Imminent risk; activate early warning |
| 🔴 CRITICAL | 75 – 100 | Emergency; initiate evacuation protocols |

---

### Confidence Score

Confidence (0–100%) is reduced when:
- **Sensor is dead** → −20%
- **No prior-day data** (surge rate unavailable) → −15%
- **All inflow sensors read zero** → −10%

---

### Time-to-Failure Estimate

| Level | Surge > threshold | Estimate |
|-------|-------------------|----------|
| CRITICAL | > 50% | < 6 hours |
| CRITICAL | ≤ 50% | 6–12 hours |
| HIGH | > 30% | 12–24 hours |
| HIGH | ≤ 30% | 24–48 hours |
| MEDIUM | — | 2–5 days |
| LOW | — | > 7 days |

---

### Data Sources

- **MI Tank Fill Report** — district-level tank storage % for Y.S.R Kadapa
- **Reservoir Summary** — real-time inflow/outflow for Pincha and Annamayya (Cheyyeru) reservoirs
- **Soil Moisture Summary** — volumetric soil moisture at 100 cm depth
- **Rainfall Summary** — monthly actual vs. normal rainfall and deviation %

All CSVs sourced from AP-WRIMS (Water Resources Information & Management System).
""")

    # ── Global Success Reference ────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### 🌍 Global Success Reference")

    st.markdown("""
<div style='background:#EFF6FF;border-left:5px solid #2D6A9F;padding:18px 22px;
     border-radius:8px;color:#1E3A5F;line-height:1.8;font-size:15px;
     box-shadow:0 2px 8px rgba(0,0,0,0.06);margin-bottom:20px'>
<strong>Google's Flood Hub</strong> — first piloted in India in 2018 — proves that
combining soil moisture, rainfall, and water level signals gives reliable early warning
<em>days</em> in advance, even in data-scarce regions. It now covers <strong>80 countries</strong>
and <strong>460 million people</strong>.<br><br>
It covers <strong>rivers</strong>. It does <strong>not</strong> cover earthen bunds or MI tanks.
AP has <strong>38,600 MI tanks</strong>. Annamayya 2021 showed what happens without coverage.<br><br>
We close that gap — using the same proven signal combination, built on AP's own APWRIMS data.
</div>
""", unsafe_allow_html=True)

    st.markdown("#### System Comparison")
    comparison_data = {
        "System":         ["Google Flood Hub", "EU Copernicus GloFAS", "AP-Wrims EWS (Ours)"],
        "Coverage":       ["80 countries, rivers", "Global rivers", "AP MI tanks + bunds"],
        "Data Source":    ["Satellite + gauges", "Satellite models", "APWRIMS + Sentinel-1"],
        "Bund Coverage":  ["❌ No", "❌ No", "✅ Yes"],
        "SMS Alert":      ["❌ No", "❌ No", "✅ Yes"],
        "Cost":           ["Commercial", "Free", "Free"],
    }
    df_cmp = pd.DataFrame(comparison_data)

    def highlight_ours(row):
        if row["System"] == "AP-Wrims EWS (Ours)":
            return ["background-color:#DCFCE7;font-weight:600"] * len(row)
        return [""] * len(row)

    st.dataframe(
        df_cmp.style.apply(highlight_ours, axis=1),
        hide_index=True, use_container_width=True,
    )

    # ── Cost Efficiency ─────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### 💰 Cost Efficiency")

    cost_data = {
        "Item": [
            "Sentinel-1 SAR Data",
            "APWRIMS Data",
            "Manual inspection (full season)",
            "Our system annual operating cost",
            "Inspection reduction",
            "Additional cost to govt for satellite",
        ],
        "Cost / Value": [
            "₹0 (Free — ESA Copernicus)",
            "₹0 (Existing Govt Infrastructure)",
            "₹80–100 Crore",
            "₹15–20 Crore",
            "85%",
            "₹0",
        ],
    }
    df_cost = pd.DataFrame(cost_data)

    def highlight_zero(row):
        if "₹0" in str(row["Cost / Value"]):
            return ["background-color:#F0FDF4"] * len(row)
        if "₹15" in str(row["Cost / Value"]) or "85%" in str(row["Cost / Value"]):
            return ["background-color:#EFF6FF"] * len(row)
        if "₹80" in str(row["Cost / Value"]):
            return ["background-color:#FEF2F2"] * len(row)
        return [""] * len(row)

    st.dataframe(
        df_cost.style.apply(highlight_zero, axis=1),
        hide_index=True, use_container_width=True,
    )

    # ── Footer quote ────────────────────────────────────────────────────────
    st.markdown("""
<div style='background:linear-gradient(135deg,#1E3A5F 0%,#2D6A9F 100%);
     padding:24px 28px;border-radius:12px;color:white;margin-top:24px;
     box-shadow:0 4px 16px rgba(30,58,95,0.25)'>
<p style='font-size:17px;margin:0 0 10px 0;line-height:1.7'>
<em>"Current systems tell you risk. We tell you <strong>what to do next</strong> —
where to act, which villages to alert, and what options reduce damage.
That is the difference between <strong>data</strong> and <strong>decision</strong>."</em>
</p>
<p style='margin:0;font-size:13px;opacity:0.8'>— HierachAI Technologies Pvt. Ltd.</p>
</div>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Tab 3 — Action Recommendations
# ---------------------------------------------------------------------------
def tab_action_recommendations():
    st.markdown("### 🎯 Decision Support — Action Recommendations")
    st.markdown(
        "<p style='color:#64748B;margin-top:-8px;margin-bottom:18px;font-size:14px'>"
        "System suggests feasible intervention options. "
        "<strong>Engineer approval required.</strong></p>",
        unsafe_allow_html=True,
    )

    # Reference Nov 18 data (CRITICAL scenario)
    data_n18 = all_data.get("Nov18", {})
    risk_n18 = risks.get("Nov18", {})

    st.markdown("""
<div class="critical-alert">
    🚨 Showing recommendations for CRITICAL scenario — November 18, 2021 08:00 AM<br>
    <span style="font-size:13px;font-weight:normal;">
    Risk Score: 88/100 · Time to Failure: 6–12 hours · Confidence: 65%
    </span>
</div>
""", unsafe_allow_html=True)

    st.markdown("#### Intervention Options")
    ca, cb, cc = st.columns(3)

    # ── Option A ────────────────────────────────────────────────────────────
    with ca:
        st.markdown("""
<div style='background:#FFFFFF;border:2px solid #16A34A;border-radius:10px;
     padding:20px;box-shadow:0 4px 16px rgba(22,163,74,0.12);height:100%'>
<div style='display:flex;align-items:center;gap:8px;margin-bottom:12px'>
    <span style='background:#16A34A;color:white;padding:4px 10px;border-radius:4px;
          font-size:11px;font-weight:700;letter-spacing:0.5px'>✅ RECOMMENDED</span>
</div>
<h4 style='color:#15803D;margin:0 0 14px 0;font-size:13px;letter-spacing:0.3px'>OPTION A — DIVERSION PATHWAY ASSESSMENT</h4>
<table style='width:100%;font-size:12px;color:#475569;border-collapse:collapse'>
<tr><td style='padding:6px 0;font-weight:700;color:#1B4F91;width:45%;border-bottom:1px solid #E2E8F0'>Potential path</td>
    <td style='border-bottom:1px solid #E2E8F0;color:#1E293B'>Cheyyeru → Pennar diversion canal</td></tr>
<tr><td style='padding:6px 0;font-weight:700;color:#1B4F91;border-bottom:1px solid #E2E8F0'>Relief window</td>
    <td style='border-bottom:1px solid #E2E8F0;color:#1E293B'>6–8 hours</td></tr>
<tr><td style='padding:6px 0;font-weight:700;color:#1B4F91;border-bottom:1px solid #E2E8F0'>Confidence</td>
    <td style='border-bottom:1px solid #E2E8F0;color:#1E293B'>Medium</td></tr>
<tr><td style='padding:6px 0;font-weight:700;color:#1B4F91;border-bottom:1px solid #E2E8F0'>Prerequisite</td>
    <td style='border-bottom:1px solid #E2E8F0;color:#1E293B'>Confirm canal gate status with field engineer</td></tr>
<tr><td style='padding:6px 0;font-weight:700;color:#1B4F91;vertical-align:top'>Why</td>
    <td style='color:#1E293B'>Annamayya inflow (11,531 cs) exceeds safe discharge capacity</td></tr>
</table>
</div>
""", unsafe_allow_html=True)
        st.button("✅ Recommend to Engineer", use_container_width=True,
                  key="btn_option_a", type="primary")

    # ── Option B ────────────────────────────────────────────────────────────
    with cb:
        st.markdown("""
<div style='background:#FFFFFF;border:2px solid #D97706;border-radius:10px;
     padding:20px;box-shadow:0 4px 16px rgba(217,119,6,0.12);height:100%'>
<div style='display:flex;align-items:center;gap:8px;margin-bottom:12px'>
    <span style='background:#D97706;color:white;padding:4px 10px;border-radius:4px;
          font-size:11px;font-weight:700;letter-spacing:0.5px'>📋 ALTERNATIVE</span>
</div>
<h4 style='color:#B45309;margin:0 0 14px 0;font-size:13px;letter-spacing:0.3px'>OPTION B — UPSTREAM RELEASE REDUCTION</h4>
<table style='width:100%;font-size:12px;color:#475569;border-collapse:collapse'>
<tr><td style='padding:6px 0;font-weight:700;color:#1B4F91;width:45%;border-bottom:1px solid #E2E8F0'>Suggest</td>
    <td style='border-bottom:1px solid #E2E8F0;color:#1E293B'>Reduce Gandikota releases by 20–30%</td></tr>
<tr><td style='padding:6px 0;font-weight:700;color:#1B4F91;border-bottom:1px solid #E2E8F0'>Current outflow</td>
    <td style='border-bottom:1px solid #E2E8F0;color:#1E293B'>15,000 cs (Nov 18 data)</td></tr>
<tr><td style='padding:6px 0;font-weight:700;color:#1B4F91;border-bottom:1px solid #E2E8F0'>Estimated relief</td>
    <td style='border-bottom:1px solid #E2E8F0;color:#1E293B'>4–6 hours</td></tr>
<tr><td style='padding:6px 0;font-weight:700;color:#1B4F91;border-bottom:1px solid #E2E8F0'>Confidence</td>
    <td style='border-bottom:1px solid #E2E8F0;color:#1E293B'>Medium</td></tr>
<tr><td style='padding:6px 0;font-weight:700;color:#1B4F91;vertical-align:top'>Why</td>
    <td style='color:#1E293B'>Reducing upstream pressure buys time for downstream preparation</td></tr>
</table>
</div>
""", unsafe_allow_html=True)
        st.button("📋 Flag for Review", use_container_width=True,
                  key="btn_option_b")

    # ── Option C ────────────────────────────────────────────────────────────
    with cc:
        st.markdown("""
<div style='background:#FFFFFF;border:2px solid #DC2626;border-radius:10px;
     padding:20px;box-shadow:0 4px 16px rgba(220,38,38,0.12);height:100%'>
<div style='display:flex;align-items:center;gap:8px;margin-bottom:12px'>
    <span style='background:#DC2626;color:white;padding:4px 10px;border-radius:4px;
          font-size:11px;font-weight:700;letter-spacing:0.5px'>🚨 LAST RESORT</span>
</div>
<h4 style='color:#B91C1C;margin:0 0 14px 0;font-size:13px;letter-spacing:0.3px'>OPTION C — CONTROLLED EMERGENCY RELEASE + ALERT</h4>
<table style='width:100%;font-size:12px;color:#475569;border-collapse:collapse'>
<tr><td style='padding:6px 0;font-weight:700;color:#1B4F91;width:45%;border-bottom:1px solid #E2E8F0'>Action</td>
    <td style='border-bottom:1px solid #E2E8F0;color:#1E293B'>Trigger controlled release from Annamayya</td></tr>
<tr><td style='padding:6px 0;font-weight:700;color:#1B4F91;border-bottom:1px solid #E2E8F0'>Parallel</td>
    <td style='border-bottom:1px solid #E2E8F0;color:#1E293B'>Alert all downstream villages simultaneously</td></tr>
<tr><td style='padding:6px 0;font-weight:700;color:#1B4F91;border-bottom:1px solid #E2E8F0'>Safe window</td>
    <td style='border-bottom:1px solid #E2E8F0;color:#1E293B'>3–4 hours for evacuation</td></tr>
<tr><td style='padding:6px 0;font-weight:700;color:#1B4F91;border-bottom:1px solid #E2E8F0;vertical-align:top'>Villages</td>
    <td style='border-bottom:1px solid #E2E8F0;color:#1E293B'>Mandapalli · Togurupeta · Pulapathur · Gundlur</td></tr>
<tr><td style='padding:6px 0;font-weight:700;color:#1B4F91;vertical-align:top'>Why</td>
    <td style='color:#1E293B'>If A &amp; B not feasible, controlled release is safer than uncontrolled breach</td></tr>
</table>
</div>
""", unsafe_allow_html=True)
        st.button("🚨 Initiate Alert Protocol", use_container_width=True,
                  key="btn_option_c")

    # ── Signal rationale table ───────────────────────────────────────────────
    st.markdown("---")
    st.markdown("#### Why These Recommendations")

    signal_data = {
        "Signal": [
            "Soil Saturation",
            "Inflow vs Outflow",
            "Pincha Surge",
            "Rainfall Anomaly",
            "Sensor Status",
        ],
        "Value": [
            "100% all depths",
            "11,531 vs 12,159 cs",
            "+16.6% in 24 hrs",
            "+380% above normal",
            "Suspicious (same reading 2 days)",
        ],
        "Implication": [
            "Ground cannot absorb more water",
            "Outflow exceeding inflow — pressure building",
            "Upstream stress escalating",
            "No relief expected",
            "Ground truth unavailable",
        ],
    }

    def highlight_signal(row):
        if "Suspicious" in str(row["Value"]) or "+380" in str(row["Value"]):
            return ["background-color:#FEE2E2;color:#7F1D1D"] * len(row)
        if "+16" in str(row["Value"]):
            return ["background-color:#FEF3C7;color:#78350F"] * len(row)
        return ["background-color:#F8FAFC;color:#1E293B"] * len(row)

    st.dataframe(
        pd.DataFrame(signal_data).style.apply(highlight_signal, axis=1),
        hide_index=True, use_container_width=True,
    )

    # ── Disclaimer ──────────────────────────────────────────────────────────
    st.markdown("""
<div style='background:#1A0D00;border:1px solid #FFB300;border-radius:6px;
     padding:14px 18px;margin-top:10px;color:#FDE68A;font-size:13px'>
⚠️ <strong style='color:#FFB300'>Disclaimer:</strong> These are AI-generated recommendations for decision support only.
All actions require authorization from <strong>APSDMA engineers</strong> and
<strong>district administration</strong>.
</div>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Tab 4 — Village Alert System
# ---------------------------------------------------------------------------
def tab_village_alerts():
    st.markdown("### 📱 Village Alert System — Last Mile Communication")

    # ── Alert status panel ──────────────────────────────────────────────────
    st.markdown("""
<div style='background:linear-gradient(135deg,#7C3AED,#DC2626);color:white;
     padding:16px 24px;border-radius:10px;margin-bottom:20px;
     box-shadow:0 4px 16px rgba(220,38,38,0.3)'>
<div style='display:flex;justify-content:space-between;flex-wrap:wrap;gap:10px'>
    <div>
        <div style='font-size:18px;font-weight:700'>🚨 Alert Status: ACTIVE</div>
        <div style='font-size:13px;opacity:0.9;margin-top:4px'>
            Risk Level: CRITICAL &nbsp;|&nbsp; Date: Nov 18, 2021
        </div>
    </div>
    <div style='text-align:right;font-size:13px;opacity:0.9'>
        <div>📞 Registered contacts in impact zone: <strong>1,247 numbers</strong></div>
        <div>⏰ Alert dispatch time: 08:15 AM &nbsp;|&nbsp; Hours before breach: ~17 hours</div>
    </div>
</div>
</div>
""", unsafe_allow_html=True)

    # ── SMS boxes ───────────────────────────────────────────────────────────
    st.markdown("#### Alert Messages Dispatched")
    sms_en, sms_te = st.columns(2)

    with sms_en:
        st.markdown("**🇬🇧 English**")
        st.markdown("""
<div class="sms-box">
APSDMA EARLY WARNING ALERT<br>
─────────────────────────────<br>
Date: Nov 18, 2021 | 08:15 AM<br>
Zone: Mandapalli, Togurupeta,<br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Pulapathur, Gundlur<br>
<br>
⚠️ RISK: CRITICAL<br>
Water levels rising rapidly at<br>
Annamayya Dam &amp; Pincha Project.<br>
<br>
ACTION: Move to safe location<br>
IMMEDIATELY<br>
<br>
Relief Camp: Rajampet Govt School<br>
Helpline: 1800-XXX-XXXX<br>
<br>
- APSDMA Disaster Management
</div>
""", unsafe_allow_html=True)

    with sms_te:
        st.markdown("**🇮🇳 Telugu**")
        st.markdown("""
<div class="sms-box">
APSDMA హెచ్చరిక సందేశం<br>
─────────────────────────────<br>
తేదీ: నవంబర్ 18, 2021 | 08:15 AM<br>
ప్రాంతం: మండపల్లి, తోగురుపేట,<br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;పులపత్తూర్, గుండ్లూరు<br>
<br>
⚠️ ప్రమాదం: తీవ్రం<br>
అన్నమయ్య డ్యామ్ వద్ద నీటి మట్టాలు<br>
వేగంగా పెరుగుతున్నాయి.<br>
<br>
చర్య: వెంటనే సురక్షిత ప్రాంతానికి<br>
వెళ్ళండి<br>
<br>
సహాయ శిబిరం: రాజంపేట ప్రభుత్వ పాఠశాల<br>
హెల్ప్లైన్: 1800-XXX-XXXX<br>
<br>
- APSDMA విపత్తు నిర్వహణ
</div>
""", unsafe_allow_html=True)

    # ── Village table ────────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("#### Impact Zone — Village Alert Status")

    village_data = {
        "Village":            ["Mandapalli", "Togurupeta", "Pulapathur", "Gundlur"],
        "Population":         ["~500", "~500", "~300", "~250"],
        "Distance from Dam":  ["2.1 km", "2.8 km", "3.2 km", "4.1 km"],
        "Risk Level":         ["CRITICAL", "CRITICAL", "HIGH", "HIGH"],
        "Alert Status":       ["✅ Alerted", "✅ Alerted", "✅ Alerted", "✅ Alerted"],
    }

    def highlight_village(row):
        if row["Risk Level"] == "CRITICAL":
            return ["background-color:#FEE2E2"] * len(row)
        return ["background-color:#FEF3C7"] * len(row)

    st.dataframe(
        pd.DataFrame(village_data).style.apply(highlight_village, axis=1),
        hide_index=True, use_container_width=True,
    )

    # ── Comparison section ───────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("#### Why SMS Beats Existing Systems")

    col_curr, col_ours, col_goog = st.columns(3)

    with col_curr:
        st.markdown("""
<div style='background:#FEF2F2;border:1px solid #EF4444;border-radius:10px;
     padding:18px;height:100%'>
<div style='font-size:15px;font-weight:700;color:#DC2626;margin-bottom:12px'>
    ❌ Current System
</div>
<div style='font-size:13px;color:#374151;line-height:2'>
    Data in portal<br>
    → Engineer logs in<br>
    → Reads data<br>
    → Decides<br>
    → Calls collector<br>
    → Villages informed<br>
    <span style='font-weight:700;color:#DC2626'>⏱ 6–8 hours</span>
</div>
</div>
""", unsafe_allow_html=True)

    with col_ours:
        st.markdown("""
<div style='background:#F0FDF4;border:2px solid #22C55E;border-radius:10px;
     padding:18px;height:100%;box-shadow:0 2px 8px rgba(34,197,94,0.15)'>
<div style='font-size:15px;font-weight:700;color:#16A34A;margin-bottom:12px'>
    ✅ Our System
</div>
<div style='font-size:13px;color:#374151;line-height:2'>
    Risk detected<br>
    → Auto-alert generated<br>
    → SMS to 1,247 numbers<br>
    &nbsp;&nbsp;&nbsp;directly<br>
    <br>
    <span style='font-weight:700;color:#16A34A'>⏱ &lt; 15 minutes</span>
</div>
</div>
""", unsafe_allow_html=True)

    with col_goog:
        st.markdown("""
<div style='background:#F8FAFC;border:1px solid #CBD5E1;border-radius:10px;
     padding:18px;height:100%'>
<div style='font-size:15px;font-weight:700;color:#64748B;margin-bottom:12px'>
    🌍 Google Flood Hub
</div>
<div style='font-size:13px;color:#374151;line-height:1.9'>
    Covers rivers only.<br>
    No village-level SMS.<br>
    No Telugu language support.<br>
    No MI tank coverage.<br>
    <br>
    <span style='font-weight:700;color:#64748B'>Gap: Earthen bunds &amp; tanks</span>
</div>
</div>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
tabs = st.tabs([
    "🗺️ Overview",
    "📅 Historical Replay",
    "🎯 Action Recommendations",
    "📱 Village Alert System",
    "📡 Live 2026",
    "ℹ️ How It Works",
])
with tabs[0]:
    tab_overview()
with tabs[1]:
    tab_historical()
with tabs[2]:
    tab_action_recommendations()
with tabs[3]:
    tab_village_alerts()
with tabs[4]:
    tab_live()
with tabs[5]:
    tab_how_it_works()

# ---------------------------------------------------------------------------
# Footer bar + close wrapper div
# ---------------------------------------------------------------------------
st.markdown("""
</div>
<div class="ews-footer">
  <span>📡 Data Sources: AP-WRIMS Portal · Sentinel-1 SAR (ESA Copernicus) · APSDMA Real-Time Feed</span>
  <span>🏢 HierachAI Technologies Pvt. Ltd. · DPIIT Recognised · Women-Led Startup · Kadapa, Andhra Pradesh</span>
  <span>⚠ For authorized APSDMA / district administration use only</span>
</div>
""", unsafe_allow_html=True)
