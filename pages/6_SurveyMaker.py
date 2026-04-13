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
    "Browse scored questions from the question bank · filter by topic and persuasion tier · assemble surveys"
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
# PERSUASION PATHWAY SEQUENCING
# ─────────────────────────────────────────────────────────────────

st.markdown("### Persuasion Pathway Sequencing")
st.markdown(
    "The pathway matters. Entry topics build common ground, Bridge topics open skeptics, "
    "Downstream topics close on specific policy positions. Survey questions should flow in this order.",
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
