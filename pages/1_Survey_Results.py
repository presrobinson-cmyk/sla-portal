"""
Message Persuasion Testing (MPT v3)
Scatter: MrP Reach × Universality. Each dot is a scored survey item.
Quadrants: Golden Zone / Primary Fuel / General Arsenal / Dead Weight.
Reach from MrP-adjusted population support. Universality from party-based gap.
"""

import streamlit as st
from pathlib import Path
import sys
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import requests
from collections import defaultdict

# Auth gate
sys.path.insert(0, str(Path(__file__).parent.parent))
from auth import require_auth

# Theme
from theme import (
    apply_theme, portal_footer, get_supabase_config, get_supabase_headers,
    CJ_SURVEYS, SURVEY_STATE, TIER_MAP, tier_badge_html,
    NAVY, NAVY2, GOLD, GOLD_MID, TEXT1, TEXT2, TEXT3, BORDER2, BG, CARD_BG,
    STATE_COLORS, STATE_ABBR,
)

# Scoring engine (bundled locally)
sys.path.insert(0, str(Path(__file__).parent.parent))
try:
    from content_scoring import FAVORABLE_DIRECTION, SKIPPED_QIDS, get_construct, score_content
    SCORING_AVAILABLE = True
except ImportError:
    SCORING_AVAILABLE = False

st.set_page_config(
    page_title="Message Persuasion Testing — SLA Portal",
    page_icon="⚡",
    layout="wide",
)

apply_theme()
username = require_auth("Second Look Alliance", accent_color=GOLD)

SUPABASE_URL, SUPABASE_KEY = get_supabase_config()
HEADERS = get_supabase_headers()

# Quadrant colors
QUAD_COLORS = {
    "Golden Zone": "#1B6B3A",
    "Base Hardening": "#1155AA",
    "Coalition Building": "#B85400",
    "Ineffective": "#8B1A1A",
}

# Human-readable construct names (replace internal codes)
CONSTRUCT_LABELS = {
    "PD_FUNDING": "Public Defender Funding",
    "INVEST": "Community Investment",
    "LIT": "Literacy Programs",
    "COUNSEL_ACCESS": "Right to Counsel",
    "DV": "Domestic Violence",
    "CAND-DV": "Candidates on DV",
    "PROP": "Property Crime Reform",
    "REDEMPTION": "Redemption / Second Chances",
    "EXPUNGE": "Record Expungement",
    "SENTREVIEW": "Sentence Review",
    "JUDICIAL": "Judicial Discretion",
    "RETRO": "Retroactive Relief",
    "FINES": "Fines & Fees",
    "MAND": "Mandatory Minimums",
    "BAIL": "Bail Reform",
    "REENTRY": "Reentry Programs",
    "RECORD": "Criminal Record Reform",
    "JUV": "Juvenile Justice",
    "FAMILY": "Family Reunification",
    "ELDERLY": "Compassionate Release",
    "COURT": "Court Reform",
    "COURTREVIEW": "Court Review Process",
    "TRUST": "System Trust",
    "PLEA": "Plea Bargaining Reform",
    "PROS": "Prosecutor Accountability",
    "CAND": "Candidate Favorability",
    "TOUGHCRIME": "Tough on Crime Attitudes",
    "ISSUE_SALIENCE": "Issue Importance",
    "IMPACT": "Personal Impact",
    "DETER": "Deterrence Beliefs",
    "FISCAL": "Fiscal Responsibility",
    "DP_ABOLITION": "Death Penalty Abolition",
    "DP_RELIABILITY": "Death Penalty Reliability",
    "LWOP": "Life Without Parole",
    "COMPASSION": "Compassionate Release",
}


# ══════════════════════════════════════════════════════════════════
# DATA LOADING
# ══════════════════════════════════════════════════════════════════

def _paginate(url_base, headers, limit=1000, max_rows=200000):
    """Paginate a Supabase REST query."""
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


