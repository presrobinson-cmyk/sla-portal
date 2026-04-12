"""
Message Testing — Persuasion Architecture Scatter
Click any dot to see item detail: question text, segment breakdown, demographics, bridge connections.
Filters: state, construct, demographic subgroup.
"""

import streamlit as st
from pathlib import Path
import sys
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import requests
import math
from collections import defaultdict

# Auth gate
sys.path.insert(0, str(Path(__file__).parent.parent))
from auth import require_auth

# ── Theme ──
from theme import (
    apply_theme, portal_footer, get_supabase_config, get_supabase_headers,
    CJ_SURVEYS, SURVEY_STATE, TIER_MAP, tier_badge_html,
    NAVY, GOLD, GOLD_MID, TEXT3, BORDER2, STATE_COLORS, STATE_ABBR
)

# ── Scoring engine (bundled locally) ──
sys.path.insert(0, str(Path(__file__).parent.parent))
try:
    from content_scoring import (
        FAVORABLE_DIRECTION, SKIPPED_QIDS, get_construct, score_content,
    )
    SCORING_AVAILABLE = True
except ImportError:
    SCORING_AVAILABLE = False

st.set_page_config(
    page_title="Message Testing — SLA Portal",
    page_icon="🎯",
    layout="wide",
)

# ── Apply theme ──
apply_theme()

username = require_auth("Second Look Alliance", accent_color=GOLD)

# ── Supabase config ──
SUPABASE_URL, SUPABASE_KEY = get_supabase_config()
HEADERS = get_supabase_headers()

# Segment bar colors (updated for light theme readability)
SEGMENT_COLORS = {
    1: "#8B1A1A",  # Q1 (red)
    2: "#B85400",  # Q2 (amber)
    3: "#B8870A",  # Q3 (gold)
    4: "#1155AA",  # Q4 (blue)
    5: "#1B6B3A",  # Q5 (green)
}

# Bridge colors
BRIDGE_AGREE_COLOR = "#1B6B3A"  # green
BRIDGE_DISAGREE_COLOR = "#8B1A1A"  # red


# ══════════════════════════════════════════════════════════════════
# DATA LOADING (cached)
# ══════════════════════════════════════════════════════════════════

@st.cache_data(ttl=3600, show_spinner="Loading survey data...")
def load_data():
    """Pull L2 responses and L1 demographics, score everything."""
    # Pull L2
    all_rows = []
    for sid in CJ_SURVEYS:
        offset = 0
        while True:
            url = (f"{SUPABASE_URL}/rest/v1/l2_responses"
                   f"?select=respondent_id,survey_id,question_id,question_text,response"
                   f"&survey_id=eq.{sid}&offset={offset}&limit=1000")
            resp = requests.get(url, headers=HEADERS, timeout=120)
            resp.raise_for_status()
            rows = resp.json()
            all_rows.extend(rows)
            if len(rows) < 1000:
                break
            offset += 1000

    # Pull L1 demographics
    demo_rows = []
    for sid in CJ_SURVEYS:
        offset = 0
        while True:
            url = (f"{SUPABASE_URL}/rest/v1/l1_respondents"
                   f"?select=respondent_id,survey_id,party_id,ideology,race_ethnicity,age_bracket,gender,education"
                   f"&survey_id=eq.{sid}&offset={offset}&limit=1000")
            resp = requests.get(url, headers=HEADERS, timeout=120)
            resp.raise_for_status()
            rows = resp.json()
            demo_rows.extend(rows)
            if len(rows) < 1000:
                break
            offset += 1000

    demo_lookup = {}
    for d in demo_rows:
        demo_lookup[d["respondent_id"]] = d

    # Score all responses
    scored = []
    qid_text = {}
    for r in all_rows:
        qid = r.get("question_id")
        if not qid or qid in SKIPPED_QIDS:
            continue
        construct = get_construct(qid)
        if not construct:
            continue
        fav, intensity, has_int = score_content(qid, r["response"], r.get("survey_id"))
        if fav is None:
            continue
        scored.append({
            "rid": r["respondent_id"],
            "sid": r["survey_id"],
            "qid": qid,
            "construct": construct,
            "fav": 1 if fav == 1 else 0,
        })
        if qid not in qid_text and r.get("question_text"):
            qid_text[qid] = r["question_text"]

    # Compute disposition scores
    resp_agg = defaultdict(lambda: {"fav": 0, "n": 0, "sid": None})
    for s in scored:
        resp_agg[s["rid"]]["fav"] += s["fav"]
        resp_agg[s["rid"]]["n"] += 1
        resp_agg[s["rid"]]["sid"] = s["sid"]

    disposition = {}
    for rid, d in resp_agg.items():
        if d["n"] >= 3:
            disposition[rid] = d["fav"] / d["n"]

    # Assign quintiles
    sorted_scores = sorted(disposition.items(), key=lambda x: x[1])
    n = len(sorted_scores)
    segments = {}
    for i, (rid, sc) in enumerate(sorted_scores):
        segments[rid] = min(int(i / n * 5) + 1, 5)

    return scored, qid_text, demo_lookup, disposition, segments


