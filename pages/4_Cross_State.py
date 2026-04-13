"""
Cross-State Comparison — SLA Portal
Compares topic support across states using runtime scoring.
Shows which reform messages transfer across state lines and which need adaptation.
"""

import streamlit as st
from pathlib import Path
import sys
import requests
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).parent.parent))
from theme import (
    apply_theme, portal_footer, get_supabase_config, get_supabase_headers,
    CJ_SURVEYS, SURVEY_STATE, STATE_COLORS, STATE_ABBR, TIER_MAP,
    NAVY, NAVY2, GOLD, GOLD_MID, TEXT1, TEXT2, TEXT3, BORDER2, BG, CARD_BG,
)
from auth import require_auth
from chat_widget import render_chat

# Scoring engine
try:
    from content_scoring import SKIPPED_QIDS, get_construct, score_content
    SCORING_AVAILABLE = True
except ImportError:
    SCORING_AVAILABLE = False

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
    "PROS": "Prosecutor Accountability", "DP_ABOLITION": "Death Penalty Abolition",
    "DP_RELIABILITY": "Death Penalty Reliability", "LWOP": "Life Without Parole",
    "COMPASSION": "Compassionate Release",
}

GAUGE_CONSTRUCTS = {"CAND", "TOUGHCRIME", "ISSUE_SALIENCE", "IMPACT"}

st.set_page_config(page_title="Cross-State — SLA Portal", page_icon="🗺️", layout="wide")
apply_theme()
username = require_auth("Second Look Alliance", accent_color=GOLD)

SUPABASE_URL, SUPABASE_KEY = get_supabase_config()
HEADERS = get_supabase_headers()


# ══════════════════════════════════════════════════════════════════
# DATA LOADING — runtime scoring per state
# ══════════════════════════════════════════════════════════════════

def _paginate(url_base, headers, limit=1000, max_rows=200000):
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


