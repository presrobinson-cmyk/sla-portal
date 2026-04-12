"""
Persuasion Architecture — Construct Tiers & Voter Pathways
Live data: constructs grouped by persuasion tier, with Q1 support rates and bridge logic.
"""

import streamlit as st
from pathlib import Path
import sys
import pandas as pd
import requests
from collections import defaultdict

# Auth gate
sys.path.insert(0, str(Path(__file__).parent.parent))
from theme import (
    apply_theme, portal_footer, get_supabase_config, get_supabase_headers,
    CJ_SURVEYS, SURVEY_STATE, TIER_MAP, tier_badge_html, TIER_STYLES,
    NAVY, GOLD, GOLD_MID, CARD_BG, TEXT1, TEXT2, TEXT3, BORDER, BORDER2, BG,
    STATE_COLORS, STATE_ABBR,
)
from auth import require_auth

# Scoring engine (bundled locally)
try:
    from content_scoring import FAVORABLE_DIRECTION, SKIPPED_QIDS, get_construct, score_content
    SCORING_AVAILABLE = True
except ImportError:
    SCORING_AVAILABLE = False

st.set_page_config(
    page_title="Persuasion Architecture — SLA Portal",
    page_icon="🧩",
    layout="wide",
)

apply_theme()
username = require_auth("Second Look Alliance", accent_color=GOLD)

SUPABASE_URL, SUPABASE_KEY = get_supabase_config()
HEADERS = get_supabase_headers()

# Tier display order and descriptions
TIER_ORDER = ["Entry", "Entry (VA)", "Bridge", "Downstream", "Destination", "Gauge"]
TIER_DESC = {
    "Entry": "Highest Q1 anti-reform agreement. These proposals don't challenge worldview — system trusters accept them readily. The foothold.",
    "Entry (VA)": "Entry-tier construct fielded only in Virginia.",
    "Bridge": "The wedge. Gets anti-reformers to concede that circumstances cause crime — without feeling like they're criticizing the system.",
    "Downstream": "Reform proposals that become accessible once Entry + Bridge agreement is established. The policy payload.",
    "Destination": "Hardest proposals for anti-reformers. Only reachable after accumulating agreement on upstream constructs.",
    "Gauge": "Outcome measures and ideology indicators. Not persuasion targets — they measure where someone sits.",
}


# ══════════════════════════════════════════════════════════════════
# DATA LOADING
# ══════════════════════════════════════════════════════════════════

@st.cache_data(ttl=3600, show_spinner="Loading construct data...")
def load_construct_data():
    """Pull L2 responses, score, compute per-construct and per-segment rates."""
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

    # Score all responses
    scored = []
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

    # Compute disposition scores (average favorable rate per respondent)
    resp_agg = defaultdict(lambda: {"fav": 0, "n": 0})
    for s in scored:
        resp_agg[s["rid"]]["fav"] += s["fav"]
        resp_agg[s["rid"]]["n"] += 1

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

    # Compute per-construct stats
    con_stats = defaultdict(lambda: {
        "q1_f": 0, "q1_n": 0, "q5_f": 0, "q5_n": 0,
        "all_f": 0, "all_n": 0, "states": set(), "qids": set(),
    })
    for s in scored:
        rid = s["rid"]
        if rid not in segments:
            continue
        c = s["construct"]
        seg = segments[rid]
        con_stats[c]["all_f"] += s["fav"]
        con_stats[c]["all_n"] += 1
        con_stats[c]["states"].add(SURVEY_STATE.get(s["sid"], ""))
        con_stats[c]["qids"].add(s["qid"])
        if seg == 1:
            con_stats[c]["q1_f"] += s["fav"]
            con_stats[c]["q1_n"] += 1
        elif seg == 5:
            con_stats[c]["q5_f"] += s["fav"]
            con_stats[c]["q5_n"] += 1

    constructs = []
    for c, st in con_stats.items():
        if st["all_n"] < 20:
            continue
        tier = TIER_MAP.get(c, "Unassigned")
        q1_rate = (st["q1_f"] / st["q1_n"] * 100) if st["q1_n"] > 10 else None
        q5_rate = (st["q5_f"] / st["q5_n"] * 100) if st["q5_n"] > 10 else None
        overall = st["all_f"] / st["all_n"] * 100
        constructs.append({
            "construct": c,
            "tier": tier,
            "q1_pct": q1_rate,
            "q5_pct": q5_rate,
            "overall_pct": overall,
            "n_responses": st["all_n"],
            "n_states": len(st["states"] - {""}),
            "n_items": len(st["qids"]),
            "gap": (q5_rate - q1_rate) if q1_rate is not None and q5_rate is not None else None,
        })

    n_respondents = len(disposition)
    n_q1 = sum(1 for s in segments.values() if s == 1)
    return constructs, n_respondents, n_q1