# ══════════════════════════════════════════════════════════════════
# COMPUTE FUNCTIONS
# ══════════════════════════════════════════════════════════════════

def compute_item_stats(scored, segments, qid_text, state_filter=None, demo_filter=None, demo_lookup=None):
    """Compute per-item Q1/Q5/overall rates, optionally filtered."""
    filtered = scored
    if state_filter and state_filter != "All States":
        valid_surveys = [sid for sid, st_name in SURVEY_STATE.items() if st_name == state_filter]
        filtered = [s for s in filtered if s["sid"] in valid_surveys]

    if demo_filter and demo_filter != "All" and demo_lookup:
        cat, val = demo_filter.split("::")
        filtered = [s for s in filtered if demo_lookup.get(s["rid"], {}).get(cat) == val]

    stats = defaultdict(lambda: {"q1_f": 0, "q1_n": 0, "q5_f": 0, "q5_n": 0, "all_f": 0, "all_n": 0})
    for s in filtered:
        rid = s["rid"]
        if rid not in segments:
            continue
        seg = segments[rid]
        key = s["qid"]
        stats[key]["all_f"] += s["fav"]
        stats[key]["all_n"] += 1
        if seg == 1:
            stats[key]["q1_f"] += s["fav"]
            stats[key]["q1_n"] += 1
        if seg == 5:
            stats[key]["q5_f"] += s["fav"]
            stats[key]["q5_n"] += 1

    items = []
    for qid, st in stats.items():
        if st["all_n"] < 20:
            continue
        construct = get_construct(qid)
        if not construct:
            continue
        q1_rate = st["q1_f"] / st["q1_n"] if st["q1_n"] > 10 else None
        q5_rate = st["q5_f"] / st["q5_n"] if st["q5_n"] > 10 else None
        items.append({
            "qid": qid,
            "construct": construct,
            "q1_rate": q1_rate,
            "q5_rate": q5_rate,
            "overall_rate": st["all_f"] / st["all_n"],
            "n": st["all_n"],
            "q1_n": st["q1_n"],
            "text": qid_text.get(qid, ""),
        })
    return items


def compute_segment_breakdown(scored, segments, qid):
    """Per-segment support rate for a single item."""
    seg_data = defaultdict(lambda: {"fav": 0, "n": 0})
    for s in scored:
        if s["qid"] != qid:
            continue
        rid = s["rid"]
        if rid not in segments:
            continue
        seg = segments[rid]
        seg_data[seg]["fav"] += s["fav"]
        seg_data[seg]["n"] += 1
    result = {}
    for seg in range(1, 6):
        d = seg_data[seg]
        result[seg] = {"rate": d["fav"] / d["n"] if d["n"] > 0 else 0, "n": d["n"]}
    return result


