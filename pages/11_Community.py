"""
Community — Discussion board for portal users.
Backed by Supabase `community_posts` table.

Initial setup SQL (run once in Supabase SQL editor):
    CREATE TABLE IF NOT EXISTS community_posts (
        id           BIGSERIAL PRIMARY KEY,
        username     TEXT NOT NULL,
        display_name TEXT NOT NULL DEFAULT '',
        channel      TEXT NOT NULL DEFAULT 'general',
        message      TEXT NOT NULL,
        tags         TEXT[] NOT NULL DEFAULT '{}',
        created_at   TIMESTAMPTZ DEFAULT NOW()
    );
    CREATE INDEX IF NOT EXISTS community_posts_channel_idx ON community_posts (channel);
    CREATE INDEX IF NOT EXISTS community_posts_created_idx ON community_posts (created_at DESC);

If upgrading an existing table, run this instead:
    ALTER TABLE community_posts ADD COLUMN IF NOT EXISTS tags TEXT[] NOT NULL DEFAULT '{}';
"""

import streamlit as st
from pathlib import Path
import sys
import requests
import json
from datetime import datetime, timezone, timedelta

sys.path.insert(0, str(Path(__file__).parent.parent))
from theme import (
    apply_theme, portal_footer, get_supabase_config, get_supabase_headers,
    NAVY, NAVY2, GOLD, GOLD_MID, TEXT1, TEXT2, TEXT3, BORDER2, BG, CARD_BG,
)
from auth import require_auth

st.set_page_config(
    page_title="Community — SLA Portal",
    page_icon="💬",
    layout="wide",
)
apply_theme()
username = require_auth("Second Look Alliance", accent_color=GOLD)

# ─────────────────────────────────────────────────────────────────
# CHANNEL DEFINITIONS
# ─────────────────────────────────────────────────────────────────

CHANNELS = {
    "# general":         {"key": "general",     "desc": "General discussion — news, questions, announcements"},
    "# strategy":        {"key": "strategy",    "desc": "Campaign strategy, message sequencing, targeting decisions"},
    "# data-research":   {"key": "data",        "desc": "Survey findings, methodology, data questions"},
    "# louisiana":       {"key": "louisiana",   "desc": "Louisiana-specific work and findings"},
    "# oklahoma":        {"key": "oklahoma",    "desc": "Oklahoma-specific work and findings"},
    "# virginia":        {"key": "virginia",    "desc": "Virginia-specific work and findings"},
    "# massachusetts":   {"key": "massachusetts","desc": "Massachusetts-specific work and findings"},
    "# north-carolina":  {"key": "north-carolina","desc": "North Carolina-specific work and findings"},
    "# new-jersey":      {"key": "new-jersey",  "desc": "New Jersey-specific work and findings"},
    "# media-creative":  {"key": "media",       "desc": "Scripts, creative production, MediaMaker outputs"},
    "# survey-design":   {"key": "surveys",     "desc": "Survey design, question review, fielding coordination"},
}

CHANNEL_KEYS = {v["key"]: k for k, v in CHANNELS.items()}

# ─────────────────────────────────────────────────────────────────
# TAG DEFINITIONS
# ─────────────────────────────────────────────────────────────────

# State tags — navy/gold per-state colors
STATE_TAG_COLORS = {
    "Louisiana":      ("#1155AA", "rgba(17,85,170,0.10)"),
    "Oklahoma":       ("#B85400", "rgba(184,84,0,0.10)"),
    "Virginia":       ("#5B1B8A", "rgba(91,27,138,0.10)"),
    "Massachusetts":  ("#8B1A1A", "rgba(139,26,26,0.10)"),
    "North Carolina": ("#1B6B3A", "rgba(27,107,58,0.10)"),
    "New Jersey":     ("#7A4800", "rgba(122,72,0,0.10)"),
}

