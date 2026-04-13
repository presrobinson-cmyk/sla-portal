"""
SurveyMaker — Question Banking and Survey Assembly
Browse scored questions from the question bank, filter by topic and persuasion tier, and preview question details.
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
    apply_theme, portal_footer, data_source_badge, get_supabase_config, get_supabase_headers,
    CJ_SURVEYS, TIER_MAP,
    NAVY, NAVY2, GOLD, GOLD_MID, TEXT1, TEXT2, TEXT3, BORDER2, BG, CARD_BG,
)
from auth import require_auth
from chat_widget import render_chat

try:
    from content_scoring import SKIPPED_QIDS, get_construct, score_content
    SCORING_AVAILABLE = True
except ImportError:
    SCORING_AVAILABLE = False

try:
    from survey_insights_cache import get_insights_for_constructs, SURVEY_INSIGHTS
    INSIGHTS_AVAILABLE = True
except ImportError:
    INSIGHTS_AVAILABLE = False

# Shared data loader (MrP primary, raw fallback)
from data_loader import load_question_data_hybrid, render_data_source_toggle, get_display_pct

st.set_page_config(
    page_title="SurveyMaker — SLA Portal",
    page_icon="✏️",
    layout="wide",
)

apply_theme()
username = require_auth("Second Look Alliance", accent_color=GOLD)

# ─────────────────────────────────────────────────────────────────
# CONSTRUCT LABELS (all ~35 constructs from other pages)
# ─────────────────────────────────────────────────────────────────

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
    "COMPASSION": "Compassionate Release", "CLEMENCY": "Clemency",
    "MENTAL_ADDICTION": "Mental Health & Addiction", "RACIAL_DISPARITIES": "Racial Disparities",
    "GOODTIME": "Good Time Credits", "REVIEW": "Case Review",
    "CONDITIONS": "Prison Conditions", "AGING": "Aging in Prison",
    "PAROLE": "Parole Reform", "REVISIT": "Sentence Revisiting",
}

GAUGE_CONSTRUCTS = {"CAND", "TOUGHCRIME", "ISSUE_SALIENCE", "IMPACT"}

# ─────────────────────────────────────────────────────────────────
# PAGINATION HELPER
# ─────────────────────────────────────────────────────────────────

def _paginate(url_base, headers, limit=1000, max_rows=200000):
    """Paginate through Supabase results."""
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

# ─────────────────────────────────────────────────────────────────
# LOAD AND SCORE QUESTIONS
# ─────────────────────────────────────────────────────────────────

@st.cache_data(ttl=3600)
def load_and_score_questions_cached():
    """Load all scored questions using MrP-adjusted rates (primary), raw fallback."""
    try:
        question_data, mrp_coverage = load_question_data_hybrid()
        return question_data
    except Exception as e:
        st.error(f"Error loading questions: {str(e)}")
        return {}


def load_and_score_questions(data_mode="mrp"):
    """Build display-ready question dataframe, respecting MrP/raw toggle."""
    question_data = load_and_score_questions_cached()
    if not question_data:
        return pd.DataFrame()

    results = []
    for qid, qd in question_data.items():
        construct = qd.get("construct", "")
        if not construct or construct in GAUGE_CONSTRUCTS:
            continue
        tier = TIER_MAP.get(construct, "Unclassified")
        topic_label = CONSTRUCT_LABELS.get(construct, construct)

        results.append({
            'qid': qid,
            'text': qd["question_text"],
            'construct': construct,
            'topic_label': topic_label,
            'tier': tier,
            'overall_support': get_display_pct(qd, data_mode),
            'n_respondents': qd["n_respondents"],
            'source': "raw" if data_mode == "raw" else qd["source"],
        })

    if not results:
        return pd.DataFrame()

    result_df = pd.DataFrame(results)
    return result_df.sort_values('overall_support', ascending=False)

# ─────────────────────────────────────────────────────────────────
# PAGE HEADER
# ─────────────────────────────────────────────────────────────────

st.title("SurveyMaker")

# MrP/Raw toggle
data_mode = render_data_source_toggle()
data_source_badge(data_mode)

st.markdown(
    "Build surveys from a scored question library · start with the behavioral and demographic foundation · add policy questions by topic"
)

st.divider()

# ─────────────────────────────────────────────────────────────────
# LOAD DATA
# ─────────────────────────────────────────────────────────────────

with st.spinner("Loading question bank..."):
    questions_df = load_and_score_questions(data_mode=data_mode)

if questions_df.empty:
    st.warning("No scored questions found. Please check your Supabase connection.")
    portal_footer()
    st.stop()

# ─────────────────────────────────────────────────────────────────
# SIDEBAR FILTERS
# ─────────────────────────────────────────────────────────────────

st.sidebar.markdown("### Policy Question Filters")
st.sidebar.caption("The behavioral and demographic batteries are fixed starting blocks — use the filters below to select your policy questions.")

# Topic filter — full names only, no abbreviations
available_topics = sorted(questions_df['topic_label'].unique())
selected_topics = st.sidebar.multiselect(
    "Topic",
    available_topics,
    default=available_topics[:5] if len(available_topics) > 5 else available_topics
)

# Support level filter
support_options = [
    "All",
    "Strong Consensus (75%+)",
    "Moderate (55-74%)",
    "Contested (<55%)"
]
selected_support = st.sidebar.selectbox("Support Level", support_options, index=0)

# Sort options — no internal jargon
sort_options = [
    "Support % (descending)",
    "Support % (ascending)",
    "Topic (A-Z)",
    "Message Readiness (broadest first)",
]
selected_sort = st.sidebar.selectbox("Sort By", sort_options, index=0)

# Keep tier for internal filtering logic but don't expose it as a user-facing option
selected_tier = "All"

# ─────────────────────────────────────────────────────────────────
# APPLY FILTERS
# ─────────────────────────────────────────────────────────────────

filtered_df = questions_df.copy()

# Topic filter
if selected_topics:
    filtered_df = filtered_df[filtered_df['topic_label'].isin(selected_topics)]

# Tier filter
if selected_tier != "All":
    filtered_df = filtered_df[filtered_df['tier'] == selected_tier]

# Support level filter
if selected_support == "Strong Consensus (75%+)":
    filtered_df = filtered_df[filtered_df['overall_support'] >= 75]
elif selected_support == "Moderate (55-74%)":
    filtered_df = filtered_df[(filtered_df['overall_support'] >= 55) & (filtered_df['overall_support'] < 75)]
elif selected_support == "Contested (<55%)":
    filtered_df = filtered_df[filtered_df['overall_support'] < 55]

# Sort
if selected_sort == "Support % (descending)":
    filtered_df = filtered_df.sort_values('overall_support', ascending=False)
elif selected_sort == "Support % (ascending)":
    filtered_df = filtered_df.sort_values('overall_support', ascending=True)
elif selected_sort == "Topic (A-Z)":
    filtered_df = filtered_df.sort_values('topic_label')
elif selected_sort == "Message Readiness (broadest first)":
    tier_order = {"Entry": 1, "Bridge": 2, "Downstream": 3, "Destination": 4, "Unclassified": 5}
    filtered_df['tier_order'] = filtered_df['tier'].map(tier_order)
    filtered_df = filtered_df.sort_values(['tier_order', 'overall_support'], ascending=[True, False]).drop('tier_order', axis=1)

# ─────────────────────────────────────────────────────────────────
# QUESTION BROWSER
# ─────────────────────────────────────────────────────────────────

# ─────────────────────────────────────────────────────────────────
# STANDARD SURVEY STRUCTURE — BEHAVIORAL + DEMOGRAPHIC BATTERIES
# ─────────────────────────────────────────────────────────────────

st.markdown("### Standard Survey Structure")
st.markdown(
    "Every survey includes two fixed blocks before policy questions. "
    "These are not optional — behavioral and demographic data are what make the policy questions interpretable."
)

bat_col1, bat_col2 = st.columns(2)

with bat_col1:
    with st.expander("🧭 Behavioral Battery (include in every survey)", expanded=False):
        st.markdown(f"""
