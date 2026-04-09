"""
SLA Portal — Second Look Alliance
Multi-page Streamlit app for criminal justice reform data
Main entry point / home page
"""

import streamlit as st
from pathlib import Path
import sys

# Auth gate
sys.path.insert(0, str(Path(__file__).parent))
from auth import require_auth

# Configure page
st.set_page_config(
    page_title="SLA Portal",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Apply dark theme CSS and branding
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&display=swap');
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500&display=swap');

    * {
        font-family: 'DM Sans', sans-serif;
    }

    code {
        font-family: 'JetBrains Mono', monospace;
    }

    html, body, [data-testid="stAppViewContainer"] {
        background-color: #0f1117;
        color: #e8e8ed;
    }

    [data-testid="stSidebar"] {
        background-color: #0f1117;
        border-right: 1px solid #2a2d3a;
    }

    .stMetric {
        background-color: #1a1d29;
        padding: 1.5rem;
        border-radius: 12px;
        border: 1px solid #2a2d3a;
    }

    .stMetric label {
        color: #8b8fa3;
        font-size: 0.85rem;
        font-weight: 500;
    }

    .stMetric [data-testid="metric-container"] > div:first-child {
        color: #22c55e;
        font-size: 2rem;
        font-weight: 700;
    }

    .nav-card {
        background: linear-gradient(135deg, #1a1d29 0%, #232738 100%);
        border: 1px solid #2a2d3a;
        border-radius: 12px;
        padding: 1.5rem;
        margin: 0.5rem 0;
        cursor: pointer;
        transition: all 0.3s ease;
    }

    .nav-card:hover {
        border-color: #22c55e;
        box-shadow: 0 0 12px rgba(34, 197, 94, 0.1);
        transform: translateY(-2px);
    }

    .nav-card-title {
        font-size: 1.1rem;
        font-weight: 600;
        color: #e8e8ed;
        margin-bottom: 0.5rem;
    }

    .nav-card-desc {
        font-size: 0.85rem;
        color: #8b8fa3;
        line-height: 1.4;
    }

    .nav-card-icon {
        font-size: 2rem;
        margin-bottom: 0.75rem;
    }

    .welcome-banner {
        background: linear-gradient(135deg, rgba(34, 197, 94, 0.1) 0%, rgba(59, 130, 246, 0.1) 100%);
        border: 1px solid rgba(34, 197, 94, 0.2);
        border-radius: 16px;
        padding: 2rem;
        margin-bottom: 2rem;
    }

    .welcome-banner h1 {
        color: #22c55e;
        margin: 0;
        font-size: 2.2rem;
        font-weight: 700;
    }

    .welcome-banner p {
        color: #8b8fa3;
        margin: 0.75rem 0 0 0;
        font-size: 1rem;
    }

    .kpi-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
        gap: 1rem;
        margin-bottom: 2rem;
    }

    .kpi-card {
        background: #1a1d29;
        border: 1px solid #2a2d3a;
        border-radius: 12px;
        padding: 1.5rem;
    }

    .kpi-label {
        color: #8b8fa3;
        font-size: 0.85rem;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 0.5rem;
    }

    .kpi-value {
        color: #22c55e;
        font-size: 1.8rem;
        font-weight: 700;
    }

    .kpi-subtext {
        color: #8b8fa3;
        font-size: 0.75rem;
        margin-top: 0.5rem;
    }

    .update-timestamp {
        color: #8b8fa3;
        font-size: 0.8rem;
        text-align: center;
        margin-top: 2rem;
        padding-top: 1rem;
        border-top: 1px solid #2a2d3a;
    }

    h1, h2, h3 {
        color: #e8e8ed;
    }

    .stButton > button {
        background-color: #22c55e;
        color: #0f1117;
        font-weight: 600;
        border: none;
    }

    .stButton > button:hover {
        background-color: #16a34a;
    }
</style>
""", unsafe_allow_html=True)

# Require auth
username = require_auth("Second Look Alliance", accent_color="#22c55e")

# Main content
st.markdown("""
<div class="welcome-banner">
    <h1>⚖️ Second Look Alliance Portal</h1>
    <p>Criminal justice reform data explorer. Survey results, voter archetypes, demographic models, and media tools.</p>
</div>
""", unsafe_allow_html=True)

# KPI Cards
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(label="States Covered", value="6", delta=None)

with col2:
    st.metric(label="Total Respondents", value="12.5K", delta="↑ 2.3K this month")

with col3:
    st.metric(label="Active Surveys", value="18", delta="↑ 3 new")

with col4:
    st.metric(label="Reform Temp.", value="62°", delta="↑ 4° avg")

st.divider()

# Navigation Grid
st.markdown("### Quick Access")

nav_items = [
    {
        "title": "Survey Results",
        "icon": "📊",
        "description": "State dashboards, durability matrices, coalition heatmaps, voter pathways, and message deployment recommendations.",
        "page": "1_Survey_Results",
    },
    {
        "title": "VIP Archetypes",
        "icon": "👥",
        "description": "Voter archetype profiles, demographic distributions, persuasion pathways, and temperature gauges.",
        "page": "2_VIP_Scores",
    },
    {
        "title": "MrP Estimates",
        "icon": "📈",
        "description": "Geographic and demographic statistical models with confidence intervals and trend analysis.",
        "page": "3_MrP_Estimates",
    },
    {
        "title": "Media Portal",
        "icon": "📢",
        "description": "Campaign builder, media placement tracker, and spend management for survey fielding and paid ads.",
        "page": "4_Media_Portal",
    },
    {
        "title": "Survey Writer",
        "icon": "✏️",
        "description": "AI-powered question writing and rewriting tool with best practices guidance.",
        "page": "5_Survey_Writer",
    },
    {
        "title": "AI Search",
        "icon": "🔍",
        "description": "Chat-style interface to query survey data, compare states, and discover insights.",
        "page": "6_AI_Search",
    },
]

cols = st.columns(3)
for idx, item in enumerate(nav_items):
    with cols[idx % 3]:
        st.markdown(f"""
        <a href="/{item['page']}" style="text-decoration: none;">
            <div class="nav-card">
                <div class="nav-card-icon">{item['icon']}</div>
                <div class="nav-card-title">{item['title']}</div>
                <div class="nav-card-desc">{item['description']}</div>
            </div>
        </a>
        """, unsafe_allow_html=True)

st.divider()

# Data Overview Section
st.markdown("### Data Overview")

col1, col2 = st.columns(2)

with col1:
    st.markdown("**States & Coverage**")
    states_data = {
        "State": ["Oklahoma", "Louisiana", "North Carolina", "Virginia", "Massachusetts", "New Jersey"],
        "Respondents": [2100, 2050, 2200, 2150, 2000, 2000],
        "Surveys": [3, 3, 3, 3, 3, 3],
    }
    import pandas as pd
    df_states = pd.DataFrame(states_data)
    st.dataframe(df_states, use_container_width=True, hide_index=True)

with col2:
    st.markdown("**Key Constructs**")
    constructs = [
        "Procedural Fairness",
        "Proportionality",
        "Constitutional Rights",
        "Juvenile Compassion",
        "Rehabilitation",
        "Dangerousness Distinction",
        "Fiscal Efficiency",
        "Fines & Fees",
        "Compassion",
        "Police Discretion",
        "Promise of Redemption",
    ]
    st.markdown("\n".join([f"• {c}" for c in constructs]))

st.markdown("""
<div class="update-timestamp">
    Last data update: 2026-04-09 14:32 UTC
</div>
""", unsafe_allow_html=True)