# Content-type tags — gold
TYPE_TAG_COLORS = {
    "announcement":   ("#1B6B3A", "rgba(27,107,58,0.10)"),
    "question":       ("#5C5954", "rgba(0,0,0,0.07)"),
    "urgent":         ("#8B1A1A", "rgba(139,26,26,0.10)"),
    "data":           ("#B8870A", "rgba(184,135,10,0.10)"),
    "media":          ("#B8870A", "rgba(184,135,10,0.10)"),
    "survey":         ("#B8870A", "rgba(184,135,10,0.10)"),
    "research":       ("#B8870A", "rgba(184,135,10,0.10)"),
}

# Policy topic tags — navy
POLICY_TAG_COLORS = {
    "bail reform":      ("#0E1F3D", "rgba(14,31,61,0.08)"),
    "sentencing":       ("#0E1F3D", "rgba(14,31,61,0.08)"),
    "reentry":          ("#0E1F3D", "rgba(14,31,61,0.08)"),
    "public defender":  ("#0E1F3D", "rgba(14,31,61,0.08)"),
    "expungement":      ("#0E1F3D", "rgba(14,31,61,0.08)"),
    "death penalty":    ("#0E1F3D", "rgba(14,31,61,0.08)"),
    "juvenile justice": ("#0E1F3D", "rgba(14,31,61,0.08)"),
    "fines & fees":     ("#0E1F3D", "rgba(14,31,61,0.08)"),
    "parole":           ("#0E1F3D", "rgba(14,31,61,0.08)"),
    "mental health":    ("#0E1F3D", "rgba(14,31,61,0.08)"),
    "racial equity":    ("#0E1F3D", "rgba(14,31,61,0.08)"),
    "DV / victims":     ("#0E1F3D", "rgba(14,31,61,0.08)"),
}

ALL_TAGS = (
    sorted(STATE_TAG_COLORS.keys())
    + sorted(TYPE_TAG_COLORS.keys())
    + sorted(POLICY_TAG_COLORS.keys())
)

def tag_color(tag: str):
    """Return (text_color, bg_color) for a tag."""
    if tag in STATE_TAG_COLORS:
        return STATE_TAG_COLORS[tag]
    if tag in TYPE_TAG_COLORS:
        return TYPE_TAG_COLORS[tag]
    if tag in POLICY_TAG_COLORS:
        return POLICY_TAG_COLORS[tag]
    return ("#5C5954", "rgba(0,0,0,0.06)")

def render_tag_pill(tag: str, small: bool = False) -> str:
    color, bg = tag_color(tag)
    size = "0.68rem" if small else "0.74rem"
    return (
        f'<span style="display:inline-block;background:{bg};border:1px solid {color};'
        f'border-radius:10px;padding:1px 9px;font-size:{size};'
        f'font-weight:600;color:{color};margin:1px 3px 1px 0;">{tag}</span>'
    )

# ─────────────────────────────────────────────────────────────────
# SUPABASE HELPERS
# ─────────────────────────────────────────────────────────────────

def _headers():
    url, key = get_supabase_config()
    return url, get_supabase_headers()


def table_exists() -> bool:
    try:
        url, hdrs = _headers()
        resp = requests.get(f"{url}/rest/v1/community_posts?limit=1", headers=hdrs, timeout=6)
        return resp.status_code != 404
    except Exception:
        return False


def fetch_posts(channel: str, limit: int = 60, force: bool = False) -> list:
    """Fetch posts for a channel. Served from session_state cache unless force=True."""
    cache_key = f"_posts_{channel}"
    if not force and cache_key in st.session_state:
        return st.session_state[cache_key]
    try:
        url, hdrs = _headers()
        resp = requests.get(
            f"{url}/rest/v1/community_posts"
            f"?channel=eq.{channel}&order=created_at.desc&limit={limit}",
            headers=hdrs, timeout=10,
        )
        if resp.status_code == 200:
            st.session_state[cache_key] = resp.json()
            return st.session_state[cache_key]
    except Exception:
        pass
    return st.session_state.get(cache_key, [])


