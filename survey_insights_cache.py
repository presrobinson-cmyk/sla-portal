"""
survey_insights_cache.py — Cached snapshot of Airtable Survey Design Insights
Airtable base: appMRKczb8z3JmenI  table: tblqEL2lhAuEiPV6H
Last synced: 2026-04-13  Records: 20

Fields:
  insight       — short title
  type          — Methodology | Question Design | Scoring Lesson | Measurement Gap |
                  Strategic Signal | Construct Coverage
  priority      — Must address | Should address | Nice to have | Long-term
  constructs    — list of construct codes affected; ["ALL"] = applies everywhere
  description   — full diagnostic description
  recommended_action — what to do in future survey design
  status        — Open | Addressed
  states        — list of state codes affected; ["ALL"] = all states

Usage:
    from survey_insights_cache import SURVEY_INSIGHTS, get_insights_for_constructs

Optional live fetch (requires AIRTABLE_KEY in st.secrets or env):
    Call refresh_insights_from_airtable() to update the cache at runtime.
"""

from __future__ import annotations
from typing import List, Dict, Any

# ─── Static snapshot ──────────────────────────────────────────────────────────

SURVEY_INSIGHTS: List[Dict[str, Any]] = [
    {
        "id": "rec4eaK98rd9oDu7a",
        "insight": "Party proxy fails on low-partisan-gap questions",
        "type": "Methodology",
        "priority": "Must address",
        "constructs": ["DV", "DETER", "MAND"],
        "description": (
            "Using Democrat-mode response as the 'reform direction' produces wrong "
            "classifications on questions with low partisan gaps. DV is one of the "
            "least partisan constructs (D-R gap typically < 5pts). DV2 in MA: R at "
            "83.1% vs D at 77.5%. DETER1 direction flips across 6 states. OK "
            "Republicans are 8-16pts more favorable on DV than other-state Republicans. "
            "29 question-state pairs found where R > D. Content-based direction "
            "classification was built to replace this method entirely."
        ),
        "recommended_action": (
            "Never use party as a proxy for reform direction. The content-based "
            "REFORM_DIRECTION table (119 questions, content_scoring.py v3) should be "
            "the canonical reference. Every new question added to future waves must "
            "have its reform direction classified by content at design time, not "
            "derived from partisan signal after fielding."
        ),
        "status": "Addressed",
        "states": ["ALL"],
    },
    {
        "id": "recLOOfwHDnVbRNMY",
        "insight": "OK Republicans uniquely favorable on DV — state-specific effect",
        "type": "Strategic Signal",
        "priority": "Nice to have",
        "constructs": ["DV"],
        "description": (
            "Oklahoma Republicans score 8-16 points higher on DV questions than "
            "Republicans in other states. R > D on DV2 in LA and MA. This suggests "
            "DV reform resonance with Republicans is not uniform nationally — Oklahoma "
            "may have cultural or legislative context that makes DV reform especially "
            "salient to conservatives there (possibly religious community influence, "
            "personal experience, or state-specific advocacy framing)."
        ),
        "recommended_action": (
            "In OK-specific future waves, explore what drives Republican DV support: "
            "add questions on motivations (faith, personal experience, fairness "
            "principle). Test whether OK-specific messaging works nationally. Consider "
            "DV as a gateway construct for broader reform messaging to Republican "
            "audiences."
        ),
        "status": "Open",
        "states": ["OK"],
    },
    {
        "id": "recMhHczidDXUqvRZ",
        "insight": "EQUITY1 is multi-choice — not binary — reform direction is complex",
        "type": "Question Design",
        "priority": "Nice to have",
        "constructs": ["EQUITY"],
        "description": (
            "CJ-EQUITY1 asks 'What has the greatest influence on how people are treated "
            "in the justice system?' with 5 options: race/ethnicity, money/lawyer, "
            "political connections, seriousness of crime, or 'system treats people "
            "equally.' Currently scored as multi_favorable where picking race, money, "
            "or connections = reform-aligned (acknowledges inequity). But this means 3 "
            "of 5 options are reform — mechanically inflating the favorable rate. The "
            "'seriousness of crime' option is ambiguous. EQUITY construct at 50.3% "
            "support may be artificially depressed or elevated depending on "
            "interpretation."
        ),
        "recommended_action": (
            "Redesign equity measurement in future waves. Consider a direct "
            "agree/disagree statement ('The criminal justice system treats people of "
            "all races equally') with a Likert scale. This would give cleaner binary "
            "signal plus intensity. The current 5-choice format forces a ranked "
            "attribution that is hard to score and even harder to interpret for "
            "messaging."
        ),
        "status": "Open",
        "states": ["ALL"],
    },
    {
        "id": "recMr798llcS0OFAG",
        "insight": "COMPASSION construct inflated by duplicate questions across surveys",
        "type": "Construct Coverage",
        "priority": "Should address",
        "constructs": ["COMPASSION", "ELDERLY"],
        "description": (
            "COMPASSION3 and ELDERLY1 are the same question text. COMPASSION4 and "
            "ELDERLY-COST1 are the same question text. CJ-Q85/Q86/Q87/Q88 duplicate "
            "COMPASSION1-4 under different QIDs in MA/NJ surveys. This means "
            "COMPASSION construct scores are partly driven by duplicate items counted "
            "multiple times. Not a bug per se — these map to the same underlying "
            "attitude — but it inflates the apparent measurement density of COMPASSION "
            "relative to other constructs."
        ),
        "recommended_action": (
            "Create a QID deduplication map that identifies which questions are "
            "textually identical across different QID schemes. Use this map when "
            "computing construct-level scores to avoid double-counting. In future "
            "survey design, avoid re-numbering identical questions — use a consistent "
            "QID across all states."
        ),
        "status": "Open",
        "states": ["ALL"],
    },
    {
        "id": "recQZZXl9YyNV9rWW",
        "insight": "FIRSTAPPEAR: highest fertility ceiling but no intensity data",
        "type": "Measurement Gap",
        "priority": "Must address",
        "constructs": ["FIRSTAPPEAR", "COUNSEL"],
        "description": (
            "VA-FIRSTAPPEAR1 and VA-COUNSEL2 (same question, different QIDs) achieve "
            "91.5% support, 96 bipartisan score — the single highest-performing item "
            "in the entire battery. But both are binary (Yes/No), so intensity is "
            "completely unknown. Fertility range is 0.439-0.877. If intensity is high, "
            "this is by far the best messaging target in the whole survey. If intensity "
            "is low, it drops to mid-pack. We literally cannot make a strategic "
            "recommendation on the #1 item without Likert measurement."
        ),
        "recommended_action": (
            "Add a Likert version of the right-to-counsel-at-first-appearance question "
            "to every future state wave, not just VA. This is the single highest-value "
            "question to resolve. Even a simple 'How strongly do you feel about this?' "
            "follow-up would close the gap. This should be a top priority item in the "
            "next survey design."
        ),
        "status": "Open",
        "states": ["VA"],
    },
    {
        "id": "recX9GrDACl9g39gS",
        "insight": "Fertility score framework: support × intensity × bipartisan",
        "type": "Methodology",
        "priority": "Must address",
        "constructs": ["ALL"],
        "description": (
            "The fertility score combines three dimensions: support rate (% favorable), "
            "intensity (strong vs moderate conviction, Likert only), and bipartisan "
            "score (100 - abs(D-R gap) × 2). When intensity is measured: fertility = "
            "(support/100) × intensity × (bipartisan/100). When intensity is unknown "
            "(binary questions): reported as a floor-ceiling range assuming 0.5-1.0 "
            "intensity. For mixed constructs, blended by coverage ratio. Strategic "
            "signal categories: GOLD (all 3 confirmed), GOLD-partial (some intensity "
            "data), STRONG-BI (high support + bipartisan, intensity unknown), CRUSADE "
            "(high support + intensity but partisan), CAREFUL-BI (high support + "
            "bipartisan but low intensity)."
        ),
        "recommended_action": (
            "This framework should be the standard for all future VIP analysis. "
            "Document the formula and thresholds in the VIP methodology guide. The "
            "key insight: fertility ranges on binary-only constructs represent genuine "
            "uncertainty about strategic posture, not a scoring artifact. Closing those "
            "ranges requires Likert measurement."
        ),
        "status": "Open",
        "states": ["ALL"],
    },
    {
        "id": "recbILiHlz55tE7Xk",
        "insight": "Likert scoring Bug 1: 'Somewhat support' excluded",
        "type": "Scoring Lesson",
        "priority": "Must address",
        "constructs": ["DV", "COMPASSION", "PD", "FINES"],
        "description": (
            "Original scoring only counted 'Strongly support' as favorable on Likert "
            "scales, missing 'Somewhat support' entirely. Impact: DV2 was 38.4 points "
            "too low, DV3 was 32.2 points too low, DV5 was 39.1 points too low. The "
            "'DV is internally split' finding was entirely an artifact of this bug. "
            "Fixed in classify_response_v2."
        ),
        "recommended_action": (
            "Any future scoring pipeline must handle all Likert variants from the "
            "start. Build a unit test suite that verifies every response option from "
            "the actual Alchemer export maps correctly. Never assume the only favorable "
            "response on a Likert scale is the most extreme."
        ),
        "status": "Addressed",
        "states": ["ALL"],
    },
    {
        "id": "recdq3GMiZNHZ0Yex",
        "insight": "Content-based reform direction table now canonical (119 questions)",
        "type": "Methodology",
        "priority": "Must address",
        "constructs": ["ALL"],
        "description": (
            "The REFORM_DIRECTION dictionary in content_scoring.py v3 classifies all "
            "119 policy questions by their text content — which response is "
            "'reform-aligned' based on whether it reduces incarceration, increases "
            "discretion, supports rehabilitation, acknowledges system problems, or "
            "favors proportionality. Three classification types: 'likert' "
            "(reform_side = support/oppose), 'binary' (reform_contains text match), "
            "'multi_favorable' (list of favorable responses). 15 questions excluded as "
            "non-policy. Saved as reform_direction_table.json."
        ),
        "recommended_action": (
            "When designing new survey questions, add the reform direction "
            "classification at design time and append to REFORM_DIRECTION. This table "
            "is the single source of truth for all scoring. Store the classification "
            "in Alchemer question metadata or a companion document so it survives "
            "personnel transitions."
        ),
        "status": "Open",
        "states": ["ALL"],
    },
    {
        "id": "recdybh4lIieR1lor",
        "insight": "Trust items measure a distinct dimension from reform support (r=0.13-0.18)",
        "type": "Methodology",
        "priority": "Should address",
        "constructs": ["TRUST", "EQUITY", "COUNSEL", "FIRSTAPPEAR", "ALPR"],
        "description": (
            "Trust ↔ Reform correlation held weak through all scoring corrections: "
            "0.107 → 0.116 → 0.134 → 0.183. The trust gate is real and robust. "
            "High-trust voters don't systematically support more reform — but trust "
            "moderates the messaging strategy. Tightened trust-adjacent constructs: "
            "TRUST, EQUITY, COUNSEL, FIRSTAPPEAR, ALPR, DISPARITIES."
        ),
        "recommended_action": (
            "Maintain TRUST items in every future wave. They are not redundant "
            "with reform items — they measure an independent dimension that determines "
            "messaging strategy. Consider adding 1-2 more trust items to strengthen "
            "measurement (currently only CJ-TRUST1 is a direct trust measure; others "
            "are adjacent concepts like right-to-counsel)."
        ),
        "status": "Open",
        "states": ["ALL"],
    },
    {
        "id": "reciZrc5kUbcWgmzM",
        "insight": "Ranking/JSON questions (EQUITY1-RANK, PURPOSE1b) are unscorable",
        "type": "Question Design",
        "priority": "Should address",
        "constructs": ["EQUITY"],
        "description": (
            "CJ-EQUITY1-RANK and CJ-PURPOSE1b store response data as JSON ranking "
            "objects rather than selectable text. These cannot be scored by any "
            "text-matching classifier and are excluded from all analysis. They "
            "represent wasted survey real estate from a scoring perspective — we ask "
            "the question but can't use the answer in the VIP framework."
        ),
        "recommended_action": (
            "Either: (a) add a post-processing step in the ingestion pipeline that "
            "parses ranking JSON into ordinal scores, or (b) replace ranking questions "
            "with standard select/Likert formats in future waves. If rankings are "
            "retained for specific analytic purposes, pair them with a scoreable "
            "version of the same concept."
        ),
        "status": "Open",
        "states": ["ALL"],
    },
    {
        "id": "recj0GHaN9uqNGe4f",
        "insight": "Likert scoring Bug 2: bare 'Support'/'Agree' misclassified",
        "type": "Scoring Lesson",
        "priority": "Must address",
        "constructs": ["COMPASSION", "PD", "FINES"],
        "description": (
            "Response options 'Support' and 'Agree' (without 'Somewhat' or 'Strongly' "
            "prefix) were classified as 'other' instead of moderate-favorable. Impact: "
            "COMPASSION1 jumped from 45.4% to 74.5%, PD2 from 49.3% to 84.4%, FINES3 "
            "from 37.3% to 76.4%. Some questions genuinely use bare Support/Oppose "
            "scales. Fixed in classify_response_v2 by explicitly matching bare forms."
        ),
        "recommended_action": (
            "Standardize Likert scale wording across all future surveys. Use consistent "
            "'Strongly support / Somewhat support / Somewhat oppose / Strongly oppose' "
            "everywhere. Avoid bare 'Support'/'Agree' options that create classifier "
            "ambiguity. If bare forms are used, document them in the question metadata "
            "so the scoring pipeline knows to expect them."
        ),
        "status": "Addressed",
        "states": ["ALL"],
    },
    {
        "id": "recqBenTSiB95AmlV",
        "insight": "DV is among least partisan constructs — bipartisan messaging opportunity",
        "type": "Strategic Signal",
        "priority": "Should address",
        "constructs": ["DV"],
        "description": (
            "DV construct has D-R gap of only +4.4pts (compared to CONDITIONS at +12, "
            "RETRO at +11.4, BAIL at +17). DV2 has bipartisan score of 93, DV3 is 91, "
            "DV5 is 91. OK Republicans are uniquely strong on DV (8-16pts above "
            "other-state Rs). DV construct is GOLD-partial (0.423-0.555 fertility). "
            "Rare construct where bipartisan messaging is backed by real data — not "
            "just high topline but high bipartisan score AND measured intensity (74% "
            "on Likert items)."
        ),
        "recommended_action": (
            "Design DV questions for future waves that explore WHY bipartisan support "
            "exists. Add questions probing Republican-specific DV framing (personal "
            "responsibility for protecting families? faith-based compassion?). Test "
            "whether OK-specific messaging works nationally. Consider DV as a gateway "
            "construct for broader reform messaging to Republican audiences."
        ),
        "status": "Open",
        "states": ["ALL"],
    },
    {
        "id": "recrwW8QNkD498WNX",
        "insight": "Binary questions lack intensity measurement",
        "type": "Measurement Gap",
        "priority": "Must address",
        "constructs": ["PROP", "FIRSTAPPEAR", "CONDITIONS", "LIT", "REENTRY", "RETRO", "LWOP", "ELDERLY"],
        "description": (
            "Binary (two-choice) questions tell us whether someone favors reform but "
            "NOT how strongly. Intensity can only be measured on Likert scales. "
            "Currently ~75% of questions are binary, meaning we have no intensity data "
            "for most of the battery. This creates a massive blind spot: we can't "
            "distinguish 'crusade' messaging territory from 'careful' territory on "
            "constructs like PROP (0.36-0.72 fertility range), FIRSTAPPEAR (0.44-0.88), "
            "CONDITIONS, LIT, REENTRY, RETRO, LWOP. These constructs have strong "
            "bipartisan support but we cannot tell a client whether conviction runs "
            "deep or shallow."
        ),
        "recommended_action": (
            "Add Likert-scaled follow-up versions of at least the top binary questions "
            "(e.g., 'How strongly do you support or oppose...' variants) for PROP, "
            "FIRSTAPPEAR, CONDITIONS, LIT, REENTRY, RETRO, LWOP. Even one Likert item "
            "per construct would allow intensity measurement. Prioritize constructs "
            "currently rated STRONG-BI where the fertility range spans more than 2x."
        ),
        "status": "Open",
        "states": ["ALL"],
    },
    {
        "id": "recs8sZQaUyDNYVVD",
        "insight": "TRUST1 has only 4-point scale — no 'reform direction' analog",
        "type": "Question Design",
        "priority": "Should address",
        "constructs": ["TRUST"],
        "description": (
            "CJ-TRUST1 ('How much trust do you have in local prosecutors...') uses a "
            "4-point trust scale (A lot / Some / Not much / No trust at all). This "
            "works as a landscape/gauge item but doesn't map cleanly to the reform direction "
            "framework. Currently scored as multi_favorable where high trust = "
            "favorable. But for reform messaging, the relationship "
            "between trust and reform support is not linear — it's gated."
        ),
        "recommended_action": (
            "Add more trust measurement items to future waves. Consider: trust in "
            "judges, trust in public defenders, trust in the parole board, trust in "
            "police. A multi-item trust battery would allow sub-dimensions of trust "
            "to emerge. Also consider adding a direct 'Does the system need reform?' "
            "meta-question."
        ),
        "status": "Open",
        "states": ["ALL"],
    },
    {
        "id": "recsPxVThtjev26rv",
        "insight": "Factor analysis: 3 construct clusters with r=0.53-0.59 between clusters",
        "type": "Methodology",
        "priority": "Long-term",
        "constructs": ["ALL"],
        "description": (
            "Factor analysis found 3 construct clusters with moderate inter-cluster "
            "correlations (r=0.53-0.59), meaning the clusters are related but not "
            "redundant. The persuasion tier sequence (Entry → Bridge → Downstream) is "
            "a strategic design choice grounded in this cluster structure, not a "
            "statistical necessity. The 3 clusters align roughly with: "
            "(1) system trust/fairness, (2) sentence reform/compassion, "
            "(3) process reform/rights."
        ),
        "recommended_action": (
            "Future waves could test whether adding items at cluster boundaries "
            "strengthens or weakens the factor structure. The moderate inter-cluster "
            "correlations suggest there may be a general 'reform openness' latent "
            "factor underneath — this is what the Temperature Gauge concept aims to "
            "measure."
        ),
        "status": "Open",
        "states": ["ALL"],
    },
    {
        "id": "recuZ8gvoUYVFmkan",
        "insight": "DETER1 reform direction flips across states",
        "type": "Question Design",
        "priority": "Should address",
        "constructs": ["DETER"],
        "description": (
            "DETER1 ('long prison sentences are an effective deterrent') shows the "
            "reform-skeptical position winning overall (59.7% say yes, sentences "
            "deter). But the D-R gap direction flips between states — in some states "
            "Democrats are more reform-aligned, in others the gap narrows or reverses. "
            "This makes DETER a poor candidate for universal messaging. Current "
            "fertility is low (0.136-0.272 range, Uphill signal)."
        ),
        "recommended_action": (
            "Consider redesigning deterrence questions to separate the empirical "
            "belief ('do long sentences deter?') from the policy preference ('should "
            "we use long sentences?'). The current question conflates the two. Someone "
            "might believe sentences deter but still oppose them on cost or "
            "proportionality grounds. A two-part question would give cleaner signal."
        ),
        "status": "Open",
        "states": ["ALL"],
    },
    {
        "id": "recv2evYVab2voZrE",
        "insight": "APPROACH construct is highly partisan (D-R = +22.6) despite high topline",
        "type": "Strategic Signal",
        "priority": "Nice to have",
        "constructs": ["APPROACH"],
        "description": (
            "APPROACH ('Smart on crime' vs 'Tough on crime') gets 66.2% overall "
            "support but has the highest D-R gap (+22.6pts) of any construct above "
            "65% support. Bipartisan score is only 55. This means the topline is "
            "misleading for strategic purposes — the support is heavily concentrated "
            "among Democrats. CRUSADE signal, not GOLD. Similarly, CRIMEAPPROACH1 "
            "shows D-R gap of +26.9."
        ),
        "recommended_action": (
            "Test alternative framings that capture the same 'approach to reform' "
            "concept without the partisan trigger words 'smart on crime' vs 'tough on "
            "crime.' These phrases have become politically coded. A reframe like "
            "'balancing accountability with prevention' vs 'prioritizing punishment "
            "and deterrence' might yield different partisan distributions while "
            "measuring the same underlying attitude."
        ),
        "status": "Open",
        "states": ["ALL"],
    },
    {
        "id": "recvrYVfiKMx5QjwE",
        "insight": "Standardize Likert scales across all surveys",
        "type": "Question Design",
        "priority": "Must address",
        "constructs": ["ALL"],
        "description": (
            "Current battery uses at least 4 different Likert formats: (1) Strongly "
            "support / Somewhat support / Somewhat oppose / Strongly oppose, (2) "
            "Strongly agree / Somewhat agree / Somewhat disagree / Strongly disagree, "
            "(3) bare Support/Oppose (no intensity), (4) bare Agree/Disagree (no "
            "intensity). This inconsistency caused both scoring bugs and creates "
            "structural inequality in the fertility metric — questions with full "
            "4-point Likert scales get accurate intensity measurement while bare-scale "
            "questions get penalized or left as unknown."
        ),
        "recommended_action": (
            "Adopt a single standard Likert format for all support/oppose questions: "
            "'Strongly support / Somewhat support / Somewhat oppose / Strongly oppose "
            "/ Not sure.' For agree/disagree: 'Strongly agree / Somewhat agree / "
            "Somewhat disagree / Strongly disagree / Not sure.' Document this as a "
            "survey design rule. Never use bare Support/Oppose without the intensity "
            "prefix."
        ),
        "status": "Open",
        "states": ["ALL"],
    },
    {
        "id": "recwDqMXXCdQnoRB3",
        "insight": "VA-COUNSEL1 and VA-ALPR1 use bare Support/Oppose — intensity reads low",
        "type": "Question Design",
        "priority": "Should address",
        "constructs": ["COUNSEL", "ALPR"],
        "description": (
            "VA-COUNSEL1 (right to counsel in constitution) gets 83.7% support and 99 "
            "bipartisan score — but only 50% intensity because the response options are "
            "bare 'Support'/'Oppose' with no Strongly/Somewhat split. Same for "
            "VA-ALPR1 (69.7% support, 50% intensity, CAREFUL-BI signal). The low "
            "intensity is likely an artifact of scale design, not genuine weak "
            "conviction. Both get penalized in the fertility ranking as a result."
        ),
        "recommended_action": (
            "Replace bare Support/Oppose scales with full 4-point Likert (Strongly "
            "support / Somewhat support / Somewhat oppose / Strongly oppose) in future "
            "waves. This is especially important for high-performing items like COUNSEL "
            "and ALPR where the intensity gap is likely measurement artifact, not real."
        ),
        "status": "Open",
        "states": ["VA"],
    },
    {
        "id": "recxU6l4VmItjsmaK",
        "insight": "DV-PROP are independent constructs (r=0.035)",
        "type": "Construct Coverage",
        "priority": "Nice to have",
        "constructs": ["DV", "PROP"],
        "description": (
            "DV (domestic violence context) and PROP (proportionality) have near-zero "
            "correlation at the individual level (r=0.035). Despite surface similarity "
            "— both involve sentence fairness — they measure fundamentally different "
            "things: DV is empathy-driven (compassion for abuse survivors), PROP is "
            "principle-driven (abstract fairness of punishment matching crime). A voter "
            "who strongly supports proportional sentencing may or may not care about "
            "DV context, and vice versa."
        ),
        "recommended_action": (
            "Keep DV and PROP as separate constructs in future waves. Do not merge or "
            "combine them. They appeal to different voter motivations and require "
            "different messaging strategies. This finding supports the VIP construct "
            "architecture."
        ),
        "status": "Open",
        "states": ["ALL"],
    },
]

