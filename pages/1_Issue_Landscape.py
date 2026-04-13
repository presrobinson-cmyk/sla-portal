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
    apply_theme, portal_footer, data_source_badge, get_supabase_config, get_supabase_headers,
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

# Shared data loader (MrP primary, raw fallback)
from data_loader import load_question_data_hybrid, load_party_splits, render_data_source_toggle, get_display_pct

# New loaders added in Session 5 — defensive import so old deploys don't crash
try:
    from data_loader import load_demo_splits, load_mrp_question_summary, load_respondent_level_data
    DEMO_SPLITS_AVAILABLE = True
except ImportError:
    DEMO_SPLITS_AVAILABLE = False
    def load_demo_splits(*a, **kw): return {}
    def load_mrp_question_summary(*a, **kw): return {}, set()
    def load_respondent_level_data(*a, **kw): return {}, []

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
    "DETER": "Sentence Severity Deters Crime",
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


@st.cache_data(ttl=604800, show_spinner="Loading survey data...")
def load_question_data_cached():
    """Load all question-level data using MrP-adjusted rates (primary)
    with raw fallback for surveys not yet in MrP.
    Returns (question_data dict, demo_data dict, mrp_coverage dict).
    """
    question_data, mrp_coverage = load_question_data_hybrid()
    try:
        demo_data = load_demo_splits()
    except Exception:
        demo_data = {}  # Demographic splits unavailable — page still loads
    return question_data, demo_data, mrp_coverage


# Demographic subgroup options: display label → demo_splits key
DEMO_SUBGROUPS = {
    # Party
    "Republicans":          "r",
    "Democrats":            "d",
    "Independents":         "ind",
    # Ideology
    "Very Conservative":    "very_conservative",
    "Conservative":         "conservative",
    "Moderate":             "moderate",
    "Liberal":              "liberal",
    "Very Liberal":         "very_liberal",
    # Race / Ethnicity
    "White":                "white",
    "Black":                "black",
    "Hispanic":             "hispanic",
    "Non-White":            "non_white",
    # Education
    "HS or Less":           "hs_or_less",
    "Some College":         "some_college",
    "College Educated":     "college_plus",
    # Age
    "Ages 18-34":           "m18_34",
    "Ages 35-54":           "m35_54",
    "Ages 55-64":           "m55_64",
    "Ages 65+":             "m65plus",
    # Gender
    "Men":                  "male",
    "Women":                "female",
    # Community Type
    "Urban":                "urban",
    "Suburban":             "suburban",
    "Rural":                "rural",
}


def compute_intersection_support(demo_lookup, scored_responses, group_keys):
    """
    Compute per-QID support for respondents matching ALL of group_keys.
    Used when multiple demographic filters are selected simultaneously
    (e.g. Republicans + Women = respondents who are both).

    Returns dict[qid → support_pct | None]
    Groups with fewer than 10 matching respondents return None.
    """
    from collections import defaultdict as _dd
    group_set = frozenset(group_keys)
    # Respondents in the intersection of ALL selected groups
    selected_rids = {
        rid for rid, groups in demo_lookup.items()
        if group_set.issubset(groups)
    }
    if not selected_rids:
        return {}
    tallies = _dd(lambda: {"f": 0, "n": 0})
    for row in scored_responses:
        if row["respondent_id"] not in selected_rids:
            continue
        tallies[row["qid"]]["n"] += 1
        if row["fav"] == 1:
            tallies[row["qid"]]["f"] += 1
    return {
        qid: (t["f"] / t["n"] * 100) if t["n"] >= 10 else None
        for qid, t in tallies.items()
    }


def load_question_data(mode="mrp", subgroup_key="r"):
    """Build display-ready question data, applying the MrP/raw toggle
    and the selected demographic subgroup for the skeptic/X axis."""
    question_data, demo_data, mrp_coverage = load_question_data_cached()
    st.session_state["mrp_coverage"] = mrp_coverage

    result = {}
    for qid, qd in question_data.items():
        demo = demo_data.get(qid, {})
        result[qid] = {
            "skeptic_support": demo.get(subgroup_key),  # Selected subgroup rate
            "overall_support": get_display_pct(qd, mode),
            "construct": qd["construct"],
            "text": qd["question_text"],
            "response_label": qd.get("response_label", ""),  # Favorable response text
            "n": qd["n_respondents"],
            "source": "raw" if mode == "raw" else qd["source"],
        }
    return result