def post_message(uname: str, display_name: str, channel: str, message: str, tags: list = None) -> bool:
    try:
        url, hdrs = _headers()
        hdrs["Content-Type"] = "application/json"
        payload = {
            "username": uname,
            "display_name": display_name or uname,
            "channel": channel,
            "message": message.strip(),
            "tags": tags or [],
        }
        resp = requests.post(
            f"{url}/rest/v1/community_posts",
            headers=hdrs, data=json.dumps(payload), timeout=10,
        )
        return resp.status_code in (200, 201)
    except Exception:
        return False


def delete_post(post_id: int, uname: str) -> bool:
    """Delete a post — only if it belongs to the current user."""
    try:
        url, hdrs = _headers()
        resp = requests.delete(
            f"{url}/rest/v1/community_posts?id=eq.{post_id}&username=eq.{uname}",
            headers=hdrs, timeout=10,
        )
        return resp.status_code in (200, 204)
    except Exception:
        return False


def load_display_name(uname: str) -> str:
    try:
        url, hdrs = _headers()
        resp = requests.get(
            f"{url}/rest/v1/user_profiles?username=eq.{uname}&select=display_name",
            headers=hdrs, timeout=6,
        )
        if resp.status_code == 200:
            rows = resp.json()
            if rows and rows[0].get("display_name"):
                return rows[0]["display_name"]
    except Exception:
        pass
    return uname


def get_channel_counts(force: bool = False) -> dict:
    """Get post count per channel. Served from session_state cache unless force=True."""
    if not force and "_ch_counts" in st.session_state:
        return st.session_state["_ch_counts"]
    try:
        url, hdrs = _headers()
        resp = requests.get(
            f"{url}/rest/v1/community_posts?select=channel",
            headers=hdrs, timeout=8,
        )
        if resp.status_code == 200:
            rows = resp.json()
            counts = {}
            for r in rows:
                ch = r.get("channel", "")
                counts[ch] = counts.get(ch, 0) + 1
            st.session_state["_ch_counts"] = counts
            return counts
    except Exception:
        pass
    return st.session_state.get("_ch_counts", {})


# ─────────────────────────────────────────────────────────────────
# TIMESTAMP FORMATTING
# ─────────────────────────────────────────────────────────────────

def format_ts(ts_str: str) -> str:
    try:
        ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        delta = now - ts
        if delta < timedelta(minutes=1):
            return "just now"
        if delta < timedelta(hours=1):
            mins = int(delta.total_seconds() / 60)
            return f"{mins}m ago"
        if delta < timedelta(hours=24):
            hrs = int(delta.total_seconds() / 3600)
            return f"{hrs}h ago"
        if delta < timedelta(days=7):
            return ts.strftime("%-d %b")
        return ts.strftime("%-d %b %Y")
    except Exception:
        return ts_str[:10]


# ─────────────────────────────────────────────────────────────────
# PAGE
# ─────────────────────────────────────────────────────────────────

# Setup check
if not table_exists():
    st.title("Community")
    st.error("The `community_posts` table hasn't been created yet.")
    with st.expander("Setup SQL (run once in Supabase SQL editor)", expanded=True):
        st.code("""
CREATE TABLE IF NOT EXISTS community_posts (
    id           BIGSERIAL PRIMARY KEY,
    username     TEXT NOT NULL,
    display_name TEXT NOT NULL DEFAULT '',
    channel      TEXT NOT NULL DEFAULT 'general',
    message      TEXT NOT NULL,
    tags         TEXT[] NOT NULL DEFAULT '{}',
    created_at   TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS community_posts_channel_idx ON community_posts (channel);
CREATE INDEX IF NOT EXISTS community_posts_created_idx ON community_posts (created_at DESC);

-- If upgrading an existing table:
-- ALTER TABLE community_posts ADD COLUMN IF NOT EXISTS tags TEXT[] NOT NULL DEFAULT '{}';
""", language="sql")
    portal_footer()
    st.stop()