<div style="font-size:0.83rem;color:{TEXT2};line-height:1.6;">
<strong>Why this matters:</strong> Behavioral past-action questions reveal intensity and salience — not just what
people think, but whether they care enough to act. Someone who has spoken to a neighbor about
criminal justice reform is a different kind of respondent than someone who holds the same stated
opinion but has never engaged. Behavioral data predicts who will show up, who can be organized, and who
will persuade others in their network.
<br><br>
<strong>Rule: every question asks what they HAVE done, not what they would do.</strong>
Aspirational-intent questions ("Would you contact an official?") inflate estimates
and measure nothing actionable.
</div>
""", unsafe_allow_html=True)
        st.markdown("")
        behavioral_questions = [
            ("B1", "In the past 12 months, have you spoken with a friend, family member, or neighbor about the criminal justice system?",
             "Yes / No", "Measures social salience — who is already talking about this. High yes-rate = issue has organic reach."),
            ("B2", "Have you or anyone close to you ever been arrested, charged, or incarcerated?",
             "Yes / No", "Personal experience predictor. Experience = higher intensity, higher persuadability on reform."),
            ("B3", "Have you ever contacted a state or local elected official about any issue related to criminal justice or public safety?",
             "Yes / No", "Civic engagement baseline. Separates passive holders from active advocates."),
            ("B4", "In the past 12 months, have you shared news or information about criminal justice on social media or via text?",
             "Yes / No", "Network diffusion potential. These are your organic amplifiers."),
            ("B5", "Have you ever attended a community meeting, town hall, or public event focused on criminal justice or public safety?",
             "Yes / No", "Organizational engagement indicator. High yes-rate = organized community, not just sympathetic one."),
            ("B6", "Do you personally know anyone who is currently serving a prison or jail sentence?",
             "Yes / No", "Proximity indicator. Strongest driver of attitude change and behavioral engagement on CJ issues."),
            ("B7", "Have you ever served as a juror in a criminal case?",
             "Yes / No", "First-hand system exposure. Jurors have visceral system knowledge — frames their reading of reform questions."),
            ("B8", "How likely are you, in the next 12 months, to take action on criminal justice issues — such as signing a petition, attending a meeting, contacting an official, or voting specifically on this issue?",
             "Very likely / Somewhat likely / Somewhat unlikely / Very unlikely",
             "Forward behavioral intention. Combined with B1-B7, identifies your top persuasion and mobilization targets."),
        ]
        for code, text, scale, rationale in behavioral_questions:
            st.markdown(f"""
<div style="background:rgba(14,31,61,0.03);border-left:3px solid {NAVY2};border-radius:6px;
     padding:0.5rem 0.75rem;margin-bottom:8px;">
<div style="font-size:0.78rem;font-weight:700;color:{NAVY};">{code}: {text}</div>
<div style="font-size:0.72rem;color:{TEXT3};margin-top:2px;">Scale: {scale}</div>
<div style="font-size:0.74rem;color:{TEXT2};margin-top:4px;font-style:italic;">{rationale}</div>
</div>
""", unsafe_allow_html=True)

with bat_col2:
    with st.expander("📊 Demographic Battery (standard weighting variables)", expanded=False):
        st.markdown(f"""
<div style="font-size:0.83rem;color:{TEXT2};line-height:1.6;">
<strong>Why this matters:</strong> Demographics make MrP (Multilevel Regression with Poststratification) possible.
Without them, you can't weight results to population targets, and you can't disaggregate findings by
subgroup. Every variable below serves double duty: it's a weighting variable AND an analysis dimension.
<br><br>
<strong>Standard = required. Optional = add only when needed for specific research goals.</strong>
</div>
""", unsafe_allow_html=True)
        st.markdown("")
        demo_standard = [
            ("D1", "Age", "18–29 / 30–44 / 45–64 / 65 or older", "Standard"),
            ("D2", "Gender", "Man / Woman / Non-binary or gender non-conforming / Prefer not to say", "Standard"),
            ("D3", "Race / Ethnicity", "White (non-Hispanic) / Black or African American / Hispanic or Latino / Asian or Pacific Islander / Mixed race or multiracial / Other / Prefer not to say", "Standard"),
            ("D4", "Education", "Less than high school / High school diploma or GED / Some college / Bachelor's degree / Graduate or professional degree", "Standard"),
            ("D5", "Household income (approximate)", "Under $30,000 / $30,000–$50,000 / $50,000–$75,000 / $75,000–$100,000 / Over $100,000 / Prefer not to say", "Standard"),
            ("D6", "Political party", "Republican / Democrat / Independent / Another party / No affiliation", "Standard"),
            ("D7", "Political ideology", "Very conservative / Somewhat conservative / Moderate / Somewhat liberal / Very liberal", "Standard"),
            ("D8", "Area type", "Urban (large city) / Suburban / Small town / Rural", "Standard"),
            ("D9", "State of residence", "[Dropdown by state]", "Standard"),
            ("D10", "Employment status", "Employed full-time / Part-time / Self-employed / Retired / Student / Unemployed or looking / Not in workforce", "Optional"),
            ("D11", "Union household", "Yes, I or someone in my household is a union member / No", "Optional"),
            ("D12", "Religious service attendance", "Weekly or more / Monthly / A few times per year / Rarely or never", "Optional — adds predictive power for DV, compassion, redemption constructs"),
        ]
        for code, label, options, flag in demo_standard:
            flag_color = "#1B6B3A" if flag == "Standard" else "#B8870A"
            flag_bg = "rgba(27,107,58,0.08)" if flag == "Standard" else "rgba(184,135,10,0.08)"
            st.markdown(f"""
