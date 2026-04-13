"""
SLA Portal — Shared Theme & Design System
Navy / Gold / Serif design (Playfair Display headings + DM Sans body)
Matches Preston's portal design spec.
"""

import streamlit as st

# ── Design Tokens ──
NAVY = "#0E1F3D"
NAVY2 = "#1a3260"
NAVY3 = "#1F2B47"
GOLD = "#B8870A"
GOLD_MID = "#D4A843"
GOLD_PALE = "#FDF6E3"
GREEN = "#1B6B3A"
RED = "#8B1A1A"
AMBER = "#B85400"
TEXT1 = "#1A1A18"
TEXT2 = "#4A4A42"
TEXT3 = "#5C5954"
BORDER = "#D4D0C8"
BORDER2 = "#E8E4DC"
BG = "#FAF9F6"
CARD_BG = "#FFFFFF"

# State colors
STATE_COLORS = {
    "Oklahoma": "#B85400",
    "Louisiana": "#1155AA",
    "North Carolina": "#1B6B3A",
    "Virginia": "#5B1B8A",
    "Massachusetts": "#8B1A1A",
    "New Jersey": "#7A4800",
}

STATE_ABBR = {
    "Oklahoma": "OK", "Louisiana": "LA", "North Carolina": "NC",
    "Virginia": "VA", "Massachusetts": "MA", "New Jersey": "NJ",
}

# Tier colors and labels
TIER_STYLES = {
    "Entry": {"bg": "rgba(27, 107, 58, 0.12)", "color": "#1B6B3A", "border": "#1B6B3A"},
    "Entry (VA)": {"bg": "rgba(27, 107, 58, 0.08)", "color": "#1B6B3A", "border": "#1B6B3A"},
    "Bridge": {"bg": "rgba(17, 85, 170, 0.12)", "color": "#1155AA", "border": "#1155AA"},
    "Downstream": {"bg": "rgba(184, 135, 10, 0.12)", "color": "#B8870A", "border": "#B8870A"},
    "Destination": {"bg": "rgba(139, 26, 26, 0.12)", "color": "#8B1A1A", "border": "#8B1A1A"},
    "Gauge": {"bg": "rgba(91, 27, 138, 0.12)", "color": "#5B1B8A", "border": "#5B1B8A"},
}


# ── Supabase Config ──
SUPABASE_URL = "https://sthbsrmdvxjmqympmdnc.supabase.co"
SUPABASE_KEY_FALLBACK = (
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9."
    "eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InN0aGJzcm1kdnhqbXF5bXBtZG5jIiwi"
    "cm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3NTA2OTgyNSwiZXhwIjoyMDkw"
    "NjQ1ODI1fQ.AoN7ptAGqnXkDyVTYUK6qztCjlzDRwz-bbLjkW2pGE8"
)

CJ_SURVEYS = [
    "LA-CJ-2025-002", "LA-CJ-2025-001",
    "OK-CJ-2025-001",
    "VA-CJ-2026-001", "MA-CJ-2026-001", "NC-CJ-2026-001", "NJ-CJ-2026-001",
]
# OK-CJ-2024-001 excluded from portal scoring — old survey, OK-CJ-2025-001 carries Oklahoma.
# Data remains in Supabase for historical reference / trend analysis.

SURVEY_STATE = {
    "LA-CJ-2025-002": "Louisiana", "LA-CJ-2025-001": "Louisiana",
    "OK-CJ-2025-001": "Oklahoma",
    "VA-CJ-2026-001": "Virginia", "MA-CJ-2026-001": "Massachusetts",
    "NC-CJ-2026-001": "North Carolina", "NJ-CJ-2026-001": "New Jersey",
}

# Persuasion tier assignments from today's analysis
TIER_MAP = {
    "PD_FUNDING": "Entry", "INVEST": "Entry", "LIT": "Entry",
    "COUNSEL_ACCESS": "Entry (VA)",
    "DV": "Bridge", "CAND-DV": "Bridge",
    "COMPASSION": "Bridge", "FINES": "Bridge",
    "PROP": "Downstream", "REDEMPTION": "Downstream",
    "EXPUNGE": "Downstream", "SENTREVIEW": "Downstream",
    "JUDICIAL": "Downstream", "RETRO": "Downstream",
    "MAND": "Downstream",
    "BAIL": "Downstream", "REENTRY": "Downstream",
    "RECORD": "Downstream", "JUV": "Downstream",
    "FAMILY": "Downstream", "ELDERLY": "Downstream",
    "COURT": "Downstream", "COURTREVIEW": "Downstream",
    "TRUST": "Downstream", "PLEA": "Downstream",
    "PROS": "Downstream",
    "CAND": "Gauge", "TOUGHCRIME": "Gauge",
    "ISSUE_SALIENCE": "Gauge", "IMPACT": "Gauge",
    "DETER": "Destination", "FISCAL": "Destination",
    "DP_ABOLITION": "Destination", "DP_RELIABILITY": "Destination",
    "LWOP": "Destination",
}


