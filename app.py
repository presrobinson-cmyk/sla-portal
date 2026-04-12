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
    apply_theme, portal_header, portal_footer,
    get_supabase_config, get_supabase_headers, CJ_SURVEYS, SURVEY_STATE,
    STATE_COLORS, STATE_ABBR, NAVY, GOLD, GOLD_MID, TEXT3, BORDER2, CARD_BG,
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

# ── Quick stats row ──
cols = st.columns(4)
with cols[0]:
    st.metric("Total Respondents", f"{stats['total_respondents']:,}")
with cols[1]:
    st.metric("States Active", str(len(stats["states_live"])))
with cols[2]:
    st.metric("Scored Responses", f"{stats['n_scored']:,}")
with cols[3]:
    pending = len(stats["states_pending"])
    st.metric("States Pending", str(pending) if pending > 0 else "0")

# ── US Map ──
import plotly.graph_objects as go

ABBR_TO_STATE = {v: k for k, v in STATE_ABBR.items()}
active_abbrs = [STATE_ABBR[s] for s in stats["states_live"] if s in STATE_ABBR]

ALL_US_STATES = [
    "AL","AK","AZ","AR","CA","CO","CT","DE","FL","GA",
    "HI","ID","IL","IN","IA","KS","KY","LA","ME","MD",
    "MA","MI","MN","MS","MO","MT","NE","NV","NH","NJ",
    "NM","NY","NC","ND","OH","OK","OR","PA","RI","SC",
    "SD","TN","TX","UT","VT","VA","WA","WV","WI","WY","DC",
]

z_vals = []
hover_texts = []
for abbr in ALL_US_STATES:
    if abbr in active_abbrs:
        full = ABBR_TO_STATE.get(abbr, abbr)
        n = stats["state_counts"].get(full, 0)
        z_vals.append(1)
        hover_texts.append(f"<b>{full}</b><br>{n:,} respondents<br><i>Click below to view report</i>")
    else:
        z_vals.append(0)
        hover_texts.append(f"{abbr}")

fig_map = go.Figure(data=go.Choropleth(
    locations=ALL_US_STATES,
    z=z_vals,
    locationmode="USA-states",
    colorscale=[[0, "#E8E4DC"], [0.49, "#E8E4DC"], [0.51, GOLD], [1, GOLD]],
    showscale=False,
    hovertext=hover_texts,
    hoverinfo="text",
    marker_line_color="white",
    marker_line_width=1.5,
))
fig_map.update_layout(
    geo=dict(scope="usa", bgcolor="rgba(0,0,0,0)", lakecolor="rgba(0,0,0,0)",
             landcolor="#F5F3EF", showlakes=False),
    margin=dict(l=0, r=0, t=0, b=0),
    height=380,
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
)
st.plotly_chart(fig_map, use_container_width=True, key="us_map")

# State navigation buttons
st.markdown(f"<div style='text-align:center;margin-bottom:0.5rem;font-size:0.85rem;color:{TEXT3};'>Select a state to view its report:</div>", unsafe_allow_html=True)
state_cols = st.columns(len(active_abbrs) if active_abbrs else 1)
for i, abbr in enumerate(sorted(active_abbrs)):
    full = ABBR_TO_STATE.get(abbr, abbr)
    color = STATE_COLORS.get(full, NAVY)
    with state_cols[i]:
        if st.button(f"{abbr}  —  {full}", key=f"state_{abbr}", use_container_width=True):
            st.session_state["selected_state"] = abbr
            st.switch_page("pages/8_State_Report.py")

st.divider()

# ── Navigation Grid ──
st.markdown("### Quick Access")

nav_items = [
    {
        "title": "Issue Landscape",
        "icon": "⚡",
        "description": "See which issues have the broadest public support and strongest cross-party appeal. Find Golden Zone winners.",
        "page": "pages/1_Survey_Results.py",
    },
    {
        "title": "Voter Segments",
        "icon": "🎯",
        "description": "How different voter groups respond to each issue. Party, age, race, and education breakdowns.",
        "page": "pages/2_VIP_Scores.py",
    },
    {
        "title": "Persuasion Pathways",
        "icon": "🧩",
        "description": "Which issues open the door to persuasion, which build coalitions, and which close the deal.",
        "page": "pages/3_MrP_Estimates.py",
    },
    {
        "title": "Cross-State",
        "icon": "🗺️",
        "description": "Compare support levels across states. See which messages transfer and which need local adaptation.",
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
        <div style="background:{CARD_BG};border:1px solid {BORDER2};border-radius:10px;
             padding:1.25rem;margin-bottom:0.5rem;min-height:140px;
             box-shadow:0 1px 3px rgba(0,0,0,0.04);">
            <div style="font-size:1.8rem;margin-bottom:0.5rem;">{item['icon']}</div>
            <div style="font-weight:700;color:{NAVY};font-size:1rem;margin-bottom:0.4rem;">{item['title']}</div>
            <div style="font-size:0.82rem;color:{TEXT3};line-height:1.45;">{item['description']}</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button(f"Open {item['title']}", key=f"nav_{idx}", use_container_width=True):
            st.switch_page(item["page"])

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
        ("Issue Landscape", "Overall support vs. cross-party appeal for every question", "Live"),
        ("Voter Segments", "How different voter groups respond — by party, age, race", "Live"),
        ("Persuasion Pathways", "Which issues open doors, build coalitions, close deals", "Live"),
        ("Cross-State", "Support comparison across states, message transferability", "Live"),
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
