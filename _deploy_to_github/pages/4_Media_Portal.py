"""
Cross-State Comparison
Live data from Supabase showing per-state results and transfer analysis.
"""

import streamlit as st
from pathlib import Path
import sys
import requests
import pandas as pd
from datetime import datetime

# Auth gate
sys.path.insert(0, str(Path(__file__).parent.parent))
from theme import (
    apply_theme, portal_footer, get_supabase_config, get_supabase_headers,
    CJ_SURVEYS, SURVEY_STATE, STATE_COLORS, STATE_ABBR,
    NAVY, GOLD, TEXT3, BORDER2, CARD_BG
)
from auth import require_auth

st.set_page_config(
    page_title="Cross-State — SLA Portal",
    page_icon="🗺️",
    layout="wide",
)

apply_theme()
username = require_auth("Second Look Alliance", accent_color=GOLD)

st.title("Cross-State Comparison")
st.markdown(
    "Compare CJ reform polling results across states. See which messages transfer and which need adaptation.",
    unsafe_allow_html=True
)

st.divider()

# ─────────────────────────────────────────────────────────────────
# DATA LOADING
# ─────────────────────────────────────────────────────────────────

@st.cache_data(ttl=3600)
def load_state_respondent_counts():
    """Load respondent counts per survey."""
    url, key = get_supabase_config()
    headers = get_supabase_headers()

    counts = {}
    for survey_id in CJ_SURVEYS:
        try:
            # Use count=exact to get total respondent count
            resp = requests.get(
                f"{url}/rest/v1/l1_respondents",
                headers={**headers, "Prefer": "count=exact, Range: 0-0"},
                params={"survey_id": f"eq.{survey_id}"},
                timeout=10
            )
            if resp.status_code == 200:
                # Parse Content-Range header: "0-0/N" where N is total count
                content_range = resp.headers.get("Content-Range", "0-0/0")
                total = int(content_range.split("/")[-1])
                counts[survey_id] = total
            else:
                counts[survey_id] = 0
        except Exception as e:
            st.warning(f"Error loading {survey_id}: {e}")
            counts[survey_id] = 0

    return counts

@st.cache_data(ttl=3600)
def load_survey_questions():
    """Load scored questions per survey."""
    url, key = get_supabase_config()
    headers = get_supabase_headers()

    questions = {}
    for survey_id in CJ_SURVEYS:
        try:
            resp = requests.get(
                f"{url}/rest/v1/l2_responses",
                headers=headers,
                params={
                    "survey_id": f"eq.{survey_id}",
                    "select": "question_id,question_text,bh_score,cb_score,dual_utility_score,durability_quadrant",
                    "bh_score": "not.is.null",
                    "limit": "1000"
                },
                timeout=10
            )
            if resp.status_code == 200:
                data = resp.json()
                # Deduplicate by question_id and get top 4 by CB score
                dedup = {}
                for row in data:
                    qid = row.get("question_id")
                    if qid not in dedup:
                        dedup[qid] = row

                sorted_questions = sorted(
                    dedup.values(),
                    key=lambda x: float(x.get("cb_score") or 0),
                    reverse=True
                )[:4]

                questions[survey_id] = sorted_questions
            else:
                questions[survey_id] = []
        except Exception as e:
            st.warning(f"Error loading questions for {survey_id}: {e}")
            questions[survey_id] = []

    return questions

# Load data
with st.spinner("Loading survey data..."):
    respondent_counts = load_state_respondent_counts()
    survey_questions = load_survey_questions()

# ─────────────────────────────────────────────────────────────────
# STATE CARDS
# ─────────────────────────────────────────────────────────────────

st.subheader("Live Survey Results by State")

# Group surveys by state
surveys_by_state = {}
for survey_id in CJ_SURVEYS:
    state = SURVEY_STATE[survey_id]
    if state not in surveys_by_state:
        surveys_by_state[state] = []
    surveys_by_state[state].append(survey_id)

