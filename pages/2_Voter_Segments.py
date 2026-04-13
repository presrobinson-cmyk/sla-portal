"""
Voter Segments — SLA Portal
Shows the five voter segments (Skeptics → Champions), their demographic profiles,
and a heat map of topic support across segments.
"""

import streamlit as st
from pathlib import Path
import sys
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import requests
from collections import defaultdict

# Auth gate
sys.path.insert(0, str(Path(__file__).parent.parent))
from auth import require_auth
from chat_widget import render_chat

# Theme
from theme import (
    apply_theme, portal_footer, get_supabase_config, get_supabase_headers,
    CJ_SURVEYS, SURVEY_STATE, TIER_MAP,
    NAVY, NAVY2, GOLD, GOLD_MID, TEXT1, TEXT2, TEXT3, BORDER2, BG, CARD_BG,
)

# Scoring engine
sys.path.insert(0, str(Path(__file__).parent.parent))
try:
    from content_scoring import SKIPPED_QIDS, get_construct, score_content
    SCORING_AVAILABLE = True
except ImportError:
    SCORING_AVAILABLE = False

st.set_page_config(page_title="Voter Segments — SLA Portal", page_icon="👥", layout="wide")

apply_theme()
username = require_auth("Second Look Alliance", accent_color=GOLD)

SUPABASE_URL, SUPABASE_KEY = get_supabase_config()
HEADERS = get_supabase_headers()

# Segment definitions
SEGMENT_NAMES = ["Skeptics", "Lean Skeptic", "Middle", "Lean Reform", "Champions"]
SEGMENT_COLORS = ["#8B1A1A", "#B85400", "#B8870A", "#1155AA", "#1B6B3A"]
SEGMENT_DESC = {
    "Skeptics": "Bottom 20% — Strongest opposition. Believe the system works. Only Entry-tier topics gain any traction.",
    "Lean Skeptic": "20-40th percentile — Persuadable with the right framing. Bridge topics are the key.",
    "Middle": "40-60th percentile — Open to reform arguments. Respond to cost/efficiency and fairness framing.",
    "Lean Reform": "60-80th percentile — Broadly favorable but inconsistent. Need inoculation against opposition attacks.",
    "Champions": "Top 20% — Strongest supporters. Already aligned. Focus on mobilization, not persuasion.",
}

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
    "PROS": "Prosecutor Accountability", "CAND": "Candidate Favorability",
    "TOUGHCRIME": "Tough on Crime Attitudes", "ISSUE_SALIENCE": "Issue Importance",
    "IMPACT": "Personal Impact", "DETER": "Deterrence Beliefs",
    "FISCAL": "Fiscal Responsibility", "DP_ABOLITION": "Death Penalty Abolition",
    "DP_RELIABILITY": "Death Penalty Reliability", "LWOP": "Life Without Parole",
    "COMPASSION": "Compassionate Release",
}

# Gauge constructs — excluded from heat map (not reform topics)
GAUGE_CONSTRUCTS = {"CAND", "TOUGHCRIME", "ISSUE_SALIENCE", "IMPACT"}


# ══════════════════════════════════════════════════════════════════
# DATA LOADING
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


@st.cache_data(ttl=3600, show_spinner="Loading voter segment data...")
def load_segment_data():
    """Pull L2 responses and L1 demographics, score, compute segments."""
    # Pull L2 responses
    all_l2 = []
    for sid in CJ_SURVEYS:
        rows = _paginate(
            f"{SUPABASE_URL}/rest/v1/l2_responses"
            f"?select=respondent_id,survey_id,question_id,question_text,response"
            f"&survey_id=eq.{sid}",
            HEADERS,
        )
        all_l2.extend(rows)

    # Pull L1 demographics
    all_l1 = []
    for sid in CJ_SURVEYS:
        rows = _paginate(
            f"{SUPABASE_URL}/rest/v1/l1_respondents"
            f"?select=respondent_id,survey_id,party_id,ideology,race_ethnicity,age_bracket,gender,education"
            f"&survey_id=eq.{sid}",
            HEADERS,
        )
        all_l1.extend(rows)

    demo_lookup = {d["respondent_id"]: d for d in all_l1}

    # Score all responses
    scored = []
    for r in all_l2:
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

    # Compute disposition scores (average favorable rate per respondent)
    resp_agg = defaultdict(lambda: {"fav": 0, "n": 0})
    for s in scored:
        resp_agg[s["rid"]]["fav"] += s["fav"]
        resp_agg[s["rid"]]["n"] += 1

    disposition = {}
    for rid, d in resp_agg.items():
        if d["n"] >= 3:
            disposition[rid] = d["fav"] / d["n"]

    # Assign quintiles (1=Skeptics, 5=Champions)
    sorted_scores = sorted(disposition.items(), key=lambda x: x[1])
    n = len(sorted_scores)
    segments = {}
    for i, (rid, sc) in enumerate(sorted_scores):
        segments[rid] = min(int(i / n * 5) + 1, 5)

    # Compute per-construct per-segment support rates
    con_seg = defaultdict(lambda: defaultdict(lambda: {"fav": 0, "n": 0}))
    for s in scored:
        rid = s["rid"]
        if rid not in segments:
            continue
        seg = segments[rid]
        con = s["construct"]
        con_seg[con][seg]["fav"] += s["fav"]
        con_seg[con][seg]["n"] += 1

    # Build heat map data
    heat_map = {}
    for con, seg_data in con_seg.items():
        if con in GAUGE_CONSTRUCTS:
            continue
        rates = {}
        total_n = 0
        for seg_num in range(1, 6):
            d = seg_data[seg_num]
            total_n += d["n"]
            rates[seg_num] = (d["fav"] / d["n"] * 100) if d["n"] >= 10 else None
        if total_n >= 50:
            heat_map[con] = rates

    # Compute demographic profiles per segment
    seg_demos = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
    for rid, seg in segments.items():
        demo = demo_lookup.get(rid, {})
        for cat in ["party_id", "ideology", "race_ethnicity", "age_bracket", "gender", "education"]:
            val = demo.get(cat)
            if val:
                seg_demos[seg][cat][val] += 1

    seg_counts = defaultdict(int)
    for seg in segments.values():
        seg_counts[seg] += 1

    return heat_map, seg_demos, seg_counts, len(disposition)


