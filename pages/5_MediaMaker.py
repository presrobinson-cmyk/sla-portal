"""
MediaMaker — Evidence-Based Message Guidance
Campaign message generation powered by Actionable Intel research.
Words That Work / Words to Avoid + Persuasion Framework Box.
Phase 1 (Apr 13 2026): Wired to live Supabase data — dynamic Data Anchors,
live audience targeting from party splits, cross-state variation panel,
and persuasion tier context.
"""

import streamlit as st
from pathlib import Path
from collections import defaultdict
import sys

# Auth gate
sys.path.insert(0, str(Path(__file__).parent.parent))
from theme import (
    apply_theme, portal_footer, data_source_badge, TIER_MAP, TIER_STYLES, SURVEY_STATE,
    NAVY, NAVY2, GOLD, GOLD_MID, TEXT1, TEXT2, TEXT3, BORDER2, BG, CARD_BG,
    GREEN, RED,
)
from auth import require_auth
from chat_widget import render_chat
from data_loader import (
    render_data_source_toggle, get_display_pct,
    load_question_data_hybrid, load_party_splits, load_mrp_question_summary,
)
from creative_system import (
    REGISTERS, RULES, RULE1_VARIANTS, PRINCIPLES, STRUCTURAL_MOVES, PRODUCTION_DOCTRINE,
    FORMAT_TV_30, FORMAT_TV_60, FORMAT_RADIO_30, FORMAT_RADIO_60,
    FORMAT_DIGITAL_30, FORMAT_CORPORATE, ALL_FORMATS,
    get_registers_for_format, get_rule1_variant, get_register_display_list,
    validate_script, get_required_moves_for_register, get_structural_move,
)

try:
    from content_scoring import get_construct, SKIPPED_QIDS
    SCORING_AVAILABLE = True
except ImportError:
    SCORING_AVAILABLE = False

try:
    from script_generator import build_prompt, generate_script, flag_rule_violations, FORMAT_WORD_COUNTS
    GENERATOR_AVAILABLE = True
except ImportError:
    GENERATOR_AVAILABLE = False

try:
    import anthropic as _anthropic_module
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    def get_construct(qid):
        return None
    SKIPPED_QIDS = set()

st.set_page_config(
    page_title="MediaMaker — SLA Portal",
    page_icon="📢",
    layout="wide",
)

apply_theme()
username = require_auth("Second Look Alliance", accent_color=GOLD)

# ─────────────────────────────────────────────────────────────────
# CONSTRUCT LABELS & GAUGE CONSTRUCTS
# ─────────────────────────────────────────────────────────────────

CONSTRUCT_LABELS = {
    "PD_FUNDING": "Public Defender Funding",
    "INVEST": "Community Investment",
    "LIT": "Literacy Programs",
    "COUNSEL_ACCESS": "Right to Counsel",
    "DV": "Domestic Violence",
    "CAND-DV": "Candidates on DV",
    "PROP": "Property Crime Reform",
    "REDEMPTION": "Redemption / Second Chances",
    "EXPUNGE": "Record Expungement",
    "SENTREVIEW": "Sentence Review",
    "JUDICIAL": "Judicial Discretion",
    "RETRO": "Retroactive Relief",
    "FINES": "Fines & Fees",
    "MAND": "Mandatory Minimums",
    "BAIL": "Bail Reform",
    "REENTRY": "Reentry Programs",
    "RECORD": "Criminal Record Reform",
    "JUV": "Juvenile Justice",
    "FAMILY": "Family Reunification",
    "ELDERLY": "Compassionate Release",
    "COURT": "Court Reform",
    "COURTREVIEW": "Court Review Process",
    "TRUST": "System Trust",
    "PLEA": "Plea Bargaining Reform",
    "PROS": "Prosecutor Accountability",
    "DETER": "Deterrence Beliefs",
    "FISCAL": "Fiscal Responsibility",
    "DP_ABOLITION": "Death Penalty Abolition",
    "DP_RELIABILITY": "Death Penalty Reliability",
    "LWOP": "Life Without Parole Reform",
}

GAUGE_CONSTRUCTS = {"CAND", "TOUGHCRIME", "ISSUE_SALIENCE", "IMPACT"}

# ─────────────────────────────────────────────────────────────────
# WORDS THAT WORK / WORDS TO AVOID MAP
# ─────────────────────────────────────────────────────────────────

WORDS_MAP = {
    "PD_FUNDING": {
        "work": [
            "Every American deserves a fair trial",
            "Underfunded public defenders",
            "Constitutional right to counsel",
            "Justice system integrity",
            "Level playing field",
        ],
        "avoid": [
            "Free lawyers for criminals",
            "Taxpayer-funded defense for bad guys",
            "Soft on crime",
            "Rewarding criminals",
        ],
    },
    "INVEST": {
        "work": [
            "Invest in safer communities",
            "Prevention saves money",
            "Evidence-based programs",
            "Break the cycle",
            "Community healing",
        ],
        "avoid": [
            "Defund police",
            "Social spending on criminals",
            "Government handouts",
            "Throwing money at the problem",
        ],
    },
    "DV": {
        "work": [
            "Victims trapped in violent homes",
            "Courts failing abuse survivors",
            "Circumstances matter",
            "Holding the real abuser accountable",
            "Protecting the vulnerable",
        ],
        "avoid": [
            "Excuses for crime",
            "Get-out-of-jail-free card",
            "Playing the victim card",
            "Blaming the victim",
        ],
    },
    "REDEMPTION": {
        "work": [
            "People can change",
            "Earned second chances",
            "Productive taxpaying citizens",
            "Proven by the evidence",
            "Rehabilitation works",
        ],
        "avoid": [
            "Letting criminals loose",
            "Coddling offenders",
            "Easy on crime",
            "No consequences",
        ],
    },
    "EXPUNGE": {
        "work": [
            "Clean slate for those who earned it",
            "Remove barriers to employment",
            "Reduce recidivism",
            "Taxpayer savings",
            "Second chances that work",
        ],
        "avoid": [
            "Erasing criminal history",
            "Hiding past crimes",
            "No accountability",
            "Pretend it never happened",
        ],
    },
    "SENTREVIEW": {
        "work": [
            "Review outdated sentences",
            "Proportional punishment",
            "Judicial oversight",
            "Correcting injustice",
            "Fairness in sentencing",
        ],
        "avoid": [
            "Letting prisoners go free",
            "Overturning verdicts",
            "Ignoring victims",
            "Criminals getting away with it",
        ],
    },
    "BAIL": {
        "work": [
            "Innocent until proven guilty",
            "Risk-based release",
            "Don't punish poverty",
            "Taxpayer costs of pretrial detention",
            "Fair bail system",
        ],
        "avoid": [
            "Free bail for everyone",
            "Open the jailhouse doors",
            "No consequences before trial",
            "Criminals back on the streets",
        ],
    },
    "MAND": {
        "work": [
            "Let judges judge",
            "Case-by-case justice",
            "One size doesn't fit all",
            "Judicial discretion",
            "Individual circumstances matter",
        ],
        "avoid": [
            "Soft sentences",
            "Weak on crime",
            "Judge shopping",
            "No standards",
        ],
    },
    "JUDICIAL": {
        "work": [
            "Judges know their communities",
            "Justice requires flexibility",
            "Context matters",
            "Fair and reasoned decisions",
            "Trust in our courts",
        ],
        "avoid": [
            "Judges letting criminals off",
            "No accountability",
            "Inconsistent sentences",
            "Politicizing the courts",
        ],
    },
    "REENTRY": {
        "work": [
            "Successful reentry reduces crime",
            "Employment = stability",
            "Supporting those who've paid their debt",
            "Evidence-based pathways",
            "Building productive lives",
        ],
        "avoid": [
            "Coddling released prisoners",
            "Wasting tax dollars",
            "No consequences",
            "Soft approach to crime",
        ],
    },
}