# Display state cards
for state in sorted(surveys_by_state.keys()):
    state_surveys = surveys_by_state[state]
    state_color = STATE_COLORS.get(state, "#8C8984")
    state_abbr = STATE_ABBR.get(state, state[:2])

    # Sum respondents across all surveys in this state
    total_respondents = sum(respondent_counts.get(sid, 0) for sid in state_surveys)

    # Count golden zone questions (CB score > some threshold, e.g., >= 0.65)
    golden_zone_count = 0
    all_state_questions = []
    for survey_id in state_surveys:
        all_state_questions.extend(survey_questions.get(survey_id, []))

    for q in all_state_questions:
        cb = float(q.get("cb_score") or 0)
        if cb >= 0.65:
            golden_zone_count += 1

    # Get top 4 questions for this state
    top_4 = sorted(
        all_state_questions,
        key=lambda x: float(x.get("cb_score") or 0),
        reverse=True
    )[:4]

    # Render card
    st.markdown(f"""
    <div style="background:{CARD_BG};border:1px solid {BORDER2};border-radius:10px;padding:1.5rem;margin-bottom:1rem;box-shadow:0 1px 3px rgba(0,0,0,0.04);">
        <div style="display:flex;align-items:center;gap:12px;margin-bottom:1rem;">
            <div style="font-size:1.8rem;color:{state_color};">{state_abbr}</div>
            <div>
                <div style="font-size:1.15rem;font-weight:700;color:{NAVY};">{state}</div>
                <div style="font-size:0.8rem;color:{TEXT3};">{len(state_surveys)} survey{'' if len(state_surveys) == 1 else 's'}</div>
            </div>
        </div>

        <div style="display:flex;gap:2rem;margin-bottom:1.5rem;">
            <div>
                <div style="color:{state_color};font-weight:600;font-size:1.2rem;">{total_respondents:,}</div>
                <div style="font-size:0.75rem;color:{TEXT3};text-transform:uppercase;letter-spacing:0.05em;">Respondents</div>
            </div>
            <div>
                <div style="color:{state_color};font-weight:600;font-size:1.2rem;">{golden_zone_count}</div>
                <div style="font-size:0.75rem;color:{TEXT3};text-transform:uppercase;letter-spacing:0.05em;">Golden Zone</div>
            </div>
        </div>

        <div style="border-top:1px solid {BORDER2};padding-top:1rem;">
            <div style="font-size:0.8rem;font-weight:600;color:{TEXT3};text-transform:uppercase;margin-bottom:0.75rem;">Top 4 questions</div>
    """, unsafe_allow_html=True)

    # Top 4 questions with mini bars
    for q in top_4:
        cb_score = float(q.get("cb_score") or 0)
        question_text = q.get("question_text", "Unknown")[:80]

        # Mini horizontal bar
        bar_width = cb_score * 100  # Assume 0-1 scale
        st.markdown(f"""
        <div style="margin-bottom:0.5rem;">
            <div style="font-size:0.8rem;color:{NAVY};margin-bottom:2px;font-weight:500;">{question_text}</div>
            <div style="width:100%;height:6px;background:{BORDER2};border-radius:3px;overflow:hidden;">
                <div style="width:{bar_width}%;height:100%;background:{state_color};"></div>
            </div>
            <div style="font-size:0.7rem;color:{TEXT3};margin-top:2px;">CB Score: {cb_score:.2f}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

st.divider()

# ─────────────────────────────────────────────────────────────────
# TRANSFER ANALYSIS
# ─────────────────────────────────────────────────────────────────

st.subheader("Message Transfer Analysis")
st.markdown(
    "Questions appearing in multiple states are evaluated for **transfer readiness**: Can this message work across different contexts?",
    unsafe_allow_html=True
)

# Build cross-state question map
question_states = {}  # question_text -> {state: cb_score}
for survey_id in CJ_SURVEYS:
    state = SURVEY_STATE[survey_id]
    for q in survey_questions.get(survey_id, []):
        q_text = q.get("question_text", "")
        cb = float(q.get("cb_score") or 0)

        if q_text not in question_states:
            question_states[q_text] = {}
        question_states[q_text][state] = cb

# Filter to questions in 2+ states
multi_state_questions = {
    q: scores for q, scores in question_states.items()
    if len(scores) >= 2
}

if multi_state_questions:
    transfer_data = []
    for q_text, state_scores in sorted(multi_state_questions.items()):
        states_list = sorted(state_scores.items())

        if len(states_list) >= 2:
            scores = [s[1] for s in states_list]
            spread = max(scores) - min(scores)

            if spread <= 0.08:
                transfer_rating = "Direct transfer"
                transfer_color = "#1B6B3A"  # Green
            elif spread <= 0.15:
                transfer_rating = "Needs adaptation"
                transfer_color = "#B85400"  # Amber
            else:
                transfer_rating = "State-specific"
                transfer_color = "#8B1A1A"  # Red

            transfer_data.append({
                "Question": q_text[:60] + ("..." if len(q_text) > 60 else ""),
                "States": " vs ".join([STATE_ABBR.get(s[0], s[0][:2]) for s in states_list]),
                "Scores": " vs ".join([f"{s[1]:.2f}" for s in states_list]),
                "Spread": f"{spread:.2f}",
                "Transfer": transfer_rating,
                "_color": transfer_color
            })

    # Display as simple table with color coding
    for item in transfer_data[:15]:  # Show top 15
        color = item["_color"]
        st.markdown(f"""
        <div style="background:{CARD_BG};border:1px solid {BORDER2};border-radius:8px;padding:1rem;margin-bottom:0.75rem;display:flex;justify-content:space-between;align-items:center;">
            <div style="flex:1;">
                <div style="font-weight:500;color:{NAVY};margin-bottom:0.25rem;">{item['Question']}</div>
                <div style="font-size:0.8rem;color:{TEXT3};">{item['States']}: {item['Scores']}</div>
            </div>
            <div style="text-align:right;">
                <div style="background:{color};color:#fff;padding:4px 12px;border-radius:6px;font-size:0.75rem;font-weight:600;margin-bottom:0.25rem;">{item['Transfer']}</div>
                <div style="font-size:0.75rem;color:{TEXT3};">Spread: {item['Spread']}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
else:
    st.info("No multi-state questions found yet. More survey data needed for transfer analysis.")

st.divider()

st.info(
    "🔄 **Transfer Ratings:** Direct transfer (spread ≤ 0.08) = message works consistently across states. Needs adaptation (0.08–0.15) = core message works, customize framing. State-specific (>0.15) = different audiences need different approaches.",
    icon="ℹ️"
)

portal_footer()