@st.cache_data(ttl=3600, show_spinner="Loading MrP estimates...")
def load_mrp_reach():
    """Compute MrP-adjusted Reach per question from mrp_estimates table.
    Reach = sum(mrp_support * pop_weight) / sum(pop_weight), pooled across surveys.
    """
    rows = _paginate(
        f"{SUPABASE_URL}/rest/v1/mrp_estimates"
        f"?select=survey_id,question_id,mrp_support,pop_weight",
        HEADERS, max_rows=80000,
    )

    # Pool across surveys for each QID
    qid_data = defaultdict(lambda: {"weighted_sum": 0.0, "weight_sum": 0.0, "surveys": set()})
    for r in rows:
        qid = r["question_id"]
        mrp = r.get("mrp_support")
        pw = r.get("pop_weight")
        if mrp is None or pw is None or pw <= 0:
            continue
        qid_data[qid]["weighted_sum"] += mrp * pw
        qid_data[qid]["weight_sum"] += pw
        qid_data[qid]["surveys"].add(r["survey_id"])

    reach = {}
    for qid, d in qid_data.items():
        if d["weight_sum"] > 0:
            reach[qid] = {
                "reach": d["weighted_sum"] / d["weight_sum"] * 100,
                "n_surveys": len(d["surveys"]),
            }
    return reach


@st.cache_data(ttl=3600, show_spinner="Computing universality...")
def load_universality():
    """Compute Universality per question from raw L2 + L1 party data.
    Universality = 100 - |R_rate - D_rate| (party gap).
    """
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

    # Pull L1 party
    all_l1 = []
    for sid in CJ_SURVEYS:
        rows = _paginate(
            f"{SUPABASE_URL}/rest/v1/l1_respondents"
            f"?select=respondent_id,party_id"
            f"&survey_id=eq.{sid}",
            HEADERS,
        )
        all_l1.extend(rows)

    party_lookup = {d["respondent_id"]: d.get("party_id", "") for d in all_l1}

    # Score responses and compute party-split rates
    q_stats = defaultdict(lambda: {
        "r_f": 0, "r_n": 0, "d_f": 0, "d_n": 0, "all_f": 0, "all_n": 0,
        "construct": None, "text": "",
    })

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
        is_fav = 1 if fav == 1 else 0

        q_stats[qid]["all_f"] += is_fav
        q_stats[qid]["all_n"] += 1
        q_stats[qid]["construct"] = construct
        if r.get("question_text"):
            q_stats[qid]["text"] = r["question_text"]

        party = party_lookup.get(r["respondent_id"], "")
        if party and "republican" in party.lower():
            q_stats[qid]["r_f"] += is_fav
            q_stats[qid]["r_n"] += 1
        elif party and "democrat" in party.lower():
            q_stats[qid]["d_f"] += is_fav
            q_stats[qid]["d_n"] += 1

    result = {}
    for qid, st in q_stats.items():
        if st["all_n"] < 20:
            continue
        if st["r_n"] >= 10 and st["d_n"] >= 10:
            r_rate = st["r_f"] / st["r_n"] * 100
            d_rate = st["d_f"] / st["d_n"] * 100
            gap = abs(r_rate - d_rate)
            univ = max(0, 100 - gap)
        else:
            univ = None

        result[qid] = {
            "universality": univ,
            "construct": st["construct"],
            "text": st["text"],
            "n": st["all_n"],
            "raw_reach": st["all_f"] / st["all_n"] * 100,
        }
    return result


@st.cache_data(ttl=3600, show_spinner="Loading state comparison...")
def load_state_reach_mrp():
    """Per-state MrP reach for cross-state comparison."""
    rows = _paginate(
        f"{SUPABASE_URL}/rest/v1/mrp_estimates"
        f"?select=survey_id,question_id,mrp_support,pop_weight",
        HEADERS, max_rows=80000,
    )

    # Group by (survey, qid)
    data = defaultdict(lambda: {"ws": 0.0, "wt": 0.0})
    for r in rows:
        key = (r["survey_id"], r["question_id"])
        mrp = r.get("mrp_support")
        pw = r.get("pop_weight")
        if mrp is None or pw is None or pw <= 0:
            continue
        data[key]["ws"] += mrp * pw
        data[key]["wt"] += pw

    state_reach = defaultdict(dict)  # qid -> {state: reach}
    for (sid, qid), d in data.items():
        if d["wt"] > 0:
            state = SURVEY_STATE.get(sid, sid)
            state_reach[qid][state] = d["ws"] / d["wt"] * 100
    return dict(state_reach)


