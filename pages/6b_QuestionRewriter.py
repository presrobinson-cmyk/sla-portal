"""
QuestionRewriter — Redesign and adapt survey questions for new contexts.

Select a question from the library (or paste your own), review its scoring
profile and known design issues, then choose a rewrite mode to generate a
tailored brief for the AI Analysis page.

Rewrite modes:
  1. Scale Standardization  — convert binary/bare-Likert to full 4-point Likert
  2. Audience Adaptation    — rephrase for a specific state, party, or demo
  3. Framing Shift          — test alternative frames (safety/cost/values/empirical)
  4. Design Validation      — expose known measurement issues; get redesign guidance
"""

import streamlit as st
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
from theme import (
    apply_theme, portal_footer, data_source_badge, get_supabase_config, get_supabase_headers,
    TIER_MAP,
    NAVY, NAVY2, GOLD, GOLD_MID, TEXT1, TEXT2, TEXT3, BORDER2, BG, CARD_BG,
)
from auth import require_auth
from chat_widget import render_chat
from data_loader import (
    load_question_data_hybrid, render_data_source_toggle, get_display_pct,
    load_party_splits,
)

try:
    from content_scoring import get_construct, SKIPPED_QIDS
    SCORING_AVAILABLE = True
except ImportError:
    SCORING_AVAILABLE = False

try:
    from survey_insights_cache import get_insights_for_constructs
    INSIGHTS_AVAILABLE = True
except ImportError:
    INSIGHTS_AVAILABLE = False

st.set_page_config(
    page_title="Question Rewriter — SLA Portal",
    page_icon="🔄",
    layout="wide",
)

apply_theme()
username = require_auth("Second Look Alliance", accent_color=GOLD)

# ─────────────────────────────────────────────────────────────────
# CONSTRUCT LABELS (mirror from SurveyMaker)
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
    "MENTAL_ADDICTION": "Mental Health & Addiction",
    "RACIAL_DISPARITIES": "Racial Disparities",
    "GOODTIME": "Good Time Credits", "REVIEW": "Case Review",
    "CONDITIONS": "Prison Conditions", "AGING": "Aging in Prison",
    "PAROLE": "Parole Reform", "REVISIT": "Sentence Revisiting",
    "FIRSTAPPEAR": "First Appearance / Right to Counsel",
    "COUNSEL": "Right to Counsel (Constitutional)",
    "ALPR": "Automated License Plate Readers",
    "EQUITY": "Equity / Racial Disparities",
    "APPROACH": "Reform Approach (Smart vs Tough)",
    "COMPASSION": "Compassionate Release",
    "TRUST": "System Trust",
}

GAUGE_CONSTRUCTS = {"CAND", "TOUGHCRIME", "ISSUE_SALIENCE", "IMPACT"}

# Scale type labels for the UI
SCALE_TYPES = {
    "binary": "Binary (Yes/No)",
    "likert": "Likert (4-point Strongly/Somewhat)",
    "bare_support": "Bare Support/Oppose (no intensity)",
    "bare_agree": "Bare Agree/Disagree (no intensity)",
    "multi_choice": "Multi-choice / Ranking",
    "unknown": "Unknown",
}

REWRITE_MODES = [
    ("Scale Standardization", "📏", "Convert to full 4-point Likert to capture intensity measurement."),
    ("Audience Adaptation", "🎯", "Rephrase for a specific state, party, or demographic group."),
    ("Framing Shift", "🔄", "Test an alternative frame — safety, fiscal cost, values, or empirical."),
    ("Design Validation", "🔍", "Expose known measurement issues and get redesign guidance."),
]

# ─────────────────────────────────────────────────────────────────
# DATA LOADERS
# ─────────────────────────────────────────────────────────────────

@st.cache_data(ttl=3600, show_spinner=False)
def load_question_library():
    """Return {qid: qd} for all scoreable questions in the library."""
    question_data, _ = load_question_data_hybrid()
    return {
        qid: qd for qid, qd in question_data.items()
        if qd.get("construct") and qd["construct"] not in GAUGE_CONSTRUCTS
    }


