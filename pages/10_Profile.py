"""
Profile — User profile, geographic focus areas, policy areas, and team directory.
Backed by Supabase `user_profiles` table.

Initial setup SQL (run once in Supabase SQL editor):
    CREATE TABLE IF NOT EXISTS user_profiles (
        username        TEXT PRIMARY KEY,
        display_name    TEXT NOT NULL DEFAULT '',
        organization    TEXT NOT NULL DEFAULT '',
        role            TEXT NOT NULL DEFAULT '',
        bio             TEXT NOT NULL DEFAULT '',
        phone           TEXT NOT NULL DEFAULT '',
        email           TEXT NOT NULL DEFAULT '',
        website         TEXT NOT NULL DEFAULT '',
        states          TEXT[] NOT NULL DEFAULT '{}',
        policy_areas    TEXT[] NOT NULL DEFAULT '{}',
        created_at      TIMESTAMPTZ DEFAULT NOW(),
        updated_at      TIMESTAMPTZ DEFAULT NOW()
    );

If upgrading an existing table:
    ALTER TABLE user_profiles ADD COLUMN IF NOT EXISTS phone   TEXT NOT NULL DEFAULT '';
    ALTER TABLE user_profiles ADD COLUMN IF NOT EXISTS email   TEXT NOT NULL DEFAULT '';
    ALTER TABLE user_profiles ADD COLUMN IF NOT EXISTS website TEXT NOT NULL DEFAULT '';
"""

import streamlit as st
from pathlib import Path
import sys
import requests
import json
from datetime import datetime, timezone

sys.path.insert(0, str(Path(__file__).parent.parent))
from theme import (
    apply_theme, portal_footer, get_supabase_config, get_supabase_headers,
    NAVY, NAVY2, GOLD, GOLD_MID, TEXT1, TEXT2, TEXT3, BORDER2, BG, CARD_BG,
)
from auth import require_auth

st.set_page_config(
    page_title="Profile — SLA Portal",
    page_icon="👤",
    layout="wide",
)
apply_theme()
username = require_auth("Second Look Alliance", accent_color=GOLD)

# ─────────────────────────────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────────────────────────────

ALL_STATES = [
    "Alabama", "Alaska", "Arizona", "Arkansas", "California", "Colorado",
    "Connecticut", "Delaware", "Florida", "Georgia", "Hawaii", "Idaho",
    "Illinois", "Indiana", "Iowa", "Kansas", "Kentucky", "Louisiana",
    "Maine", "Maryland", "Massachusetts", "Michigan", "Minnesota",
    "Mississippi", "Missouri", "Montana", "Nebraska", "Nevada",
    "New Hampshire", "New Jersey", "New Mexico", "New York",
    "North Carolina", "North Dakota", "Ohio", "Oklahoma", "Oregon",
    "Pennsylvania", "Rhode Island", "South Carolina", "South Dakota",
    "Tennessee", "Texas", "Utah", "Vermont", "Virginia", "Washington",
    "West Virginia", "Wisconsin", "Wyoming",
]

ACTIVE_SURVEY_STATES = ["Louisiana", "Oklahoma", "Virginia", "Massachusetts", "North Carolina", "New Jersey"]

POLICY_TOPICS = [
    "Public Defender Funding", "Community Investment", "Literacy Programs",
    "Right to Counsel", "Domestic Violence", "Property Crime Reform",
    "Redemption / Second Chances", "Record Expungement", "Sentence Review",
    "Judicial Discretion", "Retroactive Relief", "Fines & Fees",
    "Mandatory Minimums", "Bail Reform", "Reentry Programs",
    "Juvenile Justice", "Family Reunification", "Compassionate Release",
    "Court Reform", "Prosecutor Accountability", "Death Penalty",
    "Life Without Parole", "Mental Health & Addiction", "Racial Disparities",
    "Good Time Credits", "Prison Conditions", "Parole Reform",
]

ROLES = [
    "Advocate / Organizer",
    "Researcher / Analyst",
    "Policymaker / Legislative Staff",
    "Communications / Media",
    "Legal / Defense Counsel",
    "Partner Organization",
    "Consultant",
    "Staff / Operations",
    "Other",
]

# ─────────────────────────────────────────────────────────────────
# SUPABASE HELPERS
# ─────────────────────────────────────────────────────────────────

def _headers():
    url, key = get_supabase_config()
    return url, get_supabase_headers()


def load_profile(uname: str) -> dict:
    """Load profile for one user. Returns empty dict if not found."""
    try:
        url, hdrs = _headers()
        resp = requests.get(
            f"{url}/rest/v1/user_profiles?username=eq.{uname}&select=*",
            headers=hdrs, timeout=10,
        )
        if resp.status_code == 200:
            rows = resp.json()
            return rows[0] if rows else {}
    except Exception:
        pass
    return {}