# ─── Priority ordering ─────────────────────────────────────────────────────────

PRIORITY_ORDER = ["Must address", "Should address", "Nice to have", "Long-term"]
TYPE_ORDER = [
    "Measurement Gap",
    "Question Design",
    "Scoring Lesson",
    "Construct Coverage",
    "Strategic Signal",
    "Methodology",
]


# ─── Helper functions ──────────────────────────────────────────────────────────

def get_insights_for_constructs(
    constructs: List[str],
    status_filter: str | None = None,
    priority_filter: str | None = None,
) -> List[Dict[str, Any]]:
    """Return insights relevant to any of the given construct codes.

    Args:
        constructs: list of construct codes (e.g. ["DV", "PROP"])
        status_filter: "Open" | "Addressed" | None (all)
        priority_filter: "Must address" | "Should address" | etc. | None (all)

    Returns:
        Sorted list of matching insight dicts (priority order, then type order).
    """
    results = []
    for insight in SURVEY_INSIGHTS:
        # Match if insight applies to ALL constructs or specifically one of ours
        if "ALL" in insight["constructs"] or any(c in insight["constructs"] for c in constructs):
            if status_filter and insight["status"] != status_filter:
                continue
            if priority_filter and insight["priority"] != priority_filter:
                continue
            results.append(insight)

    results.sort(key=lambda r: (
        PRIORITY_ORDER.index(r["priority"]) if r["priority"] in PRIORITY_ORDER else 99,
        TYPE_ORDER.index(r["type"]) if r["type"] in TYPE_ORDER else 99,
    ))
    return results


