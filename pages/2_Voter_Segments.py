"""
Coalition Heatmap™ — SLA Portal
Shows support rates for reform topics broken down by actual demographic subgroups:
party, ideology, race/ethnicity, age, gender.
"""

import streamlit as st
from pathlib import Path
import sys
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import requests
from collections import defaultdict
import re

# Auth gate
sys.path.insert(0, str(Path(__file__).parent.parent))
from auth import require_auth
from chat_widget import render_chat

# Theme
from theme import (
    apply_theme, portal_footer, get_supabase_config, get_supabase_headers,
    CJ_SURVEYS, SURVEY_STATE, TIER_MAP,
    NAVY, NAVY2, GOLD, GOLD_MID, TEXT1, TEXT2, TEXT3, BORDER2, BG, CARD_BG,
)

# Scoring engine
sys.path.insert(0, str(Path(__file__).parent.parent))
try:
    from content_scoring import SKIPPED_QIDS, get_construct, score_content
    SCORING_AVAILABLE = True
except ImportError:
    SCORING_AVAILABLE = False

st.set_page_config(page_title="Voter Segments — SLA Portal", page_icon="🎯", layout="wide")

apply_theme()
username = require_auth("Second Look Alliance", accent_color=GOLD)

SUPABASE_URL, SUPABASE_KEY = get_supabase_config()
HEADERS = get_supabase_headers()

# Human-readable construct names
CONSTRUCT_LABELS = {
    "PD_FUNDING": "Public Defender Funding", "INVEST": "Community Investment",
    "LIT": "Literacy Programs", "COUNSEL_ACCESS": "Right to Counsel",
    "DV": "Domestic Violence", "CAND-DV": "Candidates on DV",
    "PROP": "Property Crime Reform", "REDEMPTION": "Redemption / Second Chances",
    "EXPUNGE": "Record Expungement", "SENTREVIEW": "Sentence Review",
    "JUDICIAL": "Judicial Discretion", "RETRO": "Retroactive Relief",
    "FINES": "Fines & Fees", "MAND": "Mandatory Minimums",
    "BAIL": "Bail Reform", "REENTRY": "Reentry Programs",
    "RECORD": "Criminal Record Reform", "JUV": "Juvenile Justice",
    "FAMILY": "Family Reunification", "ELDERLY": "Compassionate Release",
    "COURT": "Court Reform", "COURTREVIEW": "Court Review Process",
    "TRUST": "System Trust", "PLEA": "Plea Bargaining Reform",
    "PROS": "Prosecutor Accountability", "CAND": "Candidate Favorability",
    "TOUGHCRIME": "Tough on Crime Attitudes", "ISSUE_SALIENCE": "Issue Importance",
    "IMPACT": "Personal Impact", "DETER": "Deterrence Beliefs",
    "FISCAL": "Fiscal Responsibility", "DP_ABOLITION": "Death Penalty Abolition",
    "DP_RELIABILITY": "Death Penalty Reliability", "LWOP": "Life Without Parole",
    "COMPASSION": "Compassionate Release",
}

# Gauge constructs — excluded from heat map (not reform topics)
GAUGE_CONSTRUCTS = {"CAND", "TOUGHCRIME", "ISSUE_SALIENCE", "IMPACT"}

# Demographic subgroups displayed in heatmap
DEMOGRAPHIC_SUBGROUPS = [
    "Overall",
    "Republicans", "Democrats", "Independents",
    "Conservatives", "Moderates", "Liberals",
    "White", "Black", "Hispanic",
    "Age 18-34", "Age 35-54", "Age 55+",
    "Male", "Female",
]


# ══════════════════════════════════════════════════════════════════
# DATA LOADING
# ══════════════════════════════════════════════════════════════════

