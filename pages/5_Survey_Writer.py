"""
Survey Writer Page — AI-powered question writing and rewriting tool
"""

import streamlit as st
from pathlib import Path
import sys
import pandas as pd

# Auth gate
sys.path.insert(0, str(Path(__file__).parent.parent))
from auth import require_auth

st.set_page_config(
    page_title="Survey Writer — SLA Portal",
    page_icon="✏️",
    layout="wide",
)

# Dark theme
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&display=swap');
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500&display=swap');

    html, body, [data-testid="stAppViewContainer"] {
        background-color: #0f1117;
        color: #e8e8ed;
    }
    [data-testid="stSidebar"] {
        background-color: #0f1117;
        border-right: 1px solid #2a2d3a;
    }

    .best-practice {
        background: rgba(34, 197, 94, 0.1);
        border-left: 4px solid #22c55e;
        padding: 1rem;
        border-radius: 4px;
        margin: 0.5rem 0;
        font-size: 0.9rem;
    }

    .question-card {
        background: #1a1d29;
        border: 1px solid #2a2d3a;
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
    }

    .question-text {
        font-size: 1rem;
        font-weight: 500;
        color: #e8e8ed;
        margin-bottom: 1rem;
    }

    .question-meta {
        display: flex;
        gap: 1rem;
        flex-wrap: wrap;
        margin-top: 1rem;
        padding-top: 1rem;
        border-top: 1px solid #2a2d3a;
    }

    .meta-badge {
        background: #0f1117;
        padding: 0.5rem 0.75rem;
        border-radius: 6px;
        font-size: 0.8rem;
        color: #8b8fa3;
    }

    .suggestion-box {
        background: rgba(59, 130, 246, 0.1);
        border-left: 4px solid #3b82f6;
        padding: 1rem;
        border-radius: 4px;
        margin: 0.75rem 0;
    }
</style>
""", unsafe_allow_html=True)

username = require_auth("Second Look Alliance", accent_color="#22c55e")

st.title("✏️ Survey Writer")

st.markdown("""
AI-powered tool for writing and improving survey questions. Generate behavioral items,
reduce bias, improve clarity, and export question banks.

