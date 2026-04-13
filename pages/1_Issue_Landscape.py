"""
Issue Landscape — SLA Portal
Consensus Gauge primary view: sorted horizontal bars by topic support (Consensus Gauge™ style).
Scatter as secondary view with fixed labels (hover-only).
All questions ranked below.
"""

import streamlit as st
from pathlib import Path
import sys
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import requests
from collections import defaultdict

# Auth gate
sys.path.insert(0, str(Path(__file__).parent.parent))
from auth import require_auth
from chat_widget import render_chat

# Theme
from theme import (
    apply_theme, portal_footer, get_supabase_config, get_supabase_headers,
    CJ_SURVEYS, SURVEY_STATE, TIER_MAP, tier_badge_html,
    NAVY, NAVY2, GOLD, GOLD_MID, TEXT1, TEXT2, TEXT3, BORDER2, BG, CARD_BG,
    STATE_COLORS, STATE_ABBR,
)

# Scoring engine (bundled locally)
sys.path.insert(0, str(Path(__file__).parent.parent))
try:
    from content_scoring import FAVORABLE_DIRECTION, SKIPPED_QIDS, get_construct, score_content
    SCORING_AVAILABLE = True
except ImportError:
    SCORING_AVAILABLE = False

st.set_page_config(
    page_title="Issue Landscape — SLA Portal",
    page_icon="⚡",
    layout="wide",
)

apply_theme()
username = require_auth("Second Look Alliance", accent_color=GOLD)

SUPABASE_URL, SUPABASE_KEY = get_supabase_config()
HEADERS = get_supabase_headers()

# Quadrant colors
QUAD_COLORS = {
    "Golden Zone": "#1B6B3A",
    "Base Only": "#1155AA",
    "Persuasion Target": "#B85400",
    "Low Support": "#8B1A1A",
}

# Consensus Gauge colors (by support level)
GAUGE_COLORS = {
    "strong": "#1B6B3A",      # Green: 75%+
    "moderate": "#B8870A",    # Gold: 55-74%
    "contested": "#8B1A1A",   # Red: <55%
}

# Human-readable construct names (replace internal codes)
CONSTRUCT_LABELS = {
    "PD_FUNDING": "Public Defender Funding",
    "INVEST": "Community Investment",
    "LIT": "Literacy Programs",
    "COUNSEL_ACCESS": "Right to Counsel",
    "DV": "Domestic Violence",
    "CAND-DV": "Candidates on DV",
    "PROP": "Property Crime Reform",
    "REDEMPTION": "Redemption / Second Chances",
    "EXPUNGE": "Record Expungement",
    "SENTREVIEW": "Sentence Review",
    "JUDICIAL": "Judicial Discretion",
    "RETRO": "Retroactive Relief",
    "FINES": "Fines & Fees",
    "MAND": "Mandatory Minimums",
    "BAIL": "Bail Reform",
    "REENTRY": "Reentry Programs",
    "RECORD": "Criminal Record Reform",
    "JUV": "Juvenile Justice",
    "FAMILY": "Family Reunification",
    "ELDERLY": "Compassionate Release",
    "COURT": "Court Reform",
    "COURTREVIEW": "Court Review Process",
    "TRUST": "System Trust",
    "PLEA": "Plea Bargaining Reform",
    "PROS": "Prosecutor Accountability",
    "CAND": "Candidate Favorability",
    "TOUGHCRIME": "Tough on Crime Attitudes",
    "ISSUE_SALIENCE": "Issue Importance",
    "IMPACT": "Personal Impact",
    "DETER": "Deterrence Beliefs",
    "FISCAL": "Fiscal Responsibility",
    "DP_ABOLITION": "Death Penalty Abolition",
    "DP_RELIABILITY": "Death Penalty Reliability",
    "LWOP": "Life Without Parole",
    "COMPASSION": "Compassionate Release",
}