<div style="background:{flag_bg};border-left:3px solid {flag_color};border-radius:6px;
     padding:0.45rem 0.75rem;margin-bottom:7px;">
<div style="display:flex;justify-content:space-between;align-items:center;">
    <span style="font-size:0.78rem;font-weight:700;color:{NAVY};">{code}: {label}</span>
    <span style="font-size:0.68rem;color:{flag_color};font-weight:600;">{flag}</span>
</div>
<div style="font-size:0.71rem;color:{TEXT2};margin-top:3px;">{options}</div>
</div>
""", unsafe_allow_html=True)

st.divider()

# ─────────────────────────────────────────────────────────────────
# POLICY QUESTION BROWSER
# ─────────────────────────────────────────────────────────────────

col_left, col_right = st.columns([2, 1])

with col_left:
    st.markdown("### Policy Question Library")
    st.markdown(f"**{len(filtered_df)} questions** matching filters")

    if filtered_df.empty:
        st.info("No questions match your filter criteria. Try adjusting the filters.")
    else:
        # Create display table
        display_df = filtered_df[[
            'text', 'topic_label', 'tier', 'overall_support', 'n_respondents'
        ]].copy()
        display_df.columns = ['Question', 'Topic', 'Tier', 'Support %', 'N']
        display_df['Support %'] = display_df['Support %'].round(1).astype(str) + "%"

        # Interactive selection
        selected_idx = st.selectbox(
            "Select a question to view details:",
            range(len(filtered_df)),
            format_func=lambda i: f"{filtered_df.iloc[i]['topic_label']}: {filtered_df.iloc[i]['text'][:60]}..."
        )

        # Display table
        st.dataframe(
            display_df,
            use_container_width=True,
            height=400,
            hide_index=True
        )

with col_right:
    st.markdown("### Summary Stats")

    total_qs = len(questions_df)
    total_topics = questions_df['topic_label'].nunique()
    avg_support = questions_df['overall_support'].mean()

    st.metric("Total Questions", total_qs)
    st.metric("Topics Covered", total_topics)
    st.metric("Avg Support", f"{avg_support:.1f}%")

# ─────────────────────────────────────────────────────────────────
# QUESTION DETAIL VIEW
# ─────────────────────────────────────────────────────────────────

st.divider()

selected_question = filtered_df.iloc[selected_idx]

st.markdown("### Question Detail")

detail_col1, detail_col2 = st.columns([2, 1])

with detail_col1:
    st.markdown(f"""
    <div style="background:{CARD_BG};border:2px solid {GOLD};border-radius:10px;padding:2rem;box-shadow:0 2px 8px rgba(0,0,0,0.08);">
        <div style="font-size:1.1rem;line-height:1.8;color:{TEXT1};font-family:'Georgia',serif;margin-bottom:1.5rem;">
            {selected_question['text']}
        </div>
        <div style="display:flex;gap:0.5rem;flex-wrap:wrap;">
            <span style="background:{NAVY};color:white;padding:0.4rem 0.8rem;border-radius:4px;font-size:0.85rem;font-weight:600;">
                {selected_question['tier']}
            </span>
            <span style="background:{GOLD};color:{NAVY};padding:0.4rem 0.8rem;border-radius:4px;font-size:0.85rem;font-weight:600;">
                {selected_question['topic_label']}
            </span>
        </div>
    </div>
    """, unsafe_allow_html=True)

with detail_col2:
    st.markdown("#### Support Metrics")
    support_pct = selected_question['overall_support']
    st.metric("Overall Support", f"{support_pct:.1f}%")
    st.metric("Respondents", f"{selected_question['n_respondents']:,}")

# Support visualization
st.markdown("#### Support Distribution")
support_bar_html = f"""
<div style="margin-top:1rem;">
    <div style="display:flex;align-items:center;gap:1rem;">
        <div style="width:100%;background:{BORDER2};height:30px;border-radius:5px;overflow:hidden;">
            <div style="background:{GOLD};height:100%;width:{support_pct:.1f}%;transition:width 0.3s;"></div>
        </div>
        <div style="min-width:60px;font-weight:600;color:{NAVY};">{support_pct:.1f}%</div>
    </div>
