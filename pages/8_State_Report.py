"""
State Report — Single-state analysis memo
Pulls live data from Supabase, scores at runtime with content_scoring.py.
Shows respondent overview, persuasion tier breakdown, top questions, and topic performance.
"""

import streamlit as st
from pathlib import Path
import sys
import requests
import pandas as pd
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).parent.parent))
from theme import (
    apply_theme, portal_footer, data_source_badge, get_supabase_config, get_supabase_headers,
    CJ_SURVEYS, SURVEY_STATE, STATE_COLORS, STATE_ABBR, TIER_MAP, TIER_STYLES,
    NAVY, NAVY2, GOLD, GOLD_MID, TEXT1, TEXT2, TEXT3, BORDER2, CARD_BG,
)
from auth import require_auth
from chat_widget import render_chat

# Scoring engine (bundled locally)
try:
    from content_scoring import FAVORABLE_DIRECTION, SKIPPED_QIDS, get_construct, score_content
    SCORING_AVAILABLE = True
except ImportError:
    SCORING_AVAILABLE = False

# Shared data loader (MrP primary, raw fallback)
from data_loader import load_state_question_data, _paginate as paginate_supabase

# Human-readable topic names
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
    "COMPASSION": "Compassionate Release", "CLEMENCY": "Clemency",
    "MENTAL_ADDICTION": "Mental Health & Addiction", "RACIAL_DISPARITIES": "Racial Disparities",
    "GOODTIME": "Good Time Credits", "REVIEW": "Case Review",
    "CONDITIONS": "Prison Conditions", "AGING": "Aging in Prison",
    "PAROLE": "Parole Reform", "REVISIT": "Sentence Revisiting",
    "MAND-DEPART": "Mandatory Departure", "EARLYRELEASE": "Early Release",
    "JURY": "Jury Reform", "DRUGPOSS": "Drug Possession",
    "ECON_DISPARITIES": "Economic Disparities", "ALPR": "License Plate Surveillance",
    "REFORM_LEGITIMACY": "Reform Legitimacy",
}

st.set_page_config(page_title="State Report — SLA Portal", page_icon="📊", layout="wide")
apply_theme()
username = require_auth("Second Look Alliance", accent_color=GOLD)

# Remove default page title — we render our own with the pills
# st.title handled below with pills

SUPABASE_URL, SUPABASE_KEY = get_supabase_config()
HEADERS = get_supabase_headers()

# ─────────────────────────────────────────────────────────────────
# STATE SELECTION
# ─────────────────────────────────────────────────────────────────

ABBR_TO_STATE = {v: k for k, v in STATE_ABBR.items()}
# Sort by full state name alphabetically, then get their abbreviations in that order
all_active_states = sorted(set(s for s in SURVEY_STATE.values() if s in STATE_ABBR))
all_active_abbrs = [STATE_ABBR[s] for s in all_active_states]

if not all_active_abbrs:
    st.warning("No states with data available.")
    st.stop()

selected_abbr = st.session_state.get("selected_state", all_active_abbrs[0])
if selected_abbr not in all_active_abbrs:
    selected_abbr = all_active_abbrs[0]

# ── State pills — alphabetical row of clickable buttons ──
st.markdown(
    f'<div style="font-family:Playfair Display,serif;font-weight:700;color:{NAVY};'
    f'font-size:1.5rem;margin-bottom:0.75rem;">📊 State Report</div>',
    unsafe_allow_html=True,
)

pill_cols = st.columns(len(all_active_abbrs))
for i, abbr in enumerate(all_active_abbrs):
    full_name = ABBR_TO_STATE.get(abbr, abbr)
    with pill_cols[i]:
        is_selected = (abbr == selected_abbr)
        if st.button(
            f"**{abbr}**" if is_selected else abbr,
            key=f"pill_{abbr}",
            use_container_width=True,
            type="primary" if is_selected else "secondary",
            help=full_name,
        ):
            selected_abbr = abbr
            st.session_state["selected_state"] = abbr
            st.rerun()

st.markdown("")  # spacing
data_source_badge("mrp")

state_name = ABBR_TO_STATE.get(selected_abbr, selected_abbr)
state_color = STATE_COLORS.get(state_name, "#8C8984")
state_surveys = [sid for sid in CJ_SURVEYS if SURVEY_STATE.get(sid) == state_name]

if not SCORING_AVAILABLE:
    st.error("Scoring engine not available. Cannot generate state report.")
    st.stop()


# ─────────────────────────────────────────────────────────────────
# DATA LOADING — score at runtime
# ─────────────────────────────────────────────────────────────────