# ─────────────────────────────────────────────────────────────────
# MESSAGE FRAMEWORK MAP
# frame / inoculation / cta are strategic guidance — static.
# data field is now generated live from MrP numbers (see get_data_anchor_text).
# Hardcoded data strings kept as fallback for constructs without live coverage.
# ─────────────────────────────────────────────────────────────────

FRAMEWORK_MAP = {
    "PD_FUNDING": {
        "data_fallback": "82% of voters — including strong majorities of Republicans — support adequate funding for public defenders.",
        "frame": "Constitutional rights frame: this is about the 6th Amendment working as intended, not expanding government.",
        "inoculation": "Opponents say this is 'more spending.' Counter: underfunded defense costs MORE through wrongful convictions and appeals.",
        "cta": "Support adequate public defender funding in your state.",
    },
    "DV": {
        "data_fallback": "65% of the most anti-reform voters agree that domestic violence should be considered a mitigating factor in sentencing.",
        "frame": "Mitigating circumstances frame: courts should consider WHY someone committed a crime, especially abuse victims.",
        "inoculation": "Opponents say this 'excuses crime.' Counter: recognizing DV as a factor IS part of proportional justice.",
        "cta": "Advocate for DV-informed sentencing guidelines.",
    },
    "REDEMPTION": {
        "data_fallback": "53% of reform skeptics believe people can earn a second chance — the key persuasion bridge.",
        "frame": "Earned redemption frame: focus on demonstrated change, not automatic forgiveness.",
        "inoculation": "Opponents say 'once a criminal, always a criminal.' Counter: decades of evidence show people change, and reentry programs reduce crime.",
        "cta": "Support evidence-based reentry and second-chance programs.",
    },
    "EXPUNGE": {
        "data_fallback": "60% of voters support clearing records for people who have served their time and stayed out of trouble.",
        "frame": "Clean slate frame: removing barriers to employment, housing, and education reduces recidivism.",
        "inoculation": "Opponents say records are 'forever evidence.' Counter: expungement is only for those who've earned it, not automatic.",
        "cta": "Support earned record expungement in your state.",
    },
    "BAIL": {
        "data_fallback": "71% of voters believe bail should be based on flight risk and danger, not ability to pay.",
        "frame": "Constitutional fairness frame: money shouldn't be the only way to get out of jail before trial.",
        "inoculation": "Opponents say 'criminals will flee.' Counter: risk-based systems are more effective at preventing both.",
        "cta": "Advocate for risk-based bail reform.",
    },
    "SENTREVIEW": {
        "data_fallback": "68% of voters support judicial review of disproportionately long sentences.",
        "frame": "Judicial oversight frame: letting judges review and adjust outdated sentences.",
        "inoculation": "Opponents say this 'overturns justice.' Counter: proportionality is fundamental to any fair system.",
        "cta": "Support sentence review and proportionality reforms.",
    },
    "MAND": {
        "data_fallback": "64% of voters believe judges should have flexibility to consider individual circumstances.",
        "frame": "Justice flexibility frame: one size doesn't fit all; judges are trained to make these decisions.",
        "inoculation": "Opponents say 'crime needs one standard.' Counter: sentencing guidelines provide structure while allowing flexibility.",
        "cta": "Support reducing mandatory minimum sentences.",
    },
    "INVEST": {
        "data_fallback": "73% of voters support investing in prevention and treatment programs.",
        "frame": "Proven prevention frame: programs that work save money and prevent future crime.",
        "inoculation": "Opponents say 'government shouldn't fund criminals.' Counter: prevention programs aren't for offenders, they're for communities.",
        "cta": "Invest in evidence-based prevention and reentry programs.",
    },
}

# ─────────────────────────────────────────────────────────────────
# SUGGESTED TARGET AUDIENCE — fallback when party splits unavailable
# ─────────────────────────────────────────────────────────────────

SUGGESTED_AUDIENCE_FALLBACK = {
    "PD_FUNDING": "State legislators",
    "INVEST": "General public",
    "LIT": "General public",
    "COUNSEL_ACCESS": "State legislators",
    "DV": "Republican persuadables",
    "COMPASSION": "Republican persuadables",
    "FINES": "Independent / swing voters",
    "CAND-DV": "Republican persuadables",
    "PROP": "Independent / swing voters",
    "REDEMPTION": "Independent / swing voters",
    "EXPUNGE": "Grassroots advocates / organizers",
    "SENTREVIEW": "State legislators",
    "JUDICIAL": "State legislators",
    "RETRO": "Grassroots advocates / organizers",
    "MAND": "Independent / swing voters",
    "BAIL": "Local media / editorial boards",
    "REENTRY": "Donors and funders",
    "RECORD": "Independent / swing voters",
    "JUV": "General public",
    "FAMILY": "Democratic base (mobilization)",
    "ELDERLY": "Republican persuadables",
    "COURT": "State legislators",
    "TRUST": "General public",
    "PLEA": "Local media / editorial boards",
    "PROS": "Grassroots advocates / organizers",
}

AUDIENCE_RATIONALE = {
    "General public": "Broad bipartisan support — wide distribution works across the political spectrum.",
    "Republican persuadables": "Live polling shows significant Republican movement on this topic. Target moderate Republicans and conservative-leaning independents.",
    "Democratic base (mobilization)": "Strong Democratic support with limited Republican persuadability — use for turnout and mobilization, not persuasion.",
    "Independent / swing voters": "This topic is a swing-voter wedge. Focus on voters who haven't formed strong opinions yet.",
    "State legislators": "High bipartisan support makes this ripe for legislative action. Lead with the numbers.",
    "Local media / editorial boards": "This topic benefits from earned media. Frame for journalists and opinion writers.",
    "Grassroots advocates / organizers": "Use this topic to energize organizing efforts and coalition-building.",
    "Donors and funders": "Strong evidence base makes this a compelling investment case for reform funders.",
}

# ─────────────────────────────────────────────────────────────────
# PERSUASION PATHWAY — tier context + sequential relationships
# ─────────────────────────────────────────────────────────────────

TIER_ROLE = {
    "Entry": "Opens the door. Broadest bipartisan appeal — establish these before moving to Bridge or Downstream.",
    "Entry (VA)": "VA-specific Entry topic. Functions as an Entry topic in Virginia surveys; Bridge tier in other states.",
    "Bridge": "Opens persuadable audiences to reform. Requires Entry foundation. Unlocks Downstream positions.",
    "Downstream": "Requires setup. Lead with Entry and Bridge topics first to build the persuasion pathway.",
    "Destination": "Significant headwinds. Only after extensive Entry and Bridge groundwork.",
    "Gauge": "Measures baseline attitudes — not a primary persuasion vehicle.",
}

