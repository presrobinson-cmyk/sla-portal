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
from chat_widget import render_chat

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

# Assign each active state a unique color index for distinct coloring
active_state_list = sorted(stats["states_live"])
state_color_idx = {STATE_ABBR.get(s, s[:2]): i + 1 for i, s in enumerate(active_state_list)}
n_active = len(active_state_list)

z_vals = []
hover_texts = []
for abbr in ALL_US_STATES:
    if abbr in active_abbrs:
        full = ABBR_TO_STATE.get(abbr, abbr)
        n = stats["state_counts"].get(full, 0)
        z_vals.append(state_color_idx.get(abbr, 1))
        hover_texts.append(f"<b>{full}</b><br>{n:,} respondents<br><i>Click below to view report</i>")
    else:
        z_vals.append(0)
        hover_texts.append(f"{abbr}")

# Build a colorscale with distinct colors per active state
# Index 0 = inactive (light grey), then one color per active state
_distinct_colors = ["#E8E4DC"]  # index 0 = inactive
for s in active_state_list:
    _distinct_colors.append(STATE_COLORS.get(s, NAVY))

# Build Plotly colorscale as normalized [position, color] pairs
if n_active > 0:
    _cscale = [[0, "#E8E4DC"]]
    for i, color in enumerate(_distinct_colors[1:], 1):
        pos = i / n_active
        prev_pos = (i - 1) / n_active + 0.001 if i > 1 else 0.001
        _cscale.append([prev_pos, color])
        _cscale.append([pos, color])
    # Ensure we end at 1.0
    if _cscale[-1][0] != 1.0:
        _cscale[-1][0] = 1.0
else:
    _cscale = [[0, "#E8E4DC"], [1, "#E8E4DC"]]

fig_map = go.Figure(data=go.Choropleth(
    locations=ALL_US_STATES,
    z=z_vals,
    locationmode="USA-states",
    colorscale=_cscale,
    zmin=0,
    zmax=n_active if n_active > 0 else 1,
    showscale=False,
    hovertext=hover_texts,
    hoverinfo="text",
    marker_line_color="white",
    marker_line_width=1.5,
    selectedpoints=[],
))
fig_map.update_layout(
    geo=dict(scope="usa", bgcolor="rgba(0,0,0,0)", lakecolor="rgba(0,0,0,0)",
             landcolor="#F5F3EF", showlakes=False),
    margin=dict(l=0, r=0, t=0, b=0),
    height=420,
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    dragmode=False,
)

# Render map with click detection — disable zoom/scroll/pan
map_event = st.plotly_chart(
    fig_map, use_container_width=True, key="us_map",
    on_select="rerun", selection_mode=["points"],
    config={
        "scrollZoom": False,
        "doubleClick": False,
        "displayModeBar": False,
    },
)

# Handle map click → navigate to state report
if map_event and map_event.selection and map_event.selection.points:
    clicked_pt = map_event.selection.points[0]
    clicked_idx = clicked_pt.get("point_index", -1)
    if 0 <= clicked_idx < len(ALL_US_STATES):
        clicked_abbr = ALL_US_STATES[clicked_idx]
        if clicked_abbr in active_abbrs:
            st.session_state["selected_state"] = clicked_abbr
            st.switch_page("pages/8_State_Report.py")
        else:
            st.toast(f"{clicked_abbr} — no survey data yet")

st.markdown(f"<div style='text-align:center;font-size:0.8rem;color:{TEXT3};margin-top:-0.5rem;'>Click any highlighted state to view its report</div>", unsafe_allow_html=True)

st.divider()

# ── Navigation Grid — clickable cards ──
# Streamlit buttons styled as cards via injected CSS.
# Each card IS the button — no separate link below.

st.markdown("### Quick Access")

# Inject CSS to make buttons look like cards
st.markdown(f"""
<style>
div[data-testid="stVerticalBlock"] div[data-testid="stButton"] > button.nav-card-btn {{
    background: {CARD_BG};
    border: 1px solid {BORDER2};
    border-radius: 10px;
    padding: 1.25rem;
    min-height: 160px;
    text-align: left;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    transition: border-color 0.2s, box-shadow 0.2s;
    display: flex;
    flex-direction: column;
    justify-content: flex-start;
    cursor: pointer;
}}
div[data-testid="stVerticalBlock"] div[data-testid="stButton"] > button.nav-card-btn:hover {{
    border-color: {GOLD};
    box-shadow: 0 2px 8px rgba(212,168,67,0.2);
}}
</style>
""", unsafe_allow_html=True)

nav_items = [
    {
        "title": "Issue Landscape",
        "icon": "⚡",
        "description": "Which issues have the broadest support and strongest cross-party appeal. Find Golden Zone winners.",
        "page": "pages/1_Issue_Landscape.py",
    },
    {
        "title": "Voter Segments",
        "icon": "🎯",
        "description": "How different voter groups respond to each issue. Party, age, race, and education breakdowns.",
        "page": "pages/2_Voter_Segments.py",
    },
    {
        "title": "Persuasion Pathways",
        "icon": "🧩",
        "description": "Which issues open the door to persuasion, which build coalitions, and which close the deal.",
        "page": "pages/3_Persuasion_Pathways.py",
    },
    {
        "title": "Cross-State",
        "icon": "🗺️",
        "description": "Compare support levels across states. See which messages transfer and need local adaptation.",
        "page": "pages/4_Cross_State.py",
    },
    {
        "title": "MediaMaker",
        "icon": "📢",
        "description": "Golden Zone issue → audience targeting specs + AI-generated message scripts.",
        "page": "pages/5_MediaMaker.py",
    },
    {
        "title": "SurveyMaker",
        "icon": "✏️",
        "description": "Question bank, AI rewriter with Actionable Intel methodology, survey assembly and export.",
        "page": "pages/6_SurveyMaker.py",
    },
]

# Render cards in 3-column grid — the button IS the card
row1 = st.columns(3)
row2 = st.columns(3)
all_cols = row1 + row2

for idx, item in enumerate(nav_items):
    with all_cols[idx]:
        if st.button(
            f"{item['icon']}  **{item['title']}**\n\n{item['description']}",
            key=f"nav_{idx}",
            use_container_width=True,
        ):
            st.switch_page(item["page"])

# ── Footer ──
portal_footer()
