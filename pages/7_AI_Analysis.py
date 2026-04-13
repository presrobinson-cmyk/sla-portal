"""
AI Analysis — PLACEHOLDER
Plain-language interpretation of CJ reform polling data powered by Claude.
"""

import streamlit as st
from pathlib import Path
import sys

# Auth gate
sys.path.insert(0, str(Path(__file__).parent.parent))
from theme import apply_theme, portal_footer, NAVY, GOLD, CARD_BG, BORDER2, TEXT3
from auth import require_auth
from chat_widget import render_chat

st.set_page_config(
    page_title="AI Analysis — SLA Portal",
    page_icon="🤖",
    layout="wide",
)

apply_theme()
username = require_auth("Second Look Alliance", accent_color=GOLD)

st.title("AI Analysis")
st.markdown(
    "Plain-language interpretation of CJ reform polling data · Powered by Claude",
    unsafe_allow_html=True
)

st.divider()

# ─────────────────────────────────────────────────────────────────
# COMING SOON NOTICE
# ─────────────────────────────────────────────────────────────────

st.markdown(f"""
<div style="background:{CARD_BG};border:1px solid {BORDER2};border-radius:10px;padding:2rem;text-align:center;box-shadow:0 1px 3px rgba(0,0,0,0.04);">
    <div style="font-size:3rem;margin-bottom:1rem;">💬</div>
    <div style="font-size:1.4rem;font-weight:700;color:{NAVY};margin-bottom:0.5rem;">Coming Soon</div>
    <div style="font-size:0.95rem;color:{TEXT3};line-height:1.6;max-width:600px;margin:0 auto;">
        AI Analysis is currently in development. We're preparing an intelligent query interface to help you understand your data in plain language.
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown("")

# ─────────────────────────────────────────────────────────────────
# FEATURES DESCRIPTION
# ─────────────────────────────────────────────────────────────────

st.subheader("How It Will Work")

col1, col2 = st.columns(2)

with col1:
    st.markdown(f"""
    <div style="background:{CARD_BG};border:1px solid {BORDER2};border-radius:10px;padding:1.5rem;box-shadow:0 1px 3px rgba(0,0,0,0.04);">
        <div style="font-size:1.8rem;margin-bottom:0.5rem;">🎯</div>
        <div style="font-weight:700;color:{NAVY};margin-bottom:0.75rem;">Ask Any Question</div>
        <div style="font-size:0.9rem;color:{TEXT3};line-height:1.6;">
            Type natural-language queries about your data: "Which messages are safe everywhere?" "Why is durability so low on this issue?" "Explain the crossover patterns."
        </div>
    </div>

    <div style="background:{CARD_BG};border:1px solid {BORDER2};border-radius:10px;padding:1.5rem;margin-top:1rem;box-shadow:0 1px 3px rgba(0,0,0,0.04);">
        <div style="font-size:1.8rem;margin-bottom:0.5rem;">📊</div>
        <div style="font-weight:700;color:{NAVY};margin-bottom:0.75rem;">Smart Data Context</div>
        <div style="font-size:0.9rem;color:{TEXT3};line-height:1.6;">
            AI Analysis automatically knows the survey universe, archetype breakdown, state differences, and persuasion tiers. No manual data preparation.
        </div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div style="background:{CARD_BG};border:1px solid {BORDER2};border-radius:10px;padding:1.5rem;box-shadow:0 1px 3px rgba(0,0,0,0.04);">
        <div style="font-size:1.8rem;margin-bottom:0.5rem;">✍️</div>
        <div style="font-weight:700;color:{NAVY};margin-bottom:0.75rem;">Claude-Powered Synthesis</div>
        <div style="font-size:0.9rem;color:{TEXT3};line-height:1.6;">
            Get clear, actionable interpretations: "The following voter segments are most persuadable: ... Here's why ... Recommended next steps."
        </div>
    </div>

    <div style="background:{CARD_BG};border:1px solid {BORDER2};border-radius:10px;padding:1.5rem;margin-top:1rem;box-shadow:0 1px 3px rgba(0,0,0,0.04);">
        <div style="font-size:1.8rem;margin-bottom:0.5rem;">📁</div>
        <div style="font-weight:700;color:{NAVY};margin-bottom:0.75rem;">Export Insights</div>
        <div style="font-size:0.9rem;color:{TEXT3};line-height:1.6;">
            Download analyses as .docx briefs ready for board presentations, donor updates, and strategic planning.
        </div>
    </div>
    """, unsafe_allow_html=True)

st.divider()

st.subheader("Example Queries")

st.markdown("Try asking about topics like these (once AI Analysis goes live):")

query_chips = [
    "Which messages are safe everywhere?",
    "Louisiana vs Oklahoma differences",
    "Headline for Arnold Ventures",
    "Which issues are most fragile?",
    "Explain Durability Matrix findings",
    "How to use framing lenses",
]

# Display as styled chip-like elements
cols = st.columns(3)
for i, query in enumerate(query_chips):
    col = cols[i % 3]
    with col:
        st.markdown(f"""
        <div style="background:rgba(184,135,10,0.08);border:1px solid rgba(184,135,10,0.2);border-radius:20px;padding:0.75rem 1rem;text-align:center;color:{NAVY};font-size:0.85rem;margin-bottom:0.5rem;cursor:not-allowed;opacity:0.6;">
            {query}
        </div>
        """, unsafe_allow_html=True)

st.divider()

st.info(
    "🔌 **Status:** AI Analysis requires API key configuration with Claude and will be available in the next portal update.",
    icon="ℹ️"
)

render_chat("ai_analysis")

portal_footer()