# What topics to establish BEFORE this one
PATHWAY_PREREQS = {
    "PD_FUNDING": [], "INVEST": [], "LIT": [], "COUNSEL_ACCESS": [],
    "DV": ["PD_FUNDING", "INVEST", "LIT"],
    "COMPASSION": ["PD_FUNDING", "INVEST"],
    "FINES": ["INVEST", "LIT"],
    "CAND-DV": ["DV"],
    "PROP": ["PD_FUNDING", "INVEST"],
    "REDEMPTION": ["DV", "COMPASSION"],
    "EXPUNGE": ["REDEMPTION"],
    "SENTREVIEW": ["EXPUNGE", "REDEMPTION"],
    "BAIL": ["PD_FUNDING", "INVEST"],
    "MAND": ["INVEST", "DV"],
    "REENTRY": ["REDEMPTION"],
    "RECORD": ["EXPUNGE"],
    "JUV": ["INVEST", "LIT"],
    "FAMILY": ["REDEMPTION"],
    "ELDERLY": ["COMPASSION", "REDEMPTION"],
    "COURT": ["PD_FUNDING", "INVEST"],
    "COURTREVIEW": ["PD_FUNDING", "INVEST"],
    "PLEA": ["PD_FUNDING", "JUDICIAL"],
    "PROS": ["INVEST", "PD_FUNDING"],
    "RETRO": ["SENTREVIEW", "EXPUNGE"],
    "JUDICIAL": ["PD_FUNDING", "INVEST"],
    "TRUST": ["PD_FUNDING", "REDEMPTION"],
    "LWOP": ["SENTREVIEW", "REDEMPTION"],
}

# What topics this one helps unlock
PATHWAY_UNLOCKS = {
    "PD_FUNDING": ["DV", "COMPASSION", "BAIL", "COURT", "JUDICIAL"],
    "INVEST": ["DV", "FINES", "REDEMPTION", "REENTRY", "JUV"],
    "LIT": ["DV", "FINES", "JUV"],
    "COUNSEL_ACCESS": ["PD_FUNDING"],
    "DV": ["CAND-DV", "REDEMPTION", "COMPASSION"],
    "COMPASSION": ["REDEMPTION", "EXPUNGE", "ELDERLY"],
    "FINES": ["BAIL"],
    "CAND-DV": [],
    "PROP": ["REDEMPTION"],
    "REDEMPTION": ["EXPUNGE", "REENTRY", "FAMILY"],
    "EXPUNGE": ["SENTREVIEW", "RECORD"],
    "SENTREVIEW": ["RETRO", "LWOP"],
    "BAIL": [], "MAND": [], "REENTRY": [], "RECORD": [],
    "JUV": [], "FAMILY": [], "ELDERLY": [],
    "COURT": ["PLEA"], "COURTREVIEW": [],
    "JUDICIAL": ["MAND", "PLEA"],
    "PLEA": [], "PROS": [], "RETRO": [], "TRUST": [], "LWOP": [],
}


# ─────────────────────────────────────────────────────────────────
# LIVE DATA HELPERS
# ─────────────────────────────────────────────────────────────────

@st.cache_data(ttl=3600, show_spinner=False)
def build_construct_summaries():
    """
    Aggregate question-level MrP + party data to construct level.
    Returns {construct: {mrp_pct, raw_pct, r_pct, d_pct, n}}.
    """
    question_data, _ = load_question_data_hybrid()
    party_data = load_party_splits()

    c_mrp = defaultdict(list)   # (pct, n) for weighted avg
    c_raw = defaultdict(list)
    c_n = defaultdict(int)
    c_r = defaultdict(list)
    c_d = defaultdict(list)

    for qid, qd in question_data.items():
        construct = qd.get("construct")
        if not construct:
            continue
        n = max(qd.get("n_respondents", 0) or 1, 1)
        if qd.get("mrp_pct") is not None:
            c_mrp[construct].append((qd["mrp_pct"], n))
        if qd.get("raw_pct") is not None:
            c_raw[construct].append((qd["raw_pct"], n))
        c_n[construct] += n
        if qid in party_data:
            pd = party_data[qid]
            if pd.get("r_pct") is not None:
                c_r[construct].append(pd["r_pct"])
            if pd.get("d_pct") is not None:
                c_d[construct].append(pd["d_pct"])

    def wavg(pairs):
        if not pairs:
            return None
        total_n = sum(n for _, n in pairs)
        if total_n == 0:
            return sum(v for v, _ in pairs) / len(pairs)
        return sum(v * n for v, n in pairs) / total_n

    result = {}
    for construct in set(c_mrp) | set(c_raw):
        r_vals = c_r.get(construct, [])
        d_vals = c_d.get(construct, [])
        result[construct] = {
            "mrp_pct": wavg(c_mrp.get(construct, [])),
            "raw_pct": wavg(c_raw.get(construct, [])),
            "r_pct": sum(r_vals) / len(r_vals) if r_vals else None,
            "d_pct": sum(d_vals) / len(d_vals) if d_vals else None,
            "n": c_n.get(construct, 0),
        }
    return result


@st.cache_data(ttl=3600, show_spinner=False)
def build_construct_state_summaries():
    """
    Build {construct: {state: avg_mrp_pct}} from mrp_question_summary.
    Used for the cross-state variation panel.
    """
    mrp_data, _ = load_mrp_question_summary()
    c_state = defaultdict(lambda: defaultdict(list))
    for (sid, qid), row in mrp_data.items():
        if qid in SKIPPED_QIDS:
            continue
        construct = get_construct(qid)
        if not construct:
            continue
        # state field in mrp_question_summary; fall back to SURVEY_STATE
        state = row.get("state") or SURVEY_STATE.get(sid, "")
        if not state:
            continue
        mrp_pct = row.get("mrp_pct")
        if mrp_pct is not None:
            c_state[construct][state].append(mrp_pct)

    result = {}
    for construct, state_dict in c_state.items():
        result[construct] = {
            s: sum(v) / len(v)
            for s, v in state_dict.items()
            if v
        }
    return result


def get_dynamic_audience(construct, summaries):
    """
    Compute suggested audience from live party splits.
    Logic from carry doc:
      R>60 AND D>60 → General public
      D-R gap >20  → Democratic base
      R 40-60      → Republican persuadables
      else         → Independent / swing voters
    Falls back to SUGGESTED_AUDIENCE_FALLBACK if no party data.
    """
    cs = summaries.get(construct, {})
    r_pct = cs.get("r_pct")
    d_pct = cs.get("d_pct")
    if r_pct is None or d_pct is None:
        return SUGGESTED_AUDIENCE_FALLBACK.get(construct, "General public")
    if r_pct >= 60 and d_pct >= 60:
        return "General public"
    if d_pct - r_pct >= 20:
        return "Democratic base (mobilization)"
    if 40 <= r_pct < 60:
        return "Republican persuadables"
    return "Independent / swing voters"


def get_data_anchor_text(construct, summaries, mode):
    """
    Return a live Data Anchor string built from MrP/raw pct.
    Falls back to hardcoded string in FRAMEWORK_MAP.
    """
    cs = summaries.get(construct, {})
    pct = get_display_pct(cs, mode) if cs else None
    if pct is not None:
        pct_int = round(pct)
        label = CONSTRUCT_LABELS.get(construct, construct.replace("_", " ").title()).lower()
        r_pct = cs.get("r_pct")
        r_note = ""
        if r_pct is not None and r_pct >= 55:
            r_note = " — including significant Republican support"
        elif r_pct is not None and r_pct >= 45:
            r_note = " — with notable Republican crossover"
        return f"{pct_int}% of voters support {label}{r_note}."
    # fallback to hardcoded
    if construct in FRAMEWORK_MAP:
        return FRAMEWORK_MAP[construct].get("data_fallback")
    return None


# ─────────────────────────────────────────────────────────────────
# PAGE HEADER
# ─────────────────────────────────────────────────────────────────

st.title("MediaMaker")
data_mode = render_data_source_toggle()
data_source_badge(data_mode)