@st.cache_data(ttl=604800, show_spinner="Loading MPT scatter data...")
def load_mpt_scatter_data():
    """
    Compute MrP Reach and Universality per construct for the MPT scatter.

    Reach       = population-weighted mean MrP support across all surveyed states (0-100)
    Universality = 100 - std_dev(per-state MrP rates)
                 → 100 means perfectly consistent cross-state
                 → lower means support varies heavily by state

    Constructs in fewer than 2 states are excluded (universality is undefined).
    Returns a list of dicts: {construct, topic, tier, reach, universality, n_states, n_items}
    """
    mrp_data, _ = load_mrp_question_summary()

    # Group by (construct, state) via survey_id → SURVEY_STATE mapping
    from collections import defaultdict
    construct_state = defaultdict(lambda: defaultdict(list))  # {construct: {state: [mrp_pct, ...]}}

    for (sid, qid), row in mrp_data.items():
        if not SCORING_AVAILABLE:
            continue
        construct = get_construct(qid)
        if not construct or construct in GAUGE_CONSTRUCTS or qid in SKIPPED_QIDS:
            continue
        mrp_pct = row.get("mrp_pct")
        if mrp_pct is None:
            continue
        # Use state column if present and populated, else derive from survey_id
        state = row.get("state") or SURVEY_STATE.get(sid)
        if not state:
            continue
        construct_state[construct][state].append(mrp_pct)

    records = []
    for construct, states in construct_state.items():
        if len(states) < 2:
            continue  # universality requires 2+ states

        # Per-state mean (in case multiple questions per construct per state)
        state_means = {s: np.mean(vals) for s, vals in states.items()}
        reach = float(np.mean(list(state_means.values())))
        std_dev = float(np.std(list(state_means.values())))
        universality = max(0.0, 100.0 - std_dev)

        tier = TIER_MAP.get(construct, "")
        label = CONSTRUCT_LABELS.get(construct, construct)
        n_items = sum(len(v) for v in states.values())

        records.append({
            "construct": construct,
            "topic": label,
            "tier": tier,
            "reach": reach,
            "universality": universality,
            "n_states": len(states),
            "n_items": n_items,
            "state_breakdown": {s: round(v, 1) for s, v in sorted(state_means.items())},
        })

    return records