</div>
"""
st.markdown(support_bar_html, unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────
# CONSTRUCT COVERAGE HEATMAP
# ─────────────────────────────────────────────────────────────────

st.divider()
st.markdown("### Construct Coverage Analysis")
st.markdown(
    "How many questions does the bank have per construct? "
    "Constructs with fewer than 3 questions produce unreliable MrP estimates. "
    "The LA-CJ-2025-002 lesson: thin construct coverage causes low reliability scores, not data bugs.",
)

st.markdown("")

# Build per-construct question counts from full bank
construct_counts = questions_df.groupby('construct').size().reset_index(name='n_questions')
construct_counts['topic_label'] = construct_counts['construct'].map(
    lambda c: CONSTRUCT_LABELS.get(c, c)
)
construct_counts['tier'] = construct_counts['construct'].map(
    lambda c: TIER_MAP.get(c, "Unclassified")
)
tier_order_map = {"Entry": 1, "Entry (VA)": 1, "Bridge": 2, "Downstream": 3, "Destination": 4, "Gauge": 5, "Unclassified": 6}
construct_counts['tier_order'] = construct_counts['tier'].map(tier_order_map).fillna(6)
construct_counts = construct_counts.sort_values(['tier_order', 'topic_label'])

# Summary badges
n_gap = (construct_counts['n_questions'] == 0).sum()
n_thin = ((construct_counts['n_questions'] >= 1) & (construct_counts['n_questions'] < 3)).sum()
n_min = ((construct_counts['n_questions'] >= 3) & (construct_counts['n_questions'] < 5)).sum()
n_robust = (construct_counts['n_questions'] >= 5).sum()

badge_html = f"""
<div style="display:flex;gap:12px;flex-wrap:wrap;margin-bottom:1rem;">
    <div style="background:rgba(139,26,26,0.1);border:1px solid rgba(139,26,26,0.3);border-radius:20px;
         padding:4px 14px;font-size:0.83rem;font-weight:600;color:#8B1A1A;">⚠️ {n_gap} No coverage</div>
    <div style="background:rgba(184,85,0,0.1);border:1px solid rgba(184,85,0,0.3);border-radius:20px;
         padding:4px 14px;font-size:0.83rem;font-weight:600;color:#B85500;">🔶 {n_thin} Thin (&lt;3 Qs)</div>
    <div style="background:rgba(184,135,10,0.1);border:1px solid rgba(184,135,10,0.3);border-radius:20px;
         padding:4px 14px;font-size:0.83rem;font-weight:600;color:#B8870A;">🔸 {n_min} Minimal (3-4 Qs)</div>
    <div style="background:rgba(27,107,58,0.1);border:1px solid rgba(27,107,58,0.3);border-radius:20px;
         padding:4px 14px;font-size:0.83rem;font-weight:600;color:#1B6B3A;">✅ {n_robust} Robust (5+ Qs)</div>
</div>
"""
st.markdown(badge_html, unsafe_allow_html=True)

# Build coverage grid by tier
coverage_expander = st.expander("View full coverage heatmap", expanded=False)
with coverage_expander:
    for tier_name in ["Entry", "Entry (VA)", "Bridge", "Downstream", "Destination"]:
        tier_rows = construct_counts[construct_counts['tier'].str.startswith(tier_name.split(" ")[0])]
        if tier_name in ["Entry", "Bridge"] or any(construct_counts['tier'] == tier_name):
            pass
        tier_rows = construct_counts[construct_counts['tier'] == tier_name]
        if tier_rows.empty:
            continue

        st.markdown(f"**{tier_name} tier**")
        cols = st.columns(min(len(tier_rows), 5))
        for i, (_, row) in enumerate(tier_rows.iterrows()):
            n = row['n_questions']
            if n == 0:
                bg, color = "rgba(139,26,26,0.12)", "#8B1A1A"
            elif n < 3:
                bg, color = "rgba(184,85,0,0.12)", "#B85500"
            elif n < 5:
                bg, color = "rgba(184,135,10,0.12)", "#B8870A"
            else:
                bg, color = "rgba(27,107,58,0.12)", "#1B6B3A"
            with cols[i % 5]:
                st.markdown(f"""
                <div style="background:{bg};border-radius:8px;padding:0.6rem 0.75rem;
                     margin-bottom:8px;text-align:center;">
                    <div style="font-size:0.78rem;color:{color};font-weight:700;">{n} Q{"s" if n != 1 else ""}</div>
                    <div style="font-size:0.72rem;color:#4A4A42;margin-top:2px;">{row['topic_label']}</div>
                </div>
                """, unsafe_allow_html=True)
        st.markdown("")

# Gap recommendations — constructs with < 3 questions
thin_constructs = construct_counts[construct_counts['n_questions'] < 3].sort_values('tier_order')
if not thin_constructs.empty:
    st.markdown(f"""
    <div style="background:rgba(184,85,0,0.07);border:1px solid rgba(184,85,0,0.25);border-radius:10px;
         padding:1rem 1.25rem;margin-top:0.5rem;">
        <div style="font-weight:700;color:#B85500;margin-bottom:0.5rem;font-size:0.92rem;">
            📋 Gap Recommendations — Add to Next Survey Wave
        </div>
        <div style="font-size:0.84rem;color:{TEXT2};line-height:1.6;">
            These constructs have thin coverage (&lt;3 questions). Adding questions from proven
            question banks in other states will improve reliability scores.
        </div>
        <div style="margin-top:0.75rem;display:flex;flex-wrap:wrap;gap:8px;">