# ══════════════════════════════════════════════════════════════════
# MAIN PAGE
# ══════════════════════════════════════════════════════════════════

st.title("🧩 Persuasion Architecture")
st.markdown(
    "Constructs organized by their role in cracking anti-reform respondents. "
    "Entry tiers are the foothold. Bridge is the wedge. Downstream proposals follow once agreement accumulates."
)

if not SCORING_AVAILABLE:
    st.error("content_scoring.py not found. Cannot compute construct stats.")
    st.stop()

constructs, n_respondents, n_q1 = load_construct_data()

if not constructs:
    st.warning("No construct data available.")
    st.stop()

df = pd.DataFrame(constructs)

# ── KPI row ──
col1, col2, col3, col4 = st.columns(4)
col1.metric("Respondents Scored", f"{n_respondents:,}")
col2.metric("Q1 (Anti-Reform)", f"{n_q1:,}")
col3.metric("Constructs Tracked", f"{len(df)}")
col4.metric("Persuasion Tiers", f"{len([t for t in TIER_ORDER if t in df['tier'].values])}")

st.divider()

# ── The key insight box ──
st.markdown(f"""
<div style="background:{CARD_BG};border:1px solid {BORDER2};border-left:4px solid {GOLD};
    border-radius:10px;padding:1.25rem;margin-bottom:1.5rem;box-shadow:0 1px 3px rgba(0,0,0,0.04);">
    <div style="font-family:'Playfair Display',serif;font-weight:700;color:{NAVY};font-size:1.05rem;margin-bottom:0.5rem;">
        How This Works
    </div>
    <div style="color:{TEXT2};font-size:0.88rem;line-height:1.6;">
        Anti-reform voters (Q1) believe the system works. You can't change that directly. Instead, find
        policy critiques they already accept (<strong>Entry tier</strong>), use DV as a
        <strong>Bridge</strong> to concede that circumstances cause crime, then introduce
        <strong>Downstream</strong> reform proposals that feel like natural extensions of what they've
        already agreed to. Each tier builds on the last.
    </div>
</div>
""", unsafe_allow_html=True)