def compute_demo_breakdown(scored, demo_lookup, qid, demo_cat):
    """Demographic breakdown for a single item."""
    demo_data = defaultdict(lambda: {"fav": 0, "n": 0})
    for s in scored:
        if s["qid"] != qid:
            continue
        rid = s["rid"]
        demo = demo_lookup.get(rid, {})
        val = demo.get(demo_cat, "Unknown")
        if val and val != "Unknown":
            demo_data[val]["fav"] += s["fav"]
            demo_data[val]["n"] += 1
    result = {}
    for val, d in sorted(demo_data.items()):
        if d["n"] >= 10:
            result[val] = {"rate": d["fav"] / d["n"], "n": d["n"]}
    return result


def compute_bridge_for_item(scored, segments, qid, min_overlap=15):
    """Find bridge connections from/to the construct of the selected item."""
    target_rids = {rid for rid, seg in segments.items() if seg in (1, 2)}
    construct = get_construct(qid)
    if not construct:
        return []

    # Build respondent → construct → fav_rate for anti-reform
    resp_con = defaultdict(lambda: defaultdict(lambda: {"f": 0, "n": 0}))
    for s in scored:
        if s["rid"] not in target_rids:
            continue
        resp_con[s["rid"]][s["construct"]]["f"] += s["fav"]
        resp_con[s["rid"]][s["construct"]]["n"] += 1

    resp_scores = {}
    for rid, cons in resp_con.items():
        resp_scores[rid] = {}
        for c, d in cons.items():
            if d["n"] >= 1:
                resp_scores[rid][c] = d["f"] / d["n"]

    # All constructs
    all_cons = set()
    for rid, cons in resp_scores.items():
        all_cons.update(cons.keys())

    bridges = []
    for other in sorted(all_cons):
        if other == construct:
            continue
        src_fav_tgt = []
        src_unfav_tgt = []
        for rid, cons in resp_scores.items():
            if construct not in cons or other not in cons:
                continue
            if cons[construct] > 0.5:
                src_fav_tgt.append(cons[other])
            elif cons[construct] < 0.5:
                src_unfav_tgt.append(cons[other])
        if len(src_fav_tgt) >= min_overlap and len(src_unfav_tgt) >= min_overlap:
            p_fav = np.mean(src_fav_tgt)
            p_unfav = np.mean(src_unfav_tgt)
            bridges.append({
                "target": other,
                "p_given_agree": p_fav,
                "p_given_disagree": p_unfav,
                "lift": p_fav - p_unfav,
                "n_agree": len(src_fav_tgt),
                "n_disagree": len(src_unfav_tgt),
            })
    bridges.sort(key=lambda x: -x["lift"])
    return bridges


# ══════════════════════════════════════════════════════════════════
# MAIN PAGE
# ══════════════════════════════════════════════════════════════════

st.title("🎯 Message Testing")
st.caption("Each dot is a survey item. X = anti-reform support. Y = overall support. Click a dot for full detail.")

if not SCORING_AVAILABLE:
    st.error("content_scoring.py not found. Cannot score responses.")
    st.stop()

# Load data
scored, qid_text, demo_lookup, disposition, segments = load_data()
n_resp = len(disposition)