""", unsafe_allow_html=True)
    for _, row in thin_constructs.iterrows():
        n = row['n_questions']
        status = "No questions" if n == 0 else f"{n} question{'s' if n!=1 else ''}"
        st.markdown(f"""
        <span style="display:inline-block;background:rgba(184,85,0,0.1);border:1px solid rgba(184,85,0,0.3);
              border-radius:12px;padding:3px 12px;font-size:0.8rem;color:#B85500;">
            {row['topic_label']} ({status})
        </span>
        """, unsafe_allow_html=True)
    st.markdown("</div></div>", unsafe_allow_html=True)

st.markdown("")
st.divider()

# ─────────────────────────────────────────────────────────────────
# ACTION CONVERSION — what does the data tell you to do?
# ─────────────────────────────────────────────────────────────────

st.markdown("### What Does This Data Tell You to Do?")
st.markdown(
    "Survey data is only useful if it changes what you do next. "
    "Here's how to read the support profile and translate it into campaign strategy."
)

# Compute profiles from filtered data
if not filtered_df.empty:
    avg_support = filtered_df['overall_support'].mean()
    n_high = (filtered_df['overall_support'] >= 75).sum()
    n_contested = (filtered_df['overall_support'] < 55).sum()
    n_total = len(filtered_df)

    tier_counts = filtered_df['tier'].value_counts()
    n_entry = tier_counts.get("Entry", 0) + tier_counts.get("Entry (VA)", 0)
    n_bridge = tier_counts.get("Bridge", 0)
    n_downstream = tier_counts.get("Downstream", 0)

    action_rows = []

    # High bipartisan consensus → broad campaign
    if n_high >= 3 and avg_support >= 70:
        action_rows.append({
            "signal": "✅ Broad Campaign Ready",
            "color": "#1B6B3A",
            "bg": "rgba(27,107,58,0.07)",
            "explanation": f"{n_high} of {n_total} selected questions hit 75%+ support. "
                           "These messages are safe to run broadly — no need to segment by party. "
                           "The creative challenge is differentiation, not persuasion.",
            "action": "Run a general-public campaign. Use bipartisan spokespeople. "
                      "Don't over-target — that narrows your coalition unnecessarily."
        })

    # Heavy downstream / no entry → sequencing problem
    if n_downstream > n_entry + n_bridge:
        action_rows.append({
            "signal": "⚠️ Sequencing Gap",
            "color": "#B85500",
            "bg": "rgba(184,85,0,0.07)",
            "explanation": f"Your selection is heavy on specific policy positions ({n_downstream} questions) "
                           f"but light on the common-ground topics ({n_entry}) that make voters open to hearing them. "
                           "Policy positions land harder after trust is established.",
            "action": "Add broader trust-building questions first. Survey sequencing matters — "
                      "it mirrors the persuasion order of a real conversation."
        })

    # High contested count → reframe before deploy
    if n_contested >= 3:
        action_rows.append({
            "signal": "🔴 Reframe Before Fielding",
            "color": "#8B1A1A",
            "bg": "rgba(139,26,26,0.07)",
            "explanation": f"{n_contested} questions are in contested territory (<55% support). "
                           "Fielding these without established trust first will produce discouraging numbers "
                           "that undercount your actual persuadable universe.",
            "action": "Run trust-establishing questions first in your survey. Or use these contested "
                      "items to identify where reframing is needed before campaign deployment."
        })

    # Entry-heavy → good for diagnostic / readiness survey
    if n_entry >= 4:
        action_rows.append({
            "signal": "📊 Diagnostic Survey Profile",
            "color": "#1155AA",
            "bg": "rgba(17,85,170,0.07)",
            "explanation": f"Your selection is weighted toward common-ground topics ({n_entry} questions). "
                           "This is a good diagnostic profile — ideal for mapping the persuadable landscape "
                           "before committing to specific policy messaging.",
            "action": "Use this survey to identify which door-opening topics resonate most in your specific "
                      "state or district before moving to policy-specific messaging."
        })

    # Behavioral battery reminder
    action_rows.append({
        "signal": "🧭 Cross with Behavioral Data",
        "color": NAVY2,
        "bg": "rgba(14,31,61,0.05)",
        "explanation": "Support rates tell you the position. Behavioral battery questions tell you the intensity "
                       "and organizational reach. The highest-value targets are voters who agree AND have "
                       "already engaged — they're more likely to spread the message in their networks.",
        "action": "Cross-tab your policy support rates with B2 (personal experience), B6 (knows someone incarcerated), "
                  "and B8 (forward intent). These are your most persuadable AND most activatable voters."
    })

    for row in action_rows:
        st.markdown(f"""
<div style="background:{row['bg']};border-left:4px solid {row['color']};border-radius:8px;
     padding:0.75rem 1rem;margin-bottom:10px;">
<div style="font-weight:700;color:{row['color']};font-size:0.88rem;margin-bottom:4px;">{row['signal']}</div>
<div style="font-size:0.82rem;color:{TEXT2};line-height:1.5;margin-bottom:6px;">{row['explanation']}</div>
<div style="font-size:0.79rem;color:{TEXT1};font-weight:600;">→ {row['action']}</div>
</div>
""", unsafe_allow_html=True)

st.markdown("")
st.divider()

# ─────────────────────────────────────────────────────────────────
# SURVEY SEQUENCE — plain language ordering guide
# ─────────────────────────────────────────────────────────────────

st.markdown("### Survey Question Order")
st.markdown(
    "Question order matters — it primes the respondent. This sequence maximizes data quality "
    "and mirrors the persuasion logic: establish common ground before asking about contested positions.",
)

# Tier definitions for pathway display
TIER_SEQUENCE_GROUPS = [
    ("Entry", "Opens the door — broadest bipartisan appeal. Start here.", "#1B6B3A"),
    ("Bridge", "Opens persuadable audiences to reform. Requires Entry foundation.", "#1155AA"),
    ("Downstream", "Specific policy positions. Needs Entry + Bridge groundwork.", "#B8870A"),
    ("Destination", "Significant headwinds — for audiences already persuaded.", "#8B1A1A"),
]

# Get tier counts from filtered questions
tier_counts_filtered = filtered_df.groupby('tier').size().to_dict()
tier_counts_all = questions_df.groupby('tier').size().to_dict()

# Pathway visual
pathway_cols = st.columns(len(TIER_SEQUENCE_GROUPS))
for i, (tier_name, tier_desc, tier_color) in enumerate(TIER_SEQUENCE_GROUPS):
    with pathway_cols[i]:
        n_filtered = tier_counts_filtered.get(tier_name, 0)
        n_total = tier_counts_all.get(tier_name, 0)
        tier_qs = questions_df[questions_df['tier'] == tier_name]
        constructs_in_tier = tier_qs['topic_label'].unique()

        # Count constructs with adequate coverage (3+ questions)
        adequate = sum(
            1 for c in constructs_in_tier
            if len(questions_df[questions_df['topic_label'] == c]) >= 3
        )

        tc_bg_map = {
            "#1B6B3A": "rgba(27,107,58,0.07)",
            "#1155AA": "rgba(17,85,170,0.07)",
            "#B8870A": "rgba(184,135,10,0.07)",
            "#8B1A1A": "rgba(139,26,26,0.07)",
        }
        tier_bg_css = tc_bg_map.get(tier_color, "rgba(14,31,61,0.05)")
        st.markdown(f"""
        <div style="background:{tier_bg_css};
             border:2px solid {tier_color};border-radius:12px;padding:1rem;text-align:center;
             min-height:130px;">
            <div style="font-weight:700;color:{tier_color};font-size:1rem;margin-bottom:4px;">{tier_name}</div>
            <div style="font-size:0.78rem;color:{TEXT2};line-height:1.4;margin-bottom:8px;">{tier_desc}</div>
            <div style="font-size:1.4rem;font-weight:800;color:{tier_color};">{n_total}</div>
            <div style="font-size:0.72rem;color:{TEXT3};">questions in bank</div>
            <div style="font-size:0.72rem;color:{TEXT3};">{adequate} constructs with 3+ Qs</div>
        </div>
        """, unsafe_allow_html=True)

st.markdown(f"""
<div style="font-size:0.82rem;color:{TEXT3};margin-top:0.5rem;text-align:center;">
    ⟵ Sequence surveys left to right: Entry first, Destination last