st.markdown(f"""
<div style="background:{CARD_BG};border:1px solid {BORDER2};border-radius:10px;padding:1.25rem;
     margin-bottom:1rem;box-shadow:0 1px 3px rgba(0,0,0,0.04);">
    <div style="font-size:0.95rem;color:{TEXT1};line-height:1.7;">
        <strong>How MediaMaker works:</strong> Pick a reform topic and MediaMaker pulls from our
        live MrP-adjusted polling data to show you what language resonates and what backfires.
        Each topic has a <strong>Data Anchor</strong> (the live number that opens the door),
        a <strong>Strategic Frame</strong> (how to position it), an <strong>Inoculation</strong>
        (the attack line and your counter), and a <strong>Call to Action</strong>.
    </div>
    <div style="font-size:0.85rem;color:{TEXT2};margin-top:0.5rem;">
        In Step 4, paste in a bill, news article, or list of spokespeople — MediaMaker
        will combine your source materials with the polling guidance to generate a tailored brief
        you can take to the AI Analysis page for final content.
    </div>
</div>
""", unsafe_allow_html=True)

st.divider()

# ─────────────────────────────────────────────────────────────────
# LOAD LIVE DATA (cached — fast after first load)
# ─────────────────────────────────────────────────────────────────

with st.spinner("Loading live polling data…"):
    construct_summaries = build_construct_summaries()
    construct_state_data = build_construct_state_summaries()

# ─────────────────────────────────────────────────────────────────
# STEP 1: TOPIC PICKER
# ─────────────────────────────────────────────────────────────────

st.markdown(f"""
<div style="font-family:'Playfair Display',serif;font-size:1.15rem;font-weight:700;color:{NAVY};
     margin-bottom:0.5rem;">Step 1: Pick Your Reform Topic</div>
<div style="font-size:0.88rem;color:{TEXT2};margin-bottom:0.75rem;">
    Choose the issue you want to build messaging around. The guidance below will update automatically.
</div>
""", unsafe_allow_html=True)

# Filter out gauge constructs
topic_options = {k: v for k, v in CONSTRUCT_LABELS.items() if k not in GAUGE_CONSTRUCTS}
sorted_topics = sorted(topic_options.items(), key=lambda x: x[1])
topic_labels_list = [label for _, label in sorted_topics]
label_to_code = {label: code for code, label in sorted_topics}

selected_label = st.selectbox(
    "Reform topic:",
    options=topic_labels_list,
    key="topic_picker",
)
selected_construct = label_to_code.get(selected_label, "")
selected_tier = TIER_MAP.get(selected_construct, "Unknown")

# Topic + tier row
tier_style = TIER_STYLES.get(selected_tier, {})
tier_bg = tier_style.get("bg", "rgba(0,0,0,0.04)")
tier_color = tier_style.get("color", TEXT2)
tier_border = tier_style.get("border", BORDER2)

# Live summary for selected construct
cs = construct_summaries.get(selected_construct, {})
live_pct = get_display_pct(cs, data_mode) if cs else None
r_pct = cs.get("r_pct")
d_pct = cs.get("d_pct")

# Build stat chips
stat_parts = []
if live_pct is not None:
    pct_label = "MrP" if data_mode == "mrp" else "Raw"
    stat_parts.append(
        f'<span style="background:rgba(14,31,61,0.08);padding:2px 10px;border-radius:12px;'
        f'font-size:0.82rem;color:{NAVY};font-weight:600;">Overall: {round(live_pct)}% ({pct_label})</span>'
    )
if r_pct is not None:
    stat_parts.append(
        f'<span style="background:rgba(139,26,26,0.08);padding:2px 10px;border-radius:12px;'
        f'font-size:0.82rem;color:#8B1A1A;font-weight:600;">R: {round(r_pct)}%</span>'
    )
if d_pct is not None:
    stat_parts.append(
        f'<span style="background:rgba(17,85,170,0.08);padding:2px 10px;border-radius:12px;'
        f'font-size:0.82rem;color:#1155AA;font-weight:600;">D: {round(d_pct)}%</span>'
    )
stats_html = " ".join(stat_parts)

st.markdown(f"""
<div style="display:flex;flex-wrap:wrap;gap:12px;align-items:center;margin:0.75rem 0;">
    <div style="background:{tier_bg};border:1px solid {tier_border};border-radius:20px;
         padding:3px 14px;font-size:0.85rem;font-weight:600;color:{tier_color};">
        {selected_tier} tier
    </div>
    {stats_html}
</div>
""", unsafe_allow_html=True)

st.divider()

# ─────────────────────────────────────────────────────────────────
# PERSUASION TIER CONTEXT PANEL (Step 1.5)
# ─────────────────────────────────────────────────────────────────

prereqs = PATHWAY_PREREQS.get(selected_construct, [])
unlocks = PATHWAY_UNLOCKS.get(selected_construct, [])
tier_role = TIER_ROLE.get(selected_tier, "")

prereq_labels = [CONSTRUCT_LABELS.get(c, c) for c in prereqs if c in CONSTRUCT_LABELS]
unlock_labels = [CONSTRUCT_LABELS.get(c, c) for c in unlocks if c in CONSTRUCT_LABELS]

prereq_html = ""
if prereq_labels:
    chips = "".join([
        f'<span style="display:inline-block;background:rgba(14,31,61,0.07);border:1px solid {BORDER2};'
        f'border-radius:12px;padding:2px 10px;font-size:0.8rem;color:{TEXT2};margin:2px 3px;">'
        f'{lbl}</span>'
        for lbl in prereq_labels
    ])
    prereq_html = f"""
    <div style="margin-top:0.6rem;">
        <span style="font-size:0.8rem;color:{TEXT3};font-weight:600;text-transform:uppercase;
              letter-spacing:0.04em;">Build these first:</span>
        <div style="margin-top:4px;">{chips}</div>
    </div>"""

unlock_html = ""
if unlock_labels:
    chips = "".join([
        f'<span style="display:inline-block;background:rgba(27,107,58,0.07);border:1px solid rgba(27,107,58,0.2);'
        f'border-radius:12px;padding:2px 10px;font-size:0.8rem;color:#1B6B3A;margin:2px 3px;">'
        f'{lbl}</span>'
        for lbl in unlock_labels
    ])
    unlock_html = f"""
    <div style="margin-top:0.6rem;">
        <span style="font-size:0.8rem;color:{TEXT3};font-weight:600;text-transform:uppercase;
              letter-spacing:0.04em;">This unlocks:</span>
        <div style="margin-top:4px;">{chips}</div>
    </div>"""

if tier_role or prereq_html or unlock_html:
    st.markdown(f"""
    <div style="background:{tier_bg};border:1px solid {tier_border};border-radius:10px;
         padding:1rem 1.25rem;margin-bottom:1rem;">
        <div style="font-weight:700;color:{tier_color};font-size:0.9rem;margin-bottom:0.3rem;">
            📍 Persuasion Pathway — {selected_tier}
        </div>
        <div style="font-size:0.88rem;color:{TEXT2};line-height:1.6;">{tier_role}</div>
        {prereq_html}
        {unlock_html}
    </div>
    """, unsafe_allow_html=True)

st.divider()

# ─────────────────────────────────────────────────────────────────
# STEP 2: FORMAT & REGISTER PICKER
# ─────────────────────────────────────────────────────────────────

st.markdown(f"""
<div style="font-family:'Playfair Display',serif;font-size:1.15rem;font-weight:700;color:{NAVY};
     margin-bottom:0.5rem;">Step 2: Pick Your Format & Register</div>
<div style="font-size:0.88rem;color:{TEXT2};margin-bottom:0.75rem;">
    Format determines the medium. Register is the creative approach within that format.
    Each register has proven structural patterns — choose the one that matches your goal.
</div>
""", unsafe_allow_html=True)

