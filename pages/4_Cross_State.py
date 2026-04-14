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
    apply_theme, portal_footer, data_source_badge, get_supabase_config, get_supabase_headers,
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

# Shared data loader (MrP primary, raw fallback)
from data_loader import load_mrp_question_summary, _paginate as paginate_supabase, render_data_source_toggle

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
def load_cross_state_data(data_mode="mrp"):
    """Load cross-state comparison data.
    Uses MrP-adjusted rates from mrp_question_summary when available,
    falls back to raw L2 scoring for surveys not yet through MrP.
    When data_mode="raw", uses raw_pct from MrP table (or runtime scoring).
    """
    # Step 1: Load MrP data (keyed by (survey_id, question_id))
    mrp_data, mrp_surveys = load_mrp_question_summary()

    # Step 2: Identify which CJ surveys need raw fallback
    needs_raw = [sid for sid in CJ_SURVEYS if sid not in mrp_surveys]

    # Step 3: Load raw L2 for uncovered surveys
    raw_state_question = defaultdict(lambda: defaultdict(lambda: {"fav": 0, "n": 0, "text": "", "construct": ""}))
    raw_respondent_counts = defaultdict(set)

    if needs_raw and SCORING_AVAILABLE:
        for sid in needs_raw:
            rows = paginate_supabase(
                f"{SUPABASE_URL}/rest/v1/l2_responses"
                f"?select=respondent_id,survey_id,question_id,question_text,response"
                f"&survey_id=eq.{sid}",
                HEADERS,
            )
            state = SURVEY_STATE.get(sid, "")
            if not state:
                continue
            for r in rows:
                qid = r.get("question_id")
                if not qid or qid in SKIPPED_QIDS:
                    continue
                construct = get_construct(qid)
                if not construct or construct in GAUGE_CONSTRUCTS:
                    continue
                fav, intensity, has_int = score_content(qid, r["response"], sid)
                if fav is None:
                    continue
                is_fav = 1 if fav == 1 else 0
                raw_state_question[state][qid]["fav"] += is_fav
                raw_state_question[state][qid]["n"] += 1
                if r.get("question_text"):
                    raw_state_question[state][qid]["text"] = r["question_text"]
                raw_state_question[state][qid]["construct"] = construct
                raw_respondent_counts[state].add(r.get("respondent_id"))

    # Step 4: Merge MrP + raw into unified per-state per-question data
    # Format: {state: {qid: {pct, n, text, construct, source}}}
    state_question_merged = defaultdict(dict)
    respondent_counts = defaultdict(int)

    # MrP data first
    for (sid, qid), row in mrp_data.items():
        if sid not in [s for s in CJ_SURVEYS]:
            continue
        state = row.get("state", SURVEY_STATE.get(sid, ""))
        if not state:
            continue
        construct = get_construct(qid) if SCORING_AVAILABLE else None
        if not construct or construct in GAUGE_CONSTRUCTS:
            continue
        if qid in SKIPPED_QIDS:
            continue
        pct_value = row["mrp_pct"] if data_mode == "mrp" else row.get("raw_pct", row["mrp_pct"])
        state_question_merged[state][qid] = {
            "pct": pct_value,
            "n": row.get("n_respondents", 0),
            "text": row.get("question_text", ""),
            "construct": construct,
            "source": "mrp" if data_mode == "mrp" else "raw",
        }
        respondent_counts[state] = max(respondent_counts[state], row.get("n_respondents", 0))

    # Raw fallback data
    for state, questions in raw_state_question.items():
        for qid, qd in questions.items():
            if qd["n"] < 20:
                continue
            if qid not in state_question_merged.get(state, {}):
                if state not in state_question_merged:
                    state_question_merged[state] = {}
                state_question_merged[state][qid] = {
                    "pct": qd["fav"] / qd["n"] * 100,
                    "n": qd["n"],
                    "text": qd["text"],
                    "construct": qd["construct"],
                    "source": "raw",
                }
        if state in raw_respondent_counts:
            respondent_counts[state] = max(respondent_counts[state], len(raw_respondent_counts[state]))

    # Step 5: Build topic-level cross-state matrix
    state_topic = defaultdict(lambda: defaultdict(lambda: {"sum_pct_n": 0, "sum_n": 0}))
    for state, questions in state_question_merged.items():
        for qid, qd in questions.items():
            c = qd["construct"]
            n = qd["n"]
            state_topic[state][c]["sum_pct_n"] += qd["pct"] * n
            state_topic[state][c]["sum_n"] += n

    all_states = sorted(state_question_merged.keys())
    all_constructs = set()
    for st_data in state_topic.values():
        all_constructs.update(st_data.keys())

    topic_matrix = []
    for con in sorted(all_constructs):
        row = {"construct": con, "topic": CONSTRUCT_LABELS.get(con, con), "tier": TIER_MAP.get(con, "—")}
        states_with_data = []
        for state in all_states:
            d = state_topic[state].get(con)
            if d and d["sum_n"] > 0:
                abbr = STATE_ABBR.get(state, state[:2])
                pct = d["sum_pct_n"] / d["sum_n"]
                row[abbr] = pct
                states_with_data.append(pct)
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

    # Step 6: Question-level cross-state (for questions fielded in 2+ states)
    question_cross = defaultdict(dict)
    question_meta = {}

    for state, questions in state_question_merged.items():
        abbr = STATE_ABBR.get(state, state[:2])
        for qid, qd in questions.items():
            text = qd["text"]
            if not text:
                continue
            question_cross[text][abbr] = qd["pct"]
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

    state_counts = dict(respondent_counts)

    return topic_matrix, multi_state_questions, all_states, state_counts