# Load current user's display name (for posting)
current_display = load_display_name(username)

# Channel counts for sidebar badges
ch_counts = get_channel_counts()

# ── Sidebar: channel list ──────────────────────────────────────

with st.sidebar:
    st.markdown(f"""
<div style="font-weight:700;color:{NAVY};font-size:0.9rem;
     text-transform:uppercase;letter-spacing:0.06em;
     margin-bottom:0.6rem;padding-top:0.5rem;">Channels</div>
""", unsafe_allow_html=True)

    channel_names = list(CHANNELS.keys())
    default_idx = channel_names.index("# general")
    if "community_channel" not in st.session_state:
        st.session_state["community_channel"] = "# general"

    for ch_name in channel_names:
        ch_key = CHANNELS[ch_name]["key"]
        count = ch_counts.get(ch_key, 0)
        is_active = st.session_state["community_channel"] == ch_name
        bg = f"background:rgba(14,31,61,0.08);font-weight:700;" if is_active else ""
        badge = f'<span style="margin-left:auto;font-size:0.7rem;color:{TEXT3};">{count}</span>' if count > 0 else ""
        if st.button(
            f"{ch_name}{'  · ' + str(count) if count > 0 else ''}",
            key=f"ch_{ch_key}",
            use_container_width=True,
        ):
            st.session_state["community_channel"] = ch_name
            st.session_state.pop("community_posts_cache", None)
            st.rerun()

    st.markdown("---")
    st.markdown(f"""
<div style="font-size:0.76rem;color:{TEXT3};line-height:1.5;">
    Posting as <strong style="color:{NAVY};">{current_display}</strong><br>
    <a href="/Profile" target="_self" style="color:{GOLD};font-size:0.74rem;text-decoration:none;">
        Edit your profile →
    </a>
</div>
""", unsafe_allow_html=True)

# ── Main content ───────────────────────────────────────────────

selected_ch = st.session_state.get("community_channel", "# general")
ch_info = CHANNELS.get(selected_ch, CHANNELS["# general"])
ch_key = ch_info["key"]

# Header
col_title, col_refresh = st.columns([5, 1])
with col_title:
    st.markdown(f"""
<div style="margin-bottom:0.25rem;">
    <span style="font-family:serif;font-size:1.6rem;font-weight:700;color:{NAVY};">{selected_ch}</span>
</div>
<div style="font-size:0.83rem;color:{TEXT3};margin-bottom:0.75rem;">{ch_info['desc']}</div>
""", unsafe_allow_html=True)

with col_refresh:
    if st.button("↻ Refresh", key="refresh_posts"):
        # Clear all cached post data so next render fetches fresh
        for k in [k for k in st.session_state if k.startswith("_posts_") or k == "_ch_counts"]:
            st.session_state.pop(k, None)
        st.rerun()

st.divider()

# ── Compose ────────────────────────────────────────────────────

with st.form("compose_form", clear_on_submit=True):
    new_message = st.text_area(
        "Message",
        height=90,
        placeholder=f"Post to {selected_ch}…",
        max_chars=2000,
        label_visibility="collapsed",
    )
    tag_col, btn_col = st.columns([5, 1])
    with tag_col:
        selected_tags = st.multiselect(
            "Tags",
            options=ALL_TAGS,
            default=[],
            placeholder="Add tags (state, topic, type)…",
            label_visibility="collapsed",
        )
    with btn_col:
        post_btn = st.form_submit_button("Post", type="primary", use_container_width=True)

    if post_btn:
        if not new_message.strip():
            st.warning("Type a message before posting.")
        elif len(new_message.strip()) < 3:
            st.warning("Message too short.")
        else:
            ok = post_message(username, current_display, ch_key, new_message, tags=selected_tags)
            if ok:
                st.session_state.pop(f"community_posts_cache_{ch_key}", None)
                st.rerun()
            else:
                st.error("Failed to post. Check Supabase connection.")