# ══════════════════════════════════════════════════════════════════
# MAIN PAGE
# ══════════════════════════════════════════════════════════════════

st.title("👥 Voter Segments")
st.markdown(
    "Five voter segments based on overall disposition toward reform — from strongest opposition to strongest support. "
    "Each person's segment is determined by their average response across all scored survey questions."
)

if not SCORING_AVAILABLE:
    st.error("content_scoring.py not found. Cannot compute segments.")
    st.stop()

heat_map, seg_demos, seg_counts, n_respondents = load_segment_data()

if not heat_map:
    st.warning("No segment data available.")
    st.stop()

# ── KPI row ──
cols = st.columns(5)
for i, (name, color) in enumerate(zip(SEGMENT_NAMES, SEGMENT_COLORS)):
    with cols[i]:
        count = seg_counts.get(i + 1, 0)
        st.markdown(f"""
        <div style="background:{CARD_BG};border:1px solid {BORDER2};border-top:3px solid {color};
            border-radius:8px;padding:0.75rem;text-align:center;">
            <div style="font-weight:700;color:{color};font-size:1rem;">{name}</div>
            <div style="font-size:1.4rem;font-weight:800;color:{NAVY};">{count:,}</div>
            <div style="font-size:0.7rem;color:{TEXT3};">respondents</div>
        </div>
        """, unsafe_allow_html=True)

st.divider()

# ── Sidebar: segment selector ──
with st.sidebar:
    st.markdown("### Segment Focus")
    focus_seg = st.radio(
        "Highlight segment:",
        ["All Segments"] + SEGMENT_NAMES,
        key="seg_focus",
    )

    view_mode = st.radio("View", ["Heat Map", "Segment Profiles", "Topic Comparison"], key="seg_view")

    st.divider()
    st.metric("Total Respondents", f"{n_respondents:,}")


# ══════════════════════════════════════════════════════════════════
# HEAT MAP VIEW — topics × segments
# ══════════════════════════════════════════════════════════════════