@st.cache_data(ttl=3600, show_spinner=False)
def load_party_data():
    """Return party split dict {qid: {r_pct, d_pct}}."""
    return load_party_splits()


# ─────────────────────────────────────────────────────────────────
# PAGE HEADER
# ─────────────────────────────────────────────────────────────────

st.title("Question Rewriter")
data_mode = render_data_source_toggle()
data_source_badge(data_mode)

st.markdown(
    "Select a question from the library — or paste your own — then choose a rewrite "
    "mode to generate a tailored brief for the **AI Analysis** page."
)
st.divider()

# ─────────────────────────────────────────────────────────────────
# LOAD DATA
# ─────────────────────────────────────────────────────────────────

with st.spinner("Loading question library…"):
    question_library = load_question_library()
    party_data = load_party_data()

if not question_library:
    st.warning("No questions found. Check Supabase connection.")
    portal_footer()
    st.stop()

# Build sorted display list for picker
tier_order_map = {"Entry": 1, "Bridge": 2, "Downstream": 3, "Destination": 4, "Unclassified": 5}

lib_items = []
for qid, qd in question_library.items():
    construct = qd.get("construct", "")
    tier = TIER_MAP.get(construct, "Unclassified")
    pct = get_display_pct(qd, data_mode) or 0
    lib_items.append({
        "qid": qid,
        "text": qd.get("question_text", ""),
        "construct": construct,
        "topic_label": CONSTRUCT_LABELS.get(construct, construct),
        "tier": tier,
        "pct": pct,
        "n": qd.get("n_respondents", 0),
        "source": qd.get("source", "raw"),
    })

lib_items.sort(key=lambda x: (tier_order_map.get(x["tier"], 5), -x["pct"]))

# ─────────────────────────────────────────────────────────────────
# QUESTION SOURCE SELECTOR
# ─────────────────────────────────────────────────────────────────

src_tab, paste_tab = st.tabs(["📚 Pick from Library", "✏️ Paste Your Own"])

selected_qid = None
selected_qtext = ""
selected_construct = ""
selected_tier = ""
selected_pct = None
selected_r_pct = None
selected_d_pct = None
selected_n = 0
is_library_q = False

with src_tab:
    # Sidebar-style filters in the tab
    fcol1, fcol2, fcol3 = st.columns(3)
    with fcol1:
        tier_filter = st.selectbox(
            "Filter by Tier",
            ["All Tiers", "Entry", "Bridge", "Downstream", "Destination"],
            key="qr_tier_filter",
        )
    with fcol2:
        construct_labels_sorted = sorted(set(i["topic_label"] for i in lib_items))
        topic_filter = st.selectbox(
            "Filter by Topic",
            ["All Topics"] + construct_labels_sorted,
            key="qr_topic_filter",
        )
    with fcol3:
        support_filter = st.selectbox(
            "Filter by Support",
            ["All", "Strong (75%+)", "Moderate (55-74%)", "Contested (<55%)"],
            key="qr_support_filter",
        )

    # Apply filters
    filtered_items = lib_items
    if tier_filter != "All Tiers":
        filtered_items = [i for i in filtered_items if i["tier"] == tier_filter]
    if topic_filter != "All Topics":
        filtered_items = [i for i in filtered_items if i["topic_label"] == topic_filter]
    if support_filter == "Strong (75%+)":
        filtered_items = [i for i in filtered_items if i["pct"] >= 75]
    elif support_filter == "Moderate (55-74%)":
        filtered_items = [i for i in filtered_items if 55 <= i["pct"] < 75]
    elif support_filter == "Contested (<55%)":
        filtered_items = [i for i in filtered_items if i["pct"] < 55]

    if not filtered_items:
        st.info("No questions match these filters.")
    else:
        # Build display options
        options = {
            f"{round(i['pct'])}% | [{i['tier']}] {i['topic_label']} — {i['text'][:80]}{'…' if len(i['text'])>80 else ''}": i
            for i in filtered_items
        }
        chosen_label = st.selectbox(
            f"Select a question ({len(filtered_items)} matching)",
            list(options.keys()),
            key="qr_lib_select",
        )
        if chosen_label:
            chosen = options[chosen_label]
            selected_qid = chosen["qid"]
            selected_qtext = chosen["text"]
            selected_construct = chosen["construct"]
            selected_tier = chosen["tier"]
            selected_pct = chosen["pct"]
            selected_n = chosen["n"]
            is_library_q = True
            party_row = party_data.get(selected_qid, {})
            selected_r_pct = party_row.get("r_pct")
            selected_d_pct = party_row.get("d_pct")