# ── Sidebar filters ──
with st.sidebar:
    st.markdown("### Filters")

    # State filter
    states = ["All States"] + sorted(set(SURVEY_STATE.values()))
    state_filter = st.selectbox("State", states)

    # Construct filter
    all_constructs = sorted(set(s["construct"] for s in scored if s["rid"] in segments))
    construct_options = ["All Constructs"] + all_constructs
    construct_filter = st.selectbox("Construct", construct_options)

    # Demo filter
    demo_cats = {
        "party_id": "Party", "ideology": "Ideology", "race_ethnicity": "Race",
        "age_bracket": "Age", "gender": "Gender", "education": "Education",
    }
    demo_filter_cat = st.selectbox("Demographic Category", ["None"] + list(demo_cats.values()))

    demo_filter = "All"
    if demo_filter_cat != "None":
        cat_key = [k for k, v in demo_cats.items() if v == demo_filter_cat][0]
        vals = sorted(set(d.get(cat_key, "") for d in demo_lookup.values() if d.get(cat_key)))
        if vals:
            demo_val = st.selectbox(f"{demo_filter_cat} Group", ["All"] + vals)
            if demo_val != "All":
                demo_filter = f"{cat_key}::{demo_val}"

    # Y-axis toggle
    y_mode = st.radio("Y Axis", ["Overall Support", "Q5 (Pro-Reform) Support"], index=0)

    st.divider()
    st.metric("Respondents", f"{n_resp:,}")
    seg_counts = defaultdict(int)
    for s in segments.values():
        seg_counts[s] += 1
    st.caption(f"Q1 (anti): {seg_counts[1]:,} | Q5 (pro): {seg_counts[5]:,}")

# ── Compute items ──
items = compute_item_stats(scored, segments, qid_text, state_filter,
                           demo_filter if demo_filter != "All" else None, demo_lookup)

if construct_filter != "All Constructs":
    items = [i for i in items if i["construct"] == construct_filter]

if not items:
    st.warning("No items match the current filters.")
    st.stop()

# ── Build scatter ──
df = pd.DataFrame(items)
df["q1_pct"] = df["q1_rate"].apply(lambda x: x * 100 if x is not None else None)
df["y_pct"] = df.apply(
    lambda r: (r["overall_rate"] * 100) if y_mode == "Overall Support"
    else (r["q5_rate"] * 100 if r["q5_rate"] is not None else None), axis=1)
df = df.dropna(subset=["q1_pct", "y_pct"])

if df.empty:
    st.warning("Not enough data for the selected filters.")
    st.stop()

# Tier info
df["tier"] = df["construct"].apply(lambda c: TIER_MAP.get(c, ""))

# Color by construct
fig = px.scatter(
    df, x="q1_pct", y="y_pct",
    color="construct",
    hover_name="qid",
    hover_data={
        "construct": True,
        "q1_pct": ":.0f",
        "y_pct": ":.0f",
        "n": ":,",
        "tier": True,
        "q1_rate": False,
        "q5_rate": False,
        "overall_rate": False,
        "q1_n": False,
        "text": False,
    },
    size="n",
    size_max=18,
    labels={
        "q1_pct": "Q1 (Anti-Reform) Support %",
        "y_pct": "Overall Support %" if y_mode == "Overall Support" else "Q5 (Pro-Reform) Support %",
    },
)

# Quadrant lines at 50%
fig.add_hline(y=50, line_dash="dash", line_color="#D4D0C8", line_width=1)
fig.add_vline(x=50, line_dash="dash", line_color="#D4D0C8", line_width=1)

# Quadrant labels
fig.add_annotation(x=25, y=95, text="Choir Only", showarrow=False,
                   font=dict(color=TEXT3, size=11), opacity=0.7)
fig.add_annotation(x=75, y=95, text="Winners", showarrow=False,
                   font=dict(color="#1B6B3A", size=12, family="Playfair Display"), opacity=0.9)
fig.add_annotation(x=25, y=5, text="Locked", showarrow=False,
                   font=dict(color=TEXT3, size=11), opacity=0.7)
fig.add_annotation(x=75, y=5, text="Niche Crack", showarrow=False,
                   font=dict(color=GOLD_MID, size=11), opacity=0.7)

fig.update_layout(
    template="plotly_white",
    paper_bgcolor="#FAF9F6",
    plot_bgcolor="#FFFFFF",
    height=550,
    margin=dict(l=60, r=20, t=40, b=60),
    xaxis=dict(range=[0, 100], dtick=10, gridcolor="#E8E4DC", title_font=dict(color=NAVY)),
    yaxis=dict(range=[0, 100], dtick=10, gridcolor="#E8E4DC", title_font=dict(color=NAVY)),
    legend=dict(
        font=dict(size=10, color=NAVY),
        bgcolor="rgba(250,249,246,0.9)",
        bordercolor=BORDER2,
        borderwidth=1,
    ),
    font=dict(family="DM Sans", color=NAVY),
)