def get_supabase_config():
    """Get Supabase URL and key from secrets or fallback."""
    try:
        url = st.secrets.get("SUPABASE_URL", SUPABASE_URL)
    except Exception:
        url = SUPABASE_URL
    try:
        key = st.secrets.get("SUPABASE_KEY", SUPABASE_KEY_FALLBACK)
    except Exception:
        key = SUPABASE_KEY_FALLBACK
    return url, key


def get_supabase_headers():
    """Get HTTP headers for Supabase requests."""
    _, key = get_supabase_config()
    return {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }


def apply_theme():
    """Apply the SLA navy/gold/serif theme to any Streamlit page."""
    st.markdown(f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;500;600;700;800&display=swap');
        @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600;700&display=swap');
        @import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&display=swap');

        /* Base */
        html, body, [data-testid="stAppViewContainer"] {{
            background-color: {BG};
            color: {TEXT1};
            font-family: 'DM Sans', -apple-system, sans-serif;
        }}

        [data-testid="stSidebar"] {{
            background-color: {NAVY};
            border-right: none;
        }}
        [data-testid="stSidebar"] * {{
            color: #c8cad0 !important;
        }}
        [data-testid="stSidebar"] .stSelectbox label,
        [data-testid="stSidebar"] .stRadio label {{
            color: #e8e8ed !important;
            font-weight: 500;
        }}
        [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2,
        [data-testid="stSidebar"] h3 {{
            color: {GOLD_MID} !important;
            font-family: 'Playfair Display', serif !important;
        }}

        /* Typography */
        h1, h2, h3, h4 {{
            font-family: 'Playfair Display', Georgia, serif !important;
            color: {NAVY} !important;
            font-weight: 700;
        }}
        h1 {{ font-size: 1.8rem !important; letter-spacing: -0.01em; }}
        h2 {{ font-size: 1.4rem !important; }}
        h3 {{ font-size: 1.15rem !important; }}

        p, li, span, div {{
            font-family: 'DM Sans', sans-serif;
        }}

        code, .stCode {{
            font-family: 'DM Mono', monospace;
        }}

        /* Metrics */
        .stMetric {{
            background-color: {CARD_BG};
            padding: 1.25rem;
            border-radius: 10px;
            border: 1px solid {BORDER2};
            box-shadow: 0 1px 3px rgba(0,0,0,0.04);
        }}
        .stMetric label {{
            color: {TEXT3} !important;
            font-size: 0.8rem;
            font-weight: 500;
            text-transform: uppercase;
            letter-spacing: 0.04em;
        }}
        .stMetric [data-testid="metric-container"] > div:first-child {{
            color: {NAVY} !important;
            font-family: 'Playfair Display', serif !important;
            font-size: 1.8rem;
            font-weight: 700;
        }}

        /* Buttons */
        .stButton > button {{
            background-color: {NAVY};
            color: #ffffff;
            font-weight: 600;
            border: none;
            border-radius: 8px;
            font-family: 'DM Sans', sans-serif;
        }}
        .stButton > button:hover {{
            background-color: {NAVY2};
        }}

        /* Divider */
        hr {{
            border-color: {BORDER2} !important;
        }}

        /* Portal header bar */
        .portal-header {{
            background: {NAVY};
            color: #e8e8ed;
            padding: 1rem 1.5rem;
            border-radius: 12px;
            margin-bottom: 1.25rem;
            display: flex;
            align-items: center;
            justify-content: space-between;
            flex-wrap: wrap;
            gap: 12px;
        }}
        .portal-header .brand {{
            font-family: 'Playfair Display', serif;
            font-size: 1.3rem;
            font-weight: 700;
            color: #ffffff;
        }}
        .portal-header .brand span {{
            display: block;
            font-family: 'DM Sans', sans-serif;
            font-size: 0.75rem;
            font-weight: 400;
            color: #8b8fa3;
            margin-top: 2px;
        }}
        .portal-header .stat-val {{
            font-family: 'DM Mono', monospace;
            font-size: 1.15rem;
            font-weight: 600;
            color: {GOLD_MID};
        }}
        .portal-header .stat-label {{
            font-size: 0.65rem;
            color: #8b8fa3;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}

        /* State pills */
        .state-pill {{
            display: inline-block;
            padding: 3px 12px;
            border-radius: 14px;
            font-size: 0.75rem;
            font-weight: 600;
            margin: 2px 3px;
            border: 1.5px solid;
        }}
        .pill-ok {{ background: rgba(184,84,0,0.1); color: #B85400; border-color: #B85400; }}
        .pill-la {{ background: rgba(17,85,170,0.1); color: #1155AA; border-color: #1155AA; }}
        .pill-nc {{ background: rgba(27,107,58,0.1); color: #1B6B3A; border-color: #1B6B3A; }}
        .pill-va {{ background: rgba(91,27,138,0.1); color: #5B1B8A; border-color: #5B1B8A; }}
        .pill-ma {{ background: rgba(139,26,26,0.1); color: #8B1A1A; border-color: #8B1A1A; }}
        .pill-nj {{ background: rgba(122,72,0,0.1); color: #7A4800; border-color: #7A4800; }}
        .pill-pending {{ background: {BORDER2}; color: {TEXT3}; border-color: {BORDER}; opacity: 0.7; }}

        /* Tier badges */
        .tier-badge {{
            display: inline-block;
            padding: 2px 12px;
            border-radius: 12px;
            font-size: 0.72rem;
            font-weight: 600;
            letter-spacing: 0.02em;
        }}
        .tier-entry {{ background: rgba(27,107,58,0.12); color: #1B6B3A; }}
        .tier-bridge {{ background: rgba(17,85,170,0.12); color: #1155AA; }}
        .tier-downstream {{ background: rgba(184,135,10,0.12); color: #B8870A; }}
        .tier-destination {{ background: rgba(139,26,26,0.12); color: #8B1A1A; }}
        .tier-gauge {{ background: rgba(91,27,138,0.12); color: #5B1B8A; }}

        /* Detail card */
        .detail-card {{
            background: {CARD_BG};
            border: 1px solid {BORDER2};
            border-radius: 10px;
            padding: 1.25rem;
            margin: 0.5rem 0;
            box-shadow: 0 1px 3px rgba(0,0,0,0.04);
        }}
        .detail-card h3 {{
            color: {NAVY} !important;
            margin-top: 0;
        }}

        /* Nav cards */
        .nav-card {{
            background: {CARD_BG};
            border: 1px solid {BORDER2};
            border-radius: 10px;
            padding: 1.25rem;
            margin: 0.4rem 0;
            cursor: pointer;
            transition: all 0.2s ease;
            box-shadow: 0 1px 3px rgba(0,0,0,0.04);
        }}
        .nav-card:hover {{
            border-color: {GOLD_MID};
            box-shadow: 0 4px 12px rgba(184,135,10,0.1);
            transform: translateY(-2px);
        }}
        .nav-card-title {{
            font-family: 'Playfair Display', serif;
            font-size: 1.05rem;
            font-weight: 600;
            color: {NAVY};
            margin-bottom: 0.4rem;
        }}
        .nav-card-desc {{
            font-size: 0.82rem;
            color: {TEXT3};
            line-height: 1.5;
        }}
        .nav-card-icon {{
            font-size: 1.8rem;
            margin-bottom: 0.5rem;
        }}

        /* Tier cards (Persuasion Architecture) */
        .tier-card {{
            background: {CARD_BG};
            border: 1px solid {BORDER2};
            border-radius: 10px;
            padding: 1.5rem;
            margin: 1rem 0;
            box-shadow: 0 1px 3px rgba(0,0,0,0.04);
        }}
        .tier-card-title {{
            font-family: 'Playfair Display', serif;
            font-size: 1.15rem;
            font-weight: 700;
            color: {NAVY};
            margin-bottom: 4px;
        }}
        .tier-card-sub {{
            font-size: 0.82rem;
            color: {TEXT3};
            margin-bottom: 1rem;
        }}

        /* Archetype card */
        .archetype-card {{
            background: {CARD_BG};
            border: 1px solid {BORDER2};
            border-radius: 10px;
            padding: 1.25rem;
            box-shadow: 0 1px 3px rgba(0,0,0,0.04);
        }}
        .archetype-name {{
            font-family: 'Playfair Display', serif;
            font-weight: 700;
            font-size: 1rem;
            margin-bottom: 2px;
        }}
        .archetype-pct {{
            font-family: 'DM Mono', monospace;
            font-size: 0.85rem;
            font-weight: 500;
            margin-bottom: 8px;
        }}
        .archetype-tag {{
            display: inline-block;
            padding: 2px 8px;
            border-radius: 10px;
            font-size: 0.65rem;
            font-weight: 500;
            margin: 1px 2px;
        }}

        /* Footer */
        .portal-footer {{
            text-align: center;
            padding: 1.5rem 0 1rem;
            margin-top: 2rem;
            border-top: 1px solid {BORDER2};
            font-size: 0.75rem;
            color: {TEXT3};
        }}

        /* Heatmap cell colors */
        .hm-hi {{ background: rgba(27,107,58,0.12); color: #1B6B3A; font-weight: 600; }}
        .hm-mid {{ background: rgba(184,135,10,0.12); color: #B8870A; font-weight: 500; }}
        .hm-lo {{ background: rgba(139,26,26,0.12); color: #8B1A1A; font-weight: 600; }}

        /* Hide default Streamlit chrome */
        #MainMenu {{visibility: hidden;}}
        footer {{visibility: hidden;}}
    </style>
    """, unsafe_allow_html=True)


def portal_header(n_respondents=0, n_states=0, n_questions=0):
    """Render the navy portal header bar with KPI stats."""
    st.markdown(f"""
    <div class="portal-header">
        <div>
            <div class="brand">Second Look Alliance<span>Criminal Justice Reform Intelligence Portal</span></div>
        </div>
        <div style="display:flex;gap:24px;align-items:center;">
            <div style="text-align:center;">
                <div class="stat-val">{n_respondents:,}</div>
                <div class="stat-label">Respondents</div>
            </div>
            <div style="width:1px;height:28px;background:#2a3d5c;"></div>
            <div style="text-align:center;">
                <div class="stat-val">{n_states}</div>
                <div class="stat-label">States live</div>
            </div>
            <div style="width:1px;height:28px;background:#2a3d5c;"></div>
            <div style="text-align:center;">
                <div class="stat-val">{n_questions}</div>
                <div class="stat-label">Questions scored</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def state_pills_html(states_live, states_pending=None):
    """Generate state pill HTML."""
    if states_pending is None:
        states_pending = []
    pills = []
    abbr_map = {v: k.lower() for k, v in STATE_ABBR.items()}
    for state in states_live:
        abbr = STATE_ABBR.get(state, state[:2]).lower()
        pills.append(f'<span class="state-pill pill-{abbr}">{state}</span>')
    for state in states_pending:
        pills.append(f'<span class="state-pill pill-pending">{state} (pending)</span>')
    return " ".join(pills)


def tier_badge_html(construct):
    """Generate a tier badge for a construct."""
    tier = TIER_MAP.get(construct, "")
    if not tier:
        return ""
    css_class = "tier-" + tier.split("(")[0].strip().lower()
    return f'<span class="tier-badge {css_class}">{tier}</span>'


def portal_footer():
    """Render the footer."""
    st.markdown("""
    <div class="portal-footer">
        Second Look Alliance · Criminal Justice Reform Intelligence Portal<br>
        Research & Data Infrastructure by <strong>Actionable Intel</strong> · Confidential
    </div>
    """, unsafe_allow_html=True)


def data_source_badge(source="mrp"):
    """
    Render a small badge under page titles indicating data source.
    source: "mrp" (primary — MrP-adjusted with raw fallback) or "raw" (raw only).
    """
    if source == "mrp":
        badge_color = "#1B6B3A"
        label = "MrP-Adjusted"
        tooltip = "Support rates are MrP-adjusted (multilevel regression with poststratification). Surveys not yet through MrP fall back to raw responses."
        # Also show a smaller note about party splits
        party_note = (
            f'<span title="Party breakdowns (Republican/Democrat) use raw survey data — '
            f'party ID is not in the MrP demographic model." style="'
            f'display:inline-block; padding:2px 8px; border-radius:10px; '
            f'background:{NAVY2}; color:#fff; font-size:0.65rem; '
            f'font-family:\'DM Sans\',sans-serif; margin-left:6px; cursor:help; '
            f'opacity:0.8;">Party splits: raw</span>'
        )
    else:
        badge_color = NAVY2
        label = "Raw Survey Responses"
        tooltip = "These numbers come directly from survey responses — no MrP modeling applied."
        party_note = ""
    st.markdown(f"""
    <div style="margin:-0.5rem 0 1rem 0;">
        <span title="{tooltip}" style="
            display:inline-block; padding:3px 10px; border-radius:12px;
            background:{badge_color}; color:#fff; font-size:0.72rem;
            font-family:'DM Sans',sans-serif; letter-spacing:0.3px;
            cursor:help;
        ">{label}</span>{party_note}
    </div>
    """, unsafe_allow_html=True)