**Note:** This is a UI mockup with example outputs. Full AI backend integration coming in Phase 2.
""")

# Tabs
tab1, tab2, tab3, tab4 = st.tabs(["Write New Questions", "Rewrite Questions", "Question Bank", "Best Practices"])

# ─────────────────────────────────────────
# TAB 1: WRITE NEW QUESTIONS
# ─────────────────────────────────────────
with tab1:
    st.markdown("### Generate New Questions")

    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown("**What topic or construct?**")
        topic = st.text_input(
            "Topic/Construct",
            placeholder="e.g., 'rehabilitation of incarcerated people' or 'proportionality in sentencing'",
            label_visibility="collapsed",
        )

    with col2:
        st.markdown("**Question Type**")
        q_type = st.selectbox(
            "Type",
            ["Opinion/Support", "Likelihood", "Priority", "Behavioral (Past Action)"],
            label_visibility="collapsed",
        )

    col1, col2, col3 = st.columns([1, 1, 1])

    with col1:
        target_axis = st.multiselect(
            "Related Belief Axes",
            [
                "System Reliability",
                "Capacity for Change",
                "Change-Punishment Relationship",
            ],
            max_selections=2,
        )

    with col2:
        difficulty = st.select_slider(
            "Difficulty (Persuasion Potential)",
            options=["Easy", "Moderate", "Hard"],
            value="Moderate",
        )

    with col3:
        language_level = st.selectbox(
            "Language Level",
            ["Simple", "Standard", "Technical"],
        )

    col1, col2 = st.columns(2)

    with col1:
        num_options = st.number_input(
            "Number of Response Options (Likert Scale)",
            min_value=4,
            max_value=7,
            value=5,
            step=1,
        )

    with col2:
        population = st.multiselect(
            "Target Population",
            ["General public", "Reformed advocates", "System reformers", "General electorate"],
            default=["General public"],
        )

    generate_btn = st.button("Generate Questions", type="primary", use_container_width=True)

    if generate_btn and topic:
        st.success(f"Generating {q_type} questions for **{topic}**...")

        # Demo output
        demo_questions = [
            {
                "text": "To what extent do you believe that most people who have committed crimes can learn from their mistakes and become productive members of society?",
                "type": "Opinion",
                "scale": "Strongly Disagree – Disagree – Neutral – Agree – Strongly Agree",
                "construct": "Capacity for Change",
                "quality": "✓ Behavioral past-action focused, non-leading, appropriate difficulty"
            },
            {
                "text": "How likely would you be to support a sentencing reform that allows judges to consider rehabilitation potential in addition to the severity of the crime?",
                "type": "Likelihood",
                "scale": "Very Unlikely – Unlikely – Neutral – Likely – Very Likely",
                "construct": "Proportionality",
                "quality": "✓ Clear call-to-action, avoids jargon, balanced"
            },
            {
                "text": "Have you ever known someone personally who changed their behavior after receiving support or a second chance?",
                "type": "Behavioral (Past Action)",
                "scale": "Yes / No / Unsure",
                "construct": "Redemption Belief",
                "quality": "✓ Concrete, verifiable, non-judgmental"
            },
        ]

        for idx, q in enumerate(demo_questions, 1):
            st.markdown(f"""
            <div class="question-card">
                <div class="question-text"><strong>{idx}. {q['text']}</strong></div>
                <div class="question-meta">
                    <span class="meta-badge"><strong>Type:</strong> {q['type']}</span>
                    <span class="meta-badge"><strong>Construct:</strong> {q['construct']}</span>
                    <span class="meta-badge"><strong>Scale:</strong> {q['scale']}</span>
                </div>
                <div style="margin-top: 1rem; color: #22c55e; font-size: 0.9rem;">{q['quality']}</div>
            </div>
            """, unsafe_allow_html=True)

        st.divider()

        col1, col2 = st.columns(2)

        with col1:
            if st.button("Save These Questions", use_container_width=True):
                st.success("Questions saved to your question bank!")

        with col2:
            if st.button("Refine Further", use_container_width=True):
                st.info("This would let you adjust difficulty, adjust for different populations, etc.")

# ─────────────────────────────────────────
# TAB 2: REWRITE QUESTIONS
# ─────────────────────────────────────────
with tab2:
    st.markdown("### Improve Existing Questions")

    st.markdown("**Paste or type your survey question(s) below:**")

    question_input = st.text_area(
        "Question Text",
        placeholder="e.g., 'People who commit crimes don't deserve a second chance. Do you agree?'",
        height=100,
        label_visibility="collapsed",
    )

    col1, col2 = st.columns(2)

    with col1:
        issues = st.multiselect(
            "What would you like to improve?",
            [
                "Reduce bias/leading language",
                "Improve clarity",
                "Better Likert anchoring",
                "Remove jargon",
                "Make more behavioral (past-action)",
                "Reduce response burden",
                "Improve specificity",
            ],
            default=["Reduce bias/leading language", "Improve clarity"],
        )

    with col2:
        rewrite_style = st.selectbox(
            "Rewrite Style",
            ["Conservative (minimal changes)", "Moderate (balanced)", "Aggressive (optimize for MrP)"],
        )

    rewrite_btn = st.button("Analyze & Suggest Improvements", type="primary", use_container_width=True)

    if rewrite_btn and question_input:
        st.info("Analyzing question for bias, clarity, and measurement quality...")

        st.markdown("### Issues Found")

        issues_found = [
            {
                "issue": "Leading Language",
                "severity": "High",
                "desc": "The phrase 'don't deserve' is value-laden and could bias responses toward agreement.",
                "impact": "May overstate opposition to reform."
            },
            {
                "issue": "Limited Response Scale",
                "severity": "Medium",
                "desc": "Yes/No format loses important nuance between strong and mild agreement.",
                "impact": "Reduces measurement precision for MrP."
            },
            {
                "issue": "Abstract Concept",
                "severity": "Medium",
                "desc": "'deserve' is vague and interpreted differently across respondents.",
                "impact": "Introduces measurement error."
            },
        ]

        for issue in issues_found:
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"**{issue['issue']}** — {issue['desc']}")
                st.caption(f"*Impact:* {issue['impact']}")
            with col2:
                severity_color = {"High": "#ef4444", "Medium": "#f59e0b", "Low": "#22c55e"}
                st.markdown(f"""
                <div style="text-align: center; color: {severity_color.get(issue['severity'], '#8b8fa3')};">
                    <strong>{issue['severity']}</strong>
                </div>
                """, unsafe_allow_html=True)

        st.divider()

        st.markdown("### Suggested Rewrites")

        suggestions = [
            {
                "version": "v1: Neutral Phrasing",
                "text": "Some people believe that incarcerated individuals can rehabilitate and should be given opportunities to do so. How much do you agree with this view?",
                "improvements": [
                    "✓ Removed value-laden 'deserve' language",
                    "✓ Explicit statement of both positions",
                    "✓ Clearer 5-point Likert scale",
                ],
            },
            {
                "version": "v2: Behavioral Anchor",
                "text": "Have you personally known or heard of someone who was incarcerated and later made positive changes in their life?",
                "improvements": [
                    "✓ Behavioral past-action format",
                    "✓ Concrete, verifiable experience",
                    "✓ Removes abstract judgment",
                    "✓ Lower response burden",
                ],
            },
            {
                "version": "v3: Capacity-Focused (Axes Aligned)",
                "text": "To what extent do you believe that people can meaningfully change their behavior if given appropriate support and opportunity?",
                "improvements": [
                    "✓ Aligns to 'Capacity for Change' axis",
                    "✓ General enough for diverse populations",
                    "✓ Specific conditions ('support + opportunity')",
                    "✓ Standard 5-point Likert recommended",
                ],
            },
        ]

        for suggestion in suggestions:
            st.markdown(f"""
            <div class="suggestion-box">
                <div style="font-weight: 600; color: #3b82f6; margin-bottom: 0.75rem;">{suggestion['version']}</div>
                <div style="color: #e8e8ed; margin-bottom: 0.75rem;"><strong>"{suggestion['text']}"</strong></div>
                <div style="font-size: 0.9rem;">
                    {''.join([f'<div style="color: #22c55e; margin: 0.25rem 0;">{imp}</div>' for imp in suggestion['improvements']])}
                </div>
            </div>
            """, unsafe_allow_html=True)

        st.divider()

        col1, col2 = st.columns(2)

        with col1:
            if st.button("Use v1", use_container_width=True):
                st.success("Version 1 selected!")

        with col2:
            if st.button("Use v2", use_container_width=True):
                st.success("Version 2 selected! (behavioral format)")

# ─────────────────────────────────────────
# TAB 3: QUESTION BANK
# ─────────────────────────────────────────
with tab3:
    st.markdown("### Question Bank Browser")

    col1, col2, col3 = st.columns([1, 1, 1])

    with col1:
        bank_construct = st.selectbox(
            "Filter by Construct",
            [
                "All Constructs",
                "Procedural Fairness",
                "Proportionality",
                "Constitutional Rights",
                "Juvenile Compassion",
                "Rehabilitation",
                "Dangerousness Distinction",
                "Fiscal Efficiency",
                "Fines & Fees",
                "Compassion",
                "Police Discretion",
                "Promise of Redemption",
            ],
        )

    with col2:
        bank_axis = st.selectbox(
            "Filter by Axis",
            [
                "All Axes",
                "System Reliability",
                "Capacity for Change",
                "Change-Punishment Relationship",
            ],
        )

    with col3:
        bank_type = st.selectbox(
            "Question Type",
            ["All Types", "Opinion", "Likelihood", "Behavioral", "Priority"],
        )

    st.divider()

    # Demo question bank
    demo_bank = [
        {
            "text": "Do you believe the criminal justice system generally treats people fairly?",
            "construct": "Procedural Fairness",
            "axis": "System Reliability",
            "type": "Opinion",
            "scale": "5-point Likert",
        },
        {
            "text": "To what extent should punishment be proportional to the seriousness of the crime?",
            "construct": "Proportionality",
            "axis": "Change-Punishment Relationship",
            "type": "Opinion",
            "scale": "5-point Likert",
        },
        {
            "text": "Have you known someone who received a second chance and improved their life?",
            "construct": "Promise of Redemption",
            "axis": "Capacity for Change",
            "type": "Behavioral",
            "scale": "Yes/No/Unsure",
        },
        {
            "text": "How likely would you support rehabilitation programs in your state's prisons?",
            "construct": "Rehabilitation",
            "axis": "Capacity for Change",
            "type": "Likelihood",
            "scale": "5-point Likert",
        },
        {
            "text": "Should young people who commit crimes be treated differently than adults?",
            "construct": "Juvenile Compassion",
            "axis": "System Reliability",
            "type": "Opinion",
            "scale": "5-point Likert",
        },
    ]

    # Filter bank
    filtered_bank = demo_bank
    if bank_construct != "All Constructs":
        filtered_bank = [q for q in filtered_bank if q["construct"] == bank_construct]
    if bank_axis != "All Axes":
        filtered_bank = [q for q in filtered_bank if q["axis"] == bank_axis]
    if bank_type != "All Types":
        filtered_bank = [q for q in filtered_bank if q["type"] == bank_type]

    st.markdown(f"**{len(filtered_bank)} questions found**")

    for q in filtered_bank:
        st.markdown(f"""
        <div class="question-card">
            <div class="question-text">"{q['text']}"</div>
            <div class="question-meta">
                <span class="meta-badge"><strong>Construct:</strong> {q['construct']}</span>
                <span class="meta-badge"><strong>Axis:</strong> {q['axis']}</span>
                <span class="meta-badge"><strong>Type:</strong> {q['type']}</span>
                <span class="meta-badge"><strong>Scale:</strong> {q['scale']}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.divider()

    col1, col2 = st.columns(2)

    with col1:
        if st.button("Export as CSV", use_container_width=True):
            df_export = pd.DataFrame(filtered_bank)
            csv = df_export.to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name="survey_questions.csv",
                mime="text/csv",
            )

    with col2:
        if st.button("Export as JSON", use_container_width=True):
            import json
            json_data = json.dumps(filtered_bank, indent=2)
            st.download_button(
                label="Download JSON",
                data=json_data,
                file_name="survey_questions.json",
                mime="application/json",
            )