def save_profile(uname: str, data: dict) -> bool:
    """Upsert profile. Returns True on success."""
    try:
        url, hdrs = _headers()
        hdrs["Prefer"] = "resolution=merge-duplicates"
        hdrs["Content-Type"] = "application/json"
        payload = {
            "username": uname,
            "display_name": data.get("display_name", ""),
            "organization": data.get("organization", ""),
            "role": data.get("role", ""),
            "bio": data.get("bio", ""),
            "phone": data.get("phone", ""),
            "email": data.get("email", ""),
            "website": data.get("website", ""),
            "states": data.get("states", []),
            "policy_areas": data.get("policy_areas", []),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        resp = requests.post(
            f"{url}/rest/v1/user_profiles",
            headers=hdrs, data=json.dumps(payload), timeout=10,
        )
        return resp.status_code in (200, 201, 204)
    except Exception:
        return False


def load_all_profiles() -> list:
    """Load all public profiles for the directory."""
    try:
        url, hdrs = _headers()
        resp = requests.get(
            f"{url}/rest/v1/user_profiles?select=username,display_name,organization,role,bio,phone,email,website,states,policy_areas&order=display_name.asc",
            headers=hdrs, timeout=10,
        )
        if resp.status_code == 200:
            return resp.json()
    except Exception:
        pass
    return []


def table_exists() -> bool:
    """Quick check — returns False if the table hasn't been created yet."""
    try:
        url, hdrs = _headers()
        resp = requests.get(
            f"{url}/rest/v1/user_profiles?limit=1",
            headers=hdrs, timeout=6,
        )
        return resp.status_code != 404
    except Exception:
        return False


# ─────────────────────────────────────────────────────────────────
# AVATAR HELPER
# ─────────────────────────────────────────────────────────────────

def initials_avatar(name: str, size: int = 52) -> str:
    parts = name.strip().split()
    letters = (parts[0][0] + (parts[-1][0] if len(parts) > 1 else "")).upper()
    return f"""
<div style="width:{size}px;height:{size}px;border-radius:50%;background:{NAVY};
     display:flex;align-items:center;justify-content:center;
     font-size:{int(size*0.38)}px;font-weight:700;color:{GOLD};
     letter-spacing:0.03em;flex-shrink:0;">{letters}</div>"""


# ─────────────────────────────────────────────────────────────────
# PAGE
# ─────────────────────────────────────────────────────────────────

st.title("Your Profile")
st.markdown("Tell the team who you are, which states you cover, and where your policy focus is. Visible to other portal users.")
st.divider()

# Setup check
if not table_exists():
    st.error("The `user_profiles` table hasn't been created yet.")
    with st.expander("Setup SQL (run once in Supabase SQL editor)", expanded=True):
        st.code("""
CREATE TABLE IF NOT EXISTS user_profiles (
    username        TEXT PRIMARY KEY,
    display_name    TEXT NOT NULL DEFAULT '',
    organization    TEXT NOT NULL DEFAULT '',
    role            TEXT NOT NULL DEFAULT '',
    bio             TEXT NOT NULL DEFAULT '',
    states          TEXT[] NOT NULL DEFAULT '{}',
    policy_areas    TEXT[] NOT NULL DEFAULT '{}',
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);
""", language="sql")
    portal_footer()
    st.stop()

# Load current user's profile
profile = load_profile(username)

# ── EDIT YOUR PROFILE ──────────────────────────────────────────

edit_col, dir_col = st.columns([2, 3], gap="large")

with edit_col:
    st.markdown(f"""
<div style="display:flex;align-items:center;gap:1rem;margin-bottom:1.25rem;">
    {initials_avatar(profile.get("display_name") or username, 56)}
    <div>
        <div style="font-weight:700;color:{NAVY};font-size:1.1rem;">
            {profile.get("display_name") or username}
        </div>
        <div style="font-size:0.82rem;color:{TEXT3};">@{username}</div>
    </div>
</div>
""", unsafe_allow_html=True)

    with st.form("profile_form"):
        st.markdown(f'<div style="font-weight:700;color:{NAVY};margin-bottom:0.5rem;">Edit Profile</div>', unsafe_allow_html=True)

        display_name = st.text_input(
            "Display name",
            value=profile.get("display_name", ""),
            placeholder="Your name as others will see it",
        )
        organization = st.text_input(
            "Organization",
            value=profile.get("organization", ""),
            placeholder="Law firm, nonprofit, agency, coalition…",
        )
        role = st.selectbox(
            "Role",
            options=["— select —"] + ROLES,
            index=(ROLES.index(profile["role"]) + 1) if profile.get("role") in ROLES else 0,
        )
        bio = st.text_area(
            "Bio (optional)",
            value=profile.get("bio", ""),
            height=90,
            placeholder="Brief description of your focus area, cases you've worked on, or what you're tracking.",
            max_chars=400,
        )

        st.markdown(f'<div style="font-weight:700;color:{NAVY};margin-top:0.75rem;margin-bottom:0.25rem;">Geographic Focus</div>', unsafe_allow_html=True)

        active_default = [s for s in (profile.get("states") or []) if s in ACTIVE_SURVEY_STATES]
        other_default = [s for s in (profile.get("states") or []) if s not in ACTIVE_SURVEY_STATES]

        active_states = st.multiselect(
            "Active survey states",
            options=ACTIVE_SURVEY_STATES,
            default=active_default,
            help="States currently in the SLA survey pipeline",
        )
        other_states = st.multiselect(
            "Other states (optional)",
            options=[s for s in ALL_STATES if s not in ACTIVE_SURVEY_STATES],
            default=other_default,
        )

        st.markdown(f'<div style="font-weight:700;color:{NAVY};margin-top:0.75rem;margin-bottom:0.25rem;">Policy Focus Areas</div>', unsafe_allow_html=True)
        policy_areas = st.multiselect(
            "Select all that apply",
            options=POLICY_TOPICS,
            default=[p for p in (profile.get("policy_areas") or []) if p in POLICY_TOPICS],
        )

        save_btn = st.form_submit_button("💾 Save Profile", type="primary", use_container_width=True)

        if save_btn:
            if not display_name.strip():
                st.error("Display name is required.")
            else:
                ok = save_profile(username, {
                    "display_name": display_name.strip(),
                    "organization": organization.strip(),
                    "role": role if role != "— select —" else "",
                    "bio": bio.strip(),
                    "states": active_states + other_states,
                    "policy_areas": policy_areas,
                })
                if ok:
                    st.success("Profile saved.")
                    st.cache_data.clear()
                else:
                    st.error("Could not save — check Supabase connection.")

# ── TEAM DIRECTORY ─────────────────────────────────────────────

with dir_col:
    st.markdown(f'<div style="font-weight:700;color:{NAVY};font-size:1rem;margin-bottom:0.75rem;">Team Directory</div>', unsafe_allow_html=True)

    all_profiles = load_all_profiles()
    # Filter out profiles with no display name set
    visible = [p for p in all_profiles if p.get("display_name")]

    if not visible:
        st.info("No profiles set up yet. You'll be the first once you save yours.")
    else:
        # Search / filter
        search = st.text_input("Search by name, state, or policy area", placeholder="e.g. Louisiana, bail reform…", label_visibility="collapsed", key="dir_search")
        state_filter = st.selectbox("Filter by state", ["All states"] + ALL_STATES, key="dir_state")

        filtered = visible
        if search.strip():
            q = search.strip().lower()
            filtered = [
                p for p in filtered
                if q in (p.get("display_name") or "").lower()
                or q in (p.get("organization") or "").lower()
                or any(q in s.lower() for s in (p.get("states") or []))
                or any(q in a.lower() for a in (p.get("policy_areas") or []))
                or q in (p.get("bio") or "").lower()
            ]
        if state_filter != "All states":
            filtered = [p for p in filtered if state_filter in (p.get("states") or [])]

        st.caption(f"{len(filtered)} of {len(visible)} members shown")
        st.markdown("")

        for p in filtered:
            dname = p.get("display_name", p.get("username", ""))
            org = p.get("organization", "")
            role_str = p.get("role", "")
            bio_str = p.get("bio", "")
            states_list = p.get("states") or []
            areas_list = (p.get("policy_areas") or [])[:4]  # show up to 4

            states_html = " ".join(
                f'<span style="display:inline-block;background:rgba(14,31,61,0.07);border-radius:10px;'
                f'padding:1px 9px;font-size:0.71rem;color:{NAVY};margin:1px 2px;">{s}</span>'
                for s in states_list[:6]
            )
            areas_html = " ".join(
                f'<span style="display:inline-block;background:rgba(196,153,58,0.1);border-radius:10px;'
                f'padding:1px 9px;font-size:0.71rem;color:{GOLD};margin:1px 2px;">{a}</span>'
                for a in areas_list
            )

            is_you = p.get("username") == username
            border_style = f"border:1px solid {GOLD};box-shadow:0 0 0 2px rgba(196,153,58,0.15);" if is_you else f"border:1px solid {BORDER2};"

            st.markdown(f"""
<div style="display:flex;gap:0.85rem;align-items:flex-start;
     background:{CARD_BG};{border_style}border-radius:10px;
     padding:0.75rem 1rem;margin-bottom:0.6rem;">
    {initials_avatar(dname, 40)}
    <div style="flex:1;min-width:0;">
        <div style="display:flex;align-items:baseline;gap:0.5rem;flex-wrap:wrap;">
            <span style="font-weight:700;color:{NAVY};font-size:0.93rem;">{dname}</span>
            {"<span style='font-size:0.72rem;color:" + GOLD + ";'>you</span>" if is_you else ""}
            {f'<span style="font-size:0.8rem;color:{TEXT3};">· {role_str}</span>' if role_str else ""}
        </div>
        {f'<div style="font-size:0.8rem;color:{TEXT2};margin-top:1px;">{org}</div>' if org else ""}
        {f'<div style="font-size:0.78rem;color:{TEXT3};line-height:1.4;margin-top:3px;">{bio_str[:140]}{"…" if len(bio_str)>140 else ""}</div>' if bio_str else ""}
        <div style="margin-top:5px;">{states_html}</div>
        <div style="margin-top:3px;">{areas_html}</div>
    </div>
</div>
""", unsafe_allow_html=True)

portal_footer()
