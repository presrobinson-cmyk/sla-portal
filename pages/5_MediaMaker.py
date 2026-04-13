"""
MediaMaker — Evidence-Based Message Guidance
Campaign message generation powered by Actionable Intel research.
Words That Work / Words to Avoid + Persuasion Framework Box.
"""

import streamlit as st
from pathlib import Path
import sys

# Auth gate
sys.path.insert(0, str(Path(__file__).parent.parent))
from theme import (
    apply_theme, portal_footer, TIER_MAP,
    NAVY, NAVY2, GOLD, GOLD_MID, TEXT1, TEXT2, TEXT3, BORDER2, BG, CARD_BG,
)
from auth import require_auth
from chat_widget import render_chat

st.set_page_config(
    page_title="MediaMaker — SLA Portal",
    page_icon="📢",
    layout="wide",
)

apply_theme()
username = require_auth("Second Look Alliance", accent_color=GOLD)

# ─────────────────────────────────────────────────────────────────
# CONSTRUCT LABELS & GAUGE CONSTRUCTS
# ─────────────────────────────────────────────────────────────────

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
    "DETER": "Deterrence Beliefs",
    "FISCAL": "Fiscal Responsibility",
    "DP_ABOLITION": "Death Penalty Abolition",
    "DP_RELIABILITY": "Death Penalty Reliability",
    "LWOP": "Life Without Parole Reform",
}

GAUGE_CONSTRUCTS = {"CAND", "TOUGHCRIME", "ISSUE_SALIENCE", "IMPACT"}

# ─────────────────────────────────────────────────────────────────
# WORDS THAT WORK / WORDS TO AVOID MAP
# ─────────────────────────────────────────────────────────────────

WORDS_MAP = {
    "PD_FUNDING": {
        "work": [
            "Every American deserves a fair trial",
            "Underfunded public defenders",
            "Constitutional right to counsel",
            "Justice system integrity",
            "Level playing field",
        ],
        "avoid": [
            "Free lawyers for criminals",
            "Taxpayer-funded defense for bad guys",
            "Soft on crime",
            "Rewarding criminals",
        ],
    },
    "INVEST": {
        "work": [
            "Invest in safer communities",
            "Prevention saves money",
            "Evidence-based programs",
            "Break the cycle",
            "Community healing",
        ],
        "avoid": [
            "Defund police",
            "Social spending on criminals",
            "Government handouts",
            "Throwing money at the problem",
        ],
    },
    "DV": {
        "work": [
            "Victims trapped in violent homes",
            "Courts failing abuse survivors",
            "Circumstances matter",
            "Holding the real abuser accountable",
            "Protecting the vulnerable",
        ],
        "avoid": [
            "Excuses for crime",
            "Get-out-of-jail-free card",
            "Playing the victim card",
            "Blaming the victim",
        ],
    },
    "REDEMPTION": {
        "work": [
            "People can change",
            "Earned second chances",
            "Productive taxpaying citizens",
            "Proven by the evidence",
            "Rehabilitation works",
        ],
        "avoid": [
            "Letting criminals loose",
            "Coddling offenders",
            "Easy on crime",
            "No consequences",
        ],
    },
    "EXPUNGE": {
        "work": [
            "Clean slate for those who earned it",
            "Remove barriers to employment",
            "Reduce recidivism",
            "Taxpayer savings",
            "Second chances that work",
        ],
        "avoid": [
            "Erasing criminal history",
            "Hiding past crimes",
            "No accountability",
            "Pretend it never happened",
        ],
    },
    "SENTREVIEW": {
        "work": [
            "Review outdated sentences",
            "Proportional punishment",
            "Judicial oversight",
            "Correcting injustice",
            "Fairness in sentencing",
        ],
        "avoid": [
            "Letting prisoners go free",
            "Overturning verdicts",
            "Ignoring victims",
            "Criminals getting away with it",
        ],
    },
    "BAIL": {
        "work": [
            "Innocent until proven guilty",
            "Risk-based release",
            "Don't punish poverty",
            "Taxpayer costs of pretrial detention",
            "Fair bail system",
        ],
        "avoid": [
            "Free bail for everyone",
            "Open the jailhouse doors",
            "No consequences before trial",
            "Criminals back on the streets",
        ],
    },
    "MAND": {
        "work": [
            "Let judges judge",
            "Case-by-case justice",
            "One size doesn't fit all",
            "Judicial discretion",
            "Individual circumstances matter",
        ],
        "avoid": [
            "Soft sentences",
            "Weak on crime",
            "Judge shopping",
            "No standards",
        ],
    },
    "JUDICIAL": {
        "work": [
            "Judges know their communities",
            "Justice requires flexibility",
            "Context matters",
            "Fair and reasoned decisions",
            "Trust in our courts",
        ],
        "avoid": [
            "Judges letting criminals off",
            "No accountability",
            "Inconsistent sentences",
            "Politicizing the courts",
        ],
    },
    "REENTRY": {
        "work": [
            "Successful reentry reduces crime",
            "Employment = stability",
            "Supporting those who've paid their debt",
            "Evidence-based pathways",
            "Building productive lives",
        ],
        "avoid": [
            "Coddling released prisoners",
            "Wasting tax dollars",
            "No consequences",
            "Soft approach to crime",
        ],
    },
}

