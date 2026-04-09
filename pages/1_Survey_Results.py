"""
Survey Results Page — State dashboards, durability matrices, heatmaps, comparisons, voter pathways, message deploy
"""

import streamlit as st
from pathlib import Path
import sys
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px

# Auth gate
sys.path.insert(0, str(Path(__file__).parent.parent))
from auth import require_auth

# Configure page
st.set_page_config(
    page_title="Survey Results — SLA Portal",
    page_icon="📊",
    layout="wide",
)

# Dark theme
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&display=swap');
    html, body, [data-testid="stAppViewContainer"] {
        background-color: #0f1117;
        color: #e8e8ed;
    }
    [data-testid="stSidebar"] {
        background-color: #0f1117;
        border-right: 1px solid #2a2d3a;
    }
    .metric-card {
        background: #1a1d29;
        border: 1px solid #2a2d3a;
        border-radius: 12px;
        padding: 1rem;
        margin: 0.5rem 0;
    }
    .quadrant-card {
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
        font-size: 0.9rem;
    }
    .golden-zone { background: rgba(34, 197, 94, 0.1); border-left: 4px solid #22c55e; }
    .primary-fuel { background: rgba(59, 130, 246, 0.1); border-left: 4px solid #3b82f6; }
    .general-arsenal { background: rgba(245, 158, 11, 0.1); border-left: 4px solid #f59e0b; }
    .dead-weight { background: rgba(107, 114, 128, 0.1); border-left: 4px solid #6b7280; }
</style>
""", unsafe_allow_html=True)

username = require_auth("Second Look Alliance", accent_color="#22c55e")

st.title("📊 Survey Results")

# Demo data
STATES = ["Oklahoma", "Louisiana", "North Carolina", "Virginia", "Massachusetts", "New Jersey"]
CONSTRUCTS = [
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

BELIEF_AXES = [
    {"name": "System Reliability", "desc": "Does the CJ system generally get it right?"},
    {"name": "Capacity for Change", "desc": "Can systems and people change?"},
    {"name": "Change-Punishment Relationship", "desc": "Does punishment enable change?"},
]

DEMOS = ["Party", "Ideology", "Race", "Age", "Gender", "Education", "Area Type"]

# Helper to generate demo data
def get_state_data(state):
    """Generate demo respondent/support data for a state."""
    np.random.seed(hash(state) % 2**32)
    return {
        "respondents": np.random.randint(1800, 2400),
        "golden_zone_pct": np.random.randint(35, 55),
        "top_construct": np.random.choice(CONSTRUCTS),
    }

def get_construct_support(state, construct):
    """Generate support % for construct in state."""
    np.random.seed((hash(state) + hash(construct)) % 2**32)
    return np.random.randint(40, 85)

def get_construct_durability(state, construct):
    """Generate durability score for construct."""
    np.random.seed((hash(state) + hash(construct) + 1000) % 2**32)
    return np.random.randint(30, 95)

def get_demographic_support(construct, demo_group):
    """Generate support % for demographic group on construct."""
    np.random.seed((hash(construct) + hash(demo_group)) % 2**32)
    return np.random.randint(30, 95)

# Tabs
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "State Dashboard",
    "Durability Matrix",
    "Coalition Heatmap",
    "Cross-State Comparison",
    "Voter Pathways",
    "Message Deploy",
])

# ─────────────────────────────────────────
# TAB 1: STATE DASHBOARD
# ─────────────────────────────────────────
with tab1:
    st.markdown("### State Dashboard")

    col1, col2 = st.columns([1, 3])

    with col1:
        selected_state = st.selectbox("Select State:", STATES, key="state_dash")

    with col2:
        state_data = get_state_data(selected_state)

        col_a, col_b, col_c = st.columns(3)
        with col_a:
            st.metric("Respondents", state_data["respondents"])
        with col_b:
            st.metric("Golden Zone", f"{state_data['golden_zone_pct']}%")
        with col_c:
            st.metric("Top Construct", state_data["top_construct"])

    st.divider()

    # Support gauge bars by construct
    st.markdown("**Support by Construct**")

    col1, col2 = st.columns(2)

    with col1:
        for construct in CONSTRUCTS[:6]:
            support = get_construct_support(selected_state, construct)
            st.write(f"**{construct}**")
            st.progress(support / 100, text=f"{support}%")

    with col2:
        for construct in CONSTRUCTS[6:]:
            support = get_construct_support(selected_state, construct)
            st.write(f"**{construct}**")
            st.progress(support / 100, text=f"{support}%")

    st.divider()

    # Durability snapshot
    st.markdown("**Durability Snapshot**")
    durability_data = []
    for construct in CONSTRUCTS:
        durability_data.append({
            "Construct": construct,
            "Durability": get_construct_durability(selected_state, construct),
        })

    df_durability = pd.DataFrame(durability_data)
    df_durability = df_durability.sort_values("Durability", ascending=False)

    fig = px.bar(
        df_durability.head(8),
        x="Durability",
        y="Construct",
        orientation="h",
        title="Top Durable Constructs",
        color="Durability",
        color_continuous_scale=[(0.3, "#22c55e"), (0.7, "#3b82f6")],
    )
    fig.update_layout(
        paper_bgcolor="#0f1117",
        plot_bgcolor="#1a1d29",
        font={"color": "#e8e8ed", "family": "DM Sans"},
        showlegend=False,
    )
    st.plotly_chart(fig, use_container_width=True)

# ─────────────────────────────────────────
# TAB 2: DURABILITY MATRIX
# ─────────────────────────────────────────
with tab2:
    st.markdown("### Durability Matrix")
    st.markdown("*Support % vs Durability score — each point is a construct in a state*")

    col1, col2 = st.columns([1, 4])
    with col1:
        selected_constructs_dur = st.multiselect(
            "Filter Constructs:",
            CONSTRUCTS,
            default=CONSTRUCTS[:4],
            key="dur_constructs"
        )

    # Generate scatter data
    scatter_data = []
    for state in STATES:
        for construct in selected_constructs_dur:
            scatter_data.append({
                "State": state,
                "Construct": construct,
                "Support": get_construct_support(state, construct),
                "Durability": get_construct_durability(state, construct),
            })

    df_scatter = pd.DataFrame(scatter_data)

    fig = px.scatter(
        df_scatter,
        x="Support",
        y="Durability",
        color="State",
        hover_name="Construct",
        size_max=200,
        title="Construct Performance Matrix",
    )
    fig.add_hline(y=60, line_dash="dash", line_color="#8b8fa3", annotation_text="Durability Threshold")
    fig.add_vline(x=60, line_dash="dash", line_color="#8b8fa3", annotation_text="Support Threshold")
    fig.update_layout(
        paper_bgcolor="#0f1117",
        plot_bgcolor="#1a1d29",
        font={"color": "#e8e8ed", "family": "DM Sans"},
        xaxis_title="Support %",
        yaxis_title="Durability Score",
        height=500,
    )
    st.plotly_chart(fig, use_container_width=True)

# ─────────────────────────────────────────
# TAB 3: COALITION HEATMAP
# ─────────────────────────────────────────
with tab3:
    st.markdown("### Coalition Heatmap")
    st.markdown("*Demographic group support across constructs*")

    col1, col2 = st.columns([1, 4])
    with col1:
        selected_construct_heat = st.selectbox(
            "Select Construct:",
            CONSTRUCTS,
            key="heat_construct"
        )
        selected_demo_type = st.selectbox(
            "Demographic Type:",
            ["Party", "Ideology", "Race", "Age", "Gender", "Education", "Area Type"],
            key="heat_demo"
        )

    # Map demo types to groups
    demo_map = {
        "Party": ["Republican", "Democrat", "Independent"],
        "Ideology": ["Very Conservative", "Conservative", "Moderate", "Liberal", "Very Liberal"],
        "Race": ["White", "Black", "Hispanic", "Asian", "Other"],
        "Age": ["18-34", "35-49", "50-64", "65+"],
        "Gender": ["Male", "Female", "Non-binary"],
        "Education": ["High School", "Some College", "Bachelor", "Graduate"],
        "Area Type": ["Urban", "Suburban", "Rural"],
    }

    groups = demo_map.get(selected_demo_type, [])

    # Generate heatmap data
    heatmap_data = []
    for state in STATES:
        for group in groups:
            heatmap_data.append({
                "State": state,
                "Group": group,
                "Support": get_demographic_support(f"{selected_construct_heat}_{group}", state),
            })

    df_heat = pd.DataFrame(heatmap_data)
    df_heat_pivot = df_heat.pivot(index="Group", columns="State", values="Support")

    fig = px.imshow(
        df_heat_pivot,
        color_continuous_scale="RdYlGn",
        title=f"{selected_construct_heat} by {selected_demo_type}",
        labels={"color": "Support %"},
        zmin=20,
        zmax=90,
    )
    fig.update_layout(
        paper_bgcolor="#0f1117",
        plot_bgcolor="#1a1d29",
        font={"color": "#e8e8ed", "family": "DM Sans"},
        height=400,
    )
    st.plotly_chart(fig, use_container_width=True)

# ─────────────────────────────────────────
# TAB 4: CROSS-STATE COMPARISON
# ─────────────────────────────────────────
with tab4:
    st.markdown("### Cross-State Comparison")

    col1, col2 = st.columns([1, 3])
    with col1:
        selected_states_comp = st.multiselect(
            "States to Compare:",
            STATES,
            default=STATES[:3],
            key="comp_states"
        )
        selected_constructs_comp = st.multiselect(
            "Constructs to Compare:",
            CONSTRUCTS,
            default=CONSTRUCTS[:4],
            key="comp_constructs"
        )

    # Generate comparison data
    comp_data = []
    for state in selected_states_comp:
        for construct in selected_constructs_comp:
            comp_data.append({
                "State": state,
                "Construct": construct,
                "Support": get_construct_support(state, construct),
            })

    df_comp = pd.DataFrame(comp_data)

    fig = px.bar(
        df_comp,
        x="Construct",
        y="Support",
        color="State",
        barmode="group",
        title="Support Comparison",
    )
    fig.update_layout(
        paper_bgcolor="#0f1117",
        plot_bgcolor="#1a1d29",
        font={"color": "#e8e8ed", "family": "DM Sans"},
        height=500,
        xaxis_tickangle=-45,
    )
    st.plotly_chart(fig, use_container_width=True)

# ─────────────────────────────────────────
# TAB 5: VOTER PATHWAYS
# ─────────────────────────────────────────
with tab5:
    st.markdown("### Voter Pathways — Belief Axes Decision Tree")
    st.markdown("*The 3-axis model guides messaging strategy*")

    for idx, axis in enumerate(BELIEF_AXES):
        st.markdown(f"#### Axis {idx + 1}: {axis['name']}")
        st.write(f"**Question:** {axis['desc']}")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**✓ Yes Path**")
            if idx == 0:
                st.write("System defenders — believe current processes are adequate")
                st.write("*Strategy: Reframe around shared values (safety, fiscal responsibility)*")
            elif idx == 1:
                st.write("Change optimists — people can reform")
                st.write("*Strategy: Focus on rehabilitation evidence and success stories*")
            else:
                st.write("Transformation believers — punishment can enable change")
                st.write("*Strategy: Emphasize accountability paired with redemption*")

        with col2:
            st.markdown("**✗ No Path**")
            if idx == 0:
                st.write("System skeptics — open to reform based on fairness concerns")
                st.write("*Strategy: Lead with procedural fairness and constitutional rights*")
            elif idx == 1:
                st.write("Change pessimists — systemic resistance to reform")
                st.write("*Strategy: Focus on structural barriers and policy fixes*")
            else:
                st.write("Punishment-skeptics — punishment perpetuates harm")
                st.write("*Strategy: Emphasize rehabilitation and proportionality*")

        st.divider()

# ─────────────────────────────────────────
# TAB 6: MESSAGE DEPLOY
# ─────────────────────────────────────────
with tab6:
    st.markdown("### Message Deploy — Quadrant Recommendations")
    st.markdown("*Constructs organized by support × durability quadrants*")

    col1, col2 = st.columns([1, 4])
    with col1:
        selected_state_deploy = st.selectbox(
            "State:",
            STATES,
            key="deploy_state"
        )

    # Assign constructs to quadrants
    quadrants = {
        "Golden Zone": [],
        "Primary Fuel": [],
        "General Arsenal": [],
        "Dead Weight": [],
    }

    for construct in CONSTRUCTS:
        support = get_construct_support(selected_state_deploy, construct)
        durability = get_construct_durability(selected_state_deploy, construct)

        if support > 60 and durability > 60:
            quadrants["Golden Zone"].append((construct, support, durability))
        elif support > 60:
            quadrants["Primary Fuel"].append((construct, support, durability))
        elif durability > 60:
            quadrants["General Arsenal"].append((construct, support, durability))
        else:
            quadrants["Dead Weight"].append((construct, support, durability))

    # Display quadrants
    col1, col2 = st.columns(2)

    with col1:
        st.markdown('<div class="quadrant-card golden-zone"><strong>🟢 Golden Zone</strong><br><em>High support + High durability</em><br><em>Lead with these — proven winners</em></div>', unsafe_allow_html=True)
        for construct, support, durability in sorted(quadrants["Golden Zone"], key=lambda x: x[1], reverse=True):
            st.caption(f"**{construct}** — {support}% support, {durability}/100 durability")

        st.divider()

        st.markdown('<div class="quadrant-card general-arsenal"><strong>🟡 General Arsenal</strong><br><em>Low support + High durability</em><br><em>Build foundation for future</em></div>', unsafe_allow_html=True)
        for construct, support, durability in sorted(quadrants["General Arsenal"], key=lambda x: x[2], reverse=True):
            st.caption(f"**{construct}** — {support}% support, {durability}/100 durability")

    with col2:
        st.markdown('<div class="quadrant-card primary-fuel"><strong>🔵 Primary Fuel</strong><br><em>High support + Low durability</em><br><em>Protect and reinforce</em></div>', unsafe_allow_html=True)
        for construct, support, durability in sorted(quadrants["Primary Fuel"], key=lambda x: x[1], reverse=True):
            st.caption(f"**{construct}** — {support}% support, {durability}/100 durability")

        st.divider()

        st.markdown('<div class="quadrant-card dead-weight"><strong>⚫ Dead Weight</strong><br><em>Low support + Low durability</em><br><em>Avoid or pivot</em></div>', unsafe_allow_html=True)
        for construct, support, durability in sorted(quadrants["Dead Weight"], key=lambda x: x[1], reverse=True):
            st.caption(f"**{construct}** — {support}% support, {durability}/100 durability")
