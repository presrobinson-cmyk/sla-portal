"""
State Report — Single-state analysis memo
Pulls live data from Supabase for the selected state.
Shows respondent overview, persuasion tier breakdown, top questions, and construct performance.
"""

import streamlit as st
from pathlib import Path
import sys
import requests
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent))
from theme import (
    apply_theme, portal_footer, get_supabase_config, get_supabase_headers,
    CJ_SURVEYS, SURVEY_STATE, STATE_COLORS, STATE_ABBR, TIER_MAP, TIER_STYLES,
    NAVY, NAVY2, GOLD, GOLD_MID, TEXT1, TEXT2, TEXT3, BORDER2, CARD_BG,
)
from auth import require_auth

st.set_page_config(
    page_title="State Report — SLA Portal",
    page_icon="📊",
    layout="wide",
)

apply_theme()
username = require_auth("Second Look Alliance", accent_color=GOLD)

# ─────────────────────────────────────────────────────────────────
# STATE SELECTION
# ─────────────────────────────────────────────────────────────────

ABBR_TO_STATE = {v: k for k, v in STATE_ABBR.items()}
all_active_abbrs = sorted(set(STATE_ABBR[s] for s in SURVEY_STATE.values() if s in STATE_ABBR))

# Get selected state — from session state or sidebar selector
selected_abbr = st.session_state.get("selected_state")

# Always show a selector in the sidebar so users can switch states
sidebar_choice = st.sidebar.selectbox(
    "Select State",
    options=all_active_abbrs,
    format_func=lambda a: f"{a} — {ABBR_TO_STATE.get(a, a)}",
    index=all_active_abbrs.index(selected_abbr) if selected_abbr in all_active_abbrs else 0,
    key="state_selector",
)

# Update session state if sidebar changes
if sidebar_choice != selected_abbr:
    selected_abbr = sidebar_choice
    st.session_state["selected_state"] = selected_abbr

if not selected_abbr:
    selected_abbr = all_active_abbrs[0] if all_active_abbrs else None
    st.session_state["selected_state"] = selected_abbr

if not selected_abbr:
    st.warning("No states with data available.")
    st.stop()

state_name = ABBR_TO_STATE.get(selected_abbr, selected_abbr)
state_color = STATE_COLORS.get(state_name, "#8C8984")

# Find surveys for this state
state_surveys = [sid for sid in CJ_SURVEYS if SURVEY_STATE.get(sid) == state_name]

# ─────────────────────────────────────────────────────────────────
# DATA LOADING
# ─────────────────────────────────────────────────────────────────

@st.cache_data(ttl=3600, show_spinner=False)
def load_state_data(state_survey_ids):
    """Load all scored responses for a state's surveys."""
    url, _ = get_supabase_config()
    headers = get_supabase_headers()

    all_respondent_counts = {}
    all_responses = []

    for sid in state_survey_ids:
        # Respondent count
        try:
            r = requests.get(
                f"{url}/rest/v1/l1_respondents?select=respondent_id&survey_id=eq.{sid}&limit=1",
                headers={**headers, "Prefer": "count=exact", "Range": "0-0"},
                timeout=15,
            )
            count = int(r.headers.get("Content-Range", "0/0").split("/")[1])
            all_respondent_counts[sid] = count
        except Exception:
            all_respondent_counts[sid] = 0

        # Scored responses
        try:
            r = requests.get(
                f"{url}/rest/v1/l2_responses",
                headers=headers,
                params={
                    "survey_id": f"eq.{sid}",
                    "select": "question_id,question_text,construct,bh_score,cb_score,dual_utility_score,durability_quadrant",
                    "bh_score": "not.is.null",
                    "limit": "2000",
                },
                timeout=15,
            )
            if r.status_code == 200:
                all_responses.extend(r.json())
        except Exception:
            pass

    return all_respondent_counts, all_responses


with st.spinner("Loading state data..."):
    respondent_counts, responses = load_state_data(tuple(state_surveys))

total_respondents = sum(respondent_counts.values())

# Deduplicate responses by question_id (keep first occurrence)
seen_qids = set()
unique_responses = []
for r in responses:
    qid = r.get("question_id", "")
    if qid not in seen_qids:
        seen_qids.add(qid)
        unique_responses.append(r)

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
            {len(unique_responses)} scored questions
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

st.divider()

# ─────────────────────────────────────────────────────────────────
# SECTION 1: OVERVIEW METRICS
# ─────────────────────────────────────────────────────────────────

cols = st.columns(4)

