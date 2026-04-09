"""
AI Search Page — Chat-style query interface for survey data
"""

import streamlit as st
from pathlib import Path
import sys
from datetime import datetime

# Auth gate
sys.path.insert(0, str(Path(__file__).parent.parent))
from auth import require_auth

st.set_page_config(
    page_title="AI Search — SLA Portal",
    page_icon="🔍",
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

    .message-user {
        background: #1a1d29;
        border-left: 4px solid #22c55e;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.95rem;
    }

    .message-bot {
        background: #1a1d29;
        border-left: 4px solid #3b82f6;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
    }

    .result-card {
        background: linear-gradient(135deg, #1a1d29 0%, #232738 100%);
        border: 1px solid #2a2d3a;
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
    }

    .stat-highlight {
        background: rgba(34, 197, 94, 0.1);
        border-left: 4px solid #22c55e;
        padding: 0.75rem;
        margin: 0.5rem 0;
        border-radius: 4px;
        font-weight: 600;
        color: #22c55e;
    }

    .query-chip {
        display: inline-block;
        background: #1a1d29;
        border: 1px solid #2a2d3a;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        margin: 0.25rem;
        cursor: pointer;
        transition: all 0.2s ease;
        font-size: 0.9rem;
    }

    .query-chip:hover {
        border-color: #22c55e;
        background: rgba(34, 197, 94, 0.05);
    }
</style>
""", unsafe_allow_html=True)

username = require_auth("Second Look Alliance", accent_color="#22c55e")

st.title("🔍 AI Search")

st.markdown("""
Chat with our AI data assistant to query survey data, compare states, discover insights, and get answers
about voter support, archetype distributions, and reform messaging effectiveness.

**Note:** This is a UI mockup with demo responses. Full AI backend with live database queries coming in Phase 2.
""")

# Initialize chat history if not exists
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display message history
for message in st.session_state.messages:
    if message["role"] == "user":
        st.markdown(f'<div class="message-user">👤 {message["content"]}</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="message-bot">🤖 {message["content"]}</div>', unsafe_allow_html=True)

st.divider()

# Quick query suggestions
st.markdown("### Suggested Queries")

suggested_queries = [
    "What % of NC Republicans support sentencing reform?",
    "Compare rehabilitation support across states",
    "Which constructs have the highest durability in OK?",
    "What messaging moves Cautious Reformers in LA?",
    "Show me Golden Zone constructs in each state",
    "How has reform temperature changed since January?",
    "Which archetypes are underrepresented in VA?",
    "What demographic groups support Proportionality most?",
]

cols = st.columns(2)
for idx, query in enumerate(suggested_queries):
    with cols[idx % 2]:
        if st.button(f"💡 {query}", use_container_width=True, key=f"query_{idx}"):
            # Add to message history
            st.session_state.messages.append({"role": "user", "content": query})

st.divider()

# User input
col1, col2 = st.columns([6, 1])

with col1:
    user_input = st.text_input(
        "Ask a question about the data:",
        placeholder="e.g., 'What % of Louisiana voters support rehabilitation funding?'",
        label_visibility="collapsed",
    )

with col2:
    submit_button = st.button("Send", use_container_width=True, type="primary")

if submit_button and user_input:
    # Add user message
    st.session_state.messages.append({"role": "user", "content": user_input})

    # Generate demo response based on query
    response = ""

    if "carolina" in user_input.lower() and "republican" in user_input.lower():
        response = """
        Based on the NC-CJ surveys, approximately **58% of North Carolina Republicans support sentencing reform**,
        with a 95% confidence interval of 52-64%.

        This archetype breakdown shows:
        - **Cautious Reformers** (18% of NC Republicans): 72% support
        - **Compassionate Pragmatists** (12%): 81% support
        - **System Defenders** (25%): 38% support
        - **Justice Skeptics** (8%): 89% support

        **Effective messaging**: Focus on fiscal efficiency and public safety outcomes rather than
        rehabilitation narratives (which resonate better with younger voters and Democrats).
        """

    elif "compare" in user_input.lower() and "rehabilitation" in user_input.lower():
        response = """
        Rehabilitation support comparison across states:

        **State Rankings (% Support):**
        1. Massachusetts: 71% (68-74% CI)
        2. New Jersey: 68% (64-72% CI)
        3. Virginia: 64% (59-69% CI)
        4. North Carolina: 62% (57-67% CI)
        5. Louisiana: 59% (54-64% CI)
        6. Oklahoma: 56% (51-61% CI)

        **Analysis:**
        Northeastern states show higher baseline support. In Southern states, support increases
        significantly with education level (College+: 73% vs. HS or Less: 48%).

        **MrP Insight:** The 15pp spread between MA and OK is largely explained by
        demographic composition (education, age) and archetype distribution (more Compassionate Pragmatists in MA).
        """

    elif "durability" in user_input.lower() and "ok" in user_input.lower():
        response = """
        Top durable constructs in Oklahoma (sorted by durability score):

        **Golden Zone (High Support + High Durability):**
        - Constitutional Rights: 68% support, 81/100 durability
        - Fiscal Efficiency: 64% support, 77/100 durability

        **Primary Fuel (High Support + Low Durability):**
        - Proportionality: 71% support, 54/100 durability
        - Promise of Redemption: 59% support, 48/100 durability

        **Key Insight:** Constitutional Rights messaging has strong staying power in OK,
        likely because it appeals across ideological lines. In contrast, abstract
        redemption framing is vulnerable to counter-messaging.

        **Recommendation:** Lead with Constitutional Rights + Fiscal Efficiency.
        Use durability-building strategies (testimonials, local examples) to reinforce Proportionality.
        """

    elif "move" in user_input.lower() or "messaging" in user_input.lower():
        response = """
        **What moves Cautious Reformers in Louisiana:**

        **Most Effective Messages:**
        1. Evidence-based outcomes (68% persuasion impact)
        2. Fiscal responsibility / Cost savings (64% persuasion impact)
        3. Pilot programs and testing (61% persuasion impact)
        4. Public safety improvements (58% persuasion impact)

        **Avoid These Approaches:**
        - Anti-police rhetoric (drives skepticism)
        - Radical system overhaul language (triggers risk aversion)
        - Abstract moral arguments (prefer concrete data)
        - Timeframe pressure (undermines deliberation)

        **Best Constructs to Activate:**
        1. Fiscal Efficiency (highest persuasion potential, 73%)
        2. Dangerousness Distinction (66%)
        3. Constitutional Rights (58%)

        **Media Channels:** This archetype responds best to data-driven content
        (reports, case studies, infographics) on Facebook and LinkedIn.
        """

    elif "golden zone" in user_input.lower() or "quadrant" in user_input.lower():
        response = """
        **Golden Zone Constructs by State** (high support + high durability):

        - **Oklahoma**: Constitutional Rights, Fiscal Efficiency
        - **Louisiana**: Promise of Redemption, Proportionality
        - **North Carolina**: Constitutional Rights, Fiscal Efficiency
        - **Virginia**: Proportionality, Juvenile Compassion
        - **Massachusetts**: Rehabilitation, Compassion
        - **New Jersey**: Constitutional Rights, Rehabilitation

        **Pattern:** Constitutional Rights consistently strong across all states.
        Regional variation in Rehabilitation/Compassion (stronger NE) vs. Proportionality (stronger South).

        **Strategic Implication:** Universal messaging around Constitutional Rights reaches
        everyone. Customize state/region messaging based on Golden Zone variations.
        """

    elif "archetype" in user_input.lower() or "underrepresented" in user_input.lower():
        response = """
        **Virginia Archetype Distribution:**

        - Cautious Reformers: 26% (baseline 26%) — proportional ✓
        - Compassionate Pragmatists: 22% (baseline 24%) — slightly underrepresented
        - System Defenders: 24% (baseline 22%) — slightly overrepresented
        - Justice Skeptics: 15% (baseline 16%) — proportional ✓
        - Rehabilitation Champions: 7% (baseline 7%) — proportional ✓
        - Abolition-Leaning: 6% (baseline 5%) — slightly overrepresented

        **Key Insight:** VA has a slight tilt toward System Defenders and away from
        Compassionate Pragmatists compared to the national average. This suggests:

        1. Institutional trust is stronger in VA (favorable for incremental reform messaging)
        2. Compassion-based appeals may need additional resonance-building
        3. Focus on shared-value messaging (safety, fiscal responsibility) in VA
        """

    else:
        response = """
        I can help you query the SLA database! Try asking about:

        - **State-specific support**: "What % of [State] voters support [Construct]?"
        - **Archetype messaging**: "What moves [Archetype] voters in [State]?"
        - **Cross-state comparison**: "Compare [Construct] support across states"
        - **Durability insights**: "Which constructs are most durable in [State]?"
        - **Demographic breakdowns**: "How does [Construct] vary by [Demographics]?"
        - **Trend analysis**: "How has [Construct] support changed over time?"

        Example questions are shown above. Click any to search!
        """

    # Add bot response
    st.session_state.messages.append({"role": "assistant", "content": response})

    # Rerun to display new message
    st.rerun()