# ── Tier-by-tier display ──
for tier in TIER_ORDER:
    tier_df = df[df["tier"] == tier].copy()
    if tier_df.empty:
        continue

    tier_df = tier_df.sort_values("q1_pct", ascending=False, na_position="last")

    style = TIER_STYLES.get(tier, TIER_STYLES.get(tier.split(" (")[0], {}))
    tier_color = style.get("color", NAVY)
    tier_bg = style.get("bg", "rgba(0,0,0,0.05)")

    # Tier header
    st.markdown(f"""
    <div style="background:{tier_bg};border:1px solid {tier_color}33;border-left:4px solid {tier_color};
        border-radius:10px;padding:1rem 1.25rem;margin-top:1.5rem;margin-bottom:0.75rem;">
        <div style="font-family:'Playfair Display',serif;font-weight:700;color:{tier_color};font-size:1.1rem;">
            {tier}
        </div>
        <div style="color:{TEXT3};font-size:0.82rem;margin-top:4px;">{TIER_DESC.get(tier, "")}</div>
    </div>
    """, unsafe_allow_html=True)

    # Construct cards in this tier
    cols_per_row = 3
    tier_list = tier_df.to_dict("records")
    for i in range(0, len(tier_list), cols_per_row):
        cols = st.columns(cols_per_row)
        for j, col in enumerate(cols):
            idx = i + j
            if idx >= len(tier_list):
                break
            c = tier_list[idx]
            q1_str = f"{c['q1_pct']:.0f}%" if c["q1_pct"] is not None else "—"
            q5_str = f"{c['q5_pct']:.0f}%" if c["q5_pct"] is not None else "—"
            overall_str = f"{c['overall_pct']:.0f}%"
            gap_str = f"{c['gap']:+.0f}pp" if c["gap"] is not None else "—"

            # Bar width for Q1 visual
            bar_w = c["q1_pct"] if c["q1_pct"] is not None else 0

            with col:
                st.markdown(f"""
                <div style="background:{CARD_BG};border:1px solid {BORDER2};border-radius:10px;
                    padding:1rem 1.25rem;margin-bottom:0.5rem;box-shadow:0 1px 3px rgba(0,0,0,0.04);">
                    <div style="font-family:'Playfair Display',serif;font-weight:700;color:{NAVY};
                        font-size:0.95rem;margin-bottom:8px;">{c['construct']}</div>
                    <div style="display:flex;gap:16px;margin-bottom:8px;">
                        <div>
                            <div style="font-size:0.65rem;color:{TEXT3};text-transform:uppercase;letter-spacing:0.04em;">Q1 Support</div>
                            <div style="font-family:'DM Mono',monospace;font-size:1.1rem;font-weight:700;color:{tier_color};">{q1_str}</div>
                        </div>
                        <div>
                            <div style="font-size:0.65rem;color:{TEXT3};text-transform:uppercase;letter-spacing:0.04em;">Overall</div>
                            <div style="font-family:'DM Mono',monospace;font-size:1.1rem;font-weight:600;color:{TEXT2};">{overall_str}</div>
                        </div>
                        <div>
                            <div style="font-size:0.65rem;color:{TEXT3};text-transform:uppercase;letter-spacing:0.04em;">Gap</div>
                            <div style="font-family:'DM Mono',monospace;font-size:1.1rem;font-weight:600;color:{TEXT3};">{gap_str}</div>
                        </div>
                    </div>
                    <div style="background:{BORDER2};border-radius:4px;height:6px;overflow:hidden;">
                        <div style="background:{tier_color};height:100%;width:{bar_w}%;border-radius:4px;"></div>
                    </div>
                    <div style="font-size:0.7rem;color:{TEXT3};margin-top:6px;">
                        {c['n_items']} item{'s' if c['n_items'] != 1 else ''} · {c['n_states']} state{'s' if c['n_states'] != 1 else ''} · {c['n_responses']:,} responses
                    </div>
                </div>
                """, unsafe_allow_html=True)


# ── Voter Archetypes section ──
st.divider()
st.subheader("Voter Archetypes")
st.markdown(
    "Four segments based on disposition scoring (average favorable rate across all scored items). "
    "These are empirical clusters from the data, not theoretical types."
)