# Golden zone count (dual_utility_score > 0.65)
golden_count = sum(
    1 for r in unique_responses
    if float(r.get("dual_utility_score") or r.get("cb_score") or 0) >= 0.65
)

# Unique constructs
constructs_found = set()
for r in unique_responses:
    c = r.get("construct", "")
    if c:
        constructs_found.add(c)

# Tier counts
tier_counts = {}
for c in constructs_found:
    tier = TIER_MAP.get(c, "Unassigned")
    tier_counts[tier] = tier_counts.get(tier, 0) + 1

with cols[0]:
    st.metric("Respondents", f"{total_respondents:,}")
with cols[1]:
    st.metric("Golden Zone Items", str(golden_count))
with cols[2]:
    st.metric("Constructs Covered", str(len(constructs_found)))
with cols[3]:
    st.metric("Surveys", str(len(state_surveys)))

st.divider()

# ─────────────────────────────────────────────────────────────────
# SECTION 2: PERSUASION TIER BREAKDOWN
# ─────────────────────────────────────────────────────────────────

st.subheader("Persuasion Tier Breakdown")
st.markdown(
    f"<div style='font-size:0.9rem;color:{TEXT3};margin-bottom:1rem;'>"
    "How this state's constructs distribute across the persuasion architecture.</div>",
    unsafe_allow_html=True,
)

# Group constructs by tier
tier_constructs = {}
for c in sorted(constructs_found):
    tier = TIER_MAP.get(c, "Unassigned")
    if tier not in tier_constructs:
        tier_constructs[tier] = []
    tier_constructs[tier].append(c)

tier_order = ["Entry", "Entry (VA)", "Bridge", "Downstream", "Destination", "Gauge", "Unassigned"]

for tier in tier_order:
    if tier not in tier_constructs:
        continue
    constructs = tier_constructs[tier]
    style = TIER_STYLES.get(tier, {"bg": "rgba(140,137,132,0.1)", "color": TEXT3, "border": TEXT3})

    # Get average score for this tier's questions
    tier_questions = [r for r in unique_responses if TIER_MAP.get(r.get("construct", ""), "Unassigned") == tier]
    avg_score = 0
    if tier_questions:
        scores = [float(r.get("dual_utility_score") or r.get("cb_score") or 0) for r in tier_questions]
        avg_score = sum(scores) / len(scores) if scores else 0

    construct_tags = " ".join(
        f'<span style="background:{style["bg"]};color:{style["color"]};padding:2px 8px;'
        f'border-radius:6px;font-size:0.75rem;font-weight:500;margin-right:4px;">{c}</span>'
        for c in constructs
    )

    st.markdown(f"""
    <div style="background:{CARD_BG};border-left:4px solid {style['border']};border-radius:0 8px 8px 0;
         padding:1rem 1.25rem;margin-bottom:0.75rem;box-shadow:0 1px 3px rgba(0,0,0,0.04);">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:0.5rem;">
            <div style="font-weight:700;color:{style['color']};font-size:1rem;">{tier}</div>
            <div style="font-size:0.8rem;color:{TEXT3};">{len(tier_questions)} questions · avg {avg_score:.0%}</div>
        </div>
        <div>{construct_tags}</div>
    </div>
    """, unsafe_allow_html=True)

st.divider()

# ─────────────────────────────────────────────────────────────────
# SECTION 3: TOP QUESTIONS
# ─────────────────────────────────────────────────────────────────

st.subheader("Top-Scoring Questions")
st.markdown(
    f"<div style='font-size:0.9rem;color:{TEXT3};margin-bottom:1rem;'>"
    "Ranked by dual utility score (or CB score if dual utility unavailable). "
    "Golden Zone items highlighted.</div>",
    unsafe_allow_html=True,
)

# Sort by score descending
sorted_responses = sorted(
    unique_responses,
    key=lambda r: float(r.get("dual_utility_score") or r.get("cb_score") or 0),
    reverse=True,
)