st.markdown("")

# ── Tag filter ─────────────────────────────────────────────────

filter_tag = st.selectbox(
    "Filter by tag",
    options=["All posts"] + ALL_TAGS,
    key="tag_filter",
    label_visibility="collapsed",
)

st.markdown("")

# ── Messages ───────────────────────────────────────────────────

cache_key = f"community_posts_cache_{ch_key}"
if cache_key not in st.session_state:
    st.session_state[cache_key] = fetch_posts(ch_key, limit=60)

posts = st.session_state[cache_key]

# Apply tag filter client-side
if filter_tag != "All posts":
    posts = [p for p in posts if filter_tag in (p.get("tags") or [])]

if not posts:
    st.markdown(f"""
<div style="text-align:center;padding:3rem 1rem;color:{TEXT3};font-size:0.9rem;">
    <div style="font-size:2rem;margin-bottom:0.75rem;">💬</div>
    No messages in {selected_ch} yet.<br>
    <span style="font-size:0.82rem;">Be the first to post.</span>
</div>
""", unsafe_allow_html=True)
else:
    # Show newest at top (already sorted desc by query)
    for post in posts:
        pid = post.get("id")
        poster_name = post.get("display_name") or post.get("username", "Unknown")
        poster_user = post.get("username", "")
        msg = post.get("message", "")
        ts = format_ts(post.get("created_at", ""))
        is_own = poster_user == username

        # Initials avatar (inline, small) — single-line to avoid markdown parser issue
        parts = poster_name.split()
        letters = (parts[0][0] + (parts[-1][0] if len(parts) > 1 else "")).upper()
        avatar_html = (
            f'<div style="width:34px;height:34px;border-radius:50%;background:{NAVY};flex-shrink:0;'
            f'display:flex;align-items:center;justify-content:center;'
            f'font-size:0.7rem;font-weight:700;color:{GOLD};">{letters}</div>'
        )

        delete_area = ""
        if is_own:
            # We'll render a delete expander below
            pass

        border = f"border-left:3px solid {GOLD};" if is_own else f"border-left:3px solid {BORDER2};"

        post_tags = post.get("tags") or []
        tags_html = ""
        if post_tags:
            pills = "".join(render_tag_pill(t, small=True) for t in post_tags)
            tags_html = f'<div style="margin-top:6px;">{pills}</div>'

        st.markdown(
            f'<div style="display:flex;gap:0.75rem;align-items:flex-start;'
            f'background:{CARD_BG};{border}border-radius:0 8px 8px 0;'
            f'padding:0.65rem 0.9rem;margin-bottom:0.5rem;'
            f'border-top:1px solid {BORDER2};border-right:1px solid {BORDER2};border-bottom:1px solid {BORDER2};">'
            f'{avatar_html}'
            f'<div style="flex:1;min-width:0;">'
            f'<div style="display:flex;align-items:baseline;gap:0.5rem;flex-wrap:wrap;margin-bottom:0.25rem;">'
            f'<span style="font-weight:700;font-size:0.88rem;color:{NAVY};">{poster_name}</span>'
            + (f'<span style="font-size:0.7rem;color:{GOLD};">you</span>' if is_own else '')
            + f'<span style="font-size:0.75rem;color:{TEXT3};">{ts}</span>'
            f'</div>'
            f'<div style="font-size:0.88rem;color:{TEXT1};line-height:1.6;white-space:pre-wrap;">{msg}</div>'
            f'{tags_html}'
            f'</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

        # Delete option for own posts
        if is_own:
            with st.expander("…", expanded=False):
                if st.button(f"🗑 Delete this post", key=f"del_{pid}"):
                    if delete_post(pid, username):
                        st.session_state.pop(cache_key, None)
                        st.rerun()
                    else:
                        st.error("Could not delete.")

    if len(posts) >= 60:
        st.caption("Showing the 60 most recent messages in this channel.")

portal_footer()