def aggregate_to_topics(question_data):
    """Aggregate question-level data to construct (topic) level.
    Returns a list of dicts, one per topic, with averaged metrics.
    """
    topic_agg = defaultdict(lambda: {
        "reaches": [], "skeptic_reaches": [], "n_total": 0, "questions": [],
    })

    for qid, qd in question_data.items():
        construct = qd["construct"]
        # TIER_MAP is the authoritative whitelist — only constructs with an assigned tier
        # appear in the landscape. This blocks screeners, ballot tests, and any other
        # QID whose construct leaked through without a tier assignment.
        if not construct or construct in GAUGE_CONSTRUCTS or construct not in TIER_MAP:
            continue

        overall_pct = qd["overall_support"]
        if overall_pct is None:
            continue  # Skip questions with no computable support rate (both mrp_pct and raw_pct are None)

        topic_agg[construct]["reaches"].append(overall_pct)
        topic_agg[construct]["n_total"] += qd["n"]
        topic_agg[construct]["questions"].append({
            "qid": qid,
            "text": qd["text"],
            "response_label": qd.get("response_label", ""),  # Favorable response text
            "overall_support": overall_pct,
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
            "questions": sorted(agg["questions"], key=lambda q: q["overall_support"] or 0, reverse=True),
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


def render_question_cards(q_df, key_prefix="qcard"):
    """Render questions as cards: full question text on top, support bars below.
    q_df must have columns: text, overall_support, skeptic_support, n, topic (optional).
    """
    for i, (_, row) in enumerate(q_df.iterrows()):
        q_text = row.get("text", "—") or "—"
        response_label = row.get("response_label", "") or ""
        overall = row.get("overall_support", 0) or 0
        skeptic = row.get("skeptic_support", None)
        n = row.get("n", 0)
        topic_label = row.get("topic", "")

        overall_color = get_gauge_color(overall)
        skeptic_pct = f"{skeptic:.0f}" if skeptic is not None and skeptic > 0 else None
        skeptic_bar_width = max(skeptic, 0) if skeptic is not None else 0

        # Topic badge
        topic_badge = ""
        if topic_label:
            topic_badge = (
                f'<span style="display:inline-block;background:rgba(14,31,61,0.08);color:{NAVY};'
                f'font-size:0.7rem;padding:1px 8px;border-radius:10px;margin-left:6px;'
                f'font-weight:500;">{topic_label}</span>'
            )

        # Build card HTML via concatenation — NO multiline template.
        # A whitespace-only line inside st.markdown HTML kicks Streamlit out of HTML mode,
        # so we never use an f-string template with optional {variable} placeholders.
        overall_bar = (
            f'<div style="display:flex;align-items:center;gap:8px;">'
            f'<div style="width:68px;font-size:0.72rem;color:{TEXT3};text-align:right;">Overall</div>'
            f'<div style="flex:1;height:16px;background:{BORDER2};border-radius:3px;overflow:hidden;">'
            f'<div style="width:{min(overall, 100):.0f}%;height:100%;background:{overall_color};border-radius:3px;"></div>'
            f'</div>'
            f'<div style="width:40px;font-size:0.8rem;font-weight:600;color:{overall_color};">{overall:.0f}%</div>'
            f'</div>'
        )
        skeptic_bar = ""
        if skeptic_pct:
            skeptic_bar = (
                f'<div style="display:flex;align-items:center;gap:8px;margin-top:4px;">'
                f'<div style="width:68px;font-size:0.72rem;color:{TEXT3};text-align:right;">Skeptic</div>'
                f'<div style="flex:1;height:16px;background:{BORDER2};border-radius:3px;overflow:hidden;">'
                f'<div style="width:{min(skeptic_bar_width, 100):.0f}%;height:100%;background:{GOLD};border-radius:3px;"></div>'
                f'</div>'
                f'<div style="width:40px;font-size:0.8rem;font-weight:600;color:{GOLD};">{skeptic_pct}%</div>'
                f'</div>'
            )
        response_bar = ""
        if response_label:
            response_bar = (
                f'<div style="font-size:0.78rem;color:{TEXT2};font-style:italic;'
                f'border-left:3px solid {GOLD};padding-left:8px;margin:4px 0 6px 0;line-height:1.4;">'
                f'✓ {response_label}'
                f'</div>'
            )
        n_line = f'<div style="font-size:0.65rem;color:{TEXT3};margin-top:4px;text-align:right;">n={n:,}</div>'
        stem_div = (
            f'<div style="font-size:0.88rem;color:{TEXT1};line-height:1.5;margin-bottom:0.35rem;">'
            f'{q_text}{topic_badge}'
            f'</div>'
        )
        card = (
            f'<div style="background:{CARD_BG};border:1px solid {BORDER2};border-radius:8px;'
            f'padding:0.85rem 1rem;margin-bottom:0.5rem;box-shadow:0 1px 2px rgba(0,0,0,0.03);">'
            + stem_div
            + response_bar
            + overall_bar
            + skeptic_bar
            + n_line
            + '</div>'
        )
        st.markdown(card, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════
# MAIN PAGE
# ══════════════════════════════════════════════════════════════════

st.title("⚡ Issue Landscape")

# MrP/Raw toggle (sidebar) — must come before data load so mode is set
data_mode = render_data_source_toggle()
data_source_badge(data_mode)

st.caption(
    "Each dot is a reform topic. Upper-right (Golden Zone) = broad bipartisan support. "
    "Hover any dot for details. Switch views in the sidebar for ranked lists and consensus gauges."
)

if not SCORING_AVAILABLE:
    st.error("content_scoring.py not found. Cannot score responses.")
    st.stop()

# ── Subgroup selection — session_state drives data load, multiselect lives above chart ──
# Default to Republicans on first load; multiselect widget (in scatter view) updates this
if "il_subgroups" not in st.session_state:
    st.session_state["il_subgroups"] = ["Republicans"]
_sel = st.session_state.get("il_subgroups") or ["Republicans"]
_primary_key = DEMO_SUBGROUPS.get(_sel[0], "r")

# Load and aggregate using primary (first selected) subgroup
question_data = load_question_data(mode=data_mode, subgroup_key=_primary_key)
topics = aggregate_to_topics(question_data)

if not topics:
    st.warning("No data available.")
    st.stop()

df = pd.DataFrame(topics)
# df_scatter: only rows with subgroup data — used exclusively for the Scatter view
# df_plot: full dataset — used for Gauge, Ranked List, MPT, and Question views
df_scatter = df.dropna(subset=["skeptic_support"])
df_plot = df  # all views except scatter use full data

# ── Sidebar filters ──
with st.sidebar:
    st.markdown("### Filters & View")

    all_tiers = sorted(df["tier"].dropna().unique())
    tier_filter = st.selectbox("Persuasion Tier", ["All Tiers"] + all_tiers, key="il_tier")

    quad_filter = st.multiselect(
        "Category", list(QUAD_COLORS.keys()),
        default=[],
        placeholder="All categories",
        key="il_quad",
    )
    # Empty selection = show all quadrants (cleaner than pre-selecting all tags)
    active_quads = quad_filter if quad_filter else list(QUAD_COLORS.keys())

    view_mode = st.radio("View Type", ["Scatter", "Consensus Gauge", "Ranked List", "MPT View"], key="il_view")

    st.divider()
    st.metric("Topics", f"{len(df_plot)}")
    for q, color in QUAD_COLORS.items():
        ct = len(df_plot[df_plot["quadrant"] == q])
        st.caption(f"● {q}: {ct}")

# Apply filters — scatter uses df_scatter, everything else uses df_plot
if view_mode == "Scatter":
    filtered = df_scatter.copy()
else:
    filtered = df_plot.copy()

if tier_filter != "All Tiers":
    filtered = filtered[filtered["tier"] == tier_filter]
filtered = filtered[filtered["quadrant"].isin(active_quads)]

if filtered.empty:
    if view_mode == "Scatter" and df_scatter.empty:
        _demo_loaded = st.session_state.get("_demo_rows_loaded", -1)
        if _demo_loaded == 0:
            st.warning(
                "**Scatter unavailable: no respondent demographics found.**  \n"
                "The `l1_respondents` table appears to be empty for the CJ surveys.  \n"
                "Run the ingestion pipeline locally:\n\n"
                "```bash\n"
                "cd ~/My\\ Drive/Actionable\\ Intel/01_VIP_Engine/code\n"
                "python unified_pipeline.py --survey-id LA-CJ-2025-002\n"
                "python unified_pipeline.py --survey-id LA-CJ-2025-001\n"
                "```\n\n"
                "Then click **↻ Refresh** to reload."
            )
        else:
            st.info(
                "Subgroup data is still loading — switch to **Consensus Gauge** or **Ranked List** "
                "to view all topics now. The scatter will populate once demographic splits are cached."
            )
    else:
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

    # Sort descending — highest support at top of chart (autorange="reversed" renders first item at top)
    gauge_data = filtered.sort_values("overall_support", ascending=False)

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
                q_df = pd.DataFrame(questions).sort_values("overall_support", ascending=False)
                render_question_cards(q_df, key_prefix="gauge_detail")

    # ══════════════════════════════════════════════════════════════
    # ALL QUESTIONS RANKED (always shown in Consensus Gauge view)
    # ══════════════════════════════════════════════════════════════

    st.divider()
    st.markdown("### All Questions Ranked")
    st.caption(
        "Every individual survey question. Full text on top, support bars below. "
        "Filter by topic or sort to find what you need."
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
                    "tier": topic_row_iter["tier"],
                })

    if all_questions:
        all_q_df = pd.DataFrame(all_questions)

        # Sort and filter controls
        flt_col1, flt_col2, flt_col3 = st.columns(3)
        with flt_col1:
            topic_filter_opts = ["All Topics"] + sorted(all_q_df["topic"].unique().tolist())
            topic_filter_q = st.selectbox("Filter by Topic", topic_filter_opts, key="il_q_topic_filter")
        with flt_col2:
            sort_opts = ["Support % (high to low)", "Support % (low to high)", "Topic A-Z"]
            sort_choice = st.selectbox("Sort By", sort_opts, key="il_q_sort")
        with flt_col3:
            consensus_filter = st.selectbox("Consensus Level", [
                "All Levels", "Strong (75%+)", "Moderate (55-74%)", "Contested (below 55%)"
            ], key="il_q_consensus")

        # Apply filters
        display_q = all_q_df.copy()
        if topic_filter_q != "All Topics":
            display_q = display_q[display_q["topic"] == topic_filter_q]
        if consensus_filter == "Strong (75%+)":
            display_q = display_q[display_q["overall_support"] >= 75]
        elif consensus_filter == "Moderate (55-74%)":
            display_q = display_q[(display_q["overall_support"] >= 55) & (display_q["overall_support"] < 75)]
        elif consensus_filter == "Contested (below 55%)":
            display_q = display_q[display_q["overall_support"] < 55]

        # Apply sort
        if sort_choice == "Support % (high to low)":
            display_q = display_q.sort_values("overall_support", ascending=False)
        elif sort_choice == "Support % (low to high)":
            display_q = display_q.sort_values("overall_support", ascending=True)
        else:
            display_q = display_q.sort_values(["topic", "overall_support"], ascending=[True, False])

        st.caption(f"Showing {len(display_q)} of {len(all_q_df)} questions")
        render_question_cards(display_q.head(50), key_prefix="gauge_all")


# ══════════════════════════════════════════════════════════════════
# SCATTER VIEW (SECONDARY)
# ══════════════════════════════════════════════════════════════════

elif view_mode == "Scatter":
    # ── Inline multiselect — directly above chart ──
    sel_labels = st.multiselect(
        "Compare support among:",
        list(DEMO_SUBGROUPS.keys()),
        key="il_subgroups",
        placeholder="Choose one or more groups...",
        help=(
            "Pick any group to set the X axis. "
            "**Select multiple** to see the intersection — e.g. Republicans + Women "
            "shows support among respondents who are both."
        ),
    )
    if not sel_labels:
        sel_labels = ["Republicans"]
        st.session_state["il_subgroups"] = sel_labels
    sel_keys = [DEMO_SUBGROUPS[l] for l in sel_labels]
    subgroup_label = " × ".join(sel_labels)

    # ── Multi-group intersection: patch filtered df ──
    if len(sel_keys) > 1 and DEMO_SPLITS_AVAILABLE:
        try:
            _demo_raw, _scored = load_respondent_level_data()
            _inter_q = compute_intersection_support(_demo_raw, _scored, sel_keys)
            # Re-compute topic-level skeptic_support from per-QID intersection rates
            filtered = filtered.copy()
            _new_sk = []
            for _, _row in filtered.iterrows():
                _qids = [q["qid"] for q in (_row.get("questions") or [])]
                _rates = [_inter_q[q] for q in _qids if q in _inter_q and _inter_q[q] is not None]
                _new_sk.append(float(np.mean(_rates)) if _rates else None)
            filtered["skeptic_support"] = _new_sk
            # Re-assign quadrants (intersection changes who's where)
            def _assign_quad(r):
                sk, ov = r["skeptic_support"], r["overall_support"]
                if sk is None: return "Low Support"
                if ov >= 60 and sk >= 60: return "Golden Zone"
                if ov >= 60: return "Base Only"
                if sk >= 60: return "Persuasion Target"
                return "Low Support"
            filtered["quadrant"] = filtered.apply(_assign_quad, axis=1)
            filtered = filtered[filtered["quadrant"].isin(active_quads)]
        except Exception:
            pass  # Fall back to primary single-group data on any error
    elif len(sel_keys) == 1 and sel_keys[0] != _primary_key:
        # Single group changed — trigger reload on next render
        st.session_state["il_subgroups"] = sel_labels
        st.rerun()

    # Drop rows that have no subgroup data after intersection
    filtered = filtered.dropna(subset=["skeptic_support"])
    if filtered.empty:
        st.info(
            f"No topics have enough data for **{subgroup_label}** "
            f"({len(sel_labels)}-way intersection may be too narrow). "
            "Try fewer or broader groups."
        )
        st.stop()

    st.markdown("## Scatter Plot")
    st.caption(
        f"Each dot is a reform topic. "
        f"Horizontal = support among **{subgroup_label}**. "
        f"Vertical = overall public support. Hover over dots for details. "
        f"The Golden Zone (upper right) has broad support from both this group and the public overall."
    )

    # Dynamic axis range
    x_min = max(0, filtered["skeptic_support"].min() - 8)
    x_max = min(100, filtered["skeptic_support"].max() + 5)
    y_min = max(0, filtered["overall_support"].min() - 8)
    y_max = min(100, filtered["overall_support"].max() + 5)

    quad_x, quad_y = 60, 60

    x_axis_label = f"{subgroup_label} Support %"

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
            "skeptic_support": x_axis_label,
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

    fig.add_annotation(x=label_left_x, y=label_top_y, text="Overall Only", showarrow=False,
                       font=dict(color="#1155AA", size=11), opacity=0.6)
    fig.add_annotation(x=label_right_x, y=label_top_y, text="Golden Zone", showarrow=False,
                       font=dict(color="#1B6B3A", size=13, family="Playfair Display"), opacity=0.85)
    fig.add_annotation(x=label_left_x, y=label_bot_y, text="Low Support", showarrow=False,
                       font=dict(color="#8B1A1A", size=11), opacity=0.6)
    fig.add_annotation(x=label_right_x, y=label_bot_y, text=f"Strong {subgroup_label}", showarrow=False,
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
            c2.metric(f"{subgroup_label} Support", f"{topic_row['skeptic_support']:.0f}%" if topic_row['skeptic_support'] is not None else "—")
            c3.metric("Category", topic_row["quadrant"])
            c4.metric("Persuasion Tier", topic_row["tier"] if topic_row["tier"] else "—")

            # Individual questions
            questions = topic_row["questions"]
            if questions and len(questions) > 0:
                st.markdown(
                    f'<div style="font-size:0.9rem;color:{TEXT2};margin:0.5rem 0;">'
                    f'<strong>{len(questions)} survey questions</strong> in this topic</div>',
                    unsafe_allow_html=True,
                )
                q_df = pd.DataFrame(questions).sort_values("overall_support", ascending=False)
                render_question_cards(q_df, key_prefix="scatter_detail")

    # ══════════════════════════════════════════════════════════════
    # ALL QUESTIONS RANKED (always shown below scatter)
    # ══════════════════════════════════════════════════════════════

    st.divider()
    st.markdown("#### All Questions Ranked")
    st.caption(
        "Every individual survey question. Full text on top, support bars below. "
        "Filter by topic or sort to find what you need."
    )

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
                    "tier": topic_row_iter["tier"],
                })

    if all_questions:
        all_q_df = pd.DataFrame(all_questions)

        flt_c1, flt_c2, flt_c3 = st.columns(3)
        with flt_c1:
            t_opts = ["All Topics"] + sorted(all_q_df["topic"].unique().tolist())
            t_filt = st.selectbox("Filter by Topic", t_opts, key="il_sq_topic")
        with flt_c2:
            s_opts = ["Support % (high to low)", "Support % (low to high)", "Topic A-Z"]
            s_choice = st.selectbox("Sort By", s_opts, key="il_sq_sort")
        with flt_c3:
            c_filt = st.selectbox("Consensus Level", [
                "All Levels", "Strong (75%+)", "Moderate (55-74%)", "Contested (below 55%)"
            ], key="il_sq_consensus")

        dq = all_q_df.copy()
        if t_filt != "All Topics":
            dq = dq[dq["topic"] == t_filt]
        if c_filt == "Strong (75%+)":
            dq = dq[dq["overall_support"] >= 75]
        elif c_filt == "Moderate (55-74%)":
            dq = dq[(dq["overall_support"] >= 55) & (dq["overall_support"] < 75)]
        elif c_filt == "Contested (below 55%)":
            dq = dq[dq["overall_support"] < 55]

        if s_choice == "Support % (high to low)":
            dq = dq.sort_values("overall_support", ascending=False)
        elif s_choice == "Support % (low to high)":
            dq = dq.sort_values("overall_support", ascending=True)
        else:
            dq = dq.sort_values(["topic", "overall_support"], ascending=[True, False])

        st.caption(f"Showing {len(dq)} of {len(all_q_df)} questions")
        render_question_cards(dq.head(50), key_prefix="scatter_all")


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


# ══════════════════════════════════════════════════════════════════
# MPT VIEW — MrP Reach × Universality scatter
# ══════════════════════════════════════════════════════════════════

elif view_mode == "MPT View":
    st.markdown("## MPT Scatter — Reach × Universality")
    st.caption(
        "**Reach** = MrP-adjusted overall support across all surveyed states. "
        "**Universality** = cross-state consistency (100 − std dev of state-level rates). "
        "Topics in the upper-right hold up everywhere and have broad support — the safest message investment."
    )

    mpt_records = load_mpt_scatter_data()

    if not mpt_records:
        st.warning("MPT scatter requires MrP data from at least 2 states. Run the MrP pipeline for additional state surveys first.")
        st.stop()

    mpt_df = pd.DataFrame(mpt_records)

    # Apply tier filter (reuse sidebar selection)
    if tier_filter != "All Tiers":
        mpt_df = mpt_df[mpt_df["tier"] == tier_filter]

    if mpt_df.empty:
        st.warning("No topics match the current tier filter.")
        st.stop()

    # ── KPI row ──
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Topics Plotted", f"{len(mpt_df)}")
    c2.metric("Avg Reach", f"{mpt_df['reach'].mean():.0f}%")
    c3.metric("Avg Universality", f"{mpt_df['universality'].mean():.0f}")
    c4.metric("States Covered", f"{mpt_df['n_states'].max()}")

    # ── Quadrant thresholds ──
    reach_thresh = 60.0
    univ_thresh = mpt_df["universality"].median()  # data-driven midpoint

    MPT_QUAD_COLORS = {
        "Universal Consensus": "#1B6B3A",    # High Reach + High Universality
        "Fragmented Consensus": "#1155AA",   # High Reach + Low Universality
        "Consistent Niche": "#B85400",       # Low Reach + High Universality
        "Volatile / Niche": "#8B1A1A",       # Low Reach + Low Universality
    }

    def mpt_quadrant(row):
        hi_reach = row["reach"] >= reach_thresh
        hi_univ  = row["universality"] >= univ_thresh
        if hi_reach and hi_univ:
            return "Universal Consensus"
        elif hi_reach and not hi_univ:
            return "Fragmented Consensus"
        elif not hi_reach and hi_univ:
            return "Consistent Niche"
        else:
            return "Volatile / Niche"

    mpt_df = mpt_df.copy()
    mpt_df["quadrant"] = mpt_df.apply(mpt_quadrant, axis=1)

    # ── Regression line ──
    x_vals = mpt_df["reach"].values
    y_vals = mpt_df["universality"].values
    try:
        coef = np.polyfit(x_vals, y_vals, 1)
        x_reg = np.linspace(x_vals.min() - 2, x_vals.max() + 2, 100)
        y_reg = np.polyval(coef, x_reg)
        r_sq = np.corrcoef(x_vals, y_vals)[0, 1] ** 2
        show_regression = True
    except Exception:
        show_regression = False
        r_sq = None

    # ── Build hover text (include per-state breakdown) ──
    hover_texts = []
    for _, row in mpt_df.iterrows():
        breakdown = "<br>".join(
            f"  {s}: {v}%" for s, v in row["state_breakdown"].items()
        )
        hover_texts.append(
            f"<b>{row['topic']}</b><br>"
            f"Reach: {row['reach']:.1f}%<br>"
            f"Universality: {row['universality']:.1f}<br>"
            f"Tier: {row['tier'] or '—'}<br>"
            f"States ({row['n_states']}):<br>{breakdown}"
            f"<extra></extra>"
        )

    fig_mpt = px.scatter(
        mpt_df,
        x="reach", y="universality",
        color="quadrant",
        color_discrete_map=MPT_QUAD_COLORS,
        size="n_states",
        size_max=20,
        opacity=0.88,
        text="topic",
        labels={
            "reach": "MrP Reach %",
            "universality": "MrP Universality",
            "quadrant": "Quadrant",
        },
        custom_data=["topic", "tier", "n_states"],
    )
    fig_mpt.update_traces(
        textposition="top center",
        textfont=dict(size=9, family="DM Sans", color="#1E3A5F"),
    )

    # Override hover to use our custom text
    for i, trace in enumerate(fig_mpt.data):
        quad_name = trace.name
        mask = mpt_df["quadrant"] == quad_name
        trace.hovertemplate = [
            hover_texts[j] for j in mpt_df.index[mask].tolist()
        ]

    # Regression overlay
    if show_regression:
        fig_mpt.add_trace(go.Scatter(
            x=x_reg, y=y_reg,
            mode="lines",
            line=dict(color="#9CA3AF", width=1.5, dash="dot"),
            showlegend=True,
            name=f"Regression (R²={r_sq:.2f})",
            hoverinfo="skip",
        ))

    # Quadrant dividers
    x_min = max(0, x_vals.min() - 5)
    x_max = min(100, x_vals.max() + 5)
    y_min_plot = max(0, y_vals.min() - 3)
    y_max_plot = min(100, y_vals.max() + 3)

    fig_mpt.add_hline(y=univ_thresh, line_dash="dash", line_color="#D4D0C8", line_width=1)
    if reach_thresh >= x_min and reach_thresh <= x_max:
        fig_mpt.add_vline(x=reach_thresh, line_dash="dash", line_color="#D4D0C8", line_width=1)

    # Quadrant annotations
    lx = max(x_min + 1, (x_min + reach_thresh) / 2)
    rx = min(x_max - 1, (reach_thresh + x_max) / 2)
    ty = min(y_max_plot - 0.5, y_max_plot - 1)
    by = max(y_min_plot + 0.5, y_min_plot + 1)
    fig_mpt.add_annotation(x=lx, y=ty, text="Consistent Niche",      showarrow=False, font=dict(color="#B85400", size=10), opacity=0.65)
    fig_mpt.add_annotation(x=rx, y=ty, text="Universal Consensus",   showarrow=False, font=dict(color="#1B6B3A", size=12, family="Playfair Display"), opacity=0.85)
    fig_mpt.add_annotation(x=lx, y=by, text="Volatile / Niche",      showarrow=False, font=dict(color="#8B1A1A", size=10), opacity=0.65)
    fig_mpt.add_annotation(x=rx, y=by, text="Fragmented Consensus",  showarrow=False, font=dict(color="#1155AA", size=10), opacity=0.65)

    fig_mpt.update_layout(
        template="plotly_white",
        paper_bgcolor=BG,
        plot_bgcolor=CARD_BG,
        height=640,
        margin=dict(l=60, r=20, t=50, b=60),
        xaxis=dict(
            range=[x_min, x_max], dtick=10, gridcolor="#E8E4DC",
            title="MrP Reach % (overall population support)",
            title_font=dict(color=NAVY, size=12),
        ),
        yaxis=dict(
            range=[y_min_plot, y_max_plot], gridcolor="#E8E4DC",
            title="MrP Universality (100 − cross-state std dev)",
            title_font=dict(color=NAVY, size=12),
        ),
        legend=dict(
            font=dict(size=10, color=NAVY),
            bgcolor="rgba(250,249,246,0.9)",
            bordercolor=BORDER2, borderwidth=1,
        ),
        font=dict(family="DM Sans", color=NAVY),
        title=dict(
            text=f"MrP Reach × Universality · {len(mpt_df)} topics across {mpt_df['n_states'].max()} states",
            font=dict(size=13, color=NAVY),
            x=0.01,
        ),
    )

    st.plotly_chart(fig_mpt, use_container_width=True, key="il_mpt_scatter")

    # ── Interpretation box ──
    if show_regression and r_sq is not None:
        slope_dir = "positively" if coef[0] > 0 else "negatively"
        st.markdown(f"""
        <div style="background:{CARD_BG};border:1px solid {BORDER2};border-left:4px solid {GOLD};
            border-radius:8px;padding:1rem 1.25rem;margin-top:0.5rem;font-size:0.85rem;color:{TEXT2};">
            <strong style="color:{NAVY};">Regression read:</strong>
            Reach and Universality are <strong>{slope_dir} correlated</strong>
            (R²={r_sq:.2f}). The universality threshold (dashed horizontal) is set at the median
            ({univ_thresh:.1f}) across plotted topics.
            Universality = 100 − std dev, so 90+ means &lt;10pp spread across states.
        </div>
        """, unsafe_allow_html=True)

    # ── Per-topic state breakdown table ──
    st.divider()
    st.markdown("#### State-Level Detail")
    st.caption("Select a topic to see its per-state MrP support rates.")

    topic_opts_mpt = sorted(mpt_df["topic"].tolist())
    sel_mpt = st.selectbox("Topic", ["(select a topic)"] + topic_opts_mpt, key="il_mpt_topic")
    if sel_mpt != "(select a topic)":
        sel_row = mpt_df[mpt_df["topic"] == sel_mpt].iloc[0]
        c1, c2, c3 = st.columns(3)
        c1.metric("Reach", f"{sel_row['reach']:.1f}%")
        c2.metric("Universality", f"{sel_row['universality']:.1f}")
        c3.metric("Tier", sel_row["tier"] or "—")

        # Per-state bars
        for state_name, pct in sel_row["state_breakdown"].items():
            color = STATE_COLORS.get(state_name, NAVY)
            st.markdown(
                f'<div style="display:flex;align-items:center;gap:10px;margin-bottom:6px;">'
                f'<div style="width:120px;font-size:0.82rem;color:{TEXT2};text-align:right;">{state_name}</div>'
                f'<div style="flex:1;height:18px;background:{BORDER2};border-radius:4px;overflow:hidden;">'
                f'<div style="width:{min(pct,100):.0f}%;height:100%;background:{color};border-radius:4px;"></div>'
                f'</div>'
                f'<div style="width:44px;font-size:0.85rem;font-weight:600;color:{color};">{pct:.0f}%</div>'
                f'</div>',
                unsafe_allow_html=True,
            )


portal_footer()