def _paginate(url_base, headers, limit=1000, max_rows=200000):
    """Paginate Supabase responses."""
    all_rows = []
    offset = 0
    while offset < max_rows:
        sep = "&" if "?" in url_base else "?"
        url = f"{url_base}{sep}offset={offset}&limit={limit}"
        resp = requests.get(url, headers=headers, timeout=120)
        resp.raise_for_status()
        rows = resp.json()
        all_rows.extend(rows)
        if len(rows) < limit:
            break
        offset += limit
    return all_rows


def _map_party(party_id):
    """Map party_id to party subgroup."""
    if not party_id:
        return None
    party_lower = str(party_id).lower()
    if "republican" in party_lower:
        return "Republicans"
    elif "democrat" in party_lower:
        return "Democrats"
    elif any(x in party_lower for x in ["independent", "unaffiliated", "no party"]):
        return "Independents"
    return None


def _map_ideology(ideology):
    """Map ideology field to ideology subgroup."""
    if not ideology:
        return None
    ideology_lower = str(ideology).lower()
    if "conservative" in ideology_lower:
        return "Conservatives"
    elif any(x in ideology_lower for x in ["moderate", "middle"]):
        return "Moderates"
    elif any(x in ideology_lower for x in ["liberal", "progressive"]):
        return "Liberals"
    return None


def _map_race_ethnicity(race_ethnicity):
    """Map race_ethnicity field to race subgroup."""
    if not race_ethnicity:
        return None
    race_lower = str(race_ethnicity).lower()
    if any(x in race_lower for x in ["white", "caucasian"]):
        return "White"
    elif any(x in race_lower for x in ["black", "african"]):
        return "Black"
    elif any(x in race_lower for x in ["hispanic", "latino", "latina"]):
        return "Hispanic"
    return None


def _map_age(age_bracket):
    """Map age_bracket field to age subgroup."""
    if not age_bracket:
        return None
    age_str = str(age_bracket).lower()
    # Try to extract numeric range
    numbers = re.findall(r'\d+', age_str)
    if numbers:
        min_age = int(numbers[0])
        if min_age < 35:
            return "Age 18-34"
        elif min_age < 55:
            return "Age 35-54"
        else:
            return "Age 55+"
    return None


def _map_gender(gender):
    """Map gender field to gender subgroup."""
    if not gender:
        return None
    gender_lower = str(gender).lower()
    if "female" in gender_lower or "woman" in gender_lower:
        return "Female"
    elif "male" in gender_lower and "female" not in gender_lower:
        return "Male"
    return None