# ══════════════════════════════════════════════════════════════════
# MAIN PAGE
# ══════════════════════════════════════════════════════════════════

st.title("⚡ Issue Landscape")
st.caption(
    "Each dot is a survey question. Horizontal = overall public support. "
    "Vertical = how well support holds across party lines. Best issues land upper-right (Golden Zone)."
)

if not SCORING_AVAILABLE:
    st.error("content_scoring.py not found. Cannot score responses.")
    st.stop()

# Load data
mrp_reach = load_mrp_reach()
univ_data = load_universality()

# Merge into items list
items = []
all_qids = set(mrp_reach.keys()) | set(univ_data.keys())
for qid in all_qids:
    mrp = mrp_reach.get(qid, {})
    udata = univ_data.get(qid, {})

    reach = mrp.get("reach")
    if reach is None:
        reach = udata.get("raw_reach")  # fallback to raw if no MrP
    if reach is None:
        continue

    universality = udata.get("universality")
    construct = udata.get("construct", "")
    if not construct:
        continue

    tier = TIER_MAP.get(construct, "")
    n = udata.get("n", 0)
    n_surveys = mrp.get("n_surveys", 0)
    text = udata.get("text", "")
    has_mrp = qid in mrp_reach

    # Quadrant
    if universality is not None:
        if reach >= 50 and universality >= 50:
            quad = "Golden Zone"
        elif reach >= 50 and universality < 50:
            quad = "Base Hardening"
        elif reach < 50 and universality >= 50:
            quad = "Coalition Building"
        else:
            quad = "Ineffective"
    else:
        quad = "Unknown"

    items.append({
        "qid": qid,
        "construct": construct,
        "tier": tier,
        "reach": reach,
        "universality": universality,
        "quadrant": quad,
        "n": n,
        "n_surveys": n_surveys,
        "text": text,
        "has_mrp": has_mrp,
    })

if not items:
    st.warning("No data available.")
    st.stop()

df = pd.DataFrame(items)
df_plot = df.dropna(subset=["universality"])

# ── Sidebar filters ──
with st.sidebar:
    st.markdown("### Filters")

    states = ["All States"] + sorted(set(SURVEY_STATE.values()))
    state_filter = st.selectbox("State", states, key="mpt_state")

    all_constructs = sorted(df["construct"].dropna().unique())
    construct_labels_list = [CONSTRUCT_LABELS.get(c, c) for c in all_constructs]
    construct_label_map = dict(zip(construct_labels_list, all_constructs))
    topic_filter = st.selectbox("Topic", ["All Topics"] + sorted(construct_labels_list), key="mpt_con")

    quad_filter = st.multiselect("Category", list(QUAD_COLORS.keys()),
                                  default=list(QUAD_COLORS.keys()), key="mpt_quad")

    view_mode = st.radio("View", ["Scatter", "Ranked List", "Cross-State"], key="mpt_view")

    st.divider()
    st.metric("Questions", f"{len(df_plot)}")
    for q, color in QUAD_COLORS.items():
        ct = len(df_plot[df_plot["quadrant"] == q])
        st.caption(f"● {q}: {ct}")

# Apply filters
filtered = df_plot.copy()
if topic_filter != "All Topics":
    real_construct = construct_label_map.get(topic_filter, topic_filter)
    filtered = filtered[filtered["construct"] == real_construct]
if quad_filter:
    filtered = filtered[filtered["quadrant"].isin(quad_filter)]

