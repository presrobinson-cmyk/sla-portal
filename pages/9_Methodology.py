"""
Methodology — How Our Tools Work
Plain-English explanation of the MrP modeling and VIP scoring systems,
and how they improve with each additional survey.
"""

import streamlit as st
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
from theme import (
    apply_theme, portal_footer,
    NAVY, NAVY2, GOLD, GOLD_MID, TEXT1, TEXT2, TEXT3, BORDER2, BG, CARD_BG,
)
from auth import require_auth
from chat_widget import render_chat

st.set_page_config(page_title="Methodology — SLA Portal", page_icon="📐", layout="wide")
apply_theme()
username = require_auth("Second Look Alliance", accent_color=GOLD)

# ══════════════════════════════════════════════════════════════════
# PAGE HEADER
# ══════════════════════════════════════════════════════════════════

st.title("📐 How Our Tools Work")
st.markdown(
    "This page explains the two engines behind the SLA Portal: "
    "the statistical model that adjusts raw survey data to reflect real populations, "
    "and the scoring system that identifies who to talk to and what to say."
)

st.divider()

# ══════════════════════════════════════════════════════════════════
# MrP — MULTILEVEL REGRESSION AND POSTSTRATIFICATION
# ══════════════════════════════════════════════════════════════════

st.markdown(f"""
<div style="background:{CARD_BG};border:1px solid {BORDER2};border-left:4px solid {GOLD};
    border-radius:10px;padding:1.5rem;margin-bottom:1.5rem;">
    <div style="font-family:'Playfair Display',serif;font-weight:700;color:{NAVY};font-size:1.3rem;
        margin-bottom:0.75rem;">
        MrP — Making Surveys Match Reality
    </div>
    <div style="color:{TEXT2};font-size:0.95rem;line-height:1.7;">
        <strong>The problem:</strong> Every survey has gaps. Maybe too many college graduates responded,
        or not enough younger voters. If you just count the raw answers, your numbers can be skewed
        by who happened to take the survey — not what the population actually thinks.
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown(f"""
<div style="font-family:'Playfair Display',serif;font-weight:700;color:{NAVY};font-size:1.05rem;
    margin-bottom:0.75rem;">What MrP Does</div>
<div style="color:{TEXT1};font-size:0.92rem;line-height:1.7;margin-bottom:1.5rem;">
    MrP (Multilevel Regression and Poststratification) is a statistical technique used by
    The New York Times, FiveThirtyEight, and leading political research firms. It works in two steps:
</div>
""", unsafe_allow_html=True)

col1, col2 = st.columns(2)

with col1:
    st.markdown(f"""
    <div style="background:{CARD_BG};border:1px solid {BORDER2};border-radius:10px;padding:1.25rem;
        min-height:220px;">
        <div style="font-weight:700;color:{GOLD_MID};font-size:0.85rem;text-transform:uppercase;
            letter-spacing:0.05em;margin-bottom:0.5rem;">Step 1: Learn Patterns</div>
        <div style="font-family:'Playfair Display',serif;font-weight:700;color:{NAVY};font-size:1rem;
            margin-bottom:0.5rem;">Multilevel Regression</div>
        <div style="color:{TEXT2};font-size:0.88rem;line-height:1.6;">
            The model looks at how different groups of people answered — broken down by
            party, age, education, race, and gender — and learns the pattern of who supports what.
            It borrows strength across groups: if 35-year-old college-educated women in Oklahoma
            look similar to the same group in Louisiana, the model uses both datasets to get a
            more precise estimate for each.
        </div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div style="background:{CARD_BG};border:1px solid {BORDER2};border-radius:10px;padding:1.25rem;
        min-height:220px;">
        <div style="font-weight:700;color:{GOLD_MID};font-size:0.85rem;text-transform:uppercase;
            letter-spacing:0.05em;margin-bottom:0.5rem;">Step 2: Reweight to Reality</div>
        <div style="font-family:'Playfair Display',serif;font-weight:700;color:{NAVY};font-size:1rem;
            margin-bottom:0.5rem;">Poststratification</div>
        <div style="color:{TEXT2};font-size:0.88rem;line-height:1.6;">
            Using Census data and voter registration records, the model knows what the real
            population looks like in each state. It reweights the survey patterns to match —
            so if your survey over-sampled college graduates, MrP corrects for that.
            The result is a support estimate that reflects the actual electorate, not just
            the people who answered the survey.
        </div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("")

st.markdown(f"""
<div style="background:rgba(184,135,10,0.06);border:1px solid rgba(184,135,10,0.15);border-radius:10px;
    padding:1.25rem;margin-bottom:1.5rem;">
    <div style="font-weight:700;color:{NAVY};margin-bottom:0.5rem;">Why this matters for advocates</div>
    <div style="color:{TEXT2};font-size:0.88rem;line-height:1.6;">
        Without MrP, a survey of 800 people in Louisiana might show 62% support for bail reform.
        With MrP, you know that support is <strong>64% among likely voters</strong> — adjusted for
        the fact that your survey had too few rural Republicans and too many urban Democrats.
        That 2-point difference can change whether a legislator sees the issue as safe or risky.
    </div>
</div>
""", unsafe_allow_html=True)

st.divider()

# ══════════════════════════════════════════════════════════════════
# VIP — VOTER INTELLIGENCE PROFILES
# ══════════════════════════════════════════════════════════════════

st.markdown(f"""
<div style="background:{CARD_BG};border:1px solid {BORDER2};border-left:4px solid {NAVY};
    border-radius:10px;padding:1.5rem;margin-bottom:1.5rem;">
    <div style="font-family:'Playfair Display',serif;font-weight:700;color:{NAVY};font-size:1.3rem;
        margin-bottom:0.75rem;">
        VIP Scoring — Who to Talk To and What to Say
    </div>
    <div style="color:{TEXT2};font-size:0.95rem;line-height:1.7;">
        <strong>The problem:</strong> Knowing that 65% of the public supports an issue doesn't tell you
        which voters to target. You need to know who's persuadable, who's already on your side,
        and who will never come around — and which messages work for each group.
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown(f"""
<div style="font-family:'Playfair Display',serif;font-weight:700;color:{NAVY};font-size:1.05rem;
    margin-bottom:0.75rem;">The VIP Scoring Components</div>
""", unsafe_allow_html=True)

cards = [
    {
        "title": "Reach",
        "subtitle": "How many people agree?",
        "color": "#1B6B3A",
        "text": (
            "The percentage of the population that supports a given reform topic. "
            "MrP-adjusted, so it reflects real voters — not just survey respondents. "
            "This is the primary strength signal: higher reach = more popular."
        ),
    },
    {
        "title": "Universality",
        "subtitle": "Does support cross partisan lines?",
        "color": "#1155AA",
        "text": (
            "Measures how consistent support is across different voter groups. "
            "High universality means the issue works with Democrats, Republicans, and Independents alike. "
            "Low universality means it's strong with some groups but weak with others — "
            "still useful, but you need to target carefully."
        ),
    },
    {
        "title": "Base Strength",
        "subtitle": "How committed are your supporters?",
        "color": "#B85400",
        "text": (
            "Not all support is equal. Base Strength measures the intensity and reliability of support — "
            "are people 'strongly' in favor, or just 'somewhat'? "
            "Strong base = the issue can withstand opposition attacks. "
            "Weak base = support may crumble when challenged."
        ),
    },
    {
        "title": "Persuasion Gap",
        "subtitle": "Where's the opportunity?",
        "color": "#5B1B8A",
        "text": (
            "The difference between how your supporters and skeptics feel about an issue. "
            "A large gap means there's room to persuade — the people who currently oppose "
            "this issue aren't locked in. "
            "A small gap means minds are mostly made up."
        ),
    },
]

cols = st.columns(2)
for i, card in enumerate(cards):
    with cols[i % 2]:
        st.markdown(f"""
        <div style="background:{CARD_BG};border:1px solid {BORDER2};border-top:3px solid {card['color']};
            border-radius:10px;padding:1.25rem;margin-bottom:1rem;min-height:180px;">
            <div style="font-family:'Playfair Display',serif;font-weight:700;color:{card['color']};
                font-size:1rem;">{card['title']}</div>
            <div style="font-size:0.78rem;color:{TEXT3};margin-bottom:0.5rem;">{card['subtitle']}</div>
            <div style="color:{TEXT2};font-size:0.85rem;line-height:1.6;">{card['text']}</div>
        </div>
        """, unsafe_allow_html=True)

st.divider()

# ══════════════════════════════════════════════════════════════════
# THE COMPOUNDING EFFECT
# ══════════════════════════════════════════════════════════════════

st.markdown(f"""
<div style="background:{CARD_BG};border:1px solid {BORDER2};border-left:4px solid #1B6B3A;
    border-radius:10px;padding:1.5rem;margin-bottom:1.5rem;">
    <div style="font-family:'Playfair Display',serif;font-weight:700;color:{NAVY};font-size:1.3rem;
        margin-bottom:0.75rem;">
        Why Every New Survey Makes the System Smarter
    </div>
    <div style="color:{TEXT2};font-size:0.95rem;line-height:1.7;">
        This isn't a one-survey snapshot. The SLA Portal is a <strong>compounding intelligence system</strong>
        that gets more powerful with every additional survey fielded. Here's how:
    </div>
</div>
""", unsafe_allow_html=True)

improvements = [
    {
        "number": "1",
        "title": "More precise MrP estimates",
        "text": (
            "MrP pools data across surveys. A single survey of 800 people in Louisiana gives you "
            "rough estimates. Add a second Louisiana survey six months later, and the model now has "
            "1,600 data points to work with. Add Oklahoma, Virginia, and Massachusetts surveys, "
            "and the model borrows strength across states — learning that patterns in one state "
            "often predict patterns in another. Each new survey tightens the confidence around every estimate."
        ),
    },
    {
        "number": "2",
        "title": "Cross-state transfer intelligence",
        "text": (
            "Once you've fielded the same question in two or more states, you can see whether "
            "a message works everywhere or only in certain contexts. Three states give you a pattern. "
            "Six states give you a national messaging strategy. "
            "The Cross-State page shows this directly — which messages are 'direct transfers' "
            "versus which need local adaptation."
        ),
    },
    {
        "number": "3",
        "title": "Sharper voter segments",
        "text": (
            "With one survey, you know the five voter segments exist but the boundaries are fuzzy. "
            "With multiple surveys, the system can identify finer distinctions — which skeptics are "
            "truly locked in versus which are open to persuasion on specific topics. "
            "The persuasion pathway becomes a tested route, not a hypothesis."
        ),
    },
    {
        "number": "4",
        "title": "Trend detection",
        "text": (
            "Repeat the same questions over time and you can see movement. Is support for bail reform "
            "growing or shrinking? Is the persuasion gap widening? Are skeptics softening on specific "
            "issues? This kind of tracking is impossible with one-off surveys but becomes automatic "
            "as the database accumulates."
        ),
    },
    {
        "number": "5",
        "title": "New domain expansion",
        "text": (
            "The same engine works for criminal justice, health insurance, energy policy, education, "
            "and veterans' issues. Each new domain survey adds to the cross-domain intelligence — "
            "and the system's understanding of which voter archetypes respond to which framing "
            "approaches transfers across all domains."
        ),
    },
]

for imp in improvements:
    st.markdown(f"""
    <div style="display:flex;gap:16px;margin-bottom:1rem;padding-bottom:1rem;border-bottom:1px solid {BORDER2};">
        <div style="min-width:40px;height:40px;background:{NAVY};color:white;border-radius:50%;
            display:flex;align-items:center;justify-content:center;font-weight:700;font-size:1.1rem;
            flex-shrink:0;">{imp['number']}</div>
        <div>
            <div style="font-weight:700;color:{NAVY};font-size:0.95rem;margin-bottom:4px;">{imp['title']}</div>
            <div style="color:{TEXT2};font-size:0.88rem;line-height:1.6;">{imp['text']}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("")

# Compounding visual
st.markdown(f"""
<div style="background:rgba(27,107,58,0.06);border:1px solid rgba(27,107,58,0.15);border-radius:10px;
    padding:1.25rem;margin-bottom:1.5rem;">
    <div style="font-weight:700;color:{NAVY};margin-bottom:0.5rem;">The bottom line</div>
    <div style="color:{TEXT2};font-size:0.92rem;line-height:1.7;">
        A single survey gives you a <strong>snapshot</strong>. The SLA Portal turns that snapshot into
        an <strong>intelligence system</strong> that compounds in value. Every survey fielded, every state added,
        every question tested makes every other analysis in the system more precise and more actionable.
        This is not a report — it's infrastructure that appreciates with use.
    </div>
</div>
""", unsafe_allow_html=True)

st.divider()

# ══════════════════════════════════════════════════════════════════
# TECHNICAL NOTES (collapsed)
# ══════════════════════════════════════════════════════════════════

with st.expander("Technical details (for the data-curious)"):
    st.markdown(f"""
    <div style="color:{TEXT2};font-size:0.88rem;line-height:1.7;">

    <strong>MrP implementation:</strong> Multilevel logistic regression with partial pooling across
    demographic cells (party × age × education × race × gender). Poststratification targets use
    Census ACS 5-year estimates with turnout-adjusted manual weight overrides. Temporal decay applies
    to older surveys: full weight for 12 months, half weight at 24 months, 10% at 36 months.

    <strong>VIP scoring:</strong> Five quintile segments based on disposition score (average favorable response
    rate across all scored items). A respondent must answer at least 3 scored items to be placed.
    Favorable direction is determined by policy content of response options, not by party majority response.

    <strong>Favorable direction scoring:</strong> Each survey question has a manually coded favorable direction
    (e.g., "Strongly Agree" = favorable for questions framed in a reform direction). Three scoring types:
    Likert scales, forced binary choices, and multi-phrasing items. Scoring is deterministic and version-controlled.

    <strong>Likely voter screen:</strong> 3-item voting history battery (presidential, gubernatorial, local).
    2-of-3 "Yes" = likely voter. Self-reported intent is the foundation, validated by behavioral engagement items
    (news subscription, political discussion frequency). No-party/independent voters are the primary
    overstatement risk group.

    </div>
    """, unsafe_allow_html=True)


render_chat("methodology")
portal_footer()