</div>
""", unsafe_allow_html=True)

# Pathway-ordered question suggestion
st.markdown("")
with st.expander("View pathway-ordered question sequence (for survey assembly)", expanded=False):
    st.markdown(
        "Questions below are sorted by persuasion tier — the recommended sequencing order for a new survey wave.",
    )
    pathway_ordered = questions_df.copy()
    tier_order_map2 = {"Entry": 1, "Entry (VA)": 1, "Bridge": 2, "Downstream": 3, "Destination": 4, "Gauge": 5}
    pathway_ordered['tier_order'] = pathway_ordered['tier'].map(tier_order_map2).fillna(5)
    pathway_ordered = pathway_ordered.sort_values(['tier_order', 'topic_label', 'overall_support'], ascending=[True, True, False])

    current_tier = None
    for _, row in pathway_ordered.head(40).iterrows():
        if row['tier'] != current_tier:
            current_tier = row['tier']
            tier_color_map = {
                "Entry": "#1B6B3A", "Entry (VA)": "#1B6B3A",
                "Bridge": "#1155AA", "Downstream": "#B8870A", "Destination": "#8B1A1A"
            }
            tc = tier_color_map.get(current_tier, TEXT2)
            st.markdown(f"""
            <div style="font-size:0.78rem;font-weight:700;color:{tc};text-transform:uppercase;
                 letter-spacing:0.06em;margin:1rem 0 0.3rem;">── {current_tier} ──</div>
            """, unsafe_allow_html=True)
        pct = row['overall_support']
        pct_str = f"{round(pct)}%" if pct is not None else "—"
        st.markdown(f"""
        <div style="display:flex;gap:10px;align-items:center;margin-bottom:4px;
             padding:4px 8px;border-radius:6px;background:rgba(0,0,0,0.02);">
            <span style="font-size:0.78rem;font-weight:600;color:{NAVY};min-width:42px;">{pct_str}</span>
            <span style="font-size:0.78rem;color:{TEXT2};">{row['topic_label']} — {row['text'][:70]}…</span>
        </div>
        """, unsafe_allow_html=True)

st.markdown("")
st.divider()

# ─────────────────────────────────────────────────────────────────
# QUESTION RECOMMENDATIONS
# ─────────────────────────────────────────────────────────────────

st.markdown("### 📚 Question Recommendations")
st.caption(
    "Top questions from our library for your selected topics, plus design insights "
    "flagged for these constructs. Use this to quickly identify proven questions "
    "and known measurement gaps before building your next wave."
)

rec_col1, rec_col2 = st.columns([3, 2], gap="large")

# Derive active constructs from the current topic selection
active_constructs = (
    sorted(questions_df[questions_df["topic_label"].isin(selected_topics)]["construct"].unique())
    if selected_topics
    else sorted(questions_df["construct"].unique())
)

with rec_col1:
    st.markdown(
        f"""<div style="font-weight:700;color:{NAVY};font-size:0.95rem;
        margin-bottom:0.75rem;">Top Library Picks</div>""",
        unsafe_allow_html=True,
    )

    picks_source = (
        questions_df[questions_df["topic_label"].isin(selected_topics)].copy()
        if selected_topics
        else questions_df.copy()
    )
    picks_df = picks_source.sort_values("overall_support", ascending=False).head(12)

    if picks_df.empty:
        st.info("Select topics in the sidebar to see recommended questions.")
    else:
        tier_colors = {
            "Entry": "#1B6B3A",
            "Bridge": "#1155AA",
            "Downstream": "#B8870A",
            "Destination": "#8B1A1A",
        }
        for _, row in picks_df.iterrows():
            pct = round(row["overall_support"]) if row["overall_support"] is not None else 0
            tier = row.get("tier", "")
            tc = tier_colors.get(tier, TEXT2)

            if pct >= 75:
                rec_label = "Strong consensus"
                rec_bg = "rgba(27,107,58,0.06)"
                dot_color = "#1B6B3A"
            elif pct >= 55:
                rec_label = "Moderate support"
                rec_bg = "rgba(184,135,10,0.06)"
                dot_color = "#B8870A"
            else:
                rec_label = "Contested"
                rec_bg = "rgba(139,26,26,0.05)"
                dot_color = "#8B1A1A"

            qtext = row["text"]
            short_text = (qtext[:110] + "…") if len(qtext) > 110 else qtext
            st.markdown(
                f"""
                <div style="background:{rec_bg};border-radius:8px;padding:0.6rem 0.85rem;
                     margin-bottom:7px;border-left:3px solid {tc};">
                    <div style="font-size:0.82rem;color:{TEXT1};line-height:1.45;">{short_text}</div>
                    <div style="margin-top:4px;display:flex;gap:8px;align-items:center;flex-wrap:wrap;">
                        <span style="font-size:0.76rem;font-weight:700;color:{tc};">{pct}%</span>
                        <span style="font-size:0.72rem;color:{tc};font-weight:600;
                             background:rgba(0,0,0,0.04);padding:1px 7px;border-radius:10px;">{tier}</span>
                        <span style="font-size:0.72rem;color:{TEXT3};">{row['topic_label']}</span>
                        <span style="font-size:0.72rem;color:{dot_color};">· {rec_label}</span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        if len(picks_source) > 12:
            st.caption(f"Showing top 12 of {len(picks_source)} questions for selected topics.")

with rec_col2:
    st.markdown(
        f"""<div style="font-weight:700;color:{NAVY};font-size:0.95rem;
        margin-bottom:0.75rem;">Design Insights</div>""",
        unsafe_allow_html=True,
    )

    if not INSIGHTS_AVAILABLE:
        st.info("survey_insights_cache.py not found. Add it to the portal root.")
    else:
        open_insights = get_insights_for_constructs(active_constructs, status_filter="Open")

        if not open_insights:
            st.success("No open design issues for the selected constructs.")
        else:
            priority_styles = {
                "Must address":    ("#8B1A1A", "rgba(139,26,26,0.08)"),
                "Should address":  ("#B85500", "rgba(184,85,0,0.08)"),
                "Nice to have":    ("#B8870A", "rgba(184,135,10,0.07)"),
                "Long-term":       (TEXT3,     "rgba(14,31,61,0.04)"),
            }
            type_icons = {
                "Measurement Gap":   "📏",
                "Question Design":   "✏️",
                "Scoring Lesson":    "📊",
                "Construct Coverage":"🗂️",
                "Strategic Signal":  "🎯",
                "Methodology":       "⚙️",
            }

            for ins in open_insights[:7]:
                color, bg = priority_styles.get(ins["priority"], (TEXT2, "rgba(0,0,0,0.04)"))
                icon = type_icons.get(ins["type"], "ℹ️")
                aff_constructs = ins["constructs"]
                constructs_str = (
                    ", ".join(aff_constructs[:4]) + ("…" if len(aff_constructs) > 4 else "")
                )
                desc_short = ins["description"][:170] + "…" if len(ins["description"]) > 170 else ins["description"]

                with st.expander(f"{icon} {ins['insight']}", expanded=False):
                    st.markdown(
                        f"""
                        <div style="font-size:0.75rem;color:{color};font-weight:600;
                             margin-bottom:6px;">{ins['priority']} · {ins['type']}</div>
                        <div style="font-size:0.8rem;color:{TEXT1};line-height:1.5;
                             margin-bottom:8px;">{ins['description']}</div>
                        <div style="background:rgba(0,0,0,0.03);border-radius:6px;
                             padding:0.5rem 0.75rem;margin-bottom:6px;">
                            <div style="font-size:0.73rem;font-weight:700;color:{NAVY};
                                 margin-bottom:4px;">Recommended action</div>
                            <div style="font-size:0.78rem;color:{TEXT2};line-height:1.45;">
                                {ins['recommended_action']}</div>
                        </div>
                        <div style="font-size:0.71rem;color:{TEXT3};">
                            Affects: {constructs_str}</div>
                        """,
                        unsafe_allow_html=True,
                    )

            if len(open_insights) > 7:
                st.caption(f"+ {len(open_insights) - 7} more open insights for selected constructs.")

            # Priority breakdown summary
            must = sum(1 for i in open_insights if i["priority"] == "Must address")
            should = sum(1 for i in open_insights if i["priority"] == "Should address")
            if must or should:
                st.markdown(
                    f"""
                    <div style="margin-top:0.5rem;font-size:0.75rem;color:{TEXT3};">
                        {must} must address · {should} should address · {len(open_insights)} total open
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

st.markdown("")
st.divider()

# ─────────────────────────────────────────────────────────────────
# SOURCE MATERIALS — bills, news, context for better questions
# ─────────────────────────────────────────────────────────────────

st.divider()
st.markdown("### Add Source Materials")
st.caption(
    "Drop in a bill, news article, or policy document. The AI will use these alongside polling data "
    "to suggest new survey questions or adapt existing ones for your specific context."
)

src_col1, src_col2 = st.columns(2)

with src_col1:
    st.markdown(f"""
    <div style="font-weight:600;color:{NAVY};margin-bottom:0.5rem;">📄 Bill Text or Policy Document</div>
    """, unsafe_allow_html=True)
    bill_input = st.text_area(
        "Paste bill text, executive summary, or key provisions",
        height=140,
        placeholder="e.g. SB 567 — Creates a judicial sentence review process for non-violent offenders who have served 15+ years...",
        key="sm_bill_input",
    )

    st.markdown(f"""
    <div style="font-weight:600;color:{NAVY};margin-bottom:0.5rem;margin-top:0.75rem;">🔗 News or Research Links</div>
    """, unsafe_allow_html=True)
    news_input = st.text_area(
        "Paste URLs to relevant articles or studies, one per line",
        height=100,
        placeholder="https://apnews.com/article/sentence-review-2026...\nhttps://vera.org/downloads/publications/...",
        key="sm_news_input",
    )

with src_col2:
    st.markdown(f"""
    <div style="font-weight:600;color:{NAVY};margin-bottom:0.5rem;">🎯 Survey Context</div>
    """, unsafe_allow_html=True)
    survey_context = st.text_area(
        "Describe what you're trying to learn or test with this survey",
        height=140,
        placeholder="e.g. We're fielding in Texas next month. Need to test whether bail reform language works with rural Republican voters...",
        key="sm_context",
    )

    st.markdown(f"""
    <div style="font-weight:600;color:{NAVY};margin-bottom:0.5rem;margin-top:0.75rem;">👥 Target State or Population</div>
    """, unsafe_allow_html=True)
    target_state = st.selectbox(
        "Target state (for MrP benchmarking)",
        ["Not specified", "Oklahoma", "Louisiana", "Virginia", "Massachusetts",
         "North Carolina", "New Jersey", "Texas", "Florida", "Georgia", "Ohio", "Other"],
        key="sm_target_state",
    )

has_source_inputs = bool(bill_input.strip() or news_input.strip() or survey_context.strip())

if has_source_inputs:
    gen_q_btn = st.button("✏️ Generate Question Suggestions", type="primary", key="sm_generate")

    if gen_q_btn:
        context_parts = []
        context_parts.append(f"EXISTING QUESTION BANK: {len(questions_df)} scored questions across {questions_df['topic_label'].nunique()} topics")
        if bill_input.strip():
            context_parts.append(f"BILL/POLICY TEXT: {bill_input.strip()[:2000]}")
        if news_input.strip():
            context_parts.append(f"NEWS/RESEARCH LINKS: {news_input.strip()[:500]}")
        if survey_context.strip():
            context_parts.append(f"SURVEY CONTEXT: {survey_context.strip()[:1000]}")
        if target_state != "Not specified":
            context_parts.append(f"TARGET STATE: {target_state}")

        st.info(
            "💡 **Tip**: Copy the brief below and take it to the **AI Analysis** page to generate questions. "
            "Copy the brief below and paste it into the chat — it has access to all scored questions and frameworks."
        )

        with st.expander("📋 Your question brief (copy to chat)", expanded=True):
            brief = "\n".join(context_parts)
            st.code(brief, language=None)
else:
    st.markdown(f"""
    <div style="background:rgba(184,135,10,0.08);border:1px dashed {GOLD_MID};border-radius:8px;
         padding:1rem 1.25rem;text-align:center;color:{TEXT2};">
        Add a bill, news article, or survey goal above to generate tailored question suggestions.
    </div>
    """, unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────
# SURVEY ASSEMBLY PANEL
# ─────────────────────────────────────────────────────────────────

st.divider()

st.markdown("### Survey Assembly")

n_strong = len(questions_df[questions_df['overall_support'] >= 75])
n_moderate = len(questions_df[(questions_df['overall_support'] >= 55) & (questions_df['overall_support'] < 75)])
n_contested = len(questions_df[questions_df['overall_support'] < 55])

st.markdown(f"""
Question bank includes **{len(questions_df)} scored questions** across **{questions_df['topic_label'].nunique()} topics**.
""")

asm_c1, asm_c2, asm_c3, asm_c4 = st.columns(4)
asm_c1.metric("Total Questions", len(questions_df))
asm_c2.metric("Strong Consensus (75%+)", n_strong)
asm_c3.metric("Moderate (55-74%)", n_moderate)
asm_c4.metric("Contested (<55%)", n_contested)

# ── MINIMUM-QUESTION THRESHOLD WARNING ──
st.markdown("")

# Constructs in current filtered selection — check per-construct Qs
if not filtered_df.empty:
    filtered_construct_counts = filtered_df.groupby('construct').size()
    thin_in_filter = filtered_construct_counts[filtered_construct_counts < 3]

    if not thin_in_filter.empty:
        thin_labels = [
            f"{CONSTRUCT_LABELS.get(c, c)} ({n} Q{'s' if n!=1 else ''})"
            for c, n in thin_in_filter.items()
        ]
        st.markdown(f"""
        <div style="background:rgba(139,26,26,0.07);border:1px solid rgba(139,26,26,0.3);
             border-radius:10px;padding:1rem 1.25rem;margin-bottom:0.75rem;">
            <div style="font-weight:700;color:#8B1A1A;margin-bottom:0.4rem;font-size:0.92rem;">
                ⚠️ Minimum-Question Threshold Warning
            </div>
            <div style="font-size:0.85rem;color:{TEXT2};line-height:1.5;">
                Your current filter includes constructs with fewer than 3 questions. MrP estimates
                for these constructs are unreliable — the LA-CJ-2025-002 diagnosis showed that r=0.12
                was not a bug but thin construct coverage in an omnibus survey.
            </div>
            <div style="margin-top:0.5rem;font-size:0.82rem;color:#8B1A1A;font-weight:600;">
                Thin constructs: {" · ".join(thin_labels)}
            </div>
            <div style="font-size:0.8rem;color:{TEXT3};margin-top:0.3rem;">
                Recommendation: add at least 3 questions per construct before fielding.
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.success(
            f"✅ All {filtered_construct_counts.shape[0]} constructs in your current selection "
            "have 3+ questions — above the minimum threshold for reliable MrP estimates.",
            icon=None,
        )

st.info("Full survey assembly tools (export, skip logic, randomization) coming in next update.")

# ─────────────────────────────────────────────────────────────────
# METHODOLOGY GUIDANCE
# ─────────────────────────────────────────────────────────────────

with st.expander("📐 How to write questions that actually measure what you think they measure", expanded=False):
    st.markdown(f"""
<div style="font-size:0.84rem;color:{TEXT2};line-height:1.7;">

<strong style="font-size:0.95rem;color:{NAVY};">The core problem: stated opinion ≠ what people will do.</strong><br>
Most survey questions measure where someone stands. That's useful — but it doesn't tell you how hard they'll fight,
who they'll tell, or whether they'll still agree after hearing the other side.
Behavioral questions close that gap. They reveal intensity, not just position.

<hr style="border:none;border-top:1px solid {BORDER2};margin:0.75rem 0;">

<strong>Rule 1 — Ask what people have done, not what they would do.</strong><br>
Past action is a fact. Future intent is a wish. "Would you contact an elected official?" gets you optimism.
"Have you contacted an elected official in the past year?" gets you activists.<br><br>
<em>✓ "In the past 12 months, have you discussed criminal justice with someone outside your household?"</em><br>
<em>✗ "How likely are you to discuss criminal justice with others?"</em>

<hr style="border:none;border-top:1px solid {BORDER2};margin:0.75rem 0;">

<strong>Rule 2 — Single idea per question. Double-barreled questions hide the answer.</strong><br>
"Do you support reforming sentencing and releasing nonviolent offenders?" — support for what?
Agreement on both parts? One part? Respondents average their answer and you learn nothing precise.<br><br>
<em>✓ Split it: (a) "Do you support reducing sentences for nonviolent offenses?" and separately
(b) "Do you support early release for people who complete rehabilitation programs?"</em>

<hr style="border:none;border-top:1px solid {BORDER2};margin:0.75rem 0;">

<strong>Rule 3 — Measure proximity, not just opinion.</strong><br>
"Do you support second-chance hiring?" gets you a position. "Do you personally know someone with a criminal record
who has had trouble finding work?" gets you salience and network reach. Someone who knows someone will talk.
Someone who only has an opinion may not. Both matter — they're measuring different things.

<hr style="border:none;border-top:1px solid {BORDER2};margin:0.75rem 0;">

<strong>Rule 4 — No knowledge tests. Ever.</strong><br>
Asking respondents to recall facts or demonstrate expertise measures education and media consumption — not support.
It introduces dropout (people who don't know disengage), contaminates your support scores, and tells you nothing
useful about persuasion. Replace knowledge questions with context statements: give them the fact, then ask how it
affects their view.

<hr style="border:none;border-top:1px solid {BORDER2};margin:0.75rem 0;">

<strong>Rule 5 — Test durability with inoculation.</strong><br>
Strong support that collapses under a single counterargument isn't actually strong. Before using a message in paid
media, field a durability test: ask baseline support, present the most credible opposing argument, re-ask.
The gap between pre and post is your exposure risk. If it moves more than 8 points, you need to inoculate first.

<hr style="border:none;border-top:1px solid {BORDER2};margin:0.75rem 0;">

<strong>Burden rule of thumb:</strong> Under 12 minutes. Max 15 substantive questions.
Each additional minute costs roughly 3% completion — quality degrades before abandonment does.

</div>
""", unsafe_allow_html=True)

portal_footer()