# ─────────────────────────────────────────────────────────────────
# MESSAGE FRAMEWORK MAP
# ─────────────────────────────────────────────────────────────────

FRAMEWORK_MAP = {
    "PD_FUNDING": {
        "data": "82% of voters — including strong majorities of Republicans — support adequate funding for public defenders.",
        "frame": "Constitutional rights frame: this is about the 6th Amendment working as intended, not expanding government.",
        "inoculation": "Opponents say this is 'more spending.' Counter: underfunded defense costs MORE through wrongful convictions and appeals.",
        "cta": "Support adequate public defender funding in your state.",
    },
    "DV": {
        "data": "65% of the most anti-reform voters agree that domestic violence should be considered a mitigating factor in sentencing.",
        "frame": "Mitigating circumstances frame: courts should consider WHY someone committed a crime, especially abuse victims.",
        "inoculation": "Opponents say this 'excuses crime.' Counter: recognizing DV as a factor IS part of proportional justice.",
        "cta": "Advocate for DV-informed sentencing guidelines.",
    },
    "REDEMPTION": {
        "data": "53% of reform skeptics believe people can earn a second chance — the key persuasion bridge.",
        "frame": "Earned redemption frame: focus on demonstrated change, not automatic forgiveness.",
        "inoculation": "Opponents say 'once a criminal, always a criminal.' Counter: decades of evidence show people change, and reentry programs reduce crime.",
        "cta": "Support evidence-based reentry and second-chance programs.",
    },
    "EXPUNGE": {
        "data": "60% of voters support clearing records for people who have served their time and stayed out of trouble.",
        "frame": "Clean slate frame: removing barriers to employment, housing, and education reduces recidivism.",
        "inoculation": "Opponents say records are 'forever evidence.' Counter: expungement is only for those who've earned it, not automatic.",
        "cta": "Support earned record expungement in your state.",
    },
    "BAIL": {
        "data": "71% of voters believe bail should be based on flight risk and danger, not ability to pay.",
        "frame": "Constitutional fairness frame: money shouldn't be the only way to get out of jail before trial.",
        "inoculation": "Opponents say 'criminals will flee.' Counter: risk-based systems are more effective at preventing both.",
        "cta": "Advocate for risk-based bail reform.",
    },
    "SENTREVIEW": {
        "data": "68% of voters support judicial review of disproportionately long sentences.",
        "frame": "Judicial oversight frame: letting judges review and adjust outdated sentences.",
        "inoculation": "Opponents say this 'overturns justice.' Counter: proportionality is fundamental to any fair system.",
        "cta": "Support sentence review and proportionality reforms.",
    },
    "MAND": {
        "data": "64% of voters believe judges should have flexibility to consider individual circumstances.",
        "frame": "Justice flexibility frame: one size doesn't fit all; judges are trained to make these decisions.",
        "inoculation": "Opponents say 'crime needs one standard.' Counter: sentencing guidelines provide structure while allowing flexibility.",
        "cta": "Support reducing mandatory minimum sentences.",
    },
    "INVEST": {
        "data": "73% of voters support investing in prevention and treatment programs.",
        "frame": "Proven prevention frame: programs that work save money and prevent future crime.",
        "inoculation": "Opponents say 'government shouldn't fund criminals.' Counter: prevention programs aren't for offenders, they're for communities.",
        "cta": "Invest in evidence-based prevention and reentry programs.",
    },
}