@st.cache_data(ttl=3600, show_spinner="Loading Coalition Heatmap™ data...")
def load_segment_data():
    """
    Pull L2 responses and L1 demographics, score each response,
    compute support rates by construct and demographic subgroup.

    Returns:
        dict: {construct: {subgroup: support_pct, count: n_responses}}
    """
    # Pull L2 responses
    all_l2 = []
    for sid in CJ_SURVEYS:
        rows = _paginate(
            f"{SUPABASE_URL}/rest/v1/l2_responses"
            f"?select=respondent_id,survey_id,question_id,question_text,response"
            f"&survey_id=eq.{sid}",
            HEADERS,
        )
        all_l2.extend(rows)

    # Pull L1 demographics
    all_l1 = []
    for sid in CJ_SURVEYS:
        rows = _paginate(
            f"{SUPABASE_URL}/rest/v1/l1_respondents"
            f"?select=respondent_id,survey_id,party_id,ideology,race_ethnicity,age_bracket,gender,education"
            f"&survey_id=eq.{sid}",
            HEADERS,
        )
        all_l1.extend(rows)

    demo_lookup = {d["respondent_id"]: d for d in all_l1}

    # Score all responses
    scored = []
    for r in all_l2:
        qid = r.get("question_id")
        if not qid or qid in SKIPPED_QIDS:
            continue
        construct = get_construct(qid)
        if not construct:
            continue
        fav, intensity, has_int = score_content(qid, r["response"], r.get("survey_id"))
        if fav is None:
            continue
        scored.append({
            "rid": r["respondent_id"],
            "sid": r["survey_id"],
            "qid": qid,
            "construct": construct,
            "fav": 1 if fav == 1 else 0,
        })

    # Build demographic subgroup assignments per respondent
    respondent_subgroups = defaultdict(list)
    for rid, demo in demo_lookup.items():
        # Overall
        respondent_subgroups[rid].append("Overall")

        # Party
        party = _map_party(demo.get("party_id"))
        if party:
            respondent_subgroups[rid].append(party)

        # Ideology
        ideology = _map_ideology(demo.get("ideology"))
        if ideology:
            respondent_subgroups[rid].append(ideology)

        # Race/Ethnicity
        race = _map_race_ethnicity(demo.get("race_ethnicity"))
        if race:
            respondent_subgroups[rid].append(race)

        # Age
        age = _map_age(demo.get("age_bracket"))
        if age:
            respondent_subgroups[rid].append(age)

        # Gender
        gender = _map_gender(demo.get("gender"))
        if gender:
            respondent_subgroups[rid].append(gender)

    # Compute per-construct per-subgroup support rates
    construct_subgroup_stats = defaultdict(lambda: defaultdict(lambda: {"fav": 0, "n": 0}))
    for s in scored:
        rid = s["rid"]
        construct = s["construct"]

        # Add to Overall
        construct_subgroup_stats[construct]["Overall"]["fav"] += s["fav"]
        construct_subgroup_stats[construct]["Overall"]["n"] += 1

        # Add to each demographic subgroup this respondent belongs to
        for subgroup in respondent_subgroups.get(rid, []):
            if subgroup != "Overall":
                construct_subgroup_stats[construct][subgroup]["fav"] += s["fav"]
                construct_subgroup_stats[construct][subgroup]["n"] += 1

    # Build heatmap data: exclude GAUGE_CONSTRUCTS
    heatmap_data = {}
    for construct, subgroup_stats in construct_subgroup_stats.items():
        if construct in GAUGE_CONSTRUCTS:
            continue

        row = {}
        for subgroup in DEMOGRAPHIC_SUBGROUPS:
            stats = subgroup_stats.get(subgroup, {"fav": 0, "n": 0})
            n = stats["n"]
            # Require at least 30 responses
            if n >= 30:
                support_pct = stats["fav"] / n * 100
                row[subgroup] = {
                    "pct": support_pct,
                    "n": n,
                }
            else:
                row[subgroup] = {
                    "pct": None,
                    "n": n,
                }

        # Only include construct if Overall has enough data
        if row.get("Overall", {}).get("pct") is not None:
            heatmap_data[construct] = row

    return heatmap_data


# ══════════════════════════════════════════════════════════════════
# COLOR FUNCTIONS
# ══════════════════════════════════════════════════════════════════

def get_cell_color(support_pct):
    """Return (bg_color, text_color) tuple based on support percentage."""
    if support_pct is None:
        return ("#F5F5F5", TEXT3)  # Light gray for no data

    if support_pct >= 75:
        # Green for 75%+
        return ("#E8F5E9", "#1B6B3A")
    elif support_pct >= 60:
        # Gold for 60-74%
        return ("#FEF3E0", "#B8870A")
    elif support_pct < 50:
        # Red for below 50%
        return ("#FFEBEE", "#8B1A1A")
    else:
        # Neutral for 50-59%
        return ("#F9F9F9", TEXT2)


# ══════════════════════════════════════════════════════════════════
# MAIN PAGE
# ══════════════════════════════════════════════════════════════════

st.title("🎯 Voter Segments")
st.markdown(
    "Support rates for criminal justice reform topics broken down by demographic subgroups. "
    "Green indicates strong support (75%+), gold moderate support (60-74%), and red opposition (below 50%). "
    "Cells with fewer than 30 responses are not shown."
)

if not SCORING_AVAILABLE:
    st.error("content_scoring.py not found. Cannot compute support rates.")
    st.stop()

heatmap_data = load_segment_data()