# ══════════════════════════════════════════════════════════════════
# MAIN PAGE
# ══════════════════════════════════════════════════════════════════

st.title("🗺️ Cross-State Comparison")

# MrP/Raw toggle
data_mode = render_data_source_toggle()
data_source_badge(data_mode)

st.markdown(
    "Compare reform polling results across states. See which messages transfer "
    "across state lines and which need local adaptation."
)

if not SCORING_AVAILABLE:
    st.error("content_scoring.py not found. Cannot score responses.")
    st.stop()

topic_matrix, multi_state_questions, all_states, state_counts = load_cross_state_data(data_mode=data_mode)

if not topic_matrix:
    st.warning("Not enough multi-state data available yet.")
    st.stop()

# ── VIP EXPLANATION ────────────────────────────────────────────────
total_respondents = sum(state_counts.values())

st.markdown(f"""
<div style="background:rgba(14,31,61,0.04);border:1px solid {BORDER2};border-left:4px solid {NAVY};border-radius:10px;padding:1rem 1.25rem;margin-bottom:1rem;">
<div style="font-weight:700;color:{NAVY};font-size:1rem;margin-bottom:0.6rem;">What is the Voter Intelligence Profile?</div>
<div style="font-size:0.85rem;color:{TEXT2};line-height:1.65;">
The <strong>VIP</strong> is a scoring system that measures how persuasive each criminal justice reform message is — and with which voters — using MrP-adjusted survey data. Every construct (e.g. <em>Public Defender Funding</em>, <em>Domestic Violence</em>, <em>Proportionality</em>) gets a <strong>support rate</strong>, a <strong>partisan gap</strong>, and a <strong>persuasion tier</strong> that tells you where it sits in the sequencing from broadest agreement to most contested.
</div>
<div style="font-size:0.85rem;color:{TEXT2};line-height:1.65;margin-top:0.6rem;">
<strong>The VIP strengthens with every survey fielded.</strong> Each new state adds respondents to the pooled dataset, sharpening the MrP demographic weights and reducing uncertainty in the estimates. More states also reveal which messages are <em>universal</em> (low spread across states) vs. which need local adaptation — that transferability signal is only visible when you have multiple states to compare. The current {len(all_states)}-state picture ({total_respondents:,} total respondents) already shows meaningful cross-state patterns; each new wave adds precision.
</div>
</div>
""", unsafe_allow_html=True)

# ── KPI ROW ────────────────────────────────────────────────────────
# Note: keep all style attributes on ONE line inside f-strings to avoid
# Streamlit's HTML parser dropping out of HTML mode on multiline attributes.
state_abbrs = [STATE_ABBR.get(s, s[:2]) for s in all_states]

# Build inner card HTML — single-line style attributes throughout
inner_cards = ""
for state in all_states:
    abbr = STATE_ABBR.get(state, state[:2])
    count = state_counts.get(state, 0)
    s_color = STATE_COLORS.get(state, NAVY)
    inner_cards += (
        f'<div style="background:{CARD_BG};border:1px solid {BORDER2};border-top:3px solid {s_color};border-radius:10px;padding:0.75rem 1.25rem;text-align:center;min-width:90px;flex:1;">'
        f'<div style="font-size:0.7rem;color:{TEXT3};text-transform:uppercase;letter-spacing:0.04em;font-weight:500;">{abbr}</div>'
        f'<div style="font-family:serif;font-size:1.6rem;font-weight:700;color:{NAVY};">{count:,}</div>'
        f'<div style="font-size:0.65rem;color:{TEXT3};">respondents</div>'
        f'</div>'
    )

states_card = (
    f'<div style="background:{CARD_BG};border:1px solid {BORDER2};border-radius:10px;padding:0.75rem 1.25rem;text-align:center;min-width:90px;flex:1;">'
    f'<div style="font-size:0.7rem;color:{TEXT3};text-transform:uppercase;letter-spacing:0.04em;font-weight:500;">States</div>'
    f'<div style="font-family:serif;font-size:1.6rem;font-weight:700;color:{NAVY};">{len(all_states)}</div>'
    f'</div>'
)

kpi_html = (
    f'<div style="display:flex;gap:12px;flex-wrap:wrap;margin-bottom:0.5rem;">'
    f'{states_card}{inner_cards}'
    f'</div>'
)
st.markdown(kpi_html, unsafe_allow_html=True)

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

        # Build state bars — skip states with no data (None or NaN)
        state_scores = []
        for abbr in state_abbrs:
            val = row.get(abbr)
            if val is not None and pd.notna(val):
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
            has_data = val is not None and pd.notna(val)
            z_row.append(val if has_data else None)
            if has_data:
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
        text=[[f"{v:.0f}" if (v is not None and pd.notna(v) and v > 0) else "" for v in row] for row in z_values],
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


render_chat("cross_state")
portal_footer()