# Gauge constructs — measure attitudes, not reform support. Excluded from scatter.
GAUGE_CONSTRUCTS = {"CAND", "TOUGHCRIME", "ISSUE_SALIENCE", "IMPACT"}


# ══════════════════════════════════════════════════════════════════
# DATA LOADING
# ══════════════════════════════════════════════════════════════════

def _paginate(url_base, headers, limit=1000, max_rows=200000):
    """Paginate a Supabase REST query."""
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


@st.cache_data(ttl=3600, show_spinner="Loading survey data...")
def load_question_data():
    """Load all question-level data: support rate, skeptic support, construct, text.
    Returns a dict keyed by QID with per-question stats.
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

    # Pull L1 party
    all_l1 = []
    for sid in CJ_SURVEYS:
        rows = _paginate(
            f"{SUPABASE_URL}/rest/v1/l1_respondents"
            f"?select=respondent_id,party_id"
            f"&survey_id=eq.{sid}",
            HEADERS,
        )
        all_l1.extend(rows)

    party_lookup = {d["respondent_id"]: d.get("party_id", "") for d in all_l1}

    # Score responses and compute party-split rates
    q_stats = defaultdict(lambda: {
        "r_f": 0, "r_n": 0, "d_f": 0, "d_n": 0, "all_f": 0, "all_n": 0,
        "construct": None, "text": "",
    })

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
        is_fav = 1 if fav == 1 else 0

        q_stats[qid]["all_f"] += is_fav
        q_stats[qid]["all_n"] += 1
        q_stats[qid]["construct"] = construct
        if r.get("question_text"):
            q_stats[qid]["text"] = r["question_text"]

        party = party_lookup.get(r["respondent_id"], "")
        if party and "republican" in party.lower():
            q_stats[qid]["r_f"] += is_fav
            q_stats[qid]["r_n"] += 1
        elif party and "democrat" in party.lower():
            q_stats[qid]["d_f"] += is_fav
            q_stats[qid]["d_n"] += 1

    result = {}
    for qid, s in q_stats.items():
        if s["all_n"] < 20:
            continue
        r_rate = (s["r_f"] / s["r_n"] * 100) if s["r_n"] >= 10 else None
        d_rate = (s["d_f"] / s["d_n"] * 100) if s["d_n"] >= 10 else None

        result[qid] = {
            "skeptic_support": r_rate,
            "overall_support": s["all_f"] / s["all_n"] * 100,
            "construct": s["construct"],
            "text": s["text"],
            "n": s["all_n"],
        }
    return result


def aggregate_to_topics(question_data):
    """Aggregate question-level data to construct (topic) level.
    Returns a list of dicts, one per topic, with averaged metrics.
    """
    topic_agg = defaultdict(lambda: {
        "reaches": [], "skeptic_reaches": [], "n_total": 0, "questions": [],
    })

    for qid, qd in question_data.items():
        construct = qd["construct"]
        if not construct or construct in GAUGE_CONSTRUCTS:
            continue

        topic_agg[construct]["reaches"].append(qd["overall_support"])
        topic_agg[construct]["n_total"] += qd["n"]
        topic_agg[construct]["questions"].append({
            "qid": qid,
            "text": qd["text"],
            "overall_support": qd["overall_support"],
            "skeptic_support": qd["skeptic_support"],
            "n": qd["n"],
        })
        if qd["skeptic_support"] is not None:
            topic_agg[construct]["skeptic_reaches"].append(qd["skeptic_support"])

    topics = []
    for construct, agg in topic_agg.items():
        if not agg["reaches"]:
            continue
        avg_reach = np.mean(agg["reaches"])
        avg_skeptic = np.mean(agg["skeptic_reaches"]) if agg["skeptic_reaches"] else None

        tier = TIER_MAP.get(construct, "")
        label = CONSTRUCT_LABELS.get(construct, construct)

        # Quadrant assignment
        if avg_skeptic is not None:
            if avg_reach >= 60 and avg_skeptic >= 60:
                quad = "Golden Zone"
            elif avg_reach >= 60 and avg_skeptic < 60:
                quad = "Base Only"
            elif avg_reach < 60 and avg_skeptic >= 60:
                quad = "Persuasion Target"
            else:
                quad = "Low Support"
        else:
            quad = "Unknown"

        topics.append({
            "construct": construct,
            "topic": label,
            "tier": tier,
            "overall_support": avg_reach,
            "skeptic_support": avg_skeptic,
            "quadrant": quad,
            "n_questions": len(agg["reaches"]),
            "n_respondents": agg["n_total"],
            "questions": sorted(agg["questions"], key=lambda q: q["overall_support"], reverse=True),
        })

    return topics


def get_gauge_color(support_pct):
    """Return color code based on support percentage (Consensus Gauge style)."""
    if support_pct >= 75:
        return GAUGE_COLORS["strong"]  # Green: #1B6B3A
    elif support_pct >= 55:
        return GAUGE_COLORS["moderate"]  # Gold: #B8870A
    else:
        return GAUGE_COLORS["contested"]  # Red: #8B1A1A


# ══════════════════════════════════════════════════════════════════
# MAIN PAGE
# ══════════════════════════════════════════════════════════════════

st.title("⚡ Issue Landscape")
st.caption(
    "Each dot is a reform topic. Upper-right (Golden Zone) = broad bipartisan support. "
    "Hover any dot for details. Switch views in the sidebar for ranked lists and consensus gauges."
)

if not SCORING_AVAILABLE:
    st.error("content_scoring.py not found. Cannot score responses.")
    st.stop()

# Load and aggregate
question_data = load_question_data()
topics = aggregate_to_topics(question_data)

if not topics:
    st.warning("No data available.")
    st.stop()

df = pd.DataFrame(topics)
df_plot = df.dropna(subset=["skeptic_support"])

# ── Sidebar filters ──
with st.sidebar:
    st.markdown("### Filters & View")

    all_tiers = sorted(df["tier"].dropna().unique())
    tier_filter = st.selectbox("Persuasion Tier", ["All Tiers"] + all_tiers, key="il_tier")

    quad_filter = st.multiselect("Category", list(QUAD_COLORS.keys()),
                                  default=list(QUAD_COLORS.keys()), key="il_quad")

    view_mode = st.radio("View Type", ["Scatter", "Consensus Gauge", "Ranked List"], key="il_view")

    st.divider()
    st.metric("Topics", f"{len(df_plot)}")
    for q, color in QUAD_COLORS.items():
        ct = len(df_plot[df_plot["quadrant"] == q])
        st.caption(f"● {q}: {ct}")

# Apply filters
filtered = df_plot.copy()
if tier_filter != "All Tiers":
    filtered = filtered[filtered["tier"] == tier_filter]
if quad_filter:
    filtered = filtered[filtered["quadrant"].isin(quad_filter)]

if filtered.empty:
    st.warning("No topics match the current filters.")
    st.stop()


# ══════════════════════════════════════════════════════════════════
# CONSENSUS GAUGE VIEW (PRIMARY)
# ══════════════════════════════════════════════════════════════════

if view_mode == "Consensus Gauge":
    st.markdown("## Consensus Gauge™")
    st.caption(
        "Topics sorted by overall public support. Each bar shows the proportion of respondents who favor that reform. "
        "Hover for details; select a topic below to explore individual survey questions."
    )

    # Sort by overall support descending
    gauge_data = filtered.sort_values("overall_support", ascending=True)

    # Build the horizontal bar chart
    fig_gauge = go.Figure()

    for idx, (_, row) in enumerate(gauge_data.iterrows()):
        support_pct = row["overall_support"]
        color = get_gauge_color(support_pct)
        tier = row["tier"] if row["tier"] else "—"

        fig_gauge.add_trace(go.Bar(
            y=[row["topic"]],
            x=[support_pct],
            orientation="h",
            marker=dict(color=color),
            text=f"{support_pct:.0f}%",
            textposition="auto",
            textfont=dict(color="white", size=12, family="DM Sans"),
            hovertemplate=(
                f"<b>{row['topic']}</b><br>"
                f"Overall Support: {support_pct:.1f}%<br>"
                f"Persuasion Tier: {tier}<br>"
                f"Survey Questions: {row['n_questions']}<br>"
                f"Respondents: {row['n_respondents']}"
                "<extra></extra>"
            ),
            showlegend=False,
            name="",
        ))

    fig_gauge.update_layout(
        template="plotly_white",
        paper_bgcolor=BG,
        plot_bgcolor=CARD_BG,
        height=max(400, len(gauge_data) * 45 + 100),
        margin=dict(l=350, r=60, t=40, b=60),
        xaxis=dict(
            title="Overall Support %",
            range=[0, 100],
            gridcolor="#E8E4DC",
            dtick=10,
            title_font=dict(size=12, color=NAVY),
        ),
        yaxis=dict(
            tickfont=dict(size=11, color=NAVY),
            autorange="reversed",
        ),
        font=dict(family="DM Sans", color=NAVY, size=11),
        hovermode="closest",
    )

    st.plotly_chart(fig_gauge, use_container_width=True, key="il_gauge")

    # ── Topic selection dropdown ──
    st.divider()
    st.markdown("### Explore a Topic")

    topic_opts = sorted(filtered["topic"].tolist())
    selected_label = st.selectbox(
        "Select a topic to see individual survey questions:",
        ["(click to explore)"] + topic_opts,
        key="il_topic_select",
    )

    if selected_label != "(click to explore)":
        match = filtered[filtered["topic"] == selected_label]
        if not match.empty:
            topic_row = match.iloc[0]

            # Topic detail header
            st.markdown(
                f'<div style="font-family:Playfair Display,serif;font-size:1.4rem;font-weight:700;color:{NAVY};">'
                f'{topic_row["topic"]}</div>',
                unsafe_allow_html=True,
            )

            # Metrics
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Overall Support", f"{topic_row['overall_support']:.0f}%")
            c2.metric("Skeptic Support", f"{topic_row['skeptic_support']:.0f}%" if topic_row['skeptic_support'] else "—")
            c3.metric("Category", topic_row["quadrant"])
            c4.metric("Persuasion Tier", topic_row["tier"] if topic_row["tier"] else "—")

            # Individual questions within topic
            questions = topic_row["questions"]
            if questions and len(questions) > 0:
                st.markdown(
                    f'<div style="font-size:0.95rem;color:{TEXT2};margin:1rem 0 0.5rem 0;">'
                    f'<strong>{len(questions)} survey questions</strong> supporting this topic:</div>',
                    unsafe_allow_html=True,
                )

                q_df = pd.DataFrame(questions)

                # Horizontal bar chart with full question text (no truncation)
                fig_q = go.Figure()

                fig_q.add_trace(go.Bar(
                    y=q_df["text"],
                    x=q_df["overall_support"],
                    name="Overall Support",
                    orientation="h",
                    marker_color=NAVY,
                    text=q_df["overall_support"].apply(lambda v: f"{v:.0f}%"),
                    textposition="auto",
                    textfont=dict(color="white", size=9),
                    hovertemplate="%{y}<br>Overall: %{x:.1f}%<extra></extra>",
                ))

                skeptic_vals = q_df["skeptic_support"].fillna(0)
                fig_q.add_trace(go.Bar(
                    y=q_df["text"],
                    x=skeptic_vals,
                    name="Skeptic Support",
                    orientation="h",
                    marker_color=GOLD,
                    text=skeptic_vals.apply(lambda v: f"{v:.0f}%" if v > 0 else "—"),
                    textposition="auto",
                    textfont=dict(color=NAVY, size=9),
                    hovertemplate="%{y}<br>Skeptic: %{x:.1f}%<extra></extra>",
                ))

                fig_q.update_layout(
                    barmode="group",
                    template="plotly_white",
                    paper_bgcolor=BG,
                    plot_bgcolor=CARD_BG,
                    height=max(300, len(q_df) * 60 + 100),
                    margin=dict(l=500, r=30, t=30, b=40),
                    xaxis=dict(
                        title="Support %",
                        range=[0, 100],
                        gridcolor="#E8E4DC",
                        title_font=dict(color=NAVY),
                    ),
                    yaxis=dict(
                        autorange="reversed",
                        tickfont=dict(size=10),
                    ),
                    legend=dict(
                        orientation="h",
                        yanchor="bottom",
                        y=1.02,
                        font=dict(size=10, color=NAVY),
                    ),
                    font=dict(family="DM Sans", color=NAVY),
                    hovermode="closest",
                )

                st.plotly_chart(fig_q, use_container_width=True, key="il_question_bars_gauge")

    # ══════════════════════════════════════════════════════════════
    # ALL QUESTIONS RANKED (always shown in Consensus Gauge view)
    # ══════════════════════════════════════════════════════════════

    st.divider()
    st.markdown("### All Questions Ranked")
    st.caption(
        "Every individual survey question ranked by overall support. "
        "Navy = overall public support. Gold = support among reform skeptics."
    )

    # Build flat list of all individual questions from filtered topics
    all_questions = []
    for _, topic_row_iter in filtered.iterrows():
        questions_list = topic_row_iter.get("questions", [])
        if questions_list:
            for q in questions_list:
                all_questions.append({
                    "text": q["text"],
                    "overall_support": q["overall_support"],
                    "skeptic_support": q["skeptic_support"],
                    "n": q["n"],
                    "topic": topic_row_iter["topic"],
                })

    if all_questions:
        all_q_df = pd.DataFrame(all_questions).sort_values("overall_support", ascending=True)
        # Cap at top 40 to keep page reasonable
        all_q_df = all_q_df.tail(40)

        fig_dual = go.Figure()

        fig_dual.add_trace(go.Bar(
            y=all_q_df["text"],
            x=all_q_df["overall_support"],
            name="Overall Support",
            orientation="h",
            marker_color=NAVY,
            text=all_q_df["overall_support"].apply(lambda v: f"{v:.0f}%"),
            textposition="auto",
            textfont=dict(color="white", size=10),
            hovertemplate="%{y}<br>Overall: %{x:.1f}%<extra></extra>",
        ))

        skeptic_vals = all_q_df["skeptic_support"].fillna(0)
        fig_dual.add_trace(go.Bar(
            y=all_q_df["text"],
            x=skeptic_vals,
            name="Skeptic Support",
            orientation="h",
            marker_color=GOLD,
            text=skeptic_vals.apply(lambda v: f"{v:.0f}%" if v > 0 else "—"),
            textposition="auto",
            textfont=dict(color=NAVY, size=10),
            hovertemplate="%{y}<br>Skeptic: %{x:.1f}%<extra></extra>",
        ))

        fig_dual.update_layout(
            barmode="group",
            template="plotly_white",
            paper_bgcolor=BG,
            plot_bgcolor=CARD_BG,
            height=max(500, len(all_q_df) * 50 + 100),
            margin=dict(l=500, r=30, t=30, b=50),
            xaxis=dict(
                title="Support %",
                range=[0, 100],
                gridcolor="#E8E4DC",
                dtick=10,
                title_font=dict(color=NAVY),
            ),
            yaxis=dict(tickfont=dict(size=10)),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                font=dict(size=12, color=NAVY),
            ),
            font=dict(family="DM Sans", color=NAVY),
            hovermode="closest",
        )

        st.plotly_chart(fig_dual, use_container_width=True, key="il_dual_bar_gauge")


# ══════════════════════════════════════════════════════════════════
# SCATTER VIEW (SECONDARY)
# ══════════════════════════════════════════════════════════════════

elif view_mode == "Scatter":
    st.markdown("## Scatter Plot")
    st.caption(
        "Each dot is a reform topic. Horizontal = support among reform skeptics. "
        "Vertical = overall public support. Hover over dots for details. "
        "The Golden Zone (upper right) contains topics with broad consensus."
    )

    # Dynamic axis range
    x_min = max(0, filtered["skeptic_support"].min() - 8)
    x_max = min(100, filtered["skeptic_support"].max() + 5)
    y_min = max(0, filtered["overall_support"].min() - 8)
    y_max = min(100, filtered["overall_support"].max() + 5)

    quad_x, quad_y = 60, 60

    fig = px.scatter(
        filtered, x="skeptic_support", y="overall_support",
        color="quadrant",
        color_discrete_map=QUAD_COLORS,
        hover_name="topic",
        hover_data={
            "overall_support": ":.0f",
            "skeptic_support": ":.0f",
            "n_questions": True,
            "tier": True,
            "quadrant": True,
            "construct": False,
            "n_respondents": False,
            "topic": False,
            "questions": False,
        },
        size="n_questions",
        size_max=22,
        opacity=0.85,
        labels={
            "skeptic_support": "Skeptic Support %",
            "overall_support": "Overall Support %",
            "n_questions": "Survey Questions",
            "tier": "Persuasion Tier",
            "quadrant": "Category",
        },
    )

    # Quadrant dividers (kept from original)
    if quad_y >= y_min and quad_y <= y_max:
        fig.add_hline(y=quad_y, line_dash="dash", line_color="#D4D0C8", line_width=1)
    if quad_x >= x_min and quad_x <= x_max:
        fig.add_vline(x=quad_x, line_dash="dash", line_color="#D4D0C8", line_width=1)

    # Quadrant labels (kept from original, no text annotations on dots)
    label_left_x = max(x_min + 2, (x_min + quad_x) / 2)
    label_right_x = min(x_max - 2, (quad_x + x_max) / 2)
    label_top_y = min(y_max - 1, y_max - 2)
    label_bot_y = max(y_min + 1, y_min + 2)

    fig.add_annotation(x=label_left_x, y=label_top_y, text="Base Only", showarrow=False,
                       font=dict(color="#1155AA", size=11), opacity=0.6)
    fig.add_annotation(x=label_right_x, y=label_top_y, text="Golden Zone", showarrow=False,
                       font=dict(color="#1B6B3A", size=13, family="Playfair Display"), opacity=0.85)
    fig.add_annotation(x=label_left_x, y=label_bot_y, text="Low Support", showarrow=False,
                       font=dict(color="#8B1A1A", size=11), opacity=0.6)
    fig.add_annotation(x=label_right_x, y=label_bot_y, text="Persuasion Target", showarrow=False,
                       font=dict(color="#B85400", size=11), opacity=0.6)

    # NOTE: Removed individual topic label annotations from scatter to eliminate overlapping text

    fig.update_layout(
        template="plotly_white",
        paper_bgcolor=BG,
        plot_bgcolor=CARD_BG,
        height=620,
        margin=dict(l=60, r=20, t=40, b=60),
        xaxis=dict(range=[x_min, x_max], dtick=10, gridcolor="#E8E4DC",
                   title_font=dict(color=NAVY)),
        yaxis=dict(range=[y_min, y_max], dtick=10, gridcolor="#E8E4DC",
                   title_font=dict(color=NAVY)),
        legend=dict(
            font=dict(size=10, color=NAVY),
            bgcolor="rgba(250,249,246,0.9)",
            bordercolor=BORDER2, borderwidth=1,
        ),
        font=dict(family="DM Sans", color=NAVY),
    )

    selected = st.plotly_chart(fig, use_container_width=True, on_select="rerun", key="il_scatter")

    # ── Detect which topic was clicked ──
    selected_construct = None
    if selected and selected.selection and selected.selection.points:
        pt = selected.selection.points[0]
        idx = pt.get("point_index")
        curve = pt.get("curve_number", 0)
        quads = sorted(filtered["quadrant"].unique())
        if curve < len(quads):
            sub = filtered[filtered["quadrant"] == quads[curve]]
            if idx is not None and idx < len(sub):
                selected_construct = sub.iloc[idx]["construct"]

    # Also allow dropdown selection
    topic_opts = sorted(filtered["topic"].tolist())
    if not selected_construct:
        sel_label = st.selectbox(
            "Or select a topic:",
            ["(click a dot above)"] + topic_opts,
            key="il_topic_select_scatter",
        )
        if sel_label != "(click a dot above)":
            match = filtered[filtered["topic"] == sel_label]
            if not match.empty:
                selected_construct = match.iloc[0]["construct"]

    # ── Detail panel: show individual questions for selected topic ──
    if selected_construct:
        topic_row = filtered[filtered["construct"] == selected_construct]
        if not topic_row.empty:
            topic_row = topic_row.iloc[0]
            st.divider()
            st.markdown(
                f'<div style="font-family:Playfair Display,serif;font-size:1.3rem;font-weight:700;color:{NAVY};">'
                f'{topic_row["topic"]}</div>',
                unsafe_allow_html=True,
            )

            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Overall Support", f"{topic_row['overall_support']:.0f}%")
            c2.metric("Skeptic Support", f"{topic_row['skeptic_support']:.0f}%")
            c3.metric("Category", topic_row["quadrant"])
            c4.metric("Persuasion Tier", topic_row["tier"] if topic_row["tier"] else "—")

            # Individual questions chart
            questions = topic_row["questions"]
            if questions and len(questions) > 0:
                st.markdown(
                    f'<div style="font-size:0.9rem;color:{TEXT2};margin:0.5rem 0;">'
                    f'<strong>{len(questions)} survey questions</strong> in this topic</div>',
                    unsafe_allow_html=True,
                )

                q_df = pd.DataFrame(questions)

                # Horizontal bar chart: overall support + skeptic support side by side
                fig_q = go.Figure()

                fig_q.add_trace(go.Bar(
                    y=q_df["text"],
                    x=q_df["overall_support"],
                    name="Overall Support",
                    orientation="h",
                    marker_color=NAVY,
                    text=q_df["overall_support"].apply(lambda v: f"{v:.0f}%"),
                    textposition="auto",
                    hovertemplate="%{y}<br>Overall: %{x:.0f}%<extra></extra>",
                ))

                skeptic_vals = q_df["skeptic_support"].fillna(0)
                fig_q.add_trace(go.Bar(
                    y=q_df["text"],
                    x=skeptic_vals,
                    name="Skeptic Support",
                    orientation="h",
                    marker_color=GOLD,
                    text=skeptic_vals.apply(lambda v: f"{v:.0f}%" if v > 0 else "—"),
                    textposition="auto",
                    hovertemplate="%{y}<br>Skeptic: %{x:.0f}%<extra></extra>",
                ))

                fig_q.update_layout(
                    barmode="group",
                    template="plotly_white",
                    paper_bgcolor=BG,
                    plot_bgcolor=CARD_BG,
                    height=max(250, len(q_df) * 55 + 80),
                    margin=dict(l=500, r=30, t=30, b=40),
                    xaxis=dict(title="Support %", range=[0, 100], gridcolor="#E8E4DC",
                               title_font=dict(color=NAVY)),
                    yaxis=dict(autorange="reversed", tickfont=dict(size=11)),
                    legend=dict(
                        orientation="h", yanchor="bottom", y=1.02,
                        font=dict(size=11, color=NAVY),
                    ),
                    font=dict(family="DM Sans", color=NAVY),
                )

                st.plotly_chart(fig_q, use_container_width=True, key="il_question_bars_scatter")

    # ══════════════════════════════════════════════════════════════
    # DUAL BAR — individual questions ranked (always shown below scatter)
    # ══════════════════════════════════════════════════════════════

    st.divider()
    st.markdown("#### All Questions Ranked")
    st.caption(
        "Every individual survey question ranked by overall support. "
        "Navy = overall public support. Gold = support among reform skeptics."
    )

    # Build flat list of all individual questions from filtered topics
    all_questions = []
    for _, topic_row_iter in filtered.iterrows():
        questions_list = topic_row_iter.get("questions", [])
        if questions_list:
            for q in questions_list:
                all_questions.append({
                    "text": q["text"],
                    "overall_support": q["overall_support"],
                    "skeptic_support": q["skeptic_support"],
                    "n": q["n"],
                    "topic": topic_row_iter["topic"],
                })

    if all_questions:
        all_q_df = pd.DataFrame(all_questions).sort_values("overall_support", ascending=True)
        # Cap at top 40 to keep page reasonable
        all_q_df = all_q_df.tail(40)

        fig_dual = go.Figure()

        fig_dual.add_trace(go.Bar(
            y=all_q_df["text"],
            x=all_q_df["overall_support"],
            name="Overall Support",
            orientation="h",
            marker_color=NAVY,
            text=all_q_df["overall_support"].apply(lambda v: f"{v:.0f}%"),
            textposition="auto",
            textfont=dict(color="white", size=10),
            hovertemplate="%{y}<br>Overall: %{x:.0f}%<extra></extra>",
        ))

        skeptic_vals = all_q_df["skeptic_support"].fillna(0)
        fig_dual.add_trace(go.Bar(
            y=all_q_df["text"],
            x=skeptic_vals,
            name="Skeptic Support",
            orientation="h",
            marker_color=GOLD,
            text=skeptic_vals.apply(lambda v: f"{v:.0f}%" if v > 0 else "—"),
            textposition="auto",
            textfont=dict(color=NAVY, size=10),
            hovertemplate="%{y}<br>Skeptic: %{x:.0f}%<extra></extra>",
        ))

        fig_dual.update_layout(
            barmode="group",
            template="plotly_white",
            paper_bgcolor=BG,
            plot_bgcolor=CARD_BG,
            height=max(500, len(all_q_df) * 40 + 100),
            margin=dict(l=500, r=30, t=30, b=50),
            xaxis=dict(title="Support %", range=[0, 100], gridcolor="#E8E4DC",
                       dtick=10, title_font=dict(color=NAVY)),
            yaxis=dict(tickfont=dict(size=10)),
            legend=dict(
                orientation="h", yanchor="bottom", y=1.02,
                font=dict(size=12, color=NAVY),
            ),
            font=dict(family="DM Sans", color=NAVY),
        )

        st.plotly_chart(fig_dual, use_container_width=True, key="il_dual_bar_scatter")


# ══════════════════════════════════════════════════════════════════
# RANKED LIST VIEW
# ══════════════════════════════════════════════════════════════════

elif view_mode == "Ranked List":
    st.markdown("#### Topics Ranked by Overall Support")
    ranked = filtered.sort_values("overall_support", ascending=False)

    display_df = ranked[["topic", "overall_support", "skeptic_support", "quadrant", "tier", "n_questions"]].copy()
    display_df.columns = ["Topic", "Overall Support %", "Skeptic Support %", "Category", "Persuasion Tier", "Questions"]
    display_df["Overall Support %"] = display_df["Overall Support %"].apply(lambda x: f"{x:.0f}%")
    display_df["Skeptic Support %"] = display_df["Skeptic Support %"].apply(lambda x: f"{x:.0f}%" if pd.notna(x) else "—")
    display_df = display_df.reset_index(drop=True)
    display_df.index = display_df.index + 1

    st.dataframe(display_df, use_container_width=True, height=500)


render_chat("issue_landscape")

portal_footer()