@st.cache_data(ttl=3600, show_spinner="Loading state data...")
def load_state_data(state_survey_ids):
    """Load state data using MrP-adjusted rates (primary), raw fallback.
    Returns respondent_counts, questions, topics.
    """
    # Get respondent counts from L1 (always needed for display)
    respondent_counts = {}
    for sid in state_survey_ids:
        try:
            r = requests.get(
                f"{SUPABASE_URL}/rest/v1/l1_respondents?select=respondent_id&survey_id=eq.{sid}&limit=1",
                headers={**HEADERS, "Prefer": "count=exact", "Range": "0-0"},
                timeout=15,
            )
            respondent_counts[sid] = int(r.headers.get("Content-Range", "0/0").split("/")[1])
        except Exception:
            respondent_counts[sid] = 0

    # Load hybrid MrP + raw question data
    question_data, has_mrp, has_raw = load_state_question_data(
        list(state_survey_ids), state_name=state_name
    )

    # Build question list
    questions = []
    for qid, qd in question_data.items():
        questions.append({
            "qid": qid,
            "construct": qd["construct"],
            "text": qd["question_text"],
            "support_pct": qd["display_pct"],
            "n": qd["n_respondents"],
            "source": qd["source"],
        })

    # Aggregate to construct (topic) level — weighted average
    c_agg = defaultdict(lambda: {"sum_pct_n": 0, "sum_n": 0, "qids": set()})
    for qid, qd in question_data.items():
        c = qd["construct"]
        n = qd["n_respondents"]
        c_agg[c]["sum_pct_n"] += qd["display_pct"] * n
        c_agg[c]["sum_n"] += n
        c_agg[c]["qids"].add(qid)

    topics = []
    for c, cs in c_agg.items():
        if cs["sum_n"] < 10:
            continue
        topics.append({
            "construct": c,
            "support_pct": cs["sum_pct_n"] / cs["sum_n"],
            "n_questions": len(cs["qids"]),
            "n_responses": cs["sum_n"],
        })

    return respondent_counts, questions, topics


with st.spinner("Loading state data..."):
    respondent_counts, questions, topics = load_state_data(tuple(state_surveys))

total_respondents = sum(respondent_counts.values())

# ─────────────────────────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────────────────────────