# ─────────────────────────────────────────────────────────────────
# PAGE HEADER
# ─────────────────────────────────────────────────────────────────

st.title("MediaMaker")
st.markdown(
    "Select a reform topic → see evidence-based messaging guidance to persuade your audience.",
    unsafe_allow_html=True,
)

st.divider()

# ─────────────────────────────────────────────────────────────────
# TOPIC PICKER
# ─────────────────────────────────────────────────────────────────

st.markdown("### Step 1: Select a Topic")

# Filter out gauge constructs
topic_options = {k: v for k, v in CONSTRUCT_LABELS.items() if k not in GAUGE_CONSTRUCTS}
sorted_topics = sorted(topic_options.items(), key=lambda x: x[1])

selected_construct = st.selectbox(
    "Choose a reform topic:",
    options=[code for code, _ in sorted_topics],
    format_func=lambda code: f"{CONSTRUCT_LABELS[code]}",
    key="topic_picker",
)

st.markdown("")

# Show selected topic details
selected_label = CONSTRUCT_LABELS[selected_construct]
selected_tier = TIER_MAP.get(selected_construct, "Unknown")

col1, col2 = st.columns([2, 1])
with col1:
    st.markdown(f"**Selected Topic:** {selected_label}")
with col2:
    st.markdown(f"**Persuasion Tier:** {selected_tier}")

st.divider()

# ─────────────────────────────────────────────────────────────────
# WORDS THAT WORK / WORDS TO AVOID
# ─────────────────────────────────────────────────────────────────

st.markdown("### Step 2: Words That Work / Words to Avoid")
st.markdown(
    "Use these phrases with persuadable audiences. Avoid phrases that trigger opposition or shut down conversation.",
    unsafe_allow_html=True,
)

st.markdown("")

# Check if construct has data in WORDS_MAP
if selected_construct in WORDS_MAP:
    words_data = WORDS_MAP[selected_construct]
    work_phrases = words_data.get("work", [])
    avoid_phrases = words_data.get("avoid", [])

    col_work, col_avoid = st.columns(2)

    # LEFT COLUMN: Words That Work (Green)
    with col_work:
        st.markdown(f"""
        <div style="
            background: rgba(27, 107, 58, 0.08);
            border-left: 5px solid #1B6B3A;
            border-radius: 8px;
            padding: 1.25rem;
            margin-bottom: 0;
        ">
            <div style="font-weight: 700; color: #1B6B3A; margin-bottom: 1rem; font-size: 1.05rem;">
                ✓ Words That Work
            </div>
            <div style="color: {TEXT1}; line-height: 1.8;">
        """, unsafe_allow_html=True)

        for phrase in work_phrases:
            st.markdown(f"- {phrase}")

        st.markdown("</div></div>", unsafe_allow_html=True)

    # RIGHT COLUMN: Words to Avoid (Red)
    with col_avoid:
        st.markdown(f"""
        <div style="
            background: rgba(139, 26, 26, 0.08);
            border-left: 5px solid #8B1A1A;
            border-radius: 8px;
            padding: 1.25rem;
            margin-bottom: 0;
        ">
            <div style="font-weight: 700; color: #8B1A1A; margin-bottom: 1rem; font-size: 1.05rem;">
                ✗ Words to Avoid
            </div>
            <div style="color: {TEXT1}; line-height: 1.8;">
        """, unsafe_allow_html=True)

        for phrase in avoid_phrases:
            st.markdown(f"- {phrase}")

        st.markdown("</div></div>", unsafe_allow_html=True)

else:
    st.info(
        f"💡 Message testing data for **{selected_label}** is coming in the next survey wave. "
        "Check back soon for Words That Work and Words to Avoid.",
        icon="ℹ️",
    )

st.markdown("")
st.divider()