if view_mode == "Heat Map":
    st.subheader("Topic Support by Voter Segment")
    st.caption(
        "Each cell shows the support rate for a topic within a voter segment. "
        "Dark green = high support. Red = low support. "
        "The gap between Skeptics and Champions reveals persuasion potential."
    )

    # Build matrix
    constructs_sorted = sorted(heat_map.keys(), key=lambda c: TIER_MAP.get(c, "ZZZ"))
    topic_labels = [CONSTRUCT_LABELS.get(c, c) for c in constructs_sorted]
    tiers = [TIER_MAP.get(c, "—") for c in constructs_sorted]

    z_values = []
    hover_texts = []
    for con in constructs_sorted:
        row = []
        hover_row = []
        for seg_num in range(1, 6):
            val = heat_map[con].get(seg_num)
            row.append(val if val is not None else 0)
            if val is not None:
                hover_row.append(
                    f"{CONSTRUCT_LABELS.get(con, con)}<br>"
                    f"{SEGMENT_NAMES[seg_num-1]}: {val:.0f}%"
                )
            else:
                hover_row.append(f"{CONSTRUCT_LABELS.get(con, con)}<br>{SEGMENT_NAMES[seg_num-1]}: insufficient data")
        z_values.append(row)
        hover_texts.append(hover_row)

    fig = go.Figure(data=go.Heatmap(
        z=z_values,
        x=SEGMENT_NAMES,
        y=[f"{t}  •  {TIER_MAP.get(c, '')}" for t, c in zip(topic_labels, constructs_sorted)],
        hovertext=hover_texts,
        hoverinfo="text",
        colorscale=[
            [0, "#8B1A1A"],     # red for low support
            [0.4, "#F5E6CC"],   # neutral cream
            [0.6, "#C5E1A5"],   # light green
            [1.0, "#1B6B3A"],   # dark green for high support
        ],
        zmin=20,
        zmax=95,
        text=[[f"{v:.0f}" if v else "" for v in row] for row in z_values],
        texttemplate="%{text}%",
        textfont=dict(size=11, color=NAVY),
    ))

    fig.update_layout(
        template="plotly_white",
        paper_bgcolor=BG,
        plot_bgcolor=CARD_BG,
        height=max(500, len(constructs_sorted) * 28 + 100),
        margin=dict(l=280, r=30, t=30, b=60),
        xaxis=dict(side="top", tickfont=dict(size=12, color=NAVY)),
        yaxis=dict(autorange="reversed", tickfont=dict(size=11)),
        font=dict(family="DM Sans", color=NAVY),
    )

    st.plotly_chart(fig, use_container_width=True, key="seg_heatmap")

    # Persuasion gap table below heat map
    st.markdown("#### Biggest Persuasion Gaps")
    st.caption("Topics with the largest difference between Skeptic and Champion support — your biggest persuasion opportunities.")

    gap_data = []
    for con in constructs_sorted:
        skep = heat_map[con].get(1)
        champ = heat_map[con].get(5)
        if skep is not None and champ is not None:
            gap_data.append({
                "Topic": CONSTRUCT_LABELS.get(con, con),
                "Tier": TIER_MAP.get(con, "—"),
                "Skeptic": f"{skep:.0f}%",
                "Champion": f"{champ:.0f}%",
                "Gap": champ - skep,
                "_gap_num": champ - skep,
            })

    if gap_data:
        gap_df = pd.DataFrame(gap_data).sort_values("_gap_num", ascending=False)
        gap_df["Gap"] = gap_df["_gap_num"].apply(lambda g: f"{g:+.0f}pp")
        st.dataframe(
            gap_df[["Topic", "Tier", "Skeptic", "Champion", "Gap"]],
            use_container_width=True, hide_index=True, height=400,
        )


# ══════════════════════════════════════════════════════════════════
# SEGMENT PROFILES — demographic makeup of each segment
# ══════════════════════════════════════════════════════════════════

