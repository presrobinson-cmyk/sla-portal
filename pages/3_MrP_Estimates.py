"""
MrP Estimates Page — Geographic and demographic model estimates
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

st.set_page_config(
    page_title="MrP Estimates — SLA Portal",
    page_icon="📈",
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
    .metric-box {
        background: #1a1d29;
        border: 1px solid #2a2d3a;
        border-radius: 12px;
        padding: 1rem;
        margin: 0.5rem 0;
    }
    .ci-label {
        font-size: 0.85rem;
        color: #8b8fa3;
    }
</style>
""", unsafe_allow_html=True)

username = require_auth("Second Look Alliance", accent_color="#22c55e")

st.title("📈 MrP Estimates")

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

def get_mrp_estimate(state, construct):
    """Generate MrP point estimate with confidence interval."""
    np.random.seed((hash(state) + hash(construct)) % 2**32)
    point = np.random.uniform(45, 75)
    ci_lower = point - np.random.uniform(3, 8)
    ci_upper = point + np.random.uniform(3, 8)
    return {
        "point": point,
        "ci_lower": max(20, ci_lower),
        "ci_upper": min(95, ci_upper),
    }

def get_demographic_estimate(construct, demo_group):
    """Generate demographic subgroup estimate."""
    np.random.seed((hash(construct) + hash(demo_group)) % 2**32)
    point = np.random.uniform(35, 85)
    return {
        "point": point,
        "ci_lower": max(20, point - np.random.uniform(4, 10)),
        "ci_upper": min(95, point + np.random.uniform(4, 10)),
    }

# Tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "State Estimates",
    "Demographic Subgroups",
    "Trend Analysis",
    "State Rankings",
    "Map Explorer",
])