def get_open_must_address() -> List[Dict[str, Any]]:
    """Return all Open + Must address insights, sorted by type."""
    return get_insights_for_constructs(
        constructs=["ALL"],
        status_filter="Open",
        priority_filter="Must address",
    )


def get_insights_summary() -> Dict[str, int]:
    """Count insights by priority × status."""
    summary: Dict[str, int] = {}
    for ins in SURVEY_INSIGHTS:
        key = f"{ins['priority']} / {ins['status']}"
        summary[key] = summary.get(key, 0) + 1
    return summary


# ─── Optional live refresh ─────────────────────────────────────────────────────

def refresh_insights_from_airtable() -> List[Dict[str, Any]]:
    """Fetch live records from Airtable and return as insight dicts.

    Requires AIRTABLE_KEY in environment or st.secrets.
    Falls back to SURVEY_INSIGHTS static snapshot on any error.

    This is intentionally not called at import time to keep the portal
    fast and independent of Airtable uptime.
    """
    AIRTABLE_BASE = "appMRKczb8z3JmenI"
    AIRTABLE_TABLE = "tblqEL2lhAuEiPV6H"

    try:
        import os, requests

        # Try Streamlit secrets first, then env var
        try:
            import streamlit as st
            key = st.secrets.get("AIRTABLE_KEY") or os.environ.get("AIRTABLE_KEY", "")
        except Exception:
            key = os.environ.get("AIRTABLE_KEY", "")

        if not key:
            return SURVEY_INSIGHTS

        headers = {"Authorization": f"Bearer {key}"}
        url = f"https://api.airtable.com/v0/{AIRTABLE_BASE}/{AIRTABLE_TABLE}"
        records, offset = [], None

        while True:
            params = {"pageSize": 100}
            if offset:
                params["offset"] = offset
            resp = requests.get(url, headers=headers, params=params, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            records.extend(data.get("records", []))
            offset = data.get("offset")
            if not offset:
                break

        def _parse(rec):
            f = rec.get("cellValuesByFieldId", {})
            return {
                "id": rec["id"],
                "insight": f.get("fldnxswSbZN5qNiR6", ""),
                "type": (f.get("fldAcvWyCXWDT2ztH") or {}).get("name", ""),
                "priority": (f.get("fldDlVDCK0qXFuZGw") or {}).get("name", ""),
                "constructs": [c["name"] for c in (f.get("fldA90vzMLSW8jX6w") or [])],
                "description": f.get("fld9TWrpQ0CFBybGk", ""),
                "recommended_action": f.get("fldPwdYBKOKls6i1J", ""),
                "status": (f.get("fldTY5RHmoOjS4L6X") or {}).get("name", ""),
                "states": [s["name"] for s in (f.get("fld6BuPm8vw5oKAiQ") or [])],
            }

        return [_parse(r) for r in records]

    except Exception:
        return SURVEY_INSIGHTS