st.markdown(f"""
<div style="display:flex;align-items:center;gap:16px;margin-bottom:1rem;">
    <div style="font-size:3rem;font-weight:800;color:{state_color};">{selected_abbr}</div>
    <div>
        <div style="font-size:1.8rem;font-weight:700;color:{NAVY};font-family:'Playfair Display',serif;">{state_name}</div>
        <div style="font-size:0.9rem;color:{TEXT3};">
            {len(state_surveys)} survey{'s' if len(state_surveys) != 1 else ''} ·
            {total_respondents:,} respondents ·
            {len(questions)} scored questions
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

st.divider()

# ─────────────────────────────────────────────────────────────────
# OVERVIEW METRICS
# ─────────────────────────────────────────────────────────────────

cols = st.columns(4)

strong_items = sum(1 for q in questions if q["support_pct"] >= 65)
constructs_found = set(q["construct"] for q in questions)

with cols[0]:
    st.metric("Respondents", f"{total_respondents:,}")
with cols[1]:
    st.metric("Strong Support Items", str(strong_items))
with cols[2]:
    st.metric("Topics Covered", str(len(constructs_found)))
with cols[3]:
    st.metric("Surveys", str(len(state_surveys)))

st.divider()

# ─────────────────────────────────────────────────────────────────
# PERSUASION TIER BREAKDOWN
# ─────────────────────────────────────────────────────────────────

st.subheader("Persuasion Tier Breakdown")
st.markdown(
    f"<div style='font-size:0.9rem;color:{TEXT3};margin-bottom:1rem;'>"
    "How this state's topics distribute across the persuasion architecture.</div>",
    unsafe_allow_html=True,
)

# Group topics by tier with average support
tier_data = defaultdict(lambda: {"constructs": [], "support_sum": 0, "n": 0})
for t in topics:
    tier = TIER_MAP.get(t["construct"], "Unassigned")
    tier_data[tier]["constructs"].append(t["construct"])
    tier_data[tier]["support_sum"] += t["support_pct"] * t["n_responses"]
    tier_data[tier]["n"] += t["n_responses"]

tier_order = ["Entry", "Entry (VA)", "Bridge", "Downstream", "Destination", "Gauge"]

for tier in tier_order:
    if tier not in tier_data:
        continue
    td = tier_data[tier]
    style = TIER_STYLES.get(tier, {"bg": "rgba(140,137,132,0.1)", "color": TEXT3, "border": TEXT3})
    avg_support = td["support_sum"] / td["n"] if td["n"] > 0 else 0

    construct_tags = " ".join(
        f'<span style="background:{style["bg"]};color:{style["color"]};padding:2px 8px;'
        f'border-radius:6px;font-size:0.75rem;font-weight:500;margin-right:4px;">'
        f'{CONSTRUCT_LABELS.get(c, c)}</span>'
        for c in sorted(td["constructs"])
    )

    st.markdown(f"""
    <div style="background:{CARD_BG};border-left:4px solid {style['border']};border-radius:0 8px 8px 0;
         padding:1rem 1.25rem;margin-bottom:0.75rem;box-shadow:0 1px 3px rgba(0,0,0,0.04);">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:0.5rem;">
            <div style="font-weight:700;color:{style['color']};font-size:1rem;">{tier}</div>
            <div style="font-size:0.8rem;color:{TEXT3};">{len(td['constructs'])} topics · avg support {avg_support:.0f}%</div>
        </div>
        <div>{construct_tags}</div>
    </div>
    """, unsafe_allow_html=True)

st.divider()

# ─────────────────────────────────────────────────────────────────
# TOP QUESTIONS
# ─────────────────────────────────────────────────────────────────

st.subheader("Top-Scoring Questions")
st.markdown(
    f"<div style='font-size:0.9rem;color:{TEXT3};margin-bottom:1rem;'>"
    "Ranked by support rate. Items with 65%+ support highlighted as strong performers.</div>",
    unsafe_allow_html=True,
)

sorted_questions = sorted(questions, key=lambda q: q["support_pct"], reverse=True)

for rank, q in enumerate(sorted_questions[:15], 1):
    construct_label = CONSTRUCT_LABELS.get(q["construct"], q["construct"])
    tier = TIER_MAP.get(q["construct"], "—")
    is_strong = q["support_pct"] >= 65
    bar_color = "#1B6B3A" if is_strong else state_color
    badge = (
        '<span style="background:#1B6B3A;color:white;padding:1px 6px;border-radius:4px;'
        'font-size:0.65rem;font-weight:600;margin-left:6px;">STRONG</span>'
        if is_strong else ""
    )
    display_text = q["text"][:120] + "…" if len(q["text"]) > 120 else q["text"]

    st.markdown(f"""
    <div style="background:{CARD_BG};border:1px solid {BORDER2};border-radius:8px;
         padding:1rem;margin-bottom:0.5rem;box-shadow:0 1px 2px rgba(0,0,0,0.03);">
        <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:0.5rem;">
            <div style="flex:1;">
                <span style="color:{TEXT3};font-size:0.75rem;font-weight:600;">#{rank}</span>
                <span style="color:{NAVY};font-weight:500;font-size:0.88rem;margin-left:6px;">{display_text}</span>
                {badge}
            </div>
            <div style="text-align:right;min-width:80px;">
                <div style="font-weight:700;color:{bar_color};font-size:1.1rem;">{q['support_pct']:.0f}%</div>
            </div>
        </div>
        <div style="width:100%;height:6px;background:{BORDER2};border-radius:3px;overflow:hidden;margin-bottom:0.4rem;">
            <div style="width:{min(q['support_pct'], 100):.0f}%;height:100%;background:{bar_color};border-radius:3px;"></div>
        </div>
        <div style="font-size:0.78rem;color:{TEXT3};">
            {construct_label} · {tier} · {q['n']:,} responses
        </div>
    </div>
    """, unsafe_allow_html=True)

st.divider()

# ─────────────────────────────────────────────────────────────────
# TOPIC PERFORMANCE TABLE
# ─────────────────────────────────────────────────────────────────

st.subheader("Topic Performance")
st.markdown(
    f"<div style='font-size:0.9rem;color:{TEXT3};margin-bottom:1rem;'>"
    "Average support by topic across all surveys in this state.</div>",
    unsafe_allow_html=True,
)

if topics:
    rows = []
    for t in sorted(topics, key=lambda x: x["support_pct"], reverse=True):
        rows.append({
            "Topic": CONSTRUCT_LABELS.get(t["construct"], t["construct"]),
            "Tier": TIER_MAP.get(t["construct"], "—"),
            "Questions": t["n_questions"],
            "Support": f"{t['support_pct']:.0f}%",
            "Responses": f"{t['n_responses']:,}",
        })
    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True, hide_index=True)
else:
    st.info("No scored topic data available for this state.")

st.divider()

# ─────────────────────────────────────────────────────────────────
# SURVEY BREAKDOWN
# ─────────────────────────────────────────────────────────────────

st.subheader("Survey Breakdown")

for sid in state_surveys:
    n = respondent_counts.get(sid, 0)
    st.markdown(f"""
    <div style="background:{CARD_BG};border:1px solid {BORDER2};border-radius:8px;
         padding:1rem;margin-bottom:0.5rem;display:flex;justify-content:space-between;align-items:center;">
        <div style="font-weight:600;color:{NAVY};">{sid}</div>
        <div style="font-weight:600;color:{state_color};">{n:,} respondents</div>
    </div>
    """, unsafe_allow_html=True)

# ── Navigation + Chat + Footer ──
st.markdown("")
if st.button("← Back to Home", use_container_width=False):
    st.switch_page("app.py")

portal_footer()
