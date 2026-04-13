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
    apply_theme, portal_footer, get_supabase_config, get_supabase_headers,
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
    "CAND": "Candidate Favorability",
    "PARTY": "Party Affiliation",
    "TOUGHCRIME": "Tough on Crime",
    "SENTENCING": "Sentencing & Incarceration",
    "REDEMPTION": "Redemption & Second Chances",
    "EXPUNGE": "Expungement & Record Clearing",
    "SENTREVIEW": "Sentence Review & Commutation",
    "POLICE": "Police Accountability",
    "BAIL": "Bail & Pretrial Release",
    "PAROLE": "Parole & Reentry",
    "PROP": "Proposition/Vote Support",
    "INVEST": "Investment in Services",
    "LIT": "Litigation & Legal Framework",
    "DV": "Domestic Violence Context",
    "CAND_OTHER": "Other Candidate Items",
    "COMPASS": "Compassion & Empathy",
    "PUNITIVE": "Punitive Attitudes",
    "PROBLEM_SOLVING": "Problem-Solving Approach",
    "ISSUE_SALIENCE": "Issue Importance",
    "IMPACT": "Personal Impact/Salience",
    "COUNSEL_ACCESS": "Legal Counsel Access",
    "JUDICIAL": "Judicial Discretion",
    "COUNSEL_QUALITY": "Counsel Quality",
    "PLEA": "Plea Bargaining",
    "VICTIM": "Victim Support",
    "RACE": "Race & Inequality",
    "WEALTH": "Wealth Inequality",
    "FINES": "Fines & Fees",
    "TRUST": "Trust in System",
    "FISCAL": "Fiscal Impact",
    "DETERRENCE": "Deterrence Belief",
    "REOFFEND": "Reoffending Risk",
    "INCAP": "Incapacitation Benefit",
    "CUSTOM": "Custom Question",
}

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
def load_and_score_questions():
    """Load all scored questions from Supabase and compute support metrics."""
    try:
        supabase_url, supabase_key = get_supabase_config()
        headers = get_supabase_headers()

        # Build filter for CJ surveys
        survey_ids = [s["id"] for s in CJ_SURVEYS]
        survey_filter = ",".join([f'"{sid}"' for sid in survey_ids])

        # Fetch L2 responses
        url = f"{supabase_url}/rest/v1/l2_responses?survey_id=in.({survey_filter})"
        rows = _paginate(url, headers)

        if not rows:
            return pd.DataFrame()

        df = pd.DataFrame(rows)

        # Score responses
        if SCORING_AVAILABLE:
            df['scored_response'] = df['response'].apply(score_content)
        else:
            # Fallback: binary scoring
            df['scored_response'] = df['response'].apply(
                lambda x: 1 if x in ['Strongly Support', 'Support', 'Agree', 'Yes', 'Favorable'] else (
                    0 if x in ['Strongly Oppose', 'Oppose', 'Disagree', 'No', 'Unfavorable'] else 0.5
                )
            )

        # Compute aggregates by question
        results = []
        grouped = df.groupby('question_id').agg({
            'scored_response': ['mean', 'count'],
            'survey_id': 'first'
        }).reset_index()

        for _, row in grouped.iterrows():
            qid = row['question_id']
            overall_support = row['scored_response']['mean']
            n_respondents = int(row['scored_response']['count'])

            # Get construct and tier
            construct = get_construct(qid) if SCORING_AVAILABLE else "CUSTOM"
            tier = TIER_MAP.get(construct, "Unclassified")
            topic_label = CONSTRUCT_LABELS.get(construct, construct)

            # Get question text from original data
            question_row = df[df['question_id'] == qid].iloc[0]
            question_text = question_row.get('question_text', qid)

            results.append({
                'qid': qid,
                'text': question_text,
                'construct': construct,
                'topic_label': topic_label,
                'tier': tier,
                'overall_support': overall_support,
                'n_respondents': n_respondents,
            })

        result_df = pd.DataFrame(results)
        return result_df.sort_values('overall_support', ascending=False)

    except Exception as e:
        st.error(f"Error loading questions: {str(e)}")
        return pd.DataFrame()

# ─────────────────────────────────────────────────────────────────
# PAGE HEADER
# ─────────────────────────────────────────────────────────────────

st.title("SurveyMaker")
st.markdown(
    "Browse scored questions from the question bank · filter by topic and persuasion tier · assemble surveys"
)

st.divider()

# ─────────────────────────────────────────────────────────────────
# LOAD DATA
# ─────────────────────────────────────────────────────────────────

with st.spinner("Loading question bank..."):
    questions_df = load_and_score_questions()

if questions_df.empty:
    st.warning("No scored questions found. Please check your Supabase connection.")
    portal_footer()
    st.stop()

# ─────────────────────────────────────────────────────────────────
# SIDEBAR FILTERS
# ─────────────────────────────────────────────────────────────────

st.sidebar.markdown("### Question Bank Filters")