format_col, reg_col = st.columns([1, 2])

with format_col:
    FORMAT_DISPLAY = {
        FORMAT_TV_30: "📺 TV :30",
        FORMAT_TV_60: "📺 TV :60",
        FORMAT_RADIO_30: "📻 Radio :30",
        FORMAT_RADIO_60: "📻 Radio :60",
        FORMAT_DIGITAL_30: "📱 Digital :30/:15",
        FORMAT_CORPORATE: "🏢 Corporate Suite",
    }
    selected_format = st.selectbox(
        "Output format / medium:",
        options=ALL_FORMATS,
        format_func=lambda f: FORMAT_DISPLAY.get(f, f),
        key="mm_format_picker",
    )

    # Production doctrine note for selected format
    doctrine_notes = {
        FORMAT_TV_30: ("C", "TV defaults to :30 — the right length for most arguments."),
        FORMAT_TV_60: ("C", "Use :60 only when the register specifically requires the depth."),
        FORMAT_RADIO_30: ("E", "Radio :30 is for jingle/ID work — not argument work. Consider :60."),
        FORMAT_RADIO_60: ("E", "Radio :60 is almost always the better investment."),
        FORMAT_DIGITAL_30: ("B,F", "Audio-off first. Two-Second Rule: hook in ≤2 seconds."),
        FORMAT_CORPORATE: ("B", "Suite = multiple pieces. Audio-off applies to any digital piece."),
    }
    doc_key, doc_note = doctrine_notes.get(selected_format, ("", ""))
    if doc_note:
        st.markdown(f"""
        <div style="font-size:0.78rem;color:{TEXT3};padding:0.35rem 0.6rem;
             background:rgba(14,31,61,0.04);border-radius:6px;margin-top:0.3rem;">
            📋 <em>Doctrine {doc_key}:</em> {doc_note}
        </div>
        """, unsafe_allow_html=True)

with reg_col:
    format_regs = get_register_display_list(selected_format)
    if format_regs:
        reg_options = [f"{name} — {desc}" for code, name, desc in format_regs]
        reg_codes = [code for code, name, desc in format_regs]
        selected_reg_display = st.selectbox(
            "Creative register:",
            options=reg_options,
            key="mm_register_picker",
        )
        selected_reg_idx = reg_options.index(selected_reg_display)
        selected_reg_code = reg_codes[selected_reg_idx]
        selected_reg = REGISTERS.get(selected_reg_code, {})
    else:
        st.info("No registers defined for this format yet.")
        selected_reg_code = ""
        selected_reg = {}

# Show register detail panel
if selected_reg:
    chars = selected_reg.get("defining_characteristics", [])
    req_moves = selected_reg.get("required_moves", [])
    opt_moves = selected_reg.get("optional_moves", [])
    rule1_hint = selected_reg.get("rule1_hint", "")
    example = selected_reg.get("example_piece")
    notes = selected_reg.get("notes")

    chars_html = "".join([
        f'<li style="margin-bottom:4px;color:{TEXT1};font-size:0.87rem;">{c}</li>'
        for c in chars
    ])
    req_chips = "".join([
        f'<span style="display:inline-block;background:rgba(14,31,61,0.09);border-radius:10px;'
        f'padding:2px 10px;font-size:0.8rem;color:{NAVY};margin:2px 3px;">{m}</span>'
        for m in req_moves
    ])
    opt_chips = "".join([
        f'<span style="display:inline-block;background:rgba(14,31,61,0.04);border:1px solid {BORDER2};'
        f'border-radius:10px;padding:2px 10px;font-size:0.8rem;color:{TEXT2};margin:2px 3px;">{m}</span>'
        for m in opt_moves
    ])

    example_html = (
        f'<div style="font-size:0.8rem;color:{TEXT3};margin-top:0.5rem;">'
        f'<strong>Exemplar:</strong> {example}</div>'
    ) if example else ""
    notes_html = (
        f'<div style="font-size:0.8rem;color:{TEXT3};margin-top:0.4rem;'
        f'font-style:italic;">{notes}</div>'
    ) if notes else ""

    # Rule 1 variant
    r1v = get_rule1_variant(selected_reg_code)
    r1_name = r1v.get("name", "") if r1v else ""
    r1_desc = RULE1_VARIANTS.get(r1_name, {}).get("description", rule1_hint) if r1_name in RULE1_VARIANTS else rule1_hint
    r1_html = (
        f'<div style="margin-top:0.75rem;padding:0.6rem 0.75rem;'
        f'background:rgba(184,135,10,0.07);border-left:3px solid {GOLD};border-radius:0 6px 6px 0;">'
        f'<span style="font-size:0.78rem;font-weight:700;color:{GOLD};text-transform:uppercase;'
        f'letter-spacing:0.04em;">Rule 1 Concession — {r1_name}</span>'
        f'<div style="font-size:0.85rem;color:{TEXT2};margin-top:3px;">{r1_desc}</div>'
        f'</div>'
    ) if r1_name else ""

    # Silent Track badge for TV/Digital
    silent_badge = ""
    if selected_format in [FORMAT_TV_30, FORMAT_TV_60, FORMAT_DIGITAL_30]:
        silent_badge = (
            f'<span style="font-size:0.75rem;background:rgba(14,31,61,0.08);padding:2px 8px;'
            f'border-radius:10px;color:{NAVY};font-weight:600;margin-left:8px;">🔇 Silent Track applies</span>'
        )

    st.markdown(f"""
    <div style="background:{CARD_BG};border:1px solid {BORDER2};border-radius:10px;
         padding:1.25rem;margin-top:0.5rem;box-shadow:0 1px 3px rgba(0,0,0,0.04);">
        <div style="font-weight:700;color:{NAVY};font-size:0.95rem;margin-bottom:0.75rem;">
            {selected_reg.get('name', '')} {silent_badge}
        </div>
        <ul style="margin:0;padding-left:1.25rem;line-height:1.7;">{chars_html}</ul>
        <div style="margin-top:0.75rem;">
            <span style="font-size:0.78rem;font-weight:700;color:{TEXT3};text-transform:uppercase;
                  letter-spacing:0.04em;">Required moves:</span>
            <div style="margin-top:4px;">{req_chips or '<span style="font-size:0.82rem;color:{TEXT3};">None specified</span>'}</div>
        </div>
        {(f'<div style="margin-top:0.5rem;"><span style="font-size:0.78rem;font-weight:700;color:{TEXT3};text-transform:uppercase;letter-spacing:0.04em;">Optional moves:</span><div style="margin-top:4px;">{opt_chips}</div></div>') if opt_chips else ''}
        {r1_html}
        {example_html}
        {notes_html}
    </div>
    """, unsafe_allow_html=True)

st.markdown("")
st.divider()

# ─────────────────────────────────────────────────────────────────
# STEP 3: WORDS THAT WORK / WORDS TO AVOID (renumbered)
# ─────────────────────────────────────────────────────────────────

st.markdown("### Step 3: Words That Work / Words to Avoid")
st.markdown(
    "Use these phrases with persuadable audiences. Avoid phrases that trigger opposition or shut down conversation.",
    unsafe_allow_html=True,
)

st.markdown("")

