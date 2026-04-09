"""
Media Portal Page — Campaign builder, active campaigns, spend tracker
"""

import streamlit as st
from pathlib import Path
import sys
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta

# Auth gate
sys.path.insert(0, str(Path(__file__).parent.parent))
from auth import require_auth

st.set_page_config(
    page_title="Media Portal — SLA Portal",
    page_icon="📢",
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
    .campaign-card {
        background: #1a1d29;
        border: 1px solid #2a2d3a;
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
    }
    .status-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
    }
    .status-active {
        background: rgba(34, 197, 94, 0.1);
        color: #22c55e;
        border: 1px solid rgba(34, 197, 94, 0.3);
    }
    .status-paused {
        background: rgba(245, 158, 11, 0.1);
        color: #f59e0b;
        border: 1px solid rgba(245, 158, 11, 0.3);
    }
    .status-completed {
        background: rgba(107, 114, 128, 0.1);
        color: #8b8fa3;
        border: 1px solid rgba(107, 114, 128, 0.3);
    }
    .kpi-stat {
        background: #1a1d29;
        border: 1px solid #2a2d3a;
        border-radius: 12px;
        padding: 1rem;
        text-align: center;
    }
    .kpi-label {
        color: #8b8fa3;
        font-size: 0.85rem;
        font-weight: 500;
    }
    .kpi-value {
        color: #22c55e;
        font-size: 1.8rem;
        font-weight: 700;
        margin-top: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

username = require_auth("Second Look Alliance", accent_color="#22c55e")

st.title("📢 Media Portal")

st.markdown("""
Campaign builder and media placement tracker for survey fielding and paid advertising on Meta, X, and other channels.
**Note:** This is an MVP interface. Actual integrations with StackAdapt, Meta, and X coming in Phase 2.
""")

# Demo campaign data
DEMO_CAMPAIGNS = [
    {
        "id": "CAMP-001",
        "name": "OK Sentencing Reform Awareness",
        "objective": "Awareness",
        "state": "Oklahoma",
        "channels": ["Meta", "X"],
        "status": "Active",
        "budget": 15000,
        "spent": 8420,
        "impressions": 245000,
        "clicks": 3200,
        "start_date": "2026-03-15",
        "end_date": "2026-04-30",
    },
    {
        "id": "CAMP-002",
        "name": "LA Rehabilitation Support Survey",
        "objective": "Survey Fielding",
        "state": "Louisiana",
        "channels": ["Meta", "X", "Display"],
        "status": "Active",
        "budget": 25000,
        "spent": 12350,
        "impressions": 520000,
        "clicks": 8750,
        "start_date": "2026-03-01",
        "end_date": "2026-05-15",
    },
    {
        "id": "CAMP-003",
        "name": "NC Proportionality Persuasion",
        "objective": "Persuasion",
        "state": "North Carolina",
        "channels": ["Meta"],
        "status": "Active",
        "budget": 10000,
        "spent": 6200,
        "impressions": 180000,
        "clicks": 2800,
        "start_date": "2026-03-20",
        "end_date": "2026-04-20",
    },
    {
        "id": "CAMP-004",
        "name": "VA Youth Justice Initiative",
        "objective": "Awareness",
        "state": "Virginia",
        "channels": ["X", "Display"],
        "status": "Paused",
        "budget": 12000,
        "spent": 8100,
        "impressions": 150000,
        "clicks": 1500,
        "start_date": "2026-02-15",
        "end_date": "2026-04-15",
    },
    {
        "id": "CAMP-005",
        "name": "MA Constitutional Rights",
        "objective": "Survey Fielding",
        "state": "Massachusetts",
        "channels": ["Meta", "X"],
        "status": "Completed",
        "budget": 20000,
        "spent": 20000,
        "impressions": 620000,
        "clicks": 12340,
        "start_date": "2026-01-15",
        "end_date": "2026-03-15",
    },
]

# Tabs
tab1, tab2, tab3 = st.tabs(["Campaign Builder", "Active Campaigns", "Spend Tracker"])

# ─────────────────────────────────────────
# TAB 1: CAMPAIGN BUILDER
# ─────────────────────────────────────────
with tab1:
    st.markdown("### Create New Campaign")

    with st.form("campaign_form"):
        col1, col2 = st.columns(2)

        with col1:
            campaign_name = st.text_input(
                "Campaign Name",
                placeholder="e.g., OK Sentencing Reform Awareness",
                help="A descriptive name for this campaign"
            )

            objective = st.selectbox(
                "Campaign Objective",
                ["Survey Fielding", "Awareness", "Persuasion"],
                help="What is the primary goal of this campaign?"
            )

            state = st.selectbox(
                "Target State",
                ["Oklahoma", "Louisiana", "North Carolina", "Virginia", "Massachusetts", "New Jersey"],
                help="Which state will this campaign focus on?"
            )

        with col2:
            channels = st.multiselect(
                "Ad Channels",
                ["Meta (Facebook/Instagram)", "X (Twitter)", "Display Network", "OTT/Streaming"],
                default=["Meta"],
                help="Which platforms should we use?"
            )

            daily_budget = st.number_input(
                "Daily Budget ($)",
                min_value=100,
                max_value=10000,
                value=1000,
                step=100,
                help="How much to spend per day?"
            )

            campaign_duration = st.selectbox(
                "Duration",
                ["1 week", "2 weeks", "3 weeks", "4 weeks", "6 weeks", "8 weeks"],
                help="How long should this campaign run?"
            )

        st.divider()

        st.markdown("### Audience Targeting")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**Demographic Filters**")

            target_party = st.multiselect(
                "Party Affiliation",
                ["Republican", "Democrat", "Independent"],
                default=["Democrat", "Independent"],
                help="Which voter segments to target?"
            )

            target_age = st.multiselect(
                "Age Range",
                ["18-34", "35-49", "50-64", "65+"],
                default=["35-49", "50-64"],
                help="Which age groups?"
            )

            target_education = st.multiselect(
                "Education Level",
                ["High School or Less", "Some College", "Bachelor", "Graduate"],
                default=["Some College", "Bachelor", "Graduate"],
                help="Education levels to include"
            )

        with col2:
            st.markdown("**Attitudinal Filters (VIP Archetypes)**")

            include_archetypes = st.multiselect(
                "Voter Archetypes",
                [
                    "System Defenders",
                    "Cautious Reformers",
                    "Compassionate Pragmatists",
                    "Justice Skeptics",
                    "Rehabilitation Champions",
                    "Abolition-Leaning",
                ],
                default=["Cautious Reformers", "Compassionate Pragmatists", "Justice Skeptics"],
                help="Which archetypes to prioritize?"
            )

            target_constructs = st.multiselect(
                "Message Constructs",
                [
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
                ],
                default=["Rehabilitation", "Proportionality"],
                help="Which constructs to emphasize?"
            )

        st.divider()

        st.markdown("### Creative & Message")

        col1, col2 = st.columns(2)

        with col1:
            creative_copy = st.text_area(
                "Ad Copy / Message",
                placeholder="Enter the main message for this campaign...",
                height=100,
                help="The core messaging for your ads"
            )

        with col2:
            st.markdown("**Creative Upload** (Placeholder)")
            st.info("📸 Upload images, videos, or other creative assets here in the production system")

        st.divider()

        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown(f"**Total Budget:** ${daily_budget * 7 * 4:,.0f}")
            st.caption("(estimated for 4 weeks)")

        with col2:
            pass

        with col3:
            submitted = st.form_submit_button("Create Campaign", type="primary", use_container_width=True)

    if submitted:
        if not campaign_name:
            st.error("Please enter a campaign name")
        else:
            st.success(f"""
            ✅ Campaign **{campaign_name}** would be created with:
            - Objective: {objective}
            - State: {state}
            - Channels: {', '.join(channels)}
            - Daily Budget: ${daily_budget}
            - Duration: {campaign_duration}

            **Note:** In production, this would integrate with StackAdapt, Meta, and X APIs.
            """)

# ─────────────────────────────────────────
# TAB 2: ACTIVE CAMPAIGNS
# ─────────────────────────────────────────
with tab2:
    st.markdown("### Active Campaigns")

    col1, col2, col3 = st.columns(3)

    with col1:
        total_budget = sum(c["budget"] for c in DEMO_CAMPAIGNS if c["status"] in ["Active", "Paused"])
        st.markdown(f"""
        <div class="kpi-stat">
            <div class="kpi-label">Total Budget</div>
            <div class="kpi-value">${total_budget / 1000:.0f}K</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        total_spent = sum(c["spent"] for c in DEMO_CAMPAIGNS if c["status"] in ["Active", "Paused"])
        pct_spent = (total_spent / total_budget * 100) if total_budget > 0 else 0
        st.markdown(f"""
        <div class="kpi-stat">
            <div class="kpi-label">Amount Spent</div>
            <div class="kpi-value">${total_spent / 1000:.0f}K</div>
            <div style="color: #8b8fa3; font-size: 0.85rem; margin-top: 0.5rem;">{pct_spent:.1f}% of budget</div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        total_impressions = sum(c["impressions"] for c in DEMO_CAMPAIGNS if c["status"] in ["Active", "Paused"])
        st.markdown(f"""
        <div class="kpi-stat">
            <div class="kpi-label">Impressions</div>
            <div class="kpi-value">{total_impressions / 1000:.0f}K</div>
        </div>
        """, unsafe_allow_html=True)

    st.divider()

    # Filter campaigns
    col1, col2, col3 = st.columns([1, 1, 2])

    with col1:
        status_filter = st.multiselect(
            "Filter by Status:",
            ["Active", "Paused", "Completed"],
            default=["Active"],
            key="status_filter"
        )

    with col2:
        state_filter = st.multiselect(
            "Filter by State:",
            ["Oklahoma", "Louisiana", "North Carolina", "Virginia", "Massachusetts", "New Jersey"],
            default=None,
            key="state_filter"
        )

    # Apply filters
    filtered_campaigns = DEMO_CAMPAIGNS
    if status_filter:
        filtered_campaigns = [c for c in filtered_campaigns if c["status"] in status_filter]
    if state_filter:
        filtered_campaigns = [c for c in filtered_campaigns if c["state"] in state_filter]

    # Display campaign cards
    for campaign in filtered_campaigns:
        col1, col2 = st.columns([2, 3])

        with col1:
            st.markdown(f"""
            <div class="campaign-card">
                <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 1rem;">
                    <div>
                        <div style="font-size: 1.1rem; font-weight: 600; color: #e8e8ed;">{campaign['name']}</div>
                        <div style="color: #8b8fa3; font-size: 0.85rem; margin-top: 0.25rem;">{campaign['state']} • {campaign['objective']}</div>
                    </div>
                    <span class="status-badge status-{campaign['status'].lower()}">{campaign['status']}</span>
                </div>

                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin-bottom: 1rem;">
                    <div>
                        <div style="color: #8b8fa3; font-size: 0.85rem;">Impressions</div>
                        <div style="color: #22c55e; font-size: 1.2rem; font-weight: 600;">{campaign['impressions']:,}</div>
                    </div>
                    <div>
                        <div style="color: #8b8fa3; font-size: 0.85rem;">Clicks</div>
                        <div style="color: #3b82f6; font-size: 1.2rem; font-weight: 600;">{campaign['clicks']:,}</div>
                    </div>
                </div>

                <div style="color: #8b8fa3; font-size: 0.8rem;">
                    {campaign['start_date']} → {campaign['end_date']}
                </div>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            progress = campaign["spent"] / campaign["budget"]
            st.markdown(f"""
            <div class="campaign-card">
                <div style="color: #8b8fa3; font-size: 0.85rem; margin-bottom: 0.5rem;">Budget Utilization</div>
                <div style="color: #e8e8ed; font-size: 1.3rem; font-weight: 600; margin-bottom: 0.5rem;">
                    ${campaign['spent']:,} / ${campaign['budget']:,}
                </div>
            </div>
            """, unsafe_allow_html=True)
            st.progress(progress, text=f"{progress*100:.0f}%")

            ctr = (campaign["clicks"] / campaign["impressions"] * 100) if campaign["impressions"] > 0 else 0
            st.markdown(f"""
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin-top: 1rem;">
                <div>
                    <div style="color: #8b8fa3; font-size: 0.85rem;">CPM</div>
                    <div style="color: #f59e0b; font-weight: 600;">${campaign['spent'] / (campaign['impressions'] / 1000):.2f}</div>
                </div>
                <div>
                    <div style="color: #8b8fa3; font-size: 0.85rem;">CTR</div>
                    <div style="color: #3b82f6; font-weight: 600;">{ctr:.2f}%</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

# ─────────────────────────────────────────
# TAB 3: SPEND TRACKER
# ─────────────────────────────────────────
with tab3:
    st.markdown("### Budget & Spend Overview")

    col1, col2, col3, col4 = st.columns(4)

    total_budget = sum(c["budget"] for c in DEMO_CAMPAIGNS)
    total_spent = sum(c["spent"] for c in DEMO_CAMPAIGNS)
    remaining_budget = total_budget - total_spent

    with col1:
        st.metric("Total Budget", f"${total_budget / 1000:.0f}K")

    with col2:
        st.metric("Spent to Date", f"${total_spent / 1000:.0f}K")

    with col3:
        st.metric("Remaining", f"${remaining_budget / 1000:.0f}K")

    with col4:
        st.metric("Utilization", f"{total_spent / total_budget * 100:.1f}%")

    st.divider()

    # Spend over time
    st.markdown("**Spend Over Time**")

    # Generate daily spend data
    days = pd.date_range(start="2026-01-15", end="2026-04-09", freq="D")
    spend_data = []

    for day in days:
        daily = 0
        for campaign in DEMO_CAMPAIGNS:
            start = pd.to_datetime(campaign["start_date"])
            end = pd.to_datetime(campaign["end_date"])
            if start <= day <= end:
                daily_budget = campaign["budget"] / 28  # Assume 4-week campaigns
                daily += daily_budget
        spend_data.append({"Date": day, "Daily Spend": daily})

    df_spend = pd.DataFrame(spend_data)

    fig = px.area(
        df_spend,
        x="Date",
        y="Daily Spend",
        title="Daily Spend Trend",
    )
    fig.update_layout(
        paper_bgcolor="#0f1117",
        plot_bgcolor="#1a1d29",
        font={"color": "#e8e8ed", "family": "DM Sans"},
        height=400,
        hovermode="x unified",
    )
    st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # Spend by channel
    st.markdown("**Spend Breakdown by Channel**")

    channel_spend = {}
    for campaign in DEMO_CAMPAIGNS:
        for channel in campaign["channels"]:
            channel_clean = channel.split("(")[0].strip()
            if channel_clean not in channel_spend:
                channel_spend[channel_clean] = 0
            channel_spend[channel_clean] += campaign["spent"] * (1 / len(campaign["channels"]))

    channel_data = pd.DataFrame([
        {"Channel": k, "Spend": v} for k, v in channel_spend.items()
    ])

    col1, col2 = st.columns([1, 2])

    with col1:
        fig = px.pie(
            channel_data,
            values="Spend",
            names="Channel",
            title="Spend by Channel",
            color_discrete_sequence=["#22c55e", "#3b82f6", "#f59e0b", "#818cf8"],
        )
        fig.update_layout(
            paper_bgcolor="#0f1117",
            font={"color": "#e8e8ed", "family": "DM Sans"},
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("**Detailed Breakdown**")
        for _, row in channel_data.iterrows():
            pct = row["Spend"] / channel_data["Spend"].sum() * 100
            st.write(f"**{row['Channel']}**: ${row['Spend']:,.0f} ({pct:.1f}%)")

    st.divider()

    # Commission breakdown
    st.markdown("**Commission & Platform Fees**")

    commission_data = {
        "Meta": total_spent * 0.05,
        "X": total_spent * 0.07,
        "Display": total_spent * 0.08,
        "Agency Fee": total_spent * 0.10,
    }

    for platform, commission in commission_data.items():
        col1, col2 = st.columns([2, 1])
        with col1:
            st.write(f"**{platform}**")
        with col2:
            st.write(f"${commission:,.0f}")