for rank, r in enumerate(sorted_responses[:15], 1):
    score = float(r.get("dual_utility_score") or r.get("cb_score") or 0)
    bh = float(r.get("bh_score") or 0)
    cb = float(r.get("cb_score") or 0)
    construct = r.get("construct", "Unknown")
    tier = TIER_MAP.get(construct, "—")
    q_text = r.get("question_text", "Unknown question")
    is_golden = score >= 0.65

    bar_width = score * 100
    bar_color = "#1B6B3A" if is_golden else state_color
    golden_badge = (
        f'<span style="background:#1B6B3A;color:white;padding:1px 6px;border-radius:4px;'
        f'font-size:0.65rem;font-weight:600;margin-left:6px;">GOLDEN ZONE</span>'
        if is_golden else ""
    )

    st.markdown(f"""
    <div style="background:{CARD_BG};border:1px solid {BORDER2};border-radius:8px;
         padding:1rem;margin-bottom:0.5rem;box-shadow:0 1px 2px rgba(0,0,0,0.03);">
        <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:0.5rem;">
            <div style="flex:1;">
                <span style="color:{TEXT3};font-size:0.75rem;font-weight:600;">#{rank}</span>
                <span style="color:{NAVY};font-weight:500;font-size:0.88rem;margin-left:6px;">{q_text[:100]}</span>
                {golden_badge}
            </div>
            <div style="text-align:right;min-width:80px;">
                <div style="font-weight:700;color:{bar_color};font-size:1.1rem;">{score:.0%}</div>
            </div>
        </div>
        <div style="width:100%;height:6px;background:{BORDER2};border-radius:3px;overflow:hidden;margin-bottom:0.4rem;">
            <div style="width:{bar_width}%;height:100%;background:{bar_color};border-radius:3px;"></div>
        </div>
        <div style="font-size:0.72rem;color:{TEXT3};">
            {construct} · {tier} · BH: {bh:.0%} · CB: {cb:.0%}
        </div>
    </div>
    """, unsafe_allow_html=True)

st.divider()

# ─────────────────────────────────────────────────────────────────
# SECTION 4: CONSTRUCT PERFORMANCE TABLE
# ─────────────────────────────────────────────────────────────────

st.subheader("Construct Performance")
st.markdown(
    f"<div style='font-size:0.9rem;color:{TEXT3};margin-bottom:1rem;'>"
    "Average scores by construct across all surveys in this state.</div>",
    unsafe_allow_html=True,
)

# Build construct summary
construct_data = {}
for r in unique_responses:
    c = r.get("construct", "Unknown")
    if c not in construct_data:
        construct_data[c] = {"scores": [], "bh_scores": [], "cb_scores": [], "count": 0}
    score = float(r.get("dual_utility_score") or r.get("cb_score") or 0)
    bh = float(r.get("bh_score") or 0)
    cb = float(r.get("cb_score") or 0)
    construct_data[c]["scores"].append(score)
    construct_data[c]["bh_scores"].append(bh)
    construct_data[c]["cb_scores"].append(cb)
    construct_data[c]["count"] += 1

rows = []
for c, d in construct_data.items():
    avg_score = sum(d["scores"]) / len(d["scores"]) if d["scores"] else 0
    avg_bh = sum(d["bh_scores"]) / len(d["bh_scores"]) if d["bh_scores"] else 0
    avg_cb = sum(d["cb_scores"]) / len(d["cb_scores"]) if d["cb_scores"] else 0
    tier = TIER_MAP.get(c, "Unassigned")
    rows.append({
        "Construct": c,
        "Tier": tier,
        "Questions": d["count"],
        "Avg Score": f"{avg_score:.0%}",
        "Avg BH": f"{avg_bh:.0%}",
        "Avg CB": f"{avg_cb:.0%}",
        "_sort": avg_score,
    })

if rows:
    df = pd.DataFrame(sorted(rows, key=lambda x: x["_sort"], reverse=True))
    df = df.drop(columns=["_sort"])
    st.dataframe(df, use_container_width=True, hide_index=True)
else:
    st.info("No scored construct data available for this state.")

st.divider()

# ─────────────────────────────────────────────────────────────────
# SECTION 5: SURVEY BREAKDOWN
# ─────────────────────────────────────────────────────────────────

st.subheader("Survey Breakdown")

for sid in state_surveys:
    n = respondent_counts.get(sid, 0)
    q_count = len([r for r in responses if r.get("survey_id") == sid or True])  # approximate

    st.markdown(f"""
    <div style="background:{CARD_BG};border:1px solid {BORDER2};border-radius:8px;
         padding:1rem;margin-bottom:0.5rem;display:flex;justify-content:space-between;align-items:center;">
        <div>
            <div style="font-weight:600;color:{NAVY};">{sid}</div>
        </div>
        <div style="text-align:right;">
            <div style="font-weight:600;color:{state_color};">{n:,} respondents</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ── Footer ──
st.markdown("")
if st.button("← Back to Home", use_container_width=False):
    st.switch_page("app.py")

portal_footer()