if selected_construct in WORDS_MAP:
    words_data = WORDS_MAP[selected_construct]
    work_phrases = words_data.get("work", [])
    avoid_phrases = words_data.get("avoid", [])

    col_work, col_avoid = st.columns(2)

    with col_work:
        st.markdown(f"""
        <div style="
            background: rgba(27, 107, 58, 0.08);
            border-left: 5px solid #1B6B3A;
            border-radius: 8px;
            padding: 1.25rem;
            margin-bottom: 0;
        ">
            <div style="font-weight: 700; color: #1B6B3A; margin-bottom: 1rem; font-size: 1.05rem;">
                ✓ Words That Work
            </div>
            <div style="color: {TEXT1}; line-height: 1.8;">
        """, unsafe_allow_html=True)

        for phrase in work_phrases:
            st.markdown(f"- {phrase}")

        st.markdown("</div></div>", unsafe_allow_html=True)

    with col_avoid:
        st.markdown(f"""
        <div style="
            background: rgba(139, 26, 26, 0.08);
            border-left: 5px solid #8B1A1A;
            border-radius: 8px;
            padding: 1.25rem;
            margin-bottom: 0;
        ">
            <div style="font-weight: 700; color: #8B1A1A; margin-bottom: 1rem; font-size: 1.05rem;">
                ✗ Words to Avoid
            </div>
            <div style="color: {TEXT1}; line-height: 1.8;">
        """, unsafe_allow_html=True)

        for phrase in avoid_phrases:
            st.markdown(f"- {phrase}")

        st.markdown("</div></div>", unsafe_allow_html=True)

else:
    st.info(
        f"💡 Message testing data for **{selected_label}** is coming in the next survey wave. "
        "Check back soon for Words That Work and Words to Avoid.",
        icon="ℹ️",
    )

st.markdown("")
st.divider()

# ─────────────────────────────────────────────────────────────────
# STEP 3: MESSAGE FRAMEWORK — live Data Anchor + static guidance
# ─────────────────────────────────────────────────────────────────

st.markdown("### Step 4: Data Intelligence & Message Framework")
st.markdown(
    "This four-step framework shows how to structure persuasive messaging for this topic. "
    "The Data Anchor is pulled live from MrP-adjusted polling.",
    unsafe_allow_html=True,
)

st.markdown("")

# Get live data anchor
live_anchor = get_data_anchor_text(selected_construct, construct_summaries, data_mode)

has_framework = selected_construct in FRAMEWORK_MAP or live_anchor