# ─────────────────────────────────────────────────────────────────
# MESSAGE FRAMEWORK BOX (Four-Step Framework)
# ─────────────────────────────────────────────────────────────────

st.markdown("### Step 3: Message Framework")
st.markdown(
    "This four-step framework shows how to structure persuasive messaging for this topic.",
    unsafe_allow_html=True,
)

st.markdown("")

# Check if construct has framework data
if selected_construct in FRAMEWORK_MAP:
    framework = FRAMEWORK_MAP[selected_construct]

    # Step 1: Data Anchor (Navy)
    st.markdown(f"""
    <div style="
        background: {CARD_BG};
        border-left: 5px solid {NAVY};
        border-radius: 8px;
        padding: 1.25rem;
        margin-bottom: 1rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    ">
        <div style="font-weight: 700; color: {NAVY}; margin-bottom: 0.5rem; font-size: 1rem;">
            1. Data Anchor
        </div>
        <div style="font-size: 0.95rem; color: {TEXT1}; line-height: 1.6;">
            {framework['data']}
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Step 2: Strategic Frame (Teal)
    st.markdown(f"""
    <div style="
        background: {CARD_BG};
        border-left: 5px solid #0D7C7C;
        border-radius: 8px;
        padding: 1.25rem;
        margin-bottom: 1rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    ">
        <div style="font-weight: 700; color: #0D7C7C; margin-bottom: 0.5rem; font-size: 1rem;">
            2. Strategic Frame
        </div>
        <div style="font-size: 0.95rem; color: {TEXT1}; line-height: 1.6;">
            {framework['frame']}
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Step 3: Inoculation (Gold)
    st.markdown(f"""
    <div style="
        background: {CARD_BG};
        border-left: 5px solid {GOLD};
        border-radius: 8px;
        padding: 1.25rem;
        margin-bottom: 1rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    ">
        <div style="font-weight: 700; color: {GOLD}; margin-bottom: 0.5rem; font-size: 1rem;">
            3. Inoculation
        </div>
        <div style="font-size: 0.95rem; color: {TEXT1}; line-height: 1.6;">
            {framework['inoculation']}
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Step 4: Call to Action (Green)
    st.markdown(f"""
    <div style="
        background: {CARD_BG};
        border-left: 5px solid #1B6B3A;
        border-radius: 8px;
        padding: 1.25rem;
        margin-bottom: 0;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    ">
        <div style="font-weight: 700; color: #1B6B3A; margin-bottom: 0.5rem; font-size: 1rem;">
            4. Call to Action
        </div>
        <div style="font-size: 0.95rem; color: {TEXT1}; line-height: 1.6;">
            {framework['cta']}
        </div>
    </div>
    """, unsafe_allow_html=True)

else:
    st.info(
        f"💡 Framework data for **{selected_label}** is being developed. Check back soon.",
        icon="ℹ️",
    )

st.markdown("")
st.divider()

# ─────────────────────────────────────────────────────────────────
# STEP 4: CUSTOM INPUTS — bills, news, assets
# ─────────────────────────────────────────────────────────────────

st.markdown("### Step 4: Add Your Source Materials")
st.caption(
    "Drop in a bill, news article, or list of spokespeople to tailor your messaging. "
    "The AI will combine your inputs with the polling data above to generate sharper communications."
)

input_col1, input_col2 = st.columns(2)

with input_col1:
    st.markdown(f"""
    <div style="font-weight:600;color:{NAVY};margin-bottom:0.5rem;">📄 Bill Text or Policy Document</div>
    """, unsafe_allow_html=True)
    bill_text = st.text_area(
        "Paste bill text, executive summary, or key provisions",
        height=150,
        placeholder="e.g. HB 1234 — Amends §18.2-308.1 to require judicial review of sentences exceeding 20 years...",
        key="mm_bill_text",
    )

    st.markdown(f"""
    <div style="font-weight:600;color:{NAVY};margin-bottom:0.5rem;margin-top:1rem;">🔗 News Links</div>
    """, unsafe_allow_html=True)
    news_links = st.text_area(
        "Paste URLs to relevant news articles, one per line",
        height=100,
        placeholder="https://apnews.com/article/sentencing-reform-2026...\nhttps://localnews.com/bail-reform-passes-committee...",
        key="mm_news_links",
    )

with input_col2:
    st.markdown(f"""
    <div style="font-weight:600;color:{NAVY};margin-bottom:0.5rem;">🎤 Spokespeople & Assets</div>
    """, unsafe_allow_html=True)
    assets_text = st.text_area(
        "List people available for ads, quotes, or testimonials (name, role, why they matter)",
        height=150,
        placeholder="e.g.\n• James Wilson — formerly incarcerated, now runs a reentry nonprofit\n• Sheriff Maria Torres — Republican sheriff, supports bail reform\n• Dr. Amari Johnson — criminologist at State U, publishes on recidivism",
        key="mm_assets",
    )

    st.markdown(f"""
    <div style="font-weight:600;color:{NAVY};margin-bottom:0.5rem;margin-top:1rem;">🎯 Target Audience</div>
    """, unsafe_allow_html=True)
    audience = st.selectbox(
        "Who is this communication for?",
        [
            "General public",
            "Republican persuadables",
            "Democratic base (mobilization)",
            "Independent / swing voters",
            "State legislators",
            "Local media / editorial boards",
            "Grassroots advocates / organizers",
            "Donors and funders",
        ],
        key="mm_audience",
    )

    output_format = st.selectbox(
        "Output format",
        [
            "Social media post (short)",
            "Op-ed / letter to editor",
            "30-second ad script",
            "60-second radio script",
            "Door-knock talking points",
            "Email to legislator",
            "Press release",
            "Fundraising email",
        ],
        key="mm_format",
    )

# Generate button
st.markdown("")
has_inputs = bool(bill_text.strip() or news_links.strip() or assets_text.strip())

if has_inputs:
    generate_btn = st.button("📢 Generate Message", type="primary", key="mm_generate")

    if generate_btn:
        # Build context string from inputs
        context_parts = []
        if selected_construct and selected_construct in WORDS_MAP:
            wm = WORDS_MAP[selected_construct]
            context_parts.append(f"TOPIC: {CONSTRUCT_LABELS.get(selected_construct, selected_construct)}")
            context_parts.append(f"TIER: {TIER_MAP.get(selected_construct, 'Unknown')}")
            context_parts.append(f"WORDS THAT WORK: {', '.join(wm['work'])}")
            context_parts.append(f"WORDS TO AVOID: {', '.join(wm['avoid'])}")
        if selected_construct and selected_construct in FRAMEWORK_MAP:
            fm = FRAMEWORK_MAP[selected_construct]
            context_parts.append(f"DATA ANCHOR: {fm['data']}")
            context_parts.append(f"STRATEGIC FRAME: {fm['frame']}")
            context_parts.append(f"INOCULATION: {fm['inoculation']}")
        if bill_text.strip():
            context_parts.append(f"BILL/POLICY TEXT: {bill_text.strip()[:2000]}")
        if news_links.strip():
            context_parts.append(f"NEWS LINKS: {news_links.strip()[:500]}")
        if assets_text.strip():
            context_parts.append(f"AVAILABLE SPOKESPEOPLE: {assets_text.strip()[:1000]}")
        context_parts.append(f"TARGET AUDIENCE: {audience}")
        context_parts.append(f"OUTPUT FORMAT: {output_format}")

        st.info(
            "💡 **Tip**: Copy the brief below and take it to the **AI Analysis** page to generate your message. "
            "Copy the context below and paste it into the AI Analysis page chat — "
            "the AI has access to all the polling data and frameworks."
        )

        with st.expander("📋 Your message brief (copy to chat)", expanded=True):
            brief = "\n".join(context_parts)
            st.code(brief, language=None)
else:
    st.markdown(f"""
    <div style="background:rgba(184,135,10,0.08);border:1px dashed {GOLD_MID};border-radius:8px;
         padding:1rem 1.25rem;text-align:center;color:{TEXT2};">
        Add a bill, news link, or spokesperson list above to generate tailored messages.
    </div>
    """, unsafe_allow_html=True)

st.markdown("")
st.divider()

# ─────────────────────────────────────────────────────────────────
# CHAT WIDGET & FOOTER
# ─────────────────────────────────────────────────────────────────

portal_footer()