ARCHETYPES = [
    {
        "name": "Worldview Defenders",
        "segment": "Q1 — Most Anti-Reform",
        "color": "#8B1A1A",
        "desc": "Believe the system works. Crime is a choice, punishment is deserved. "
                "Entry-tier issues are the ONLY foothold — DV bridge is the path forward.",
        "strategy": "DV wedge → downstream proposals that feel like fixing system failures, not challenging the system.",
    },
    {
        "name": "Conditional Compromisers",
        "segment": "Q2–Q3 — Movable Middle",
        "color": "#B85400",
        "desc": "Accept some reform premises but resist consequences (early release, resentencing). "
                "Bridge tier unlocks them — once they concede circumstances matter, downstream follows.",
        "strategy": "Entry + Bridge → Downstream. Cost/efficiency framing works. Redemption framing works if earned.",
    },
    {
        "name": "Reluctant Reformers",
        "segment": "Q4 — Leaning Reform",
        "color": "#1155AA",
        "desc": "Broadly favorable but inconsistent. Support specific proposals, not a reform identity. "
                "Vulnerable to opposition framing on tough cases.",
        "strategy": "Inoculation against opponent attacks. Lock in support before pushback. Shore up Destination tier.",
    },
    {
        "name": "Reform Champions",
        "segment": "Q5 — Most Pro-Reform",
        "color": "#1B6B3A",
        "desc": "Already aligned. The base. High support across all tiers. "
                "Messaging for this group is about activation, not persuasion.",
        "strategy": "Mobilization, not persuasion. Use for validation metrics (Q5 rate = ceiling).",
    },
]

col1, col2 = st.columns(2)
for i, arch in enumerate(ARCHETYPES):
    target = col1 if i % 2 == 0 else col2
    with target:
        st.markdown(f"""
        <div style="background:{CARD_BG};border:1px solid {BORDER2};border-left:4px solid {arch['color']};
            border-radius:10px;padding:1.25rem;margin-bottom:0.75rem;box-shadow:0 1px 3px rgba(0,0,0,0.04);">
            <div style="font-family:'Playfair Display',serif;font-weight:700;color:{arch['color']};
                font-size:1rem;margin-bottom:2px;">{arch['name']}</div>
            <div style="font-family:'DM Mono',monospace;font-size:0.78rem;color:{TEXT3};
                margin-bottom:8px;">{arch['segment']}</div>
            <div style="color:{TEXT2};font-size:0.85rem;line-height:1.5;margin-bottom:10px;">{arch['desc']}</div>
            <div style="border-top:1px solid {BORDER2};padding-top:8px;">
                <div style="font-size:0.7rem;color:{TEXT3};text-transform:uppercase;letter-spacing:0.04em;margin-bottom:4px;">Strategy</div>
                <div style="color:{TEXT1};font-size:0.82rem;line-height:1.5;">{arch['strategy']}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)


# ── Tier progression visual ──
st.divider()
st.subheader("Persuasion Pathway")
st.markdown("The sequence for cracking anti-reform segments:")

# Simple flow visualization
flow_tiers = ["Entry", "Bridge", "Downstream", "Destination"]
flow_cols = st.columns(len(flow_tiers))
for i, (col, tier) in enumerate(zip(flow_cols, flow_tiers)):
    style = TIER_STYLES.get(tier, {})
    tc = style.get("color", NAVY)
    tbg = style.get("bg", "rgba(0,0,0,0.05)")

    tier_constructs = df[df["tier"] == tier].sort_values("q1_pct", ascending=False, na_position="last")
    top = tier_constructs.head(3)
    examples = ", ".join(top["construct"].tolist()) if not top.empty else "—"
    avg_q1 = tier_constructs["q1_pct"].mean() if not tier_constructs["q1_pct"].isna().all() else None
    avg_str = f"{avg_q1:.0f}%" if avg_q1 is not None else "—"

    arrow = " →" if i < len(flow_tiers) - 1 else ""

    with col:
        st.markdown(f"""
        <div style="background:{tbg};border:1px solid {tc}33;border-radius:10px;
            padding:1rem;text-align:center;">
            <div style="font-family:'Playfair Display',serif;font-weight:700;color:{tc};
                font-size:0.95rem;">{tier}{arrow}</div>
            <div style="font-family:'DM Mono',monospace;font-size:1.3rem;font-weight:700;
                color:{tc};margin:8px 0;">Q1: {avg_str}</div>
            <div style="font-size:0.75rem;color:{TEXT3};">{examples}</div>
        </div>
        """, unsafe_allow_html=True)


portal_footer()