if filtered.empty:
    st.warning("No items match the current filters.")
    st.stop()


# ══════════════════════════════════════════════════════════════════
# SCATTER VIEW
# ══════════════════════════════════════════════════════════════════

if view_mode == "Scatter":
    # Add human-readable topic label for hover
    filtered = filtered.copy()
    filtered["topic"] = filtered["construct"].map(CONSTRUCT_LABELS).fillna(filtered["construct"])

    fig = px.scatter(
        filtered, x="reach", y="universality",
        color="quadrant",
        color_discrete_map=QUAD_COLORS,
        hover_name="topic",
        hover_data={
            "reach": ":.0f",
            "universality": ":.0f",
            "n": ":,",
            "quadrant": True,
            "construct": False,
            "tier": False,
            "text": False,
            "has_mrp": False,
            "n_surveys": False,
            "qid": False,
            "topic": False,
        },
        size="n",
        size_max=18,
        labels={
            "reach": "Overall Support %",
            "universality": "Cross-Party Appeal",
            "n": "Respondents",
            "quadrant": "Category",
        },
    )

    fig.add_hline(y=50, line_dash="dash", line_color="#D4D0C8", line_width=1)
    fig.add_vline(x=50, line_dash="dash", line_color="#D4D0C8", line_width=1)

    fig.add_annotation(x=25, y=97, text="Coalition Building", showarrow=False,
                       font=dict(color="#B85400", size=11), opacity=0.7)
    fig.add_annotation(x=75, y=97, text="Golden Zone", showarrow=False,
                       font=dict(color="#1B6B3A", size=13, family="Playfair Display"), opacity=0.9)
    fig.add_annotation(x=25, y=3, text="Ineffective", showarrow=False,
                       font=dict(color="#8B1A1A", size=11), opacity=0.7)
    fig.add_annotation(x=75, y=3, text="Base Hardening", showarrow=False,
                       font=dict(color="#1155AA", size=11), opacity=0.7)

    fig.update_layout(
        template="plotly_white",
        paper_bgcolor=BG,
        plot_bgcolor=CARD_BG,
        height=600,
        margin=dict(l=60, r=20, t=40, b=60),
        xaxis=dict(range=[0, 100], dtick=10, gridcolor="#E8E4DC",
                   title_font=dict(color=NAVY)),
        yaxis=dict(range=[0, 100], dtick=10, gridcolor="#E8E4DC",
                   title_font=dict(color=NAVY)),
        legend=dict(
            font=dict(size=10, color=NAVY),
            bgcolor="rgba(250,249,246,0.9)",
            bordercolor=BORDER2, borderwidth=1,
        ),
        font=dict(family="DM Sans", color=NAVY),
    )

    selected = st.plotly_chart(fig, use_container_width=True, on_select="rerun", key="mpt_scatter")

    # Detail panel
    selected_qid = None
    if selected and selected.selection and selected.selection.points:
        pt = selected.selection.points[0]
        idx = pt.get("point_index")
        curve = pt.get("curve_number", 0)
        quads = sorted(filtered["quadrant"].unique())
        if curve < len(quads):
            sub = filtered[filtered["quadrant"] == quads[curve]]
            if idx is not None and idx < len(sub):
                selected_qid = sub.iloc[idx]["qid"]

    if not selected_qid:
        qid_opts = sorted(filtered["qid"].tolist())
        if qid_opts:
            # Show human-readable labels in the dropdown
            qid_to_label = {}
            for _, r in filtered.iterrows():
                label = CONSTRUCT_LABELS.get(r["construct"], r["construct"])
                qid_to_label[r["qid"]] = f"{label}: {r['text'][:60]}..." if r.get("text") else label
            label_opts = ["(click a dot above)"] + [qid_to_label.get(q, q) for q in qid_opts]
            sel = st.selectbox("Select a question:", label_opts)
            if sel != "(click a dot above)":
                # Map label back to qid
                label_to_qid = {v: k for k, v in qid_to_label.items()}
                selected_qid = label_to_qid.get(sel)

    if selected_qid and selected_qid in filtered["qid"].values:
        row = filtered[filtered["qid"] == selected_qid].iloc[0]
        topic_label = CONSTRUCT_LABELS.get(row["construct"], row["construct"])
        st.divider()
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Overall Support", f"{row['reach']:.0f}%")
        c2.metric("Cross-Party Appeal", f"{row['universality']:.0f}")
        c3.metric("Category", row["quadrant"])
        c4.metric("Respondents", f"{row['n']:,}")

        st.markdown(
            f'<div style="font-size:1.1rem;font-weight:700;color:{NAVY};margin-bottom:0.5rem;">{topic_label}</div>',
            unsafe_allow_html=True)
        if row.get("text"):
            st.markdown(f'<div class="detail-card">{row["text"]}</div>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════
# RANKED LIST VIEW
# ══════════════════════════════════════════════════════════════════

elif view_mode == "Ranked List":
    st.markdown("#### Ranked by Overall Support (strongest first)")
    ranked = filtered.sort_values("reach", ascending=False)

    display_df = ranked[["construct", "reach", "universality", "quadrant", "n"]].copy()
    display_df["Topic"] = display_df["construct"].map(CONSTRUCT_LABELS).fillna(display_df["construct"])
    display_df = display_df[["Topic", "reach", "universality", "quadrant", "n"]]
    display_df.columns = ["Topic", "Overall Support %", "Cross-Party Appeal", "Category", "Respondents"]
    display_df["Overall Support %"] = display_df["Overall Support %"].apply(lambda x: f"{x:.0f}%")
    display_df["Cross-Party Appeal"] = display_df["Cross-Party Appeal"].apply(lambda x: f"{x:.0f}" if pd.notna(x) else "—")
    display_df = display_df.reset_index(drop=True)
    display_df.index = display_df.index + 1

    st.dataframe(display_df, use_container_width=True, height=500)


# ══════════════════════════════════════════════════════════════════
# CROSS-STATE VIEW
# ══════════════════════════════════════════════════════════════════

elif view_mode == "Cross-State":
    st.markdown("#### Cross-State Support Comparison")
    st.caption("Same question asked in multiple states. Low spread = message transfers well across state lines.")

    state_reach = load_state_reach_mrp()

    cross = []
    for qid, states in state_reach.items():
        if len(states) < 2:
            continue
        construct = get_construct(qid) if SCORING_AVAILABLE else ""
        if not construct:
            continue
        row = {"qid": qid, "construct": construct, "tier": TIER_MAP.get(construct, "")}
        reaches = []
        for state_name, reach_val in states.items():
            row[state_name] = reach_val
            reaches.append(reach_val)
        if len(reaches) >= 2:
            row["spread"] = max(reaches) - min(reaches)
            row["avg_reach"] = np.mean(reaches)
            row["n_states"] = len(reaches)
            if row["spread"] <= 8:
                row["transfer"] = "Direct"
            elif row["spread"] <= 15:
                row["transfer"] = "Adaptation"
            else:
                row["transfer"] = "State-specific"
            cross.append(row)

    if cross:
        cross_df = pd.DataFrame(cross).sort_values("spread", ascending=True)
        st.markdown(f"**{len(cross_df)} items** fielded in 2+ states")

        state_cols = sorted(set(SURVEY_STATE.values()))
        display_cols = (["qid", "construct", "tier"] +
                       [s for s in state_cols if s in cross_df.columns] +
                       ["spread", "transfer"])
        show_df = cross_df[display_cols].head(30).reset_index(drop=True)

        for col in state_cols:
            if col in show_df.columns:
                show_df[col] = show_df[col].apply(lambda x: f"{x:.0f}%" if pd.notna(x) else "—")
        show_df["spread"] = show_df["spread"].apply(lambda x: f"{x:.1f}")

        st.dataframe(show_df, use_container_width=True, height=500)
    else:
        st.info("Not enough cross-state MrP data.")


portal_footer()