with paste_tab:
    pasted_text = st.text_area(
        "Paste or type a question",
        height=100,
        placeholder="e.g. Do you support allowing judges to reduce prison sentences for people who have demonstrated rehabilitation?",
        key="qr_paste_text",
    )
    paste_construct = st.selectbox(
        "Assign to construct (for design insight matching)",
        ["(none)"] + sorted(CONSTRUCT_LABELS.keys(), key=lambda k: CONSTRUCT_LABELS[k]),
        format_func=lambda k: CONSTRUCT_LABELS.get(k, k) if k != "(none)" else "(none — no insights)",
        key="qr_paste_construct",
    )
    if pasted_text.strip():
        selected_qtext = pasted_text.strip()
        selected_construct = paste_construct if paste_construct != "(none)" else ""
        selected_tier = TIER_MAP.get(selected_construct, "Unclassified") if selected_construct else ""
        is_library_q = False

# ─────────────────────────────────────────────────────────────────
# QUESTION PROFILE PANEL
# ─────────────────────────────────────────────────────────────────

if selected_qtext:
    st.divider()
    st.markdown("### Question Profile")

    tier_colors = {
        "Entry": "#1B6B3A", "Bridge": "#1155AA",
        "Downstream": "#B8870A", "Destination": "#8B1A1A",
    }
    tc = tier_colors.get(selected_tier, TEXT2)

    # Header card
    st.markdown(
        f"""
        <div style="background:{CARD_BG};border:1px solid {BORDER2};border-radius:12px;
             padding:1rem 1.25rem;margin-bottom:1rem;border-left:4px solid {tc};">
            <div style="font-size:0.88rem;line-height:1.55;color:{TEXT1};margin-bottom:0.75rem;">
                {selected_qtext}
            </div>
            <div style="display:flex;gap:12px;flex-wrap:wrap;align-items:center;">
                <span style="background:{tc};color:#fff;padding:2px 10px;border-radius:12px;
                      font-size:0.75rem;font-weight:700;">{selected_tier or "Unclassified"}</span>
                <span style="font-size:0.78rem;color:{TEXT2};">
                    {CONSTRUCT_LABELS.get(selected_construct, selected_construct) if selected_construct else "No construct assigned"}
                </span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Metrics row
    if is_library_q and selected_pct is not None:
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Overall Support", f"{round(selected_pct)}%")
        m2.metric("Republican Support", f"{round(selected_r_pct)}%" if selected_r_pct is not None else "—")
        m3.metric("Democrat Support", f"{round(selected_d_pct)}%" if selected_d_pct is not None else "—")

        bipartisan = None
        if selected_r_pct is not None and selected_d_pct is not None:
            bipartisan = round(100 - abs(selected_d_pct - selected_r_pct) * 2)
            bipartisan = max(0, bipartisan)
        m4.metric("Bipartisan Score", f"{bipartisan}" if bipartisan is not None else "—")

        # Party gap note
        if selected_r_pct is not None and selected_d_pct is not None:
            gap = selected_d_pct - selected_r_pct
            if abs(gap) <= 5:
                gap_note = f"🟢 Near-zero partisan gap ({gap:+.1f}pts) — strong bipartisan territory."
                gap_color = "#1B6B3A"
            elif abs(gap) <= 15:
                gap_note = f"🟡 Moderate partisan gap ({gap:+.1f}pts) — persuasion opportunity."
                gap_color = "#B8870A"
            else:
                gap_note = f"🔴 High partisan gap ({gap:+.1f}pts D-R) — audience targeting required."
                gap_color = "#8B1A1A"
            st.markdown(
                f"""<div style="font-size:0.8rem;color:{gap_color};margin-bottom:0.5rem;
                     padding:4px 0;">{gap_note}</div>""",
                unsafe_allow_html=True,
            )
    elif not is_library_q:
        st.info(
            "This is a pasted question — no MrP or party data available. "
            "Design insights below are based on assigned construct only."
        )

    # Design insights for this question's construct
    if INSIGHTS_AVAILABLE and selected_construct:
        construct_insights = get_insights_for_constructs(
            [selected_construct], status_filter="Open"
        )
        if construct_insights:
            with st.expander(
                f"⚠️ {len(construct_insights)} open design insight{'s' if len(construct_insights)>1 else ''} "
                f"for {CONSTRUCT_LABELS.get(selected_construct, selected_construct)}",
                expanded=True,
            ):
                priority_styles = {
                    "Must address":   ("#8B1A1A", "rgba(139,26,26,0.08)"),
                    "Should address": ("#B85500", "rgba(184,85,0,0.08)"),
                    "Nice to have":   ("#B8870A", "rgba(184,135,10,0.07)"),
                    "Long-term":      (TEXT3,     "rgba(14,31,61,0.04)"),
                }
                for ins in construct_insights:
                    color, bg = priority_styles.get(ins["priority"], (TEXT2, "rgba(0,0,0,0.04)"))
                    st.markdown(
                        f"""
                        <div style="background:{bg};border-left:3px solid {color};border-radius:8px;
                             padding:0.6rem 0.85rem;margin-bottom:8px;">
                            <div style="font-weight:700;color:{color};font-size:0.81rem;">
                                {ins['insight']}
                            </div>
                            <div style="font-size:0.73rem;color:{TEXT3};margin-bottom:5px;">
                                {ins['priority']} · {ins['type']}
                            </div>
                            <div style="font-size:0.78rem;color:{TEXT2};line-height:1.45;">
                                {ins['description'][:220]}{'…' if len(ins['description'])>220 else ''}
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

# ─────────────────────────────────────────────────────────────────
# REWRITE MODE SELECTOR
# ─────────────────────────────────────────────────────────────────

if selected_qtext:
    st.divider()
    st.markdown("### Rewrite Mode")
    st.caption("Choose what kind of redesign you need. Each mode generates a focused brief for the AI Analysis page.")

    mode_cols = st.columns(4)
    mode_choice = None
    for idx, (mode_name, mode_icon, mode_desc) in enumerate(REWRITE_MODES):
        with mode_cols[idx]:
            selected_this = st.button(
                f"{mode_icon} {mode_name}",
                key=f"qr_mode_{idx}",
                use_container_width=True,
                help=mode_desc,
            )
            if selected_this:
                st.session_state["qr_active_mode"] = mode_name
            st.caption(mode_desc)

    active_mode = st.session_state.get("qr_active_mode")

    # ── REWRITE CONFIGURATION PANELS ──────────────────────────────

    if active_mode:
        st.divider()
        st.markdown(f"#### {active_mode}")

        extra_inputs = {}

        if active_mode == "Scale Standardization":
            st.markdown(
                "Converts a binary or bare-scale question to a full 4-point Likert "
                "format that captures intensity. This is the single most valuable "
                "change for closing fertility range gaps."
            )
            current_scale = st.selectbox(
                "Current scale type",
                list(SCALE_TYPES.keys()),
                format_func=lambda k: SCALE_TYPES[k],
                key="qr_scale_current",
            )
            scale_direction = st.radio(
                "Likert direction",
                ["Support / Oppose", "Agree / Disagree"],
                key="qr_scale_direction",
                horizontal=True,
            )
            include_not_sure = st.checkbox("Add 'Not sure / No opinion' option", value=True, key="qr_not_sure")
            extra_inputs = {
                "current_scale": SCALE_TYPES[current_scale],
                "scale_direction": scale_direction,
                "include_not_sure": include_not_sure,
            }

        elif active_mode == "Audience Adaptation":
            st.markdown(
                "Rephrase the question for a specific context — a state's legal "
                "landscape, a particular party's values frame, or a demographic group."
            )
            acol1, acol2 = st.columns(2)
            with acol1:
                target_state = st.selectbox(
                    "Target state",
                    ["Not state-specific", "Louisiana", "Oklahoma", "Virginia",
                     "Massachusetts", "North Carolina", "New Jersey", "Texas",
                     "Florida", "Georgia", "Ohio", "Other"],
                    key="qr_aud_state",
                )
                target_party = st.selectbox(
                    "Audience lean",
                    ["General public", "Republican / conservative persuadables",
                     "Democratic base", "Independent / swing voters"],
                    key="qr_aud_party",
                )
            with acol2:
                target_demo = st.text_input(
                    "Specific demographic (optional)",
                    placeholder="e.g. rural voters, faith community, veterans",
                    key="qr_aud_demo",
                )
                state_context = st.text_area(
                    "Relevant state or local context (optional)",
                    height=80,
                    placeholder="e.g. Louisiana has the highest incarceration rate in the nation…",
                    key="qr_aud_context",
                )
            extra_inputs = {
                "target_state": target_state,
                "target_party": target_party,
                "target_demo": target_demo,
                "state_context": state_context,
            }

        elif active_mode == "Framing Shift":
            st.markdown(
                "Tests whether an alternative frame makes the same concept more "
                "accessible — especially useful for high-partisan-gap items like "
                "APPROACH where the current frame triggers political identity."
            )
            frames = st.multiselect(
                "Frames to test",
                [
                    "Safety / public safety",
                    "Fiscal cost / taxpayer value",
                    "Family impact",
                    "Faith / values",
                    "Empirical / evidence-based",
                    "Fairness / proportionality",
                    "Personal responsibility",
                    "Victim perspective",
                ],
                default=["Safety / public safety", "Fiscal cost / taxpayer value"],
                key="qr_frames",
            )
            frame_notes = st.text_area(
                "What is the current framing doing wrong? (optional)",
                height=80,
                placeholder="e.g. 'Smart on crime' is politically coded — Democrats love it, Republicans reject it on instinct.",
                key="qr_frame_notes",
            )
            extra_inputs = {
                "frames_to_test": frames,
                "frame_notes": frame_notes,
            }

        elif active_mode == "Design Validation":
            st.markdown(
                "Surfaces all known measurement issues for this question's construct "
                "and checks whether the question design follows best-practice rules "
                "from our survey methodology guide."
            )
            validation_notes = st.text_area(
                "Specific concern or context (optional)",
                height=80,
                placeholder="e.g. This question has low fertility score — not sure if it's real low support or a scoring artifact.",
                key="qr_val_notes",
            )
            extra_inputs = {"validation_notes": validation_notes}

        # ── GENERATE BRIEF ─────────────────────────────────────────

        gen_btn = st.button(
            f"📋 Generate {active_mode} Brief",
            type="primary",
            key="qr_gen_btn",
        )

        if gen_btn:
            brief_parts = []
            brief_parts.append(f"QUESTION REWRITER BRIEF — {active_mode.upper()}")
            brief_parts.append("=" * 60)
            brief_parts.append("")

            # Question block
            brief_parts.append("SOURCE QUESTION:")
            brief_parts.append(f'"{selected_qtext}"')
            brief_parts.append("")
            if selected_construct:
                construct_label = CONSTRUCT_LABELS.get(selected_construct, selected_construct)
                brief_parts.append(f"CONSTRUCT: {construct_label} ({selected_construct})")
                brief_parts.append(f"PERSUASION TIER: {selected_tier or 'Unclassified'}")
            if is_library_q and selected_pct is not None:
                brief_parts.append(f"OVERALL SUPPORT: {round(selected_pct)}%")
                if selected_r_pct is not None:
                    brief_parts.append(f"REPUBLICAN SUPPORT: {round(selected_r_pct)}%")
                if selected_d_pct is not None:
                    brief_parts.append(f"DEMOCRAT SUPPORT: {round(selected_d_pct)}%")
                if selected_r_pct is not None and selected_d_pct is not None:
                    gap = selected_d_pct - selected_r_pct
                    brief_parts.append(f"D-R GAP: {gap:+.1f}pts")
            brief_parts.append("")

            # Known design issues from Airtable cache
            if INSIGHTS_AVAILABLE and selected_construct:
                relevant_insights = get_insights_for_constructs([selected_construct], status_filter="Open")
                if relevant_insights:
                    brief_parts.append("KNOWN DESIGN ISSUES (from Survey Design Insights database):")
                    for ins in relevant_insights:
                        brief_parts.append(f"  [{ins['priority']}] {ins['insight']}")
                        brief_parts.append(f"    → {ins['recommended_action'][:200]}")
                    brief_parts.append("")

            # Mode-specific instructions
            if active_mode == "Scale Standardization":
                brief_parts.append("TASK: SCALE STANDARDIZATION")
                brief_parts.append(f"Current scale type: {extra_inputs['current_scale']}")
                brief_parts.append(f"Target direction: {extra_inputs['scale_direction']}")
                not_sure = "Include 'Not sure / No opinion'" if extra_inputs["include_not_sure"] else "Do not include 'Not sure'"
                brief_parts.append(f"Not sure option: {not_sure}")
                brief_parts.append("")
                brief_parts.append("Please do the following:")
                brief_parts.append("1. Rewrite the question stem so it works naturally with the new scale.")
                brief_parts.append("2. Provide the full response option list in the standard format.")
                brief_parts.append("3. Note any wording changes needed to avoid double-barreled phrasing.")
                brief_parts.append("4. Flag if the new format creates leading-question risks.")
                brief_parts.append("5. Provide a short explanation of why this scale is preferred over the current one.")

            elif active_mode == "Audience Adaptation":
                brief_parts.append("TASK: AUDIENCE ADAPTATION")
                brief_parts.append(f"Target state: {extra_inputs['target_state']}")
                brief_parts.append(f"Audience lean: {extra_inputs['target_party']}")
                if extra_inputs["target_demo"]:
                    brief_parts.append(f"Specific demographic: {extra_inputs['target_demo']}")
                if extra_inputs["state_context"]:
                    brief_parts.append(f"State/local context: {extra_inputs['state_context']}")
                brief_parts.append("")
                brief_parts.append("Please do the following:")
                brief_parts.append("1. Rewrite the question so it resonates specifically with the target audience.")
                brief_parts.append("2. Avoid language that triggers partisan identity reactions.")
                brief_parts.append("3. Incorporate relevant state-specific context if provided.")
                brief_parts.append("4. Produce 2-3 alternative versions for A/B consideration.")
                brief_parts.append("5. Note any words or phrases to avoid for this audience based on known partisan patterns.")

            elif active_mode == "Framing Shift":
                brief_parts.append("TASK: FRAMING SHIFT")
                brief_parts.append(f"Frames to test: {', '.join(extra_inputs['frames_to_test'])}")
                if extra_inputs["frame_notes"]:
                    brief_parts.append(f"Current framing problem: {extra_inputs['frame_notes']}")
                brief_parts.append("")
                brief_parts.append("Please do the following:")
                brief_parts.append("1. For each requested frame, rewrite the question using that frame's language.")
                brief_parts.append("2. Keep the underlying policy concept identical — only the lens changes.")
                brief_parts.append("3. Flag which frames are likely to reduce the partisan gap vs. maintain it.")
                brief_parts.append("4. Note any frames that risk backfiring (e.g. raising salience of opposition).")
                brief_parts.append("5. Recommend which version to field first based on our audience targeting logic.")

            elif active_mode == "Design Validation":
                brief_parts.append("TASK: DESIGN VALIDATION")
                if extra_inputs["validation_notes"]:
                    brief_parts.append(f"Specific concern: {extra_inputs['validation_notes']}")
                brief_parts.append("")
                brief_parts.append("Please do the following:")
                brief_parts.append("1. Identify any double-barreled, leading, or ambiguous language in the question.")
                brief_parts.append("2. Check whether the response scale matches the question stem logically.")
                brief_parts.append("3. Assess the 'reform direction' — is it clear which response is reform-aligned?")
                brief_parts.append("4. Flag any known issues from the design insights database above.")
                brief_parts.append("5. Provide a revised version that corrects identified issues.")
                brief_parts.append("6. Rate severity of any problems found: Critical / Minor / Style only.")

            brief_parts.append("")
            brief_parts.append("─" * 40)
            brief_parts.append("Take this brief to the AI Analysis page and paste it into the chat.")

            brief_text = "\n".join(brief_parts)

            st.info(
                "📋 Brief generated. Copy and paste into the **AI Analysis** page chat "
                "to get rewritten questions."
            )
            with st.expander("Your Rewriter Brief (copy to AI Analysis chat)", expanded=True):
                st.code(brief_text, language=None)

# ─────────────────────────────────────────────────────────────────
# METHODOLOGY QUICK REFERENCE
# ─────────────────────────────────────────────────────────────────

with st.expander("Question Design Quick Reference", expanded=False):
    st.markdown(f"""
#### Scale Standardization Rules
Always use **Strongly support / Somewhat support / Somewhat oppose / Strongly oppose** for policy
questions. For agree/disagree: **Strongly agree / Somewhat agree / Somewhat disagree / Strongly
disagree**. Optionally add **Not sure / No opinion** as a final option. Never use bare
"Support/Oppose" without the intensity prefix — it caused scoring bugs in prior waves (Bug 1 + Bug 2).

#### Framing Principles
- **Bipartisan framing beats partisan framing.** If D-R gap > 15pts, the framing is triggering
  party identity. Test safety or fiscal frames instead.
- **Concrete beats abstract.** "Someone who has served 20 years" beats "long-term offender."
- **Avoid trigger words.** "Smart on crime" has a D-R gap of +22.6pts. Find neutral language.

#### Scale Type and Fertility
Binary questions (Yes/No) leave intensity unknown — fertility range spans 2x.
Full 4-point Likert closes that range. The constructs with the biggest fertility
uncertainty (PROP, FIRSTAPPEAR, LIT, CONDITIONS) all use binary questions.
Adding a single Likert item per construct would resolve strategic posture.

#### Reform Direction Tagging
Every new question must be tagged with its reform direction at design time
(which answer is "reform-aligned"?). The REFORM_DIRECTION table in content_scoring.py
is the canonical reference. Don't derive direction from partisan signal after fielding —
that method fails on low-partisan-gap questions like DV.

#### Avoid These Designs
- Multi-choice / ranking questions (unscorable in current pipeline)
- Knowledge-test items (increases dropout, contaminates support measures)
- Aspirational intent questions ("Would you vote for...?") — use behavioral past-action
- Double-barreled questions ("Do you support X and Y?")
""")

# ─────────────────────────────────────────────────────────────────
# FOOTER
# ─────────────────────────────────────────────────────────────────

portal_footer()
render_chat()