# ─────────────────────────────────────────
# TAB 4: BEST PRACTICES
# ─────────────────────────────────────────
with tab4:
    st.markdown("### Survey Design Best Practices")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Question Writing")

        st.markdown('<div class="best-practice"><strong>✓ Behavioral, Past-Action Items</strong><br>Ask about behavior respondents have experienced, not future intent or knowledge tests. Reduces aspirational bias and response burden.</div>', unsafe_allow_html=True)

        st.markdown('<div class="best-practice"><strong>✓ No Knowledge Tests</strong><br>Avoid "Did you know..." items. Respondents who don\'t know drop off; contamination from guessing exceeds filtering value. Measure attitudes, not knowledge.</div>', unsafe_allow_html=True)

        st.markdown('<div class="best-practice"><strong>✓ Likert Scales (Odd, 5-7 pt)</strong><br>Use 5-point or 7-point Likert with balanced anchors. Odd-numbered scales allow neutral responses.</div>', unsafe_allow_html=True)

        st.markdown('<div class="best-practice"><strong>✓ Avoid Jargon</strong><br>Use plain language. Define legal/technical terms. Ensure questions are understandable to your target population.</div>', unsafe_allow_html=True)

    with col2:
        st.markdown("### Bias & Clarity")

        st.markdown('<div class="best-practice"><strong>✓ Remove Leading Language</strong><br>Avoid "surely," "obviously," "don\'t you think." Neutral phrasing increases validity.</div>', unsafe_allow_html=True)

        st.markdown('<div class="best-practice"><strong>✓ Double-Barrel Questions</strong><br>One concept per question. Split "X and Y" into two questions.</div>', unsafe_allow_html=True)

        st.markdown('<div class="best-practice"><strong>✓ Balance Positive & Negative Framing</strong><br>Mix agreement and disagreement directions to avoid acquiescence bias.</div>', unsafe_allow_html=True)

        st.markdown('<div class="best-practice"><strong>✓ Test with Target Population</strong><br>Cognitive interviews identify confusing phrasing before fielding.</div>', unsafe_allow_html=True)

    st.divider()

    st.markdown("### MrP Measurement Principles")

    st.markdown("""
    1. **Low Respondent Burden**: Fewer, shorter questions increase completion and reduce missing data.
    2. **High Validity**: Behavioral anchors and clear constructs improve measurement precision.
    3. **Construct Alignment**: Questions must clearly map to the 3 Belief Axes and 11 constructs.
    4. **Demographic Coverage**: Ensure sufficient variation across party, ideology, age, education to estimate subgroup effects.
    5. **Test-Retest Reliability**: Similar questions across waves help track temporal stability.
    """)

    st.divider()

    st.markdown("### CJ Reform Survey Design Checklist")

    checklist = [
        ("Questions are behavioral (past-action) not aspirational", False),
        ("No knowledge tests or factual questions", False),
        ("Likert scale balanced with odd number of options", False),
        ("No double-barrel questions", False),
        ("Neutral, unbiased language throughout", False),
        ("Clear mapping to constructs/axes", False),
        ("Appropriate for target demographic", False),
        ("Estimated completion time: 8-12 minutes", False),
    ]

    for item, checked in checklist:
        st.checkbox(item, value=checked)