# Show scatter
selected_points = st.plotly_chart(fig, use_container_width=True, on_select="rerun", key="scatter")

# ── Determine selected item ──
selected_qid = None
if selected_points and selected_points.selection and selected_points.selection.points:
    pt = selected_points.selection.points[0]
    idx = pt.get("point_index")
    curve = pt.get("curve_number", 0)
    # Map back to QID from the dataframe
    construct_name = df["construct"].unique()
    # Plotly groups by color (construct), so we need to find the right row
    traces = sorted(df["construct"].unique())
    if curve < len(traces):
        sub = df[df["construct"] == traces[curve]]
        if idx is not None and idx < len(sub):
            selected_qid = sub.iloc[idx]["qid"]

# Fallback: manual selector
if not selected_qid:
    qid_options = sorted(df["qid"].tolist())
    if qid_options:
        selected_qid = st.selectbox("Or select an item:", ["(click a dot above)"] + qid_options)
        if selected_qid == "(click a dot above)":
            selected_qid = None

# ══════════════════════════════════════════════════════════════════
# DETAIL PANEL
# ══════════════════════════════════════════════════════════════════

if selected_qid:
    st.divider()

    item_row = df[df["qid"] == selected_qid].iloc[0] if selected_qid in df["qid"].values else None
    construct = get_construct(selected_qid)
    tier_label = TIER_MAP.get(construct, "")
    question_text = qid_text.get(selected_qid, "")

    # Header
    col_h1, col_h2 = st.columns([3, 1])
    with col_h1:
        st.markdown(f"### {selected_qid}")
        if tier_label:
            st.markdown(
                f'{tier_badge_html(construct)} &nbsp; '
                f'<span style="color: {TEXT3};">Construct: <strong>{construct}</strong></span>',
                unsafe_allow_html=True)
    with col_h2:
        if item_row is not None:
            st.metric("Q1 Support", f"{item_row['q1_pct']:.0f}%")

    # Question text
    st.markdown(f'<div class="detail-card"><strong>Question:</strong><br>{question_text}</div>',
                unsafe_allow_html=True)

    # ── Segment breakdown ──
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### Segment Breakdown")
        seg_data = compute_segment_breakdown(scored, segments, selected_qid)
        seg_labels = ["Q1 (Anti)", "Q2", "Q3 (Middle)", "Q4", "Q5 (Pro)"]
        seg_color_list = [SEGMENT_COLORS[i] for i in range(1, 6)]

        seg_df = pd.DataFrame({
            "Segment": seg_labels,
            "Support %": [seg_data[i+1]["rate"] * 100 for i in range(5)],
            "n": [seg_data[i+1]["n"] for i in range(5)],
        })

        fig_seg = go.Figure(go.Bar(
            x=seg_df["Support %"],
            y=seg_df["Segment"],
            orientation="h",
            marker_color=seg_color_list,
            text=[f'{v:.0f}% (n={n})' for v, n in zip(seg_df["Support %"], seg_df["n"])],
            textposition="auto",
            textfont=dict(size=12, color="white"),
        ))
        fig_seg.update_layout(
            template="plotly_white",
            paper_bgcolor="#FAF9F6",
            plot_bgcolor="#FFFFFF",
            height=250,
            margin=dict(l=90, r=20, t=10, b=10),
            xaxis=dict(range=[0, 100], gridcolor="#E8E4DC", title=""),
            yaxis=dict(autorange="reversed"),
            font=dict(family="DM Sans", color=NAVY),
        )
        st.plotly_chart(fig_seg, use_container_width=True)

    # ── Demographic breakdown ──
    with col2:
        demo_cat_sel = st.selectbox("Demographic Cut", list(demo_cats.values()), key="detail_demo")
        cat_key = [k for k, v in demo_cats.items() if v == demo_cat_sel][0]
        demo_data = compute_demo_breakdown(scored, demo_lookup, selected_qid, cat_key)

        if demo_data:
            demo_df = pd.DataFrame([
                {"Group": k, "Support %": v["rate"] * 100, "n": v["n"]}
                for k, v in demo_data.items()
            ])

            fig_demo = go.Figure(go.Bar(
                x=demo_df["Support %"],
                y=demo_df["Group"],
                orientation="h",
                marker_color="#1155AA",
                text=[f'{v:.0f}% (n={n})' for v, n in zip(demo_df["Support %"], demo_df["n"])],
                textposition="auto",
                textfont=dict(size=11, color="white"),
            ))
            fig_demo.update_layout(
                template="plotly_white",
                paper_bgcolor="#FAF9F6",
                plot_bgcolor="#FFFFFF",
                height=250,
                margin=dict(l=150, r=20, t=10, b=10),
                xaxis=dict(range=[0, 100], gridcolor="#E8E4DC", title=""),
                yaxis=dict(autorange="reversed"),
                font=dict(family="DM Sans", color=NAVY),
            )
            st.plotly_chart(fig_demo, use_container_width=True)
        else:
            st.info("Not enough demographic data for this item.")

    # ── States fielded ──
    st.markdown("#### States Fielded")
    item_surveys = set(s["sid"] for s in scored if s["qid"] == selected_qid)
    item_states = sorted(set(SURVEY_STATE.get(sid, sid) for sid in item_surveys))
    st.markdown(", ".join(f"**{s}**" for s in item_states) if item_states else "Unknown")

    # ── Bridge connections ──
    st.markdown("#### Bridge Connections (Anti-Reform Q1+Q2)")
    st.caption("Among anti-reformers who AGREE with this construct, what else do they support?")

    bridges = compute_bridge_for_item(scored, segments, selected_qid)
    if bridges:
        top_bridges = bridges[:10]
        bridge_df = pd.DataFrame(top_bridges)
        bridge_df["lift_pct"] = bridge_df["lift"].apply(lambda x: f"{x:+.0%}")
        bridge_df["agree_pct"] = bridge_df["p_given_agree"].apply(lambda x: f"{x:.0%}")
        bridge_df["disagree_pct"] = bridge_df["p_given_disagree"].apply(lambda x: f"{x:.0%}")

        fig_bridge = go.Figure()
        fig_bridge.add_trace(go.Bar(
            name="If AGREE with source",
            y=bridge_df["target"],
            x=bridge_df["p_given_agree"] * 100,
            orientation="h",
            marker_color=BRIDGE_AGREE_COLOR,
            text=bridge_df["agree_pct"],
            textposition="auto",
        ))
        fig_bridge.add_trace(go.Bar(
            name="If DISAGREE with source",
            y=bridge_df["target"],
            x=bridge_df["p_given_disagree"] * 100,
            orientation="h",
            marker_color=BRIDGE_DISAGREE_COLOR,
            text=bridge_df["disagree_pct"],
            textposition="auto",
        ))
        fig_bridge.update_layout(
            template="plotly_white",
            paper_bgcolor="#FAF9F6",
            plot_bgcolor="#FFFFFF",
            barmode="group",
            height=max(250, len(top_bridges) * 35),
            margin=dict(l=150, r=20, t=10, b=30),
            xaxis=dict(range=[0, 100], gridcolor="#E8E4DC", title="Support %"),
            yaxis=dict(autorange="reversed"),
            legend=dict(orientation="h", yanchor="bottom", y=-0.2),
            font=dict(family="DM Sans", color=NAVY),
        )
        st.plotly_chart(fig_bridge, use_container_width=True)
    else:
        st.info("Not enough co-fielded data for bridge analysis. More surveys with overlapping constructs will fill this in.")

# ── Footer ──
portal_footer()
