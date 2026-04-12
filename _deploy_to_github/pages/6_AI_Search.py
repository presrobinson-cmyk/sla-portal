"""
SurveyMaker — PLACEHOLDER
AI-powered question banking and survey assembly tool.
"""

import streamlit as st
from pathlib import Path
import sys

# Auth gate
sys.path.insert(0, str(Path(__file__).parent.parent))
from theme import apply_theme, portal_footer, NAVY, GOLD, CARD_BG, BORDER2, TEXT3
from auth import require_auth

st.set_page_config(
    page_title="SurveyMaker — SLA Portal",
    page_icon="✏️",
    layout="wide",
)

apply_theme()
username = require_auth("Second Look Alliance", accent_color=GOLD)

st.title("SurveyMaker")
st.markdown(
    "Pick from the question bank · rewrite any question using Actionable Intel methodology · assemble and export",
    unsafe_allow_html=True
)

st.divider()

# ─────────────────────────────────────────────────────────────────
# COMING SOON NOTICE
# ─────────────────────────────────────────────────────────────────

st.markdown(f"""
<div style="background:{CARD_BG};border:1px solid {BORDER2};border-radius:10px;padding:2rem;text-align:center;box-shadow:0 1px 3px rgba(0,0,0,0.04);">
    <div style="font-size:3rem;margin-bottom:1rem;">🔧</div>
    <div style="font-size:1.4rem;font-weight:700;color:{NAVY};margin-bottom:0.5rem;">Coming Soon</div>
    <div style="font-size:0.95rem;color:{TEXT3};line-height:1.6;max-width:600px;margin:0 auto;">
        SurveyMaker is currently in development. We're building a question bank and assembly tool to help you design surveys using proven Actionable Intel methodology.
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown("")

# ─────────────────────────────────────────────────────────────────
# FEATURES DESCRIPTION
# ─────────────────────────────────────────────────────────────────

st.subheader("What SurveyMaker Will Do")

col1, col2 = st.columns(2)

with col1:
    st.markdown(f"""
    <div style="background:{CARD_BG};border:1px solid {BORDER2};border-radius:10px;padding:1.5rem;box-shadow:0 1px 3px rgba(0,0,0,0.04);">
        <div style="font-size:1.8rem;margin-bottom:0.5rem;">📚</div>
        <div style="font-weight:700;color:{NAVY};margin-bottom:0.75rem;">Question Bank</div>
        <div style="font-size:0.9rem;color:{TEXT3};line-height:1.6;">
            Access the full Actionable Intel question repository: Behavioral Frequency battery, NCQ Core CJ items, demographic fields, and custom constructs.
        </div>
    </div>

    <div style="background:{CARD_BG};border:1px solid {BORDER2};border-radius:10px;padding:1.5rem;margin-top:1rem;box-shadow:0 1px 3px rgba(0,0,0,0.04);">
        <div style="font-size:1.8rem;margin-bottom:0.5rem;">🤖</div>
        <div style="font-weight:700;color:{NAVY};margin-bottom:0.75rem;">AI Question Rewriter</div>
        <div style="font-size:0.9rem;color:{TEXT3};line-height:1.6;">
            Adapt any question using 4 proven methodologies: Policy Anchor, Forced Trade-off, Behavioral, and Embedded Experiment framing.
        </div>
    </div>

    <div style="background:{CARD_BG};border:1px solid {BORDER2};border-radius:10px;padding:1.5rem;margin-top:1rem;box-shadow:0 1px 3px rgba(0,0,0,0.04);">
        <div style="font-size:1.8rem;margin-bottom:0.5rem;">📋</div>
        <div style="font-weight:700;color:{NAVY};margin-bottom:0.75rem;">Survey Assembly</div>
        <div style="font-size:0.9rem;color:{TEXT3};line-height:1.6;">
            Drag-and-drop survey builder with skip logic, randomization, and quality checks for respondent burden.
        </div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div style="background:{CARD_BG};border:1px solid {BORDER2};border-radius:10px;padding:1.5rem;box-shadow:0 1px 3px rgba(0,0,0,0.04);">
        <div style="font-size:1.8rem;margin-bottom:0.5rem;">📐</div>
        <div style="font-weight:700;color:{NAVY};margin-bottom:0.75rem;">Construct Mapping</div>
        <div style="font-size:0.9rem;color:{TEXT3};line-height:1.6;">
            Automatic archetype alignment: each question tagged with the belief axes it measures and the voter segments it reaches.
        </div>
    </div>

    <div style="background:{CARD_BG};border:1px solid {BORDER2};border-radius:10px;padding:1.5rem;margin-top:1rem;box-shadow:0 1px 3px rgba(0,0,0,0.04);">
        <div style="font-size:1.8rem;margin-bottom:0.5rem;">⚡</div>
        <div style="font-weight:700;color:{NAVY};margin-bottom:0.75rem;">Methodology Guidance</div>
        <div style="font-size:0.9rem;color:{TEXT3};line-height:1.6;">
            Built-in best practices: behavioral past-action items, avoid knowledge tests, minimize respondent burden, test for durability.
        </div>
    </div>

    <div style="background:{CARD_BG};border:1px solid {BORDER2};border-radius:10px;padding:1.5rem;margin-top:1rem;box-shadow:0 1px 3px rgba(0,0,0,0.04);">
        <div style="font-size:1.8rem;margin-bottom:0.5rem;">📥</div>
        <div style="font-weight:700;color:{NAVY};margin-bottom:0.75rem;">Export Options</div>
        <div style="font-size:0.9rem;color:{TEXT3};line-height:1.6;">
            Download as JSON, .docx, or Alchemer/Qualtrics format. Ready for fielding on your platform of choice.
        </div>
    </div>
    """, unsafe_allow_html=True)

st.divider()

st.info(
    "📖 **Status:** SurveyMaker requires the canonical question registry integration and will be available in the next portal update.",
    icon="ℹ️"
)

portal_footer()
