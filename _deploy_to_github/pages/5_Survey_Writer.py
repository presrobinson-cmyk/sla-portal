"""
MediaMaker — PLACEHOLDER
Campaign message generation powered by Actionable Intel AI.
"""

import streamlit as st
from pathlib import Path
import sys

# Auth gate
sys.path.insert(0, str(Path(__file__).parent.parent))
from theme import apply_theme, portal_footer, NAVY, GOLD, CARD_BG, BORDER2, TEXT3
from auth import require_auth

st.set_page_config(
    page_title="MediaMaker — SLA Portal",
    page_icon="📢",
    layout="wide",
)

apply_theme()
username = require_auth("Second Look Alliance", accent_color=GOLD)

st.title("MediaMaker")
st.markdown(
    "Select a Golden Zone issue → audience targeting specs + AI-generated message scripts",
    unsafe_allow_html=True
)

st.divider()

# ─────────────────────────────────────────────────────────────────
# COMING SOON NOTICE
# ─────────────────────────────────────────────────────────────────

st.markdown(f"""
<div style="background:{CARD_BG};border:1px solid {BORDER2};border-radius:10px;padding:2rem;text-align:center;box-shadow:0 1px 3px rgba(0,0,0,0.04);">
    <div style="font-size:3rem;margin-bottom:1rem;">🚀</div>
    <div style="font-size:1.4rem;font-weight:700;color:{NAVY};margin-bottom:0.5rem;">Coming Soon</div>
    <div style="font-size:0.95rem;color:{TEXT3};line-height:1.6;max-width:600px;margin:0 auto;">
        MediaMaker is currently in development. We're building the tools you need to go from survey intelligence to campaign-ready content.
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown("")

# ─────────────────────────────────────────────────────────────────
# FEATURES DESCRIPTION
# ─────────────────────────────────────────────────────────────────

st.subheader("What MediaMaker Will Do")

col1, col2 = st.columns(2)

with col1:
    st.markdown(f"""
    <div style="background:{CARD_BG};border:1px solid {BORDER2};border-radius:10px;padding:1.5rem;box-shadow:0 1px 3px rgba(0,0,0,0.04);">
        <div style="font-size:1.8rem;margin-bottom:0.5rem;">🎯</div>
        <div style="font-weight:700;color:{NAVY};margin-bottom:0.75rem;">Issue Selection</div>
        <div style="font-size:0.9rem;color:{TEXT3};line-height:1.6;">
            Choose any Golden Zone question from your survey results. MediaMaker will analyze audience composition and readiness.
        </div>
    </div>

    <div style="background:{CARD_BG};border:1px solid {BORDER2};border-radius:10px;padding:1.5rem;margin-top:1rem;box-shadow:0 1px 3px rgba(0,0,0,0.04);">
        <div style="font-size:1.8rem;margin-bottom:0.5rem;">👥</div>
        <div style="font-weight:700;color:{NAVY};margin-bottom:0.75rem;">Audience Targeting</div>
        <div style="font-size:0.9rem;color:{TEXT3};line-height:1.6;">
            Automatic priority audience identification with VIP score, archetype breakdown, and persuasion readiness.
        </div>
    </div>

    <div style="background:{CARD_BG};border:1px solid {BORDER2};border-radius:10px;padding:1.5rem;margin-top:1rem;box-shadow:0 1px 3px rgba(0,0,0,0.04);">
        <div style="font-size:1.8rem;margin-bottom:0.5rem;">📡</div>
        <div style="font-weight:700;color:{NAVY};margin-bottom:0.75rem;">Channel Strategy</div>
        <div style="font-size:0.9rem;color:{TEXT3};line-height:1.6;">
            Channel recommendations based on archetype media habits: Facebook, local news, streaming, talk radio, direct mail.
        </div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div style="background:{CARD_BG};border:1px solid {BORDER2};border-radius:10px;padding:1.5rem;box-shadow:0 1px 3px rgba(0,0,0,0.04);">
        <div style="font-size:1.8rem;margin-bottom:0.5rem;">🎨</div>
        <div style="font-weight:700;color:{NAVY};margin-bottom:0.75rem;">Framing Lens</div>
        <div style="font-size:0.9rem;color:{TEXT3};line-height:1.6;">
            Select from evidence-based persuasion frameworks: Redemption, Fiscal, Fairness, Secular, or Systems Angle.
        </div>
    </div>

    <div style="background:{CARD_BG};border:1px solid {BORDER2};border-radius:10px;padding:1.5rem;margin-top:1rem;box-shadow:0 1px 3px rgba(0,0,0,0.04);">
        <div style="font-size:1.8rem;margin-bottom:0.5rem;">✍️</div>
        <div style="font-weight:700;color:{NAVY};margin-bottom:0.75rem;">AI-Generated Scripts</div>
        <div style="font-size:0.9rem;color:{TEXT3};line-height:1.6;">
            Powered by Claude: 30-second social media spots, 60-second radio scripts, digital ad copy, and door-knock talking points.
        </div>
    </div>

    <div style="background:{CARD_BG};border:1px solid {BORDER2};border-radius:10px;padding:1.5rem;margin-top:1rem;box-shadow:0 1px 3px rgba(0,0,0,0.04);">
        <div style="font-size:1.8rem;margin-bottom:0.5rem;">📥</div>
        <div style="font-weight:700;color:{NAVY};margin-bottom:0.75rem;">Export & Deploy</div>
        <div style="font-size:0.9rem;color:{TEXT3};line-height:1.6;">
            Download scripts in standard formats (Docx, JSON) ready for media production and team collaboration.
        </div>
    </div>
    """, unsafe_allow_html=True)

st.divider()

st.info(
    "📋 **Status:** MediaMaker requires API integration with Claude and media production workflow systems. Expected release in the next portal update.",
    icon="ℹ️"
)

portal_footer()
