"""
How It Works — VIP & MrP explainer
The leading feature overview for Second Look Alliance partners.
Not buried methodology — this is what the portal does and why it matters.
"""

import streamlit as st
from pathlib import Path
import sys
import plotly.graph_objects as go

sys.path.insert(0, str(Path(__file__).parent))
from auth import require_auth
from theme import (
    apply_theme, portal_footer,
    NAVY, NAVY2, GOLD, GOLD_MID, TEXT1, TEXT2, TEXT3,
    BORDER2, BG, CARD_BG,
)

st.set_page_config(
    page_title="How It Works — SLA Portal",
    page_icon="⚡",
    layout="wide",
)

apply_theme()
username = require_auth("Second Look Alliance", accent_color=GOLD)


# ══════════════════════════════════════════════════════════════════
# STYLES
# ══════════════════════════════════════════════════════════════════

st.markdown(f"""
<style>
  .hero-title {{
    font-family: 'Playfair Display', serif;
    font-size: 2.6rem;
    font-weight: 700;
    color: {NAVY};
    line-height: 1.15;
    margin-bottom: 0.4rem;
  }}
  .hero-sub {{
    font-size: 1.1rem;
    color: {TEXT2};
    max-width: 680px;
    line-height: 1.6;
    margin-bottom: 2rem;
  }}
  .feature-card {{
    background: {CARD_BG};
    border: 1px solid {BORDER2};
    border-radius: 12px;
    padding: 1.8rem 2rem;
    height: 100%;
  }}
  .feature-label {{
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: {GOLD};
    margin-bottom: 0.4rem;
  }}
  .feature-title {{
    font-family: 'Playfair Display', serif;
    font-size: 1.6rem;
    font-weight: 700;
    color: {NAVY};
    margin-bottom: 0.75rem;
    line-height: 1.2;
  }}
  .feature-body {{
    font-size: 0.95rem;
    color: {TEXT2};
    line-height: 1.7;
  }}
  .stat-box {{
    background: {NAVY};
    border-radius: 10px;
    padding: 1.1rem 1.4rem;
    text-align: center;
    margin-top: 1rem;
  }}
  .stat-num {{
    font-family: 'Playfair Display', serif;
    font-size: 2rem;
    font-weight: 700;
    color: {GOLD};
    line-height: 1;
  }}
  .stat-label {{
    font-size: 0.78rem;
    color: rgba(255,255,255,0.7);
    margin-top: 0.25rem;
  }}
  .tier-pill {{
    display: inline-block;
    border-radius: 20px;
    padding: 0.2rem 0.85rem;
    font-size: 0.78rem;
    font-weight: 600;
    margin-right: 0.3rem;
    margin-bottom: 0.3rem;
  }}
  .archetype-row {{
    display: flex;
    align-items: center;
    gap: 1rem;
    padding: 0.75rem 0;
    border-bottom: 1px solid {BORDER2};
  }}
  .archetype-name {{
    font-weight: 600;
    color: {NAVY};
    font-size: 0.92rem;
    min-width: 130px;
  }}
  .archetype-pct {{
    font-family: 'Playfair Display', serif;
    font-size: 1.1rem;
    font-weight: 700;
    color: {GOLD};
    min-width: 50px;
  }}
  .archetype-desc {{
    font-size: 0.85rem;
    color: {TEXT2};
    line-height: 1.5;
  }}
  .section-head {{
    font-family: 'Playfair Display', serif;
    font-size: 1.35rem;
    font-weight: 700;
    color: {NAVY};
    margin: 2rem 0 0.5rem 0;
    border-left: 4px solid {GOLD};
    padding-left: 0.75rem;
  }}
  .callout {{
    background: rgba(197,160,77,0.08);
    border-left: 4px solid {GOLD};
    border-radius: 0 8px 8px 0;
    padding: 1rem 1.25rem;
    font-size: 0.92rem;
    color: {TEXT1};
    line-height: 1.65;
    margin: 1.25rem 0;
  }}
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════
# HERO
# ══════════════════════════════════════════════════════════════════

st.markdown(
    f'<div class="hero-title">The Science Behind the Strategy</div>',
    unsafe_allow_html=True,
)
st.markdown(
    f'<div class="hero-sub">'
    f'The SLA Portal is built on two things that make it different from a standard poll: '
    f'<strong>VIP</strong> — a system that finds exactly which criminal justice reforms can move '
    f'the hardest voters — and <strong>MrP</strong>, the statistical engine that makes every '
    f'number in this portal represent what the actual electorate thinks, not just who happened '
    f'to answer a survey.'
    f'</div>',
    unsafe_allow_html=True,
)

st.divider()


# ══════════════════════════════════════════════════════════════════
# TWO FEATURE CARDS
# ══════════════════════════════════════════════════════════════════

col_vip, col_mrp = st.columns(2, gap="large")

with col_vip:
    st.markdown(f"""
    <div class="feature-card">
      <div class="feature-label">Core Feature</div>
      <div class="feature-title">VIP — Voter Intelligence<br>& Persuasion</div>
      <div class="feature-body">
        Most polling tells you <em>what</em> voters think. VIP tells you <em>how to move them</em>.<br><br>
        It maps every criminal justice reform issue onto a persuasion sequence — from the proposals
        that anti-reform voters already agree with, to the policy changes that only become possible
        once you've built agreement on the earlier ones.<br><br>
        The result: a strategic roadmap. You don't lead with the hardest ask. You lead with
        the ones that open the door.
      </div>
    </div>
    """, unsafe_allow_html=True)

    # Stat boxes under VIP card
    s1, s2, s3 = st.columns(3)
    with s1:
        st.markdown(f'<div class="stat-box"><div class="stat-num">5,500+</div><div class="stat-label">Voters Surveyed</div></div>', unsafe_allow_html=True)
    with s2:
        st.markdown(f'<div class="stat-box"><div class="stat-num">6</div><div class="stat-label">States</div></div>', unsafe_allow_html=True)
    with s3:
        st.markdown(f'<div class="stat-box"><div class="stat-num">34</div><div class="stat-label">Issue Constructs</div></div>', unsafe_allow_html=True)

with col_mrp:
    st.markdown(f"""
    <div class="feature-card">
      <div class="feature-label">Statistical Engine</div>
      <div class="feature-title">MrP — Population-Adjusted<br>Estimates</div>
      <div class="feature-body">
        Raw survey results are biased. Who responds to a poll is never a perfect mirror of
        who actually votes. MrP — Multilevel Regression with Poststratification — fixes that.<br><br>
        It models how each demographic cell (age × education × race × gender) responds,
        then weights those estimates to match the actual Census population of each state —
        not a voter file, but the real demographic composition drawn from U.S. Census ACS data.<br><br>
        Every percentage you see in this portal is MrP-adjusted by default. That means you're
        looking at what the electorate actually thinks — not an artifact of who picked up the phone.
        Coming soon: customizable weighting so partners can tune the demographic assumptions
        to their specific district or target audience.
      </div>
    </div>
    """, unsafe_allow_html=True)

    s4, s5, s6 = st.columns(3)
    with s4:
        st.markdown(f'<div class="stat-box"><div class="stat-num">7</div><div class="stat-label">Surveys Modeled</div></div>', unsafe_allow_html=True)
    with s5:
        st.markdown(f'<div class="stat-box"><div class="stat-num">4</div><div class="stat-label">Demo Dimensions</div></div>', unsafe_allow_html=True)
    with s6:
        st.markdown(f'<div class="stat-box"><div class="stat-num">±2%</div><div class="stat-label">Typical Correction</div></div>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════
# VIP DEEP DIVE — PERSUASION TIERS
# ══════════════════════════════════════════════════════════════════

st.markdown('<div class="section-head">How VIP Works: The Persuasion Sequence</div>', unsafe_allow_html=True)

st.markdown(f"""
<div class="callout">
  The hardest voters to move on criminal justice reform are not a monolith. VIP identifies exactly
  where they crack — which issues they already agree with even if they'd never call themselves
  reform supporters — and maps the path from those agreements to the bigger policy changes.
</div>
""", unsafe_allow_html=True)

# Tier flow chart
tier_data = {
    "Entry": {
        "color": "#1B6B3A",
        "q1": "70–82%",
        "examples": "Public Defender Funding · Community Investment · Literacy Programs",
        "what": "Anti-reform voters accept these without feeling like they're endorsing 'reform.' High friction-free agreement — the foothold."
    },
    "Bridge": {
        "color": "#B8870A",
        "q1": "65–75%",
        "examples": "Domestic Violence · Compassionate Release · Fines & Fees",
        "what": "Gets skeptical voters to concede that <em>why</em> someone committed a crime matters. The key persuasion move — opens the door to everything downstream."
    },
    "Downstream": {
        "color": "#1155AA",
        "q1": "35–56%",
        "examples": "Proportionality · Second Chances · Record Expungement · Sentence Review",
        "what": "Policy proposals that become reachable once Entry + Bridge agreement is in place. The actual reform payload."
    },
}

for tier_name, td in tier_data.items():
    c_icon, c_body = st.columns([1, 11])
    with c_icon:
        st.markdown(
            f'<div style="width:36px;height:36px;border-radius:50%;background:{td["color"]};'
            f'margin-top:4px;display:flex;align-items:center;justify-content:center;'
            f'color:white;font-weight:700;font-size:0.8rem;text-align:center;line-height:1;">'
            f'{tier_name[0]}</div>',
            unsafe_allow_html=True,
        )
    with c_body:
        st.markdown(
            f'<div style="padding:0.9rem 1.1rem;background:{CARD_BG};border:1px solid {BORDER2};'
            f'border-left:4px solid {td["color"]};border-radius:0 8px 8px 0;margin-bottom:0.6rem;">'
            f'<span style="font-weight:700;color:{td["color"]};font-size:0.9rem;">{tier_name} Tier</span>'
            f'<span style="color:{TEXT3};font-size:0.8rem;margin-left:0.75rem;">Q1 anti-reform support: {td["q1"]}</span><br>'
            f'<span style="font-size:0.82rem;color:{TEXT2};">{td["examples"]}</span><br>'
            f'<span style="font-size:0.88rem;color:{TEXT1};margin-top:0.3rem;display:block;">{td["what"]}</span>'
            f'</div>',
            unsafe_allow_html=True,
        )


# ══════════════════════════════════════════════════════════════════
# FOUR VOTER ARCHETYPES
# ══════════════════════════════════════════════════════════════════

st.markdown('<div class="section-head">Who You\'re Talking To: The Four Voter Archetypes</div>', unsafe_allow_html=True)

st.markdown(
    f'<div style="font-size:0.92rem;color:{TEXT2};line-height:1.6;margin-bottom:1rem;">'
    f'VIP places every respondent on a disposition spectrum based on how they respond across all '
    f'scored items. The result is four empirically-derived voter types — not labels, but actual '
    f'behavioral clusters from the data.'
    f'</div>',
    unsafe_allow_html=True,
)

archetypes = [
    ("Skeptics",     "8%",  "#8B1A1A", "The hardest audience. Oppose reform by default. But they crack on DV and victim-framing — that's the entry point."),
    ("Pragmatists",  "56%", "#B85400", "The primary persuasion target. Open to specific reform arguments but not broad reform identity. This is where campaigns are won."),
    ("Reform-Ready", "26%", "#1155AA", "Lean reform, need the right frame. Activation and message-sharpening — not persuasion from scratch."),
    ("Committed",    "9%",  "#1B6B3A", "Already pro-reform. Mobilization, not persuasion. The base."),
]

# Donut chart
fig_arc = go.Figure(go.Pie(
    labels=[a[0] for a in archetypes],
    values=[int(a[1].strip('%')) for a in archetypes],
    hole=0.55,
    marker=dict(colors=[a[2] for a in archetypes], line=dict(color=BG, width=3)),
    textinfo="label+percent",
    textfont=dict(family="DM Sans", size=11, color="white"),
    hovertemplate="<b>%{label}</b><br>%{percent}<extra></extra>",
    direction="clockwise",
    sort=False,
))
fig_arc.update_layout(
    paper_bgcolor=BG,
    plot_bgcolor=BG,
    height=260,
    margin=dict(l=0, r=0, t=20, b=0),
    showlegend=False,
    font=dict(family="DM Sans", color=NAVY),
    annotations=[dict(
        text="Voter<br>Segments",
        x=0.5, y=0.5,
        font=dict(size=12, family="DM Sans", color=NAVY),
        showarrow=False,
    )],
)

arc_col1, arc_col2 = st.columns([1, 1], gap="large")
with arc_col1:
    st.plotly_chart(fig_arc, use_container_width=True, key="arc_donut")

with arc_col2:
    for name, pct, color, desc in archetypes:
        st.markdown(
            f'<div class="archetype-row">'
            f'<div class="archetype-pct" style="color:{color};">{pct}</div>'
            f'<div>'
            f'<div class="archetype-name" style="color:{color};">{name}</div>'
            f'<div class="archetype-desc">{desc}</div>'
            f'</div>'
            f'</div>',
            unsafe_allow_html=True,
        )


# ══════════════════════════════════════════════════════════════════
# MRP DEEP DIVE
# ══════════════════════════════════════════════════════════════════

st.markdown('<div class="section-head">Why MrP Changes Everything</div>', unsafe_allow_html=True)

mrp_col1, mrp_col2 = st.columns(2, gap="large")

with mrp_col1:
    st.markdown(f"""
    <div style="font-size:0.95rem;color:{TEXT2};line-height:1.75;">
      <strong style="color:{NAVY};">The problem with raw polls:</strong> Survey respondents are
      not a random sample of the electorate. Certain demographics over-respond (older voters,
      college-educated) while others under-respond (younger voters, non-college). A raw 63%
      support figure may actually be 58% or 67% when corrected for who really votes.<br><br>
      <strong style="color:{NAVY};">What MrP does:</strong> It builds a model that predicts
      each demographic cell's response rate, then poststratifies — weighting cells to match
      the actual Census composition of each state (U.S. Census ACS tables: race/ethnicity,
      age, education, gender). The result is an estimate of what the full population thinks,
      not just the subset who answered.
    </div>
    """, unsafe_allow_html=True)

with mrp_col2:
    st.markdown(f"""
    <div style="font-size:0.95rem;color:{TEXT2};line-height:1.75;">
      <strong style="color:{NAVY};">Why it matters for strategy:</strong> When the Issue
      Landscape shows 74% support for compassionate release, that number has already been
      corrected for sample bias. You can use it in a briefing, a press release, or a legislative
      conversation with confidence.<br><br>
      <strong style="color:{NAVY};">Toggle between MrP and Raw:</strong> Every page in this
      portal lets you switch between MrP-adjusted and raw survey numbers using the toggle at
      the top. MrP is the default — it's the more accurate number. Raw is available for
      transparency and cross-checking.
    </div>
    """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════
# WHAT YOU'LL FIND IN THIS PORTAL
# ══════════════════════════════════════════════════════════════════

st.markdown('<div class="section-head">What\'s in the Portal</div>', unsafe_allow_html=True)

pages = [
    ("⚡", "Issue Landscape",     "The big picture. Every reform issue plotted by overall support vs. support among your target group. Find your Golden Zone — issues that work with everyone."),
    ("🎯", "VIP Scores",          "Construct-by-construct persuasion architecture. Tier assignments, Q1 support rates, and the bridge map showing which agreements unlock downstream proposals."),
    ("📊", "MrP Estimates",       "The full statistical model output. Cross-state consistency, construct-level reach and universality, and the raw vs. adjusted comparison."),
    ("💬", "Message Testing",     "Side-by-side performance of individual survey items within the same construct. Framing variation — the gap between items is where message strategy lives."),
    ("📺", "Media Portal",        "Wire campaign-ready messages to paid media targeting. Connects VIP persuasion data directly to Meta and X ad targeting."),
]

for icon, name, desc in pages:
    st.markdown(
        f'<div style="display:flex;gap:1rem;padding:0.8rem 0;border-bottom:1px solid {BORDER2};">'
        f'<div style="font-size:1.4rem;width:36px;text-align:center;padding-top:2px;">{icon}</div>'
        f'<div>'
        f'<div style="font-weight:700;color:{NAVY};font-size:0.92rem;">{name}</div>'
        f'<div style="font-size:0.87rem;color:{TEXT2};line-height:1.5;margin-top:0.1rem;">{desc}</div>'
        f'</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

st.markdown("<br>", unsafe_allow_html=True)
portal_footer()