# Topic filter
available_topics = sorted(questions_df['topic_label'].unique())
selected_topics = st.sidebar.multiselect(
    "Topic",
    available_topics,
    default=available_topics[:5] if len(available_topics) > 5 else available_topics
)

# Tier filter
tier_options = ["All", "Entry", "Bridge", "Downstream", "Destination"]
selected_tier = st.sidebar.selectbox("Persuasion Tier", tier_options, index=0)

# Support level filter
support_options = [
    "All",
    "Strong Consensus (75%+)",
    "Moderate (55-74%)",
    "Contested (<55%)"
]
selected_support = st.sidebar.selectbox("Support Level", support_options, index=0)

# Sort options
sort_options = [
    "Support % (descending)",
    "Support % (ascending)",
    "Topic (A-Z)",
    "Tier (Entry → Destination)"
]
selected_sort = st.sidebar.selectbox("Sort By", sort_options, index=0)

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
    filtered_df = filtered_df[filtered_df['overall_support'] >= 0.75]
elif selected_support == "Moderate (55-74%)":
    filtered_df = filtered_df[(filtered_df['overall_support'] >= 0.55) & (filtered_df['overall_support'] < 0.75)]
elif selected_support == "Contested (<55%)":
    filtered_df = filtered_df[filtered_df['overall_support'] < 0.55]

# Sort
if selected_sort == "Support % (descending)":
    filtered_df = filtered_df.sort_values('overall_support', ascending=False)
elif selected_sort == "Support % (ascending)":
    filtered_df = filtered_df.sort_values('overall_support', ascending=True)
elif selected_sort == "Topic (A-Z)":
    filtered_df = filtered_df.sort_values('topic_label')
elif selected_sort == "Tier (Entry → Destination)":
    tier_order = {"Entry": 1, "Bridge": 2, "Downstream": 3, "Destination": 4, "Unclassified": 5}
    filtered_df['tier_order'] = filtered_df['tier'].map(tier_order)
    filtered_df = filtered_df.sort_values('tier_order').drop('tier_order', axis=1)

# ─────────────────────────────────────────────────────────────────
# QUESTION BROWSER
# ─────────────────────────────────────────────────────────────────

col_left, col_right = st.columns([2, 1])

with col_left:
    st.markdown("### Question Bank Browser")
    st.markdown(f"**{len(filtered_df)} questions** matching filters")

    if filtered_df.empty:
        st.info("No questions match your filter criteria. Try adjusting the filters.")
    else:
        # Create display table
        display_df = filtered_df[[
            'text', 'topic_label', 'tier', 'overall_support', 'n_respondents'
        ]].copy()
        display_df.columns = ['Question', 'Topic', 'Tier', 'Support %', 'N']
        display_df['Support %'] = (display_df['Support %'] * 100).round(1).astype(str) + "%"

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
    st.metric("Avg Support", f"{avg_support*100:.1f}%")

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
    support_pct = selected_question['overall_support'] * 100
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

n_strong = len(questions_df[questions_df['overall_support'] >= 0.75])
n_moderate = len(questions_df[(questions_df['overall_support'] >= 0.55) & (questions_df['overall_support'] < 0.75)])
n_contested = len(questions_df[questions_df['overall_support'] < 0.55])

st.markdown(f"""
Question bank includes **{len(questions_df)} scored questions** across **{questions_df['topic_label'].nunique()} topics**.
""")

asm_c1, asm_c2, asm_c3, asm_c4 = st.columns(4)
asm_c1.metric("Total Questions", len(questions_df))
asm_c2.metric("Strong Consensus", n_strong)
asm_c3.metric("Moderate Support", n_moderate)
asm_c4.metric("Contested", n_contested)

st.info("Full survey assembly tools (export, skip logic, randomization) coming in next update.")

# ─────────────────────────────────────────────────────────────────
# METHODOLOGY GUIDANCE
# ─────────────────────────────────────────────────────────────────

with st.expander("Question Design Methodology", expanded=False):
    st.markdown(f"""
    #### Behavioral Past-Action
    Questions should ask what people **have done**, not what they would do. Behavioral items measure real participation patterns.

    **Good:** "In the past year, have you contacted an elected official?"
    **Bad:** "Would you contact an elected official if you were concerned about a policy?"

    #### Avoid Knowledge Tests
    Don't ask respondents to recall facts or demonstrate expertise. Knowledge tests increase drop-off and contaminate support measurements. Respondents disengage or guess.

    #### Minimize Burden
    Keep surveys under 12 minutes. Each additional minute costs ~3% completion rate. Shorter surveys yield higher quality responses.

    **Burden checklist:**
    - Max 15 core substantive questions
    - Use matrix questions efficiently
    - Skip open-ended text (high abandonment)
    - Test in pilot (aim for <90 sec per question)

    #### Test for Durability
    Include counter-arguments to see if support holds under attack. Questions with weak persuasion margins collapse under messaging pressure.

    **Example durability test:** Ask original support, then present strongest opposing argument, then re-ask.
    """)

portal_footer()