if has_framework:
    framework = FRAMEWORK_MAP.get(selected_construct, {})

    # 1. Data Anchor — live from MrP
    anchor_text = live_anchor or framework.get("data_fallback", "")
    anchor_source = ""
    if live_anchor and cs:
        source_label = "MrP-Adjusted" if data_mode == "mrp" else "Raw Survey"
        anchor_source = (
            f'<span style="font-size:0.75rem;color:{TEXT3};margin-left:8px;">'
            f'({source_label} — live from database)</span>'
        )

    st.markdown(f"""
    <div style="
        background: {CARD_BG};
        border-left: 5px solid {NAVY};
        border-radius: 8px;
        padding: 1.25rem;
        margin-bottom: 1rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    ">
        <div style="font-weight: 700; color: {NAVY}; margin-bottom: 0.5rem; font-size: 1rem;">
            1. Data Anchor {anchor_source}
        </div>
        <div style="font-size: 0.95rem; color: {TEXT1}; line-height: 1.6;">
            {anchor_text}
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 2. Strategic Frame
    if framework.get("frame"):
        st.markdown(f"""
        <div style="
            background: {CARD_BG};
            border-left: 5px solid #0D7C7C;
            border-radius: 8px;
            padding: 1.25rem;
            margin-bottom: 1rem;
            box-shadow: 0 1px 3px rgba(0,0,0,0.04);
        ">
            <div style="font-weight: 700; color: #0D7C7C; margin-bottom: 0.5rem; font-size: 1rem;">
                2. Strategic Frame
            </div>
            <div style="font-size: 0.95rem; color: {TEXT1}; line-height: 1.6;">
                {framework['frame']}
            </div>
        </div>
        """, unsafe_allow_html=True)

    # 3. Inoculation
    if framework.get("inoculation"):
        st.markdown(f"""
        <div style="
            background: {CARD_BG};
            border-left: 5px solid {GOLD};
            border-radius: 8px;
            padding: 1.25rem;
            margin-bottom: 1rem;
            box-shadow: 0 1px 3px rgba(0,0,0,0.04);
        ">
            <div style="font-weight: 700; color: {GOLD}; margin-bottom: 0.5rem; font-size: 1rem;">
                3. Inoculation
            </div>
            <div style="font-size: 0.95rem; color: {TEXT1}; line-height: 1.6;">
                {framework['inoculation']}
            </div>
        </div>
        """, unsafe_allow_html=True)

    # 4. Call to Action
    if framework.get("cta"):
        st.markdown(f"""
        <div style="
            background: {CARD_BG};
            border-left: 5px solid #1B6B3A;
            border-radius: 8px;
            padding: 1.25rem;
            margin-bottom: 0;
            box-shadow: 0 1px 3px rgba(0,0,0,0.04);
        ">
            <div style="font-weight: 700; color: #1B6B3A; margin-bottom: 0.5rem; font-size: 1rem;">
                4. Call to Action
            </div>
            <div style="font-size: 0.95rem; color: {TEXT1}; line-height: 1.6;">
                {framework['cta']}
            </div>
        </div>
        """, unsafe_allow_html=True)

    # If only live anchor, no framework guidance yet
    if not framework:
        st.info(
            f"💡 Strategic frame and inoculation for **{selected_label}** are being developed. "
            "The live Data Anchor above comes from live polling.",
            icon="ℹ️",
        )

else:
    st.info(
        f"💡 Framework data for **{selected_label}** is being developed. Check back soon.",
        icon="ℹ️",
    )

st.markdown("")
st.divider()

# ─────────────────────────────────────────────────────────────────
# CROSS-STATE VARIATION PANEL
# ─────────────────────────────────────────────────────────────────

st.markdown("### Step 5: State-by-State Variation")
st.markdown(
    "Where does this topic land hardest — and where does it need more work? "
    "Ranked by MrP-adjusted support across all surveyed states.",
    unsafe_allow_html=True,
)

state_data = construct_state_data.get(selected_construct, {})

if state_data:
    sorted_states = sorted(state_data.items(), key=lambda x: x[1], reverse=True)
    n_states = len(sorted_states)

    # Color scale: strong green → amber → red
    def state_color(pct, min_pct, max_pct):
        if max_pct == min_pct:
            return "#1B6B3A"
        ratio = (pct - min_pct) / (max_pct - min_pct)
        if ratio >= 0.6:
            return "#1B6B3A"   # strong green
        elif ratio >= 0.3:
            return "#B8870A"   # amber
        else:
            return "#8B1A1A"   # red

    all_pcts = [p for _, p in sorted_states]
    min_p = min(all_pcts)
    max_p = max(all_pcts)

    # Build bar rows
    bars_html = ""
    for rank, (state, pct) in enumerate(sorted_states, 1):
        pct_int = round(pct)
        bar_width = max(4, round((pct / 100) * 100))
        color = state_color(pct, min_p, max_p)
        label = "Strongest" if rank == 1 else ("Weakest" if rank == n_states else "")
        label_chip = (
            f'<span style="font-size:0.72rem;color:{color};font-weight:600;'
            f'background:rgba(0,0,0,0.04);border-radius:8px;padding:1px 6px;margin-left:6px;">'
            f'{label}</span>' if label else ""
        )
        bars_html += f"""
        <div style="display:flex;align-items:center;gap:10px;margin-bottom:6px;">
            <div style="width:130px;font-size:0.85rem;color:{TEXT2};text-align:right;flex-shrink:0;">
                {state}
            </div>
            <div style="flex:1;background:#F0EDE8;border-radius:4px;height:20px;overflow:hidden;">
                <div style="width:{bar_width}%;background:{color};height:100%;border-radius:4px;"></div>
            </div>
            <div style="width:52px;font-size:0.85rem;font-weight:600;color:{color};flex-shrink:0;">
                {pct_int}%
            </div>
            {label_chip}
        </div>"""

    # Transferability note
    if n_states >= 2:
        spread = max_p - min_p
        if spread <= 8:
            transfer_note = "Low variation across states — this message transfers well nationally."
            note_color = "#1B6B3A"
        elif spread <= 18:
            transfer_note = "Moderate state variation — adapt messaging emphasis by state."
            note_color = "#B8870A"
        else:
            transfer_note = "High state variation — messaging needs significant adaptation by state."
            note_color = "#8B1A1A"
    else:
        transfer_note = ""
        note_color = TEXT2

    note_html = (
        f'<div style="font-size:0.8rem;color:{note_color};margin-top:0.75rem;'
        f'padding:0.4rem 0.75rem;background:rgba(0,0,0,0.03);border-radius:6px;">'
        f'📊 {transfer_note}</div>'
    ) if transfer_note else ""

    st.markdown(f"""
    <div style="background:{CARD_BG};border:1px solid {BORDER2};border-radius:10px;
         padding:1.25rem;box-shadow:0 1px 3px rgba(0,0,0,0.04);">
        {bars_html}
        {note_html}
    </div>
    """, unsafe_allow_html=True)

else:
    st.markdown(f"""
    <div style="background:rgba(184,135,10,0.06);border:1px dashed {GOLD_MID};border-radius:8px;
         padding:0.9rem 1.25rem;color:{TEXT2};font-size:0.88rem;">
        State-level data for <strong>{selected_label}</strong> will appear here as survey waves
        are processed. Currently available for: {", ".join(sorted(SURVEY_STATE.values())[:6])}.
    </div>
    """, unsafe_allow_html=True)

st.markdown("")
st.divider()

# ─────────────────────────────────────────────────────────────────
# STEP 5.5: SCRIPT SKELETON — from register required moves + Rule 1
# ─────────────────────────────────────────────────────────────────

if selected_reg_code and selected_reg:
    reg_name = selected_reg.get("name", selected_reg_code)
    req_moves = selected_reg.get("required_moves", [])
    opt_moves = selected_reg.get("optional_moves", [])
    r1v = get_rule1_variant(selected_reg_code)
    r1_name = r1v.get("name", "") if r1v else ""
    r1_desc = RULE1_VARIANTS.get(r1_name, {}).get("description", "") if r1_name in RULE1_VARIANTS else ""

    # Build skeleton text
    skeleton_lines = []
    skeleton_lines.append(f"=== SCRIPT SKELETON: {reg_name} ({selected_format}) ===")
    skeleton_lines.append(f"TOPIC: {selected_label}")
    skeleton_lines.append(f"REGISTER: {reg_name}")
    skeleton_lines.append(f"FORMAT: {selected_format}")
    skeleton_lines.append("")

    # Opening: Rule 1
    skeleton_lines.append(f"[OPEN — Rule 1: {r1_name}]")
    skeleton_lines.append(f"  ↳ {r1_desc}")
    skeleton_lines.append(f"  WRITE: ___________________________________________")
    skeleton_lines.append("")

    # Data anchor
    anchor = get_data_anchor_text(selected_construct, construct_summaries, data_mode)
    if anchor:
        skeleton_lines.append("[DATA ANCHOR — from live MrP polling]")
        skeleton_lines.append(f"  ↳ {anchor}")
        skeleton_lines.append("")

    # Required structural moves
    skeleton_lines.append("[REQUIRED STRUCTURAL MOVES — must be present]")
    for move in req_moves:
        move_data = get_structural_move(move)
        move_desc = move_data.get("description", "") if move_data else ""
        skeleton_lines.append(f"  ✓ {move}")
        if move_desc:
            skeleton_lines.append(f"    ↳ {move_desc}")
        skeleton_lines.append(f"    WRITE: ___________________________________________")
        skeleton_lines.append("")

    # Optional moves
    if opt_moves:
        skeleton_lines.append("[OPTIONAL STRUCTURAL MOVES — consider for this register]")
        for move in opt_moves:
            skeleton_lines.append(f"  ○ {move}")
        skeleton_lines.append("")

    # Bookend instruction (Rule 6)
    skeleton_lines.append("[CLOSE — Rule 6: Bookend]")
    skeleton_lines.append("  ↳ Close on the same word you opened with, but deepened by the argument.")
    skeleton_lines.append("  Bookend word: ___________")
    skeleton_lines.append("  Open meaning: ___________")
    skeleton_lines.append("  Close meaning (deepened): ___________")
    skeleton_lines.append("")

    # Silent Track check if applicable
    if selected_format in [FORMAT_TV_30, FORMAT_TV_60, FORMAT_DIGITAL_30]:
        skeleton_lines.append("[SILENT TRACK CHECK — read text cards only]")
        skeleton_lines.append("  Text card 1: ___________________________________________")
        skeleton_lines.append("  Text card 2: ___________________________________________")
        skeleton_lines.append("  Text card 3: ___________________________________________")
        skeleton_lines.append("  Does the sequence carry the argument without audio? [Y/N]")
        skeleton_lines.append("")

    # Validation reminders
    skeleton_lines.append("[VALIDATION CHECKLIST]")
    skeleton_lines.append("  □ Rule 1: Does the opening concede the opponent's strongest point?")
    skeleton_lines.append("  □ Rule 3: Are all text cards ≤ 7 words?")
    skeleton_lines.append("  □ Rule 5: Is the villain named on screen? (should be implied only)")
    skeleton_lines.append("  □ Rule 6: Does the bookend word deepen in meaning from open to close?")
    skeleton_lines.append("  □ Underwriting: Is there silence after each key text card?")

    skeleton_text = "\n".join(skeleton_lines)

    with st.expander(f"📝 Script Skeleton — {reg_name}", expanded=False):
        st.markdown(f"""
        <div style="font-size:0.82rem;color:{TEXT3};margin-bottom:0.5rem;">
            This skeleton is built from <strong>{reg_name}</strong>'s required structural moves
            and the 6 Signature Rules. Fill it in or paste it into the AI Analysis page for generation.
        </div>
        """, unsafe_allow_html=True)
        st.code(skeleton_text, language=None)

    st.markdown("")
    st.divider()

# ─────────────────────────────────────────────────────────────────
# STEP 6: GENERATE SCRIPT — inline via Anthropic API
# ─────────────────────────────────────────────────────────────────

st.markdown("### Step 6: Generate Your Script")

# ── Audience selector (needed for generation prompt) ──────────────
audience_options = [
    "General public",
    "Republican persuadables",
    "Democratic base (mobilization)",
    "Independent / swing voters",
    "State legislators",
    "Local media / editorial boards",
    "Grassroots advocates / organizers",
    "Donors and funders",
]
suggested = get_dynamic_audience(selected_construct, construct_summaries)
is_live_suggestion = selected_construct in construct_summaries
suggested_idx = audience_options.index(suggested) if suggested in audience_options else 0
rationale = AUDIENCE_RATIONALE.get(suggested, "")

aud_col, src_col = st.columns([1, 2])

with aud_col:
    audience = st.selectbox(
        "Target audience",
        audience_options,
        index=suggested_idx,
        key="mm_audience",
    )
    if is_live_suggestion and r_pct is not None and d_pct is not None:
        gap = d_pct - r_pct
        gap_str = f"+{round(abs(gap))}pt D" if gap > 0 else f"+{round(abs(gap))}pt R"
        st.markdown(
            f"""<div style="font-size:0.77rem;color:{TEXT3};padding:4px 0;">
            💡 Live data suggests <strong>{suggested}</strong> &nbsp;·&nbsp;
            R {round(r_pct)}% · D {round(d_pct)}% · gap {gap_str}</div>""",
            unsafe_allow_html=True,
        )

with src_col:
    sc1, sc2 = st.columns(2)
    with sc1:
        bill_text = st.text_area(
            "📄 Bill / policy context (optional)",
            height=120,
            placeholder="Paste key provisions, background, or bill number...",
            key="mm_bill_text",
        )
    with sc2:
        assets_text = st.text_area(
            "🎤 Spokespeople / voices (optional)",
            height=60,
            placeholder="Name, role, why they matter...",
            key="mm_assets",
        )
        additional_notes = st.text_area(
            "📝 Other notes (optional)",
            height=52,
            placeholder="State context, client constraints, tone notes...",
            key="mm_notes",
        )

st.markdown("")

# ── API key check + generate button ───────────────────────────────
_api_key = ""
if ANTHROPIC_AVAILABLE:
    try:
        _api_key = st.secrets.get("ANTHROPIC_KEY", "")
    except Exception:
        import os
        _api_key = os.environ.get("ANTHROPIC_KEY", "")

if not selected_reg_code:
    st.info("Select a format and register in Step 5 to unlock generation.")

elif not GENERATOR_AVAILABLE or not ANTHROPIC_AVAILABLE:
    st.warning("script_generator.py or anthropic package not found. Check requirements.txt and deploy.")

elif not _api_key:
    st.warning(
        "No ANTHROPIC_KEY found in secrets. "
        "Add it to .streamlit/secrets.toml on the server: `ANTHROPIC_KEY = 'sk-ant-...'`"
    )

else:
    # Show what will be generated
    word_limit = FORMAT_WORD_COUNTS.get(selected_format, 150)
    st.markdown(
        f"""<div style="font-size:0.82rem;color:{TEXT3};margin-bottom:0.75rem;">
        Generating a <strong>{selected_format}</strong> script in the
        <strong>{selected_reg.get('name', selected_reg_code)}</strong> register
        ({word_limit}-word audio limit) for <strong>{selected_label}</strong>.
        Audience: <strong>{audience}</strong>.
        </div>""",
        unsafe_allow_html=True,
    )

    gen_btn = st.button(
        "✍️ Generate Script",
        type="primary",
        key="mm_generate",
        help=f"Calls claude-opus-4-6 with the full creative system prompt — {selected_format} · {selected_reg.get('name', '')}",
    )

    if gen_btn or "mm_last_script" in st.session_state:
        # ── Build prompt if generate was just clicked ──────────────
        if gen_btn:
            st.session_state.pop("mm_last_script", None)
            st.session_state.pop("mm_last_warnings", None)

            anchor = get_data_anchor_text(selected_construct, construct_summaries, data_mode)
            fm = FRAMEWORK_MAP.get(selected_construct, {})
            wm = WORDS_MAP.get(selected_construct, {})
            r1v = get_rule1_variant(selected_reg_code)
            r1_name = r1v.get("name", "") if r1v else ""
            r1_desc = RULE1_VARIANTS.get(r1_name, {}).get("description", "") if r1_name else ""

            prompt = build_prompt(
                topic_label=selected_label,
                construct=selected_construct,
                tier=selected_tier,
                tier_role=TIER_ROLE.get(selected_tier, ""),
                selected_format=selected_format,
                reg_name=selected_reg.get("name", selected_reg_code),
                reg_description=selected_reg.get("description", ""),
                reg_characteristics=selected_reg.get("defining_characteristics", []),
                req_moves=selected_reg.get("required_moves", []),
                opt_moves=selected_reg.get("optional_moves", []),
                r1_name=r1_name,
                r1_desc=r1_desc,
                anchor_text=anchor or "",
                audience=audience,
                audience_rationale=rationale,
                live_pct=live_pct,
                r_pct=r_pct,
                d_pct=d_pct,
                words_work=wm.get("work", []),
                words_avoid=wm.get("avoid", []),
                frame=fm.get("frame", ""),
                inoculation=fm.get("inoculation", ""),
                cta=fm.get("cta", ""),
                state_data=state_data if "state_data" in dir() else {},
                bill_text=bill_text,
                assets_text=assets_text,
                additional_notes=additional_notes,
                structural_moves=STRUCTURAL_MOVES,
                rules=RULES,
                principles=PRINCIPLES,
                production_doctrine=PRODUCTION_DOCTRINE,
            )

            with st.spinner(f"Writing your {selected_format} script… (this takes 15-30 seconds)"):
                script_text, error = generate_script(prompt, _api_key)

            if error:
                st.error(f"Generation failed: {error}")
            else:
                warnings = flag_rule_violations(script_text, word_limit, selected_format)
                st.session_state["mm_last_script"] = script_text
                st.session_state["mm_last_warnings"] = warnings
                st.session_state["mm_last_topic"] = selected_label
                st.session_state["mm_last_format"] = selected_format
                st.session_state["mm_last_reg"] = selected_reg.get("name", selected_reg_code)

        # ── Display last generated script ──────────────────────────
        if "mm_last_script" in st.session_state:
            script_text = st.session_state["mm_last_script"]
            warnings = st.session_state.get("mm_last_warnings", [])
            last_topic = st.session_state.get("mm_last_topic", selected_label)
            last_format = st.session_state.get("mm_last_format", selected_format)
            last_reg = st.session_state.get("mm_last_reg", "")

            st.markdown(
                f"""<div style="font-weight:700;color:{NAVY};font-size:1rem;margin-bottom:0.5rem;">
                Generated Script — {last_format} · {last_reg} · {last_topic}
                </div>""",
                unsafe_allow_html=True,
            )

            # Rule violation warnings
            if warnings:
                for w in warnings:
                    st.warning(w)

            # Script display
            st.markdown(
                f"""<div style="background:{CARD_BG};border:1px solid {BORDER2};border-left:4px solid {GOLD};
                border-radius:10px;padding:1.1rem 1.4rem;margin-bottom:0.75rem;
                font-family:monospace;font-size:0.84rem;line-height:1.75;
                color:{TEXT1};white-space:pre-wrap;">{script_text}</div>""",
                unsafe_allow_html=True,
            )

            # Copy / regenerate row
            btn_c1, btn_c2, btn_c3 = st.columns([2, 1, 1])
            with btn_c1:
                st.code(script_text, language=None)
            with btn_c2:
                if st.button("🔄 Regenerate", key="mm_regen"):
                    st.session_state.pop("mm_last_script", None)
                    st.rerun()
            with btn_c3:
                if st.button("🗑 Clear", key="mm_clear"):
                    for k in ["mm_last_script", "mm_last_warnings", "mm_last_topic",
                              "mm_last_format", "mm_last_reg"]:
                        st.session_state.pop(k, None)
                    st.rerun()

            st.caption(
                "Script generated using claude-opus-4-6 with the full Actionable Intel creative system. "
                "Review Rule Check section for any flagged issues before sending to production."
            )

st.markdown("")
st.divider()

# ─────────────────────────────────────────────────────────────────
# CHAT WIDGET & FOOTER
# ─────────────────────────────────────────────────────────────────

portal_footer()