@st.cache_data(ttl=3600, show_spinner="Loading cross-state data...")
def load_cross_state_data():
    """Pull all L2 responses, score at runtime, compute per-state per-topic and per-question support."""
    all_l2 = []
    for sid in CJ_SURVEYS:
        rows = _paginate(
            f"{SUPABASE_URL}/rest/v1/l2_responses"
            f"?select=respondent_id,survey_id,question_id,question_text,response"
            f"&survey_id=eq.{sid}",
            HEADERS,
        )
        all_l2.extend(rows)

    # Score and aggregate by state × topic and state × question
    state_topic = defaultdict(lambda: defaultdict(lambda: {"fav": 0, "n": 0}))
    state_question = defaultdict(lambda: defaultdict(lambda: {"fav": 0, "n": 0, "text": "", "construct": ""}))
    respondent_counts = defaultdict(set)

    for r in all_l2:
        qid = r.get("question_id")
        sid = r.get("survey_id")
        if not qid or qid in SKIPPED_QIDS:
            continue
        construct = get_construct(qid)
        if not construct or construct in GAUGE_CONSTRUCTS:
            continue

        fav, intensity, has_int = score_content(qid, r["response"], sid)
        if fav is None:
            continue
        is_fav = 1 if fav == 1 else 0

        state = SURVEY_STATE.get(sid, "")
        if not state:
            continue

        state_topic[state][construct]["fav"] += is_fav
        state_topic[state][construct]["n"] += 1

        state_question[state][qid]["fav"] += is_fav
        state_question[state][qid]["n"] += 1
        if r.get("question_text"):
            state_question[state][qid]["text"] = r["question_text"]
        state_question[state][qid]["construct"] = construct

        respondent_counts[state].add(r.get("respondent_id"))

    # Build topic-level cross-state matrix
    all_states = sorted(state_topic.keys())
    all_constructs = set()
    for st_data in state_topic.values():
        all_constructs.update(st_data.keys())

    topic_matrix = []
    for con in sorted(all_constructs):
        row = {"construct": con, "topic": CONSTRUCT_LABELS.get(con, con), "tier": TIER_MAP.get(con, "—")}
        states_with_data = []
        for state in all_states:
            d = state_topic[state].get(con)
            if d and d["n"] >= 20:
                abbr = STATE_ABBR.get(state, state[:2])
                row[abbr] = d["fav"] / d["n"] * 100
                states_with_data.append(d["fav"] / d["n"] * 100)
            else:
                abbr = STATE_ABBR.get(state, state[:2])
                row[abbr] = None

        if len(states_with_data) >= 2:
            row["spread"] = max(states_with_data) - min(states_with_data)
            row["avg"] = np.mean(states_with_data)
            row["n_states"] = len(states_with_data)
            if row["spread"] <= 8:
                row["transfer"] = "Direct Transfer"
            elif row["spread"] <= 15:
                row["transfer"] = "Needs Adaptation"
            else:
                row["transfer"] = "State-Specific"
            topic_matrix.append(row)

    # Question-level cross-state (for questions fielded in 2+ states)
    question_cross = defaultdict(dict)  # question_text -> {state: support%}
    question_meta = {}  # question_text -> {construct, qid}

    for state, questions in state_question.items():
        abbr = STATE_ABBR.get(state, state[:2])
        for qid, qd in questions.items():
            if qd["n"] < 20:
                continue
            text = qd["text"]
            if not text:
                continue
            question_cross[text][abbr] = qd["fav"] / qd["n"] * 100
            question_meta[text] = {"construct": qd["construct"], "qid": qid}

    multi_state_questions = []
    for text, state_scores in question_cross.items():
        if len(state_scores) >= 2:
            scores = list(state_scores.values())
            spread = max(scores) - min(scores)
            meta = question_meta.get(text, {})
            multi_state_questions.append({
                "text": text,
                "construct": meta.get("construct", ""),
                "topic": CONSTRUCT_LABELS.get(meta.get("construct", ""), meta.get("construct", "")),
                "states": state_scores,
                "spread": spread,
                "avg": np.mean(scores),
                "n_states": len(scores),
                "transfer": "Direct Transfer" if spread <= 8 else ("Needs Adaptation" if spread <= 15 else "State-Specific"),
            })
    multi_state_questions.sort(key=lambda x: x["spread"])

    state_counts = {s: len(rids) for s, rids in respondent_counts.items()}

    return topic_matrix, multi_state_questions, all_states, state_counts


# ══════════════════════════════════════════════════════════════════
# MAIN PAGE
# ══════════════════════════════════════════════════════════════════

st.title("🗺️ Cross-State Comparison")
st.markdown(
    "Compare reform polling results across states. See which messages transfer "
    "across state lines and which need local adaptation."
)

if not SCORING_AVAILABLE:
    st.error("content_scoring.py not found. Cannot score responses.")
    st.stop()

topic_matrix, multi_state_questions, all_states, state_counts = load_cross_state_data()

if not topic_matrix:
    st.warning("Not enough multi-state data available yet.")
    st.stop()

# KPI row — custom HTML to avoid column truncation
state_abbrs = [STATE_ABBR.get(s, s[:2]) for s in all_states]
kpi_items = f"""
<div style="display:flex;gap:12px;flex-wrap:wrap;margin-bottom:0.5rem;">
    <div style="background:{CARD_BG};border:1px solid {BORDER2};border-radius:10px;
         padding:0.75rem 1.25rem;text-align:center;min-width:90px;flex:1;">
        <div style="font-size:0.7rem;color:{TEXT3};text-transform:uppercase;letter-spacing:0.04em;font-weight:500;">States</div>
        <div style="font-family:'Playfair Display',serif;font-size:1.6rem;font-weight:700;color:{NAVY};">{len(all_states)}</div>
    </div>
"""
for state in all_states:
    abbr = STATE_ABBR.get(state, state[:2])
    count = state_counts.get(state, 0)
    s_color = STATE_COLORS.get(state, NAVY)
    kpi_items += f"""
    <div style="background:{CARD_BG};border:1px solid {BORDER2};border-top:3px solid {s_color};
         border-radius:10px;padding:0.75rem 1.25rem;text-align:center;min-width:90px;flex:1;">
        <div style="font-size:0.7rem;color:{TEXT3};text-transform:uppercase;letter-spacing:0.04em;font-weight:500;">{abbr}</div>
        <div style="font-family:'Playfair Display',serif;font-size:1.6rem;font-weight:700;color:{NAVY};">{count:,}</div>
        <div style="font-size:0.65rem;color:{TEXT3};">respondents</div>
    </div>
"""
kpi_items += "</div>"
st.markdown(kpi_items, unsafe_allow_html=True)