if not heatmap_data:
    st.warning("No Coalition Heatmap data available.")
    st.stop()

# ── Sidebar: view selector ──
with st.sidebar:
    st.markdown("### Views")
    view_mode = st.radio(
        "Select view:",
        ["Coalition Heatmap", "Topic Deep Dive", "Demographic Profile"],
        key="seg_view",
    )

    st.divider()
    st.metric("Topics Analyzed", len(heatmap_data))
    st.metric("Demographic Groups", len(DEMOGRAPHIC_SUBGROUPS))


# ══════════════════════════════════════════════════════════════════
# VIEW 1: COALITION HEATMAP (default)
# ══════════════════════════════════════════════════════════════════

if view_mode == "Coalition Heatmap":
    st.subheader("Support by Topic and Demographic")
    st.caption(
        "Each row is a reform topic, sorted by persuasion tier. "
        "Each column is a demographic subgroup. "
        "Hover for exact percentages and sample sizes."
    )

    # Sort constructs by tier, then by label
    constructs_sorted = sorted(
        heatmap_data.keys(),
        key=lambda c: (TIER_MAP.get(c, "ZZZ"), CONSTRUCT_LABELS.get(c, c))
    )

    # Build matrix
    z_values = []
    hover_texts = []
    topic_labels = []

    for construct in constructs_sorted:
        row_z = []
        row_hover = []
        topic_labels.append(CONSTRUCT_LABELS.get(construct, construct))

        for subgroup in DEMOGRAPHIC_SUBGROUPS:
            cell_data = heatmap_data[construct].get(subgroup, {})
            pct = cell_data.get("pct")
            n = cell_data.get("n", 0)

            if pct is not None:
                row_z.append(pct)
                row_hover.append(f"{CONSTRUCT_LABELS.get(construct, construct)}<br>{subgroup}<br>{pct:.1f}% (n={n})")
            else:
                row_z.append(None)
                row_hover.append(f"{CONSTRUCT_LABELS.get(construct, construct)}<br>{subgroup}<br>Insufficient data (n={n})")

        z_values.append(row_z)
        hover_texts.append(row_hover)

    # Create Plotly heatmap
    fig = go.Figure(data=go.Heatmap(
        z=z_values,
        x=DEMOGRAPHIC_SUBGROUPS,
        y=[f"{label}  •  {TIER_MAP.get(c, '')}" for label, c in zip(topic_labels, constructs_sorted)],
        hovertext=hover_texts,
        hoverinfo="text",
        colorscale=[
            [0.0, "#8B1A1A"],     # red for low support
            [0.4, "#F5E6CC"],     # neutral cream
            [0.6, "#C5E1A5"],     # light green
            [1.0, "#1B6B3A"],     # dark green for high support
        ],
        zmin=20,
        zmax=95,
        text=[[f"{v:.0f}%" if v is not None else "—" for v in row] for row in z_values],
        texttemplate="%{text}",
        textfont=dict(size=10, color=NAVY),
        colorbar=dict(title="Support %", thickness=15, len=0.7),
    ))

    fig.update_layout(
        template="plotly_white",
        paper_bgcolor=BG,
        plot_bgcolor=CARD_BG,
        height=max(600, len(constructs_sorted) * 25 + 150),
        margin=dict(l=320, r=100, t=40, b=120),
        xaxis=dict(
            side="bottom",
            tickfont=dict(size=11, color=NAVY),
            tickangle=45,
        ),
        yaxis=dict(autorange="reversed", tickfont=dict(size=10, color=NAVY)),
        font=dict(family="DM Sans", color=NAVY),
    )

    st.plotly_chart(fig, use_container_width=True, key="coalition_heatmap")

    # ── Summary statistics ──
    st.markdown("#### Strongest Support")
    st.caption("Topics with the highest average support across all demographic groups.")

    avg_support = {}
    for construct in constructs_sorted:
        pcts = [
            heatmap_data[construct][subgroup].get("pct")
            for subgroup in DEMOGRAPHIC_SUBGROUPS
        ]
        pcts_valid = [p for p in pcts if p is not None]
        if pcts_valid:
            avg_support[construct] = np.mean(pcts_valid)

    top_topics = sorted(avg_support.items(), key=lambda x: x[1], reverse=True)[:5]

    summary_cols = st.columns(len(top_topics))
    for col, (construct, avg_pct) in zip(summary_cols, top_topics):
        with col:
            tier = TIER_MAP.get(construct, "—")
            st.markdown(f"""
            <div style="background:{CARD_BG};border:1px solid {BORDER2};border-top:3px solid {GOLD};
                border-radius:8px;padding:0.75rem;text-align:center;">
                <div style="font-weight:700;color:{NAVY};font-size:0.85rem;">{CONSTRUCT_LABELS.get(construct, construct)}</div>
                <div style="font-size:1.8rem;font-weight:800;color:{GOLD};">{avg_pct:.0f}%</div>
                <div style="font-size:0.65rem;color:{TEXT3};">avg support • {tier}</div>
            </div>
            """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════
# VIEW 2: TOPIC DEEP DIVE
# ══════════════════════════════════════════════════════════════════

elif view_mode == "Topic Deep Dive":
    st.subheader("Select a Topic to See Demographic Breakdown")
    st.caption("Horizontal bar chart showing support rate for one topic across all demographic subgroups.")

    constructs_sorted = sorted(
        heatmap_data.keys(),
        key=lambda c: (TIER_MAP.get(c, "ZZZ"), CONSTRUCT_LABELS.get(c, c))
    )
    topic_labels_list = [CONSTRUCT_LABELS.get(c, c) for c in constructs_sorted]
    label_to_code = dict(zip(topic_labels_list, constructs_sorted))

    selected_label = st.selectbox("Topic", sorted(topic_labels_list), key="deep_dive_topic")
    selected_construct = label_to_code.get(selected_label, "")

    if selected_construct and selected_construct in heatmap_data:
        # Get data for this construct
        construct_row = heatmap_data[selected_construct]

        # Build bar chart data
        subgroup_names = []
        support_values = []
        bar_colors = []

        for subgroup in DEMOGRAPHIC_SUBGROUPS:
            cell_data = construct_row.get(subgroup, {})
            pct = cell_data.get("pct")

            if pct is not None:
                subgroup_names.append(subgroup)
                support_values.append(pct)

                # Color by support level
                if pct >= 75:
                    bar_colors.append("#1B6B3A")  # Green
                elif pct >= 60:
                    bar_colors.append("#B8870A")  # Gold
                elif pct < 50:
                    bar_colors.append("#8B1A1A")  # Red
                else:
                    bar_colors.append(NAVY)  # Navy neutral

        fig_dive = go.Figure(go.Bar(
            y=subgroup_names,
            x=support_values,
            orientation="h",
            marker_color=bar_colors,
            text=[f"{v:.1f}%" for v in support_values],
            textposition="auto",
            textfont=dict(size=11, color="white"),
        ))

        fig_dive.update_layout(
            template="plotly_white",
            paper_bgcolor=BG,
            plot_bgcolor=CARD_BG,
            height=400,
            margin=dict(l=150, r=20, t=40, b=40),
            xaxis=dict(
                range=[0, 105],
                title="Support %",
                title_font=dict(color=NAVY, size=12),
                gridcolor="#E8E4DC",
            ),
            yaxis=dict(autorange="reversed", tickfont=dict(size=11, color=NAVY)),
            font=dict(family="DM Sans", color=NAVY),
        )

        st.plotly_chart(fig_dive, use_container_width=True, key="deep_dive_bar")

        # ── Key stats ──
        col1, col2, col3 = st.columns(3)

        overall_pct = construct_row.get("Overall", {}).get("pct")
        if overall_pct is not None:
            col1.metric("Overall Support", f"{overall_pct:.1f}%")

        tier = TIER_MAP.get(selected_construct, "—")
        col2.metric("Persuasion Tier", tier)

        # Find max and min
        valid_pcts = [construct_row[sg].get("pct") for sg in DEMOGRAPHIC_SUBGROUPS
                      if construct_row.get(sg, {}).get("pct") is not None]
        if valid_pcts:
            gap = max(valid_pcts) - min(valid_pcts)
            col3.metric("Support Gap", f"{gap:.1f}pp")


# ══════════════════════════════════════════════════════════════════
# VIEW 3: DEMOGRAPHIC PROFILE
# ══════════════════════════════════════════════════════════════════

elif view_mode == "Demographic Profile":
    st.subheader("Select a Demographic Group to See Support Profile")
    st.caption("Horizontal bar chart showing support rate for all topics within one demographic subgroup.")

    selected_subgroup = st.selectbox(
        "Demographic Group",
        DEMOGRAPHIC_SUBGROUPS,
        key="demo_profile_subgroup",
    )

    # Get data for this subgroup
    constructs_sorted = sorted(
        heatmap_data.keys(),
        key=lambda c: (TIER_MAP.get(c, "ZZZ"), CONSTRUCT_LABELS.get(c, c))
    )

    subgroup_data = []
    for construct in constructs_sorted:
        cell_data = heatmap_data[construct].get(selected_subgroup, {})
        pct = cell_data.get("pct")

        if pct is not None:
            subgroup_data.append({
                "topic": CONSTRUCT_LABELS.get(construct, construct),
                "pct": pct,
                "construct": construct,
            })

    if subgroup_data:
        # Sort by support %
        subgroup_data_sorted = sorted(subgroup_data, key=lambda x: x["pct"], reverse=True)

        topic_names = [d["topic"] for d in subgroup_data_sorted]
        support_pcts = [d["pct"] for d in subgroup_data_sorted]

        # Color by support level
        bar_colors_profile = []
        for pct in support_pcts:
            if pct >= 75:
                bar_colors_profile.append("#1B6B3A")  # Green
            elif pct >= 60:
                bar_colors_profile.append("#B8870A")  # Gold
            elif pct < 50:
                bar_colors_profile.append("#8B1A1A")  # Red
            else:
                bar_colors_profile.append(NAVY)  # Navy neutral

        fig_profile = go.Figure(go.Bar(
            y=topic_names,
            x=support_pcts,
            orientation="h",
            marker_color=bar_colors_profile,
            text=[f"{v:.1f}%" for v in support_pcts],
            textposition="auto",
            textfont=dict(size=10, color="white"),
        ))

        fig_profile.update_layout(
            template="plotly_white",
            paper_bgcolor=BG,
            plot_bgcolor=CARD_BG,
            height=max(400, len(subgroup_data_sorted) * 20),
            margin=dict(l=280, r=20, t=40, b=40),
            xaxis=dict(
                range=[0, 105],
                title="Support %",
                title_font=dict(color=NAVY, size=12),
                gridcolor="#E8E4DC",
            ),
            yaxis=dict(autorange="reversed", tickfont=dict(size=10, color=NAVY)),
            font=dict(family="DM Sans", color=NAVY),
        )

        st.plotly_chart(fig_profile, use_container_width=True, key="profile_bar")

        # ── Summary for this subgroup ──
        col1, col2, col3 = st.columns(3)

        avg_support_subgroup = np.mean(support_pcts)
        col1.metric("Average Support", f"{avg_support_subgroup:.1f}%")

        n_topics_strong = sum(1 for p in support_pcts if p >= 75)
        col2.metric("Topics with 75%+ Support", n_topics_strong)

        n_topics_weak = sum(1 for p in support_pcts if p < 50)
        col3.metric("Topics Below 50% Support", n_topics_weak)
    else:
        st.warning(f"No data available for {selected_subgroup}. This group may be underrepresented in the data.")


render_chat("voter_segments")
portal_footer()