# ─────────────────────────────────────────
# TAB 1: STATE ESTIMATES
# ─────────────────────────────────────────
with tab1:
    st.markdown("### State-Level Reform Support Estimates")

    col1, col2 = st.columns([1, 4])
    with col1:
        selected_state = st.selectbox("State:", STATES, key="state_est")
        selected_construct_mrp = st.selectbox("Construct:", CONSTRUCTS, key="construct_mrp")

    # Get estimate with CI
    estimate = get_mrp_estimate(selected_state, selected_construct_mrp)

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            label="Point Estimate",
            value=f"{estimate['point']:.1f}%",
        )

    with col2:
        st.markdown(f"""
        <div class="metric-box">
            <div style="color: #8b8fa3; font-size: 0.85rem; font-weight: 500; margin-bottom: 0.5rem;">95% Confidence Interval</div>
            <div style="color: #22c55e; font-size: 1.5rem; font-weight: 700;">
                {estimate['ci_lower']:.1f}% — {estimate['ci_upper']:.1f}%
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        margin_of_error = (estimate['ci_upper'] - estimate['ci_lower']) / 2
        st.markdown(f"""
        <div class="metric-box">
            <div style="color: #8b8fa3; font-size: 0.85rem; font-weight: 500; margin-bottom: 0.5rem;">Margin of Error</div>
            <div style="color: #3b82f6; font-size: 1.5rem; font-weight: 700;">±{margin_of_error:.1f}%</div>
        </div>
        """, unsafe_allow_html=True)

    st.divider()

    # All constructs for selected state
    st.markdown(f"**All Constructs — {selected_state}**")

    all_estimates = []
    for construct in CONSTRUCTS:
        est = get_mrp_estimate(selected_state, construct)
        all_estimates.append({
            "Construct": construct,
            "Estimate": est["point"],
            "Lower": est["ci_lower"],
            "Upper": est["ci_upper"],
        })

    df_estimates = pd.DataFrame(all_estimates).sort_values("Estimate", ascending=True)

    fig = go.Figure()

    # Add CI range as error bars
    fig.add_trace(go.Bar(
        y=df_estimates["Construct"],
        x=df_estimates["Estimate"],
        error_x=dict(
            type="data",
            symmetric=False,
            array=df_estimates["Upper"] - df_estimates["Estimate"],
            arrayminus=df_estimates["Estimate"] - df_estimates["Lower"],
        ),
        marker=dict(color="#22c55e"),
        orientation="h",
    ))

    fig.update_layout(
        title=f"MrP Estimates with 95% CI — {selected_state}",
        xaxis_title="Support %",
        yaxis_title="Construct",
        paper_bgcolor="#0f1117",
        plot_bgcolor="#1a1d29",
        font={"color": "#e8e8ed", "family": "DM Sans"},
        height=500,
    )

    st.plotly_chart(fig, use_container_width=True)

# ─────────────────────────────────────────
# TAB 2: DEMOGRAPHIC SUBGROUPS
# ─────────────────────────────────────────
with tab2:
    st.markdown("### Demographic Subgroup Estimates")

    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        selected_construct_demo = st.selectbox("Construct:", CONSTRUCTS, key="construct_demo")
    with col2:
        demo_type = st.selectbox(
            "Demographic:",
            ["Party", "Ideology", "Race", "Age", "Gender", "Education"],
            key="demo_type"
        )

    # Map demo types to groups
    demo_map = {
        "Party": ["Republican", "Democrat", "Independent"],
        "Ideology": ["Very Conservative", "Conservative", "Moderate", "Liberal", "Very Liberal"],
        "Race": ["White", "Black", "Hispanic", "Asian"],
        "Age": ["18-34", "35-49", "50-64", "65+"],
        "Gender": ["Male", "Female", "Non-binary"],
        "Education": ["High School", "Some College", "Bachelor", "Graduate"],
    }

    groups = demo_map[demo_type]

    # Generate estimates
    demo_estimates = []
    for group in groups:
        est = get_demographic_estimate(selected_construct_demo, group)
        demo_estimates.append({
            "Group": group,
            "Estimate": est["point"],
            "Lower": est["ci_lower"],
            "Upper": est["ci_upper"],
        })

    df_demo = pd.DataFrame(demo_estimates).sort_values("Estimate", ascending=True)

    fig = go.Figure()

    fig.add_trace(go.Bar(
        y=df_demo["Group"],
        x=df_demo["Estimate"],
        error_x=dict(
            type="data",
            symmetric=False,
            array=df_demo["Upper"] - df_demo["Estimate"],
            arrayminus=df_demo["Estimate"] - df_demo["Lower"],
        ),
        marker=dict(color="#3b82f6"),
        orientation="h",
    ))

    fig.update_layout(
        title=f"{selected_construct_demo} Support by {demo_type}",
        xaxis_title="Support %",
        yaxis_title=demo_type,
        paper_bgcolor="#0f1117",
        plot_bgcolor="#1a1d29",
        font={"color": "#e8e8ed", "family": "DM Sans"},
        height=400,
    )

    st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # Subgroup comparison table
    st.markdown("**Detailed Subgroup Estimates**")
    df_display = df_demo.copy()
    df_display["Estimate"] = df_display["Estimate"].apply(lambda x: f"{x:.1f}%")
    df_display["95% CI"] = df_display.apply(
        lambda row: f"{row['Lower']:.1f}% — {row['Upper']:.1f}%",
        axis=1
    )
    df_display = df_display[["Group", "Estimate", "95% CI"]]
    st.dataframe(df_display, use_container_width=True, hide_index=True)

# ─────────────────────────────────────────
# TAB 3: TREND ANALYSIS
# ─────────────────────────────────────────
with tab3:
    st.markdown("### Trend Analysis — Support Over Time")

    col1, col2 = st.columns([1, 3])
    with col1:
        selected_construct_trend = st.selectbox("Construct:", CONSTRUCTS, key="construct_trend")
        selected_state_trend = st.selectbox("State:", STATES, key="state_trend")

    # Generate synthetic trend data
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun"]
    trend_data = []

    for idx, month in enumerate(months):
        np.random.seed((hash(selected_state_trend) + hash(selected_construct_trend) + idx) % 2**32)
        base = np.random.uniform(50, 70)
        trend = base + idx * np.random.uniform(-1, 2)
        trend_data.append({
            "Month": month,
            "Estimate": trend,
            "Lower": max(30, trend - np.random.uniform(4, 8)),
            "Upper": min(95, trend + np.random.uniform(4, 8)),
        })

    df_trend = pd.DataFrame(trend_data)

    fig = go.Figure()

    # Add CI band
    fig.add_trace(go.Scatter(
        x=df_trend["Month"],
        y=df_trend["Upper"],
        fill=None,
        mode="lines",
        line_color="rgba(0,0,0,0)",
        showlegend=False,
    ))

    fig.add_trace(go.Scatter(
        x=df_trend["Month"],
        y=df_trend["Lower"],
        fill="tonexty",
        mode="lines",
        line_color="rgba(0,0,0,0)",
        fillcolor="rgba(34, 197, 94, 0.2)",
        name="95% Confidence Interval",
    ))

    # Add point estimate line
    fig.add_trace(go.Scatter(
        x=df_trend["Month"],
        y=df_trend["Estimate"],
        mode="lines+markers",
        name="Point Estimate",
        line=dict(color="#22c55e", width=3),
        marker=dict(size=8),
    ))

    fig.update_layout(
        title=f"Trend: {selected_construct_trend} in {selected_state_trend}",
        xaxis_title="Month",
        yaxis_title="Support %",
        paper_bgcolor="#0f1117",
        plot_bgcolor="#1a1d29",
        font={"color": "#e8e8ed", "family": "DM Sans"},
        hovermode="x unified",
        height=400,
    )

    st.plotly_chart(fig, use_container_width=True)

    # Trend interpretation
    start_est = df_trend.iloc[0]["Estimate"]
    end_est = df_trend.iloc[-1]["Estimate"]
    change = end_est - start_est

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"**Starting Estimate (Jan):** {start_est:.1f}%")
    with col2:
        direction = "↑ increasing" if change > 0 else "↓ decreasing" if change < 0 else "→ stable"
        st.markdown(f"**Trend:** {direction} ({abs(change):.1f}pp)")

# ─────────────────────────────────────────
# TAB 4: STATE RANKINGS
# ─────────────────────────────────────────
with tab4:
    st.markdown("### State Rankings")

    selected_construct_rank = st.selectbox("Construct:", CONSTRUCTS, key="construct_rank")

    # Generate rankings
    rank_data = []
    for state in STATES:
        est = get_mrp_estimate(state, selected_construct_rank)
        rank_data.append({
            "State": state,
            "Estimate": est["point"],
            "CI Lower": est["ci_lower"],
            "CI Upper": est["ci_upper"],
        })

    df_rank = pd.DataFrame(rank_data).sort_values("Estimate", ascending=False)
    df_rank["Rank"] = range(1, len(df_rank) + 1)

    # Display as styled table
    st.markdown(f"**{selected_construct_rank} Support Rankings**")

    for idx, row in df_rank.iterrows():
        col1, col2, col3 = st.columns([0.5, 1, 2])

        with col1:
            st.markdown(f"### {int(row['Rank'])}")

        with col2:
            st.markdown(f"**{row['State']}**")
            st.caption(f"{row['Estimate']:.1f}%")

        with col3:
            pct_filled = (row['Estimate'] - 30) / (85 - 30)
            st.progress(pct_filled, text=f"{row['CI Lower']:.1f}% – {row['CI Upper']:.1f}%")

    st.divider()

    # Ranking heatmap across all constructs
    st.markdown("**Rankings Heatmap — All Constructs**")

    heatmap_data = []
    for state in STATES:
        for construct in CONSTRUCTS:
            est = get_mrp_estimate(state, construct)
            heatmap_data.append({
                "State": state,
                "Construct": construct,
                "Estimate": est["point"],
            })

    df_heatmap = pd.DataFrame(heatmap_data).pivot(index="Construct", columns="State", values="Estimate")

    fig = px.imshow(
        df_heatmap,
        color_continuous_scale="RdYlGn",
        title="State Support Heatmap",
        labels={"color": "Support %"},
        zmin=40,
        zmax=80,
    )
    fig.update_layout(
        paper_bgcolor="#0f1117",
        font={"color": "#e8e8ed", "family": "DM Sans"},
        height=600,
    )
    st.plotly_chart(fig, use_container_width=True)

# ─────────────────────────────────────────
# TAB 5: MAP EXPLORER
# ─────────────────────────────────────────
with tab5:
    st.markdown("### Geographic Distribution Explorer")

    selected_construct_map = st.selectbox("Construct:", CONSTRUCTS, key="construct_map")

    st.info("""
    📍 **Choropleth Map Coming Soon**

    This visualization will show state-level reform support estimates on a U.S. map,
    color-coded by support percentage. Hover to see point estimates and confidence intervals.

    **In the meantime:** Use the **State Rankings** tab to compare state-level support,
    or the **State Estimates** tab to drill into specific states.
    """)

    # Generate preview data
    map_data = []
    for state in STATES:
        est = get_mrp_estimate(state, selected_construct_map)
        map_data.append({
            "State": state,
            "Estimate": est["point"],
        })

    df_map = pd.DataFrame(map_data).sort_values("Estimate", ascending=False)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Highest Support**")
        for idx, row in df_map.head(3).iterrows():
            st.metric(row["State"], f"{row['Estimate']:.1f}%")

    with col2:
        st.markdown("**Lowest Support**")
        for idx, row in df_map.tail(3).iterrows():
            st.metric(row["State"], f"{row['Estimate']:.1f}%")
