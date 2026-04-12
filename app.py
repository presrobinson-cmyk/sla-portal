"""
SLA Portal — Second Look Alliance
Criminal Justice Reform Intelligence Portal
Main entry point / home page
Navy/Gold/Serif design · Live Supabase data
"""

import streamlit as st
from pathlib import Path
import sys
import requests

# Auth + Theme
sys.path.insert(0, str(Path(__file__).parent))
from auth import require_auth
from theme import (
    apply_theme, portal_header, portal_footer, state_pills_html,
    get_supabase_config, get_supabase_headers, CJ_SURVEYS, SURVEY_STATE,
    STATE_COLORS, STATE_ABBR, NAVY, GOLD, GOLD_MID, TEXT3, BORDER2,
)

st.set_page_config(
    page_title="SLA Portal",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded",
)

apply_theme()
username = require_auth("Second Look Alliance", accent_color=GOLD)


# ── Live data counts ──
@st.cache_data(ttl=3600, show_spinner=False)
def get_portal_stats():
    """Get high-level counts from Supabase for the header."""
    url, _ = get_supabase_config()
    headers = get_supabase_headers()

    state_counts = {}
    total_respondents = 0
    states_live = []
    states_pending = []

    for sid in CJ_SURVEYS:
        try:
            r = requests.get(
                f"{url}/rest/v1/l1_respondents?select=respondent_id&survey_id=eq.{sid}&limit=1",
                headers={**headers, "Prefer": "count=exact", "Range": "0-0"},
                timeout=15,
            )
            count = int(r.headers.get("Content-Range", "0/0").split("/")[1])
            state_name = SURVEY_STATE.get(sid, "Unknown")
            if count > 0:
                if state_name not in state_counts:
                    state_counts[state_name] = 0
                state_counts[state_name] += count
                if state_name not in states_live:
                    states_live.append(state_name)
            else:
                if state_name not in states_live and state_name not in states_pending:
                    states_pending.append(state_name)
        except Exception:
            pass

    total_respondents = sum(state_counts.values())

    # Count scored questions
    try:
        r = requests.get(
            f"{url}/rest/v1/l2_responses?select=question_id&bh_score=not.is.null&limit=1",
            headers={**headers, "Prefer": "count=exact", "Range": "0-0"},
            timeout=15,
        )
        n_scored = int(r.headers.get("Content-Range", "0/0").split("/")[1])
    except Exception:
        n_scored = 0

    return {
        "total_respondents": total_respondents,
        "states_live": sorted(states_live),
        "states_pending": sorted(states_pending),
        "state_counts": state_counts,
        "n_scored": n_scored,
    }


stats = get_portal_stats()

# ── Portal Header ──
portal_header(
    n_respondents=stats["total_respondents"],
    n_states=len(stats["states_live"]),
    n_questions=stats["n_scored"],
)

# ── State pills ──
st.markdown(
    state_pills_html(stats["states_live"], stats["states_pending"]),
    unsafe_allow_html=True,
)
st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)

# ── Quick stats row ──
cols = st.columns(4)
with cols[0]:
    st.metric("Total Respondents", f"{stats['total_respondents']:,}")
with cols[1]:
    st.metric("States Active", str(len(stats["states_live"])))
with cols[2]:
    st.metric("Scored Responses", f"{stats['n_scored']:,}")
with cols[3]:
    # Show pending if any
    pending = len(stats["states_pending"])
    st.metric("States Pending", str(pending) if pending > 0 else "0")

st.divider()

# ── Navigation Grid ──
st.markdown("### Quick Access")

nav_items = [
    {
        "title": "Message Persuasion Testing",
        "icon": "⚡",
        "description": "MrP Reach × Universality scatter. Golden Zone issues, quadrant analysis, cross-state transfer ratings.",
        "page": "pages/1_Survey_Results.py",
    },
    {
        "title": "VIP Scores",
        "icon": "🎯",
        "description": "Disposition scoring, construct-level favorability, Q1–Q5 quintile breakdowns, persuasion tier assignments.",
        "page": "pages/2_VIP_Scores.py",
    },
    {
        "title": "Persuasion Architecture",
        "icon": "🧩",
        "description": "Entry → Bridge → Downstream tiers, voter archetypes, persuasion pathways, cross-state construct stability.",
        "page": "pages/3_MrP_Estimates.py",
    },
    {
        "title": "Cross-State",
        "icon": "🗺️",
        "description": "State comparison cards, Golden Zone counts, top issues, transfer analysis across all active states.",
        "page": "pages/4_Media_Portal.py",
    },
    {
        "title": "MediaMaker",
        "icon": "📢",
        "description": "Golden Zone issue → audience targeting specs + AI-generated message scripts. Channel recommendations.",
        "page": "pages/5_Survey_Writer.py",
    },
    {
        "title": "SurveyMaker",
        "icon": "✏️",
        "description": "Question bank, AI rewriter with Actionable Intel methodology, survey assembly and export.",
        "page": "pages/6_AI_Search.py",
    },
]

cols = st.columns(3)
for idx, item in enumerate(nav_items):
    with cols[idx % 3]:
        st.markdown(f"""
        <div class="nav-card">
            <div class="nav-card-icon">{item['icon']}</div>
            <div class="nav-card-title">{item['title']}</div>
            <div class="nav-card-desc">{item['description']}</div>
        </div>
        """, unsafe_allow_html=True)
        st.page_link(item["page"], label=f"Open {item['title']}", icon="➡️")

st.divider()

# ── Data Overview ──
st.markdown("### Data Overview")
col1, col2 = st.columns(2)

with col1:
    st.markdown("**States & Coverage**")
    import pandas as pd
    state_rows = []
    for state in stats["states_live"]:
        n = stats["state_counts"].get(state, 0)
        abbr = STATE_ABBR.get(state, "")
        surveys = len([sid for sid, s in SURVEY_STATE.items() if s == state])
        state_rows.append({"State": state, "Abbr": abbr, "Respondents": n, "Surveys": surveys})
    for state in stats["states_pending"]:
        state_rows.append({"State": state, "Abbr": STATE_ABBR.get(state, ""), "Respondents": 0, "Surveys": 0})
    if state_rows:
        df = pd.DataFrame(state_rows)
        st.dataframe(df, use_container_width=True, hide_index=True)

with col2:
    st.markdown("**Portal Modules**")
    modules = [
        ("Message Persuasion Testing", "MrP Reach × Universality, quadrant classification", "Live"),
        ("VIP Scores", "Disposition scoring, construct favorability, tier assignments", "Live"),
        ("Persuasion Architecture", "Entry → Bridge → Downstream tiers, voter archetypes", "Live"),
        ("Cross-State", "Transfer analysis, state comparison", "Live"),
        ("MediaMaker", "AI-generated scripts, channel targeting", "Coming Soon"),
        ("SurveyMaker", "Question bank, AI rewriter, survey export", "Coming Soon"),
    ]
    for name, desc, status in modules:
        color = "#1B6B3A" if status == "Live" else GOLD if status == "Framework" else TEXT3
        st.markdown(f'<div style="padding:6px 0;border-bottom:1px solid {BORDER2};">'
                    f'<strong style="color:{NAVY};">{name}</strong> '
                    f'<span style="font-size:0.7rem;padding:1px 8px;border-radius:8px;'
                    f'background:{color}18;color:{color};font-weight:500;">{status}</span>'
                    f'<br><span style="font-size:0.82rem;color:{TEXT3};">{desc}</span></div>',
                    unsafe_allow_html=True)

# ── Footer ──
portal_footer()