elif view_mode == "Segment Profiles":
    st.subheader("Who's in Each Segment?")
    st.caption("Demographic breakdown shows what each voter segment looks like. Use the sidebar to focus on a specific segment.")

    demo_labels = {
        "party_id": "Party", "ideology": "Ideology", "race_ethnicity": "Race/Ethnicity",
        "age_bracket": "Age", "gender": "Gender", "education": "Education",
    }

    if focus_seg == "All Segments":
        display_segs = list(range(1, 6))
    else:
        display_segs = [SEGMENT_NAMES.index(focus_seg) + 1]

    for seg_num in display_segs:
        seg_name = SEGMENT_NAMES[seg_num - 1]
        seg_color = SEGMENT_COLORS[seg_num - 1]
        seg_count = seg_counts.get(seg_num, 0)
        seg_desc = SEGMENT_DESC.get(seg_name, "")

        st.markdown(f"""
        <div style="background:{CARD_BG};border:1px solid {BORDER2};border-left:4px solid {seg_color};
            border-radius:10px;padding:1.25rem;margin-bottom:0.5rem;">
            <div style="font-family:'Playfair Display',serif;font-weight:700;color:{seg_color};
                font-size:1.15rem;">{seg_name}</div>
            <div style="font-size:0.85rem;color:{TEXT3};margin-bottom:0.5rem;">
                {seg_count:,} respondents — {seg_desc}
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Show top 2-3 demographics for this segment
        demo_data = seg_demos.get(seg_num, {})
        demo_cols = st.columns(3)

        for col_idx, (cat, cat_label) in enumerate(list(demo_labels.items())[:3]):
            with demo_cols[col_idx]:
                vals = demo_data.get(cat, {})
                if not vals:
                    st.caption(f"{cat_label}: No data")
                    continue

                total = sum(vals.values())
                sorted_vals = sorted(vals.items(), key=lambda x: x[1], reverse=True)[:6]

                fig_demo = go.Figure(go.Bar(
                    y=[v[0][:20] for v in sorted_vals],
                    x=[v[1] / total * 100 for v in sorted_vals],
                    orientation="h",
                    marker_color=seg_color,
                    text=[f"{v[1] / total * 100:.0f}%" for v in sorted_vals],
                    textposition="auto",
                    textfont=dict(size=10, color="white"),
                ))
                fig_demo.update_layout(
                    title=dict(text=cat_label, font=dict(size=12, color=NAVY)),
                    template="plotly_white",
                    paper_bgcolor=BG,
                    plot_bgcolor=CARD_BG,
                    height=180,
                    margin=dict(l=120, r=10, t=30, b=10),
                    xaxis=dict(range=[0, 100], showticklabels=False, showgrid=False),
                    yaxis=dict(autorange="reversed", tickfont=dict(size=10)),
                    font=dict(family="DM Sans", color=NAVY),
                )
                st.plotly_chart(fig_demo, use_container_width=True, key=f"demo_{seg_num}_{cat}")

        # Second row of demographics
        demo_cols2 = st.columns(3)
        for col_idx, (cat, cat_label) in enumerate(list(demo_labels.items())[3:6]):
            with demo_cols2[col_idx]:
                vals = demo_data.get(cat, {})
                if not vals:
                    st.caption(f"{cat_label}: No data")
                    continue

                total = sum(vals.values())
                sorted_vals = sorted(vals.items(), key=lambda x: x[1], reverse=True)[:6]

                fig_demo = go.Figure(go.Bar(
                    y=[v[0][:20] for v in sorted_vals],
                    x=[v[1] / total * 100 for v in sorted_vals],
                    orientation="h",
                    marker_color=seg_color,
                    text=[f"{v[1] / total * 100:.0f}%" for v in sorted_vals],
                    textposition="auto",
                    textfont=dict(size=10, color="white"),
                ))
                fig_demo.update_layout(
                    title=dict(text=cat_label, font=dict(size=12, color=NAVY)),
                    template="plotly_white",
                    paper_bgcolor=BG,
                    plot_bgcolor=CARD_BG,
                    height=180,
                    margin=dict(l=120, r=10, t=30, b=10),
                    xaxis=dict(range=[0, 100], showticklabels=False, showgrid=False),
                    yaxis=dict(autorange="reversed", tickfont=dict(size=10)),
                    font=dict(family="DM Sans", color=NAVY),
                )
                st.plotly_chart(fig_demo, use_container_width=True, key=f"demo2_{seg_num}_{cat}")

        st.divider()


# ══════════════════════════════════════════════════════════════════
# TOPIC COMPARISON — bar chart comparing segments for one topic
# ══════════════════════════════════════════════════════════════════

elif view_mode == "Topic Comparison":
    st.subheader("Compare Segments on a Topic")
    st.caption("Select a topic to see how support varies across voter segments.")

    topic_options = sorted(
        [c for c in heat_map.keys()],
        key=lambda c: CONSTRUCT_LABELS.get(c, c),
    )
    topic_labels_list = [CONSTRUCT_LABELS.get(c, c) for c in topic_options]
    label_to_code = dict(zip(topic_labels_list, topic_options))

    selected_label = st.selectbox("Topic", sorted(topic_labels_list), key="seg_topic")
    selected_con = label_to_code.get(selected_label, "")

    if selected_con and selected_con in heat_map:
        rates = heat_map[selected_con]
        bar_vals = [rates.get(i, 0) or 0 for i in range(1, 6)]

        fig_comp = go.Figure(go.Bar(
            x=SEGMENT_NAMES,
            y=bar_vals,
            marker_color=SEGMENT_COLORS,
            text=[f"{v:.0f}%" if v else "—" for v in bar_vals],
            textposition="outside",
            textfont=dict(size=13, color=NAVY),
        ))

        fig_comp.update_layout(
            template="plotly_white",
            paper_bgcolor=BG,
            plot_bgcolor=CARD_BG,
            height=400,
            margin=dict(l=40, r=20, t=40, b=60),
            yaxis=dict(range=[0, 105], title="Support %", gridcolor="#E8E4DC",
                       title_font=dict(color=NAVY)),
            xaxis=dict(tickfont=dict(size=12, color=NAVY)),
            font=dict(family="DM Sans", color=NAVY),
        )

        st.plotly_chart(fig_comp, use_container_width=True, key="seg_compare_bar")

        # Tier and gap info
        tier = TIER_MAP.get(selected_con, "—")
        skep = rates.get(1)
        champ = rates.get(5)
        gap = (champ - skep) if skep is not None and champ is not None else None

        c1, c2, c3 = st.columns(3)
        c1.metric("Persuasion Tier", tier)
        if skep is not None:
            c2.metric("Skeptic Support", f"{skep:.0f}%")
        if gap is not None:
            c3.metric("Skeptic → Champion Gap", f"{gap:+.0f}pp")


render_chat("voter_segments")
portal_footer()