st.divider()

# Sidebar
with st.sidebar:
    st.markdown("### View")
    view_mode = st.radio("Display", ["Topic Comparison", "Question Transfer", "Heat Map"], key="cs_view")

    st.divider()
    direct = sum(1 for t in topic_matrix if t["transfer"] == "Direct Transfer")
    adapt = sum(1 for t in topic_matrix if t["transfer"] == "Needs Adaptation")
    specific = sum(1 for t in topic_matrix if t["transfer"] == "State-Specific")
    st.caption(f"🟢 Direct transfer: {direct}")
    st.caption(f"🟡 Needs adaptation: {adapt}")
    st.caption(f"🔴 State-specific: {specific}")


# ══════════════════════════════════════════════════════════════════
# TOPIC COMPARISON — bar chart per topic, grouped by state
# ══════════════════════════════════════════════════════════════════

if view_mode == "Topic Comparison":
    st.subheader("Topic Support by State")
    st.caption("Each topic's average support rate, broken out by state. Low spread = message transfers well.")

    tm_df = pd.DataFrame(topic_matrix).sort_values("spread", ascending=True)

    transfer_colors = {
        "Direct Transfer": "#1B6B3A",
        "Needs Adaptation": "#B85400",
        "State-Specific": "#8B1A1A",
    }

    for _, row in tm_df.iterrows():
        topic = row["topic"]
        tier = row["tier"]
        transfer = row["transfer"]
        spread = row["spread"]
        t_color = transfer_colors.get(transfer, TEXT3)

        # Build state bars
        state_scores = []
        for abbr in state_abbrs:
            val = row.get(abbr)
            if val is not None:
                state_scores.append((abbr, val))

        state_scores.sort(key=lambda x: x[1], reverse=True)

        bars_html = ""
        for abbr, val in state_scores:
            s_color = STATE_COLORS.get({v: k for k, v in STATE_ABBR.items()}.get(abbr, ""), NAVY)
            bars_html += (
                f'<div style="display:flex;align-items:center;gap:8px;margin-bottom:3px;">'
                f'<div style="width:30px;font-weight:600;color:{NAVY};font-size:0.8rem;">{abbr}</div>'
                f'<div style="flex:1;height:8px;background:{BORDER2};border-radius:4px;overflow:hidden;">'
                f'<div style="width:{min(val, 100):.0f}%;height:100%;background:{s_color};border-radius:4px;"></div>'
                f'</div>'
                f'<div style="width:40px;font-size:0.8rem;color:{TEXT2};text-align:right;">{val:.0f}%</div>'
                f'</div>'
            )

        st.markdown(f"""
        <div style="background:{CARD_BG};border:1px solid {BORDER2};border-radius:10px;
             padding:1rem 1.25rem;margin-bottom:0.75rem;">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:0.75rem;">
                <div>
                    <span style="font-weight:700;color:{NAVY};font-size:1rem;">{topic}</span>
                    <span style="font-size:0.8rem;color:{TEXT3};margin-left:8px;">{tier}</span>
                </div>
                <div style="display:flex;align-items:center;gap:8px;">
                    <span style="background:{t_color};color:white;padding:2px 10px;border-radius:6px;
                        font-size:0.72rem;font-weight:600;">{transfer}</span>
                    <span style="font-size:0.78rem;color:{TEXT3};">spread: {spread:.0f}pp</span>
                </div>
            </div>
            {bars_html}
        </div>
        """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════
# QUESTION TRANSFER — individual questions across states
# ══════════════════════════════════════════════════════════════════

elif view_mode == "Question Transfer":
    st.subheader("Question-Level Transfer Analysis")
    st.caption(
        "Individual survey questions that appeared in 2+ states. "
        "Low spread means the exact question works the same way everywhere."
    )

    if not multi_state_questions:
        st.info("No questions fielded in multiple states yet.")
    else:
        transfer_colors = {
            "Direct Transfer": "#1B6B3A",
            "Needs Adaptation": "#B85400",
            "State-Specific": "#8B1A1A",
        }

        for q in multi_state_questions[:20]:
            text = q["text"][:100] + ("…" if len(q["text"]) > 100 else "")
            topic = q["topic"]
            transfer = q["transfer"]
            spread = q["spread"]
            t_color = transfer_colors.get(transfer, TEXT3)

            states_str = " · ".join(
                f"{abbr}: {val:.0f}%"
                for abbr, val in sorted(q["states"].items(), key=lambda x: x[1], reverse=True)
            )

            st.markdown(f"""
            <div style="background:{CARD_BG};border:1px solid {BORDER2};border-radius:8px;
                 padding:1rem;margin-bottom:0.5rem;">
                <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:0.5rem;">
                    <div style="flex:1;font-size:0.88rem;color:{NAVY};font-weight:500;">{text}</div>
                    <div style="background:{t_color};color:white;padding:2px 10px;border-radius:6px;
                        font-size:0.72rem;font-weight:600;margin-left:12px;white-space:nowrap;">{transfer}</div>
                </div>
                <div style="font-size:0.8rem;color:{TEXT2};margin-bottom:0.25rem;">{states_str}</div>
                <div style="font-size:0.75rem;color:{TEXT3};">{topic} · Spread: {spread:.0f}pp</div>
            </div>
            """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════
# HEAT MAP — topics × states
# ══════════════════════════════════════════════════════════════════

elif view_mode == "Heat Map":
    st.subheader("Support Heat Map")
    st.caption("Topics on the left, states across the top. Color intensity shows support level.")

    tm_df = pd.DataFrame(topic_matrix).sort_values("avg", ascending=False)

    topic_labels = tm_df["topic"].tolist()
    z_values = []
    hover_texts = []

    for _, row in tm_df.iterrows():
        z_row = []
        h_row = []
        for abbr in state_abbrs:
            val = row.get(abbr)
            z_row.append(val if val is not None else 0)
            if val is not None:
                h_row.append(f"{row['topic']}<br>{abbr}: {val:.0f}%")
            else:
                h_row.append(f"{row['topic']}<br>{abbr}: no data")
        z_values.append(z_row)
        hover_texts.append(h_row)

    fig = go.Figure(data=go.Heatmap(
        z=z_values,
        x=state_abbrs,
        y=topic_labels,
        hovertext=hover_texts,
        hoverinfo="text",
        colorscale=[
            [0, "#8B1A1A"],
            [0.4, "#F5E6CC"],
            [0.6, "#C5E1A5"],
            [1.0, "#1B6B3A"],
        ],
        zmin=30,
        zmax=90,
        text=[[f"{v:.0f}" if v else "" for v in row] for row in z_values],
        texttemplate="%{text}%",
        textfont=dict(size=11, color=NAVY),
    ))

    fig.update_layout(
        template="plotly_white",
        paper_bgcolor=BG,
        plot_bgcolor=CARD_BG,
        height=max(500, len(topic_labels) * 28 + 100),
        margin=dict(l=250, r=30, t=40, b=40),
        xaxis=dict(side="top", tickfont=dict(size=12, color=NAVY)),
        yaxis=dict(autorange="reversed", tickfont=dict(size=11)),
        font=dict(family="DM Sans", color=NAVY),
    )

    st.plotly_chart(fig, use_container_width=True, key="cs_heatmap")


portal_footer()
