"""
content_scoring.py — Content-based favorable direction scoring engine (v5).

Domain-agnostic scoring: works for CJ reform, energy policy, health insurance,
education, candidates, or any policy domain. Each QID defines its own favorable
direction and base ideology for VIP scoring.

Replaces the old party-signal method where "Democrat majority response = favorable."
Favorable direction is now determined by POLICY CONTENT of response options.

Usage:
    from content_scoring import score_content, FAVORABLE_DIRECTION, AXIS_ASSIGNMENTS

    fav, intensity, has_intensity = score_content("CJ-BAIL1", "Cash bail often results...")
    # fav=1, intensity=NaN, has_intensity=False  (binary question, honest intensity)

Three scoring types:
    likert          — Agree/Disagree or Support/Oppose scales. favorable_side = "agree"|"oppose"|"support"
    binary          — Forced two-option choice. favorable_contains = substring of favorable response
    multi_favorable — Multiple phrasings across surveys. favorable_contains = [list of substrings]

Per-entry fields:
    type:               "likert" | "binary" | "multi_favorable"
    favorable_side:     for likert — "agree", "oppose", or "support"
    favorable_contains: for binary/multi — substring or list of substrings
    base_ideology:      "liberal" | "conservative" (which ideology is the natural base for BH scoring)
                        Defaults to "liberal" for CJ/HI, "conservative" for Energy/CCS.
    exclude_surveys:    optional list of survey_ids to skip

v2 classifier fixes (April 2026):
    - Bare "Support"/"Agree" → moderate favorable (intensity 0.5), not "other"
    - Bare "Oppose"/"Disagree" → moderate unfavorable (intensity 0.5)
    - "Strongly" variants → intensity 1.0
    - "Somewhat" variants → intensity 0.5

v5 generalization (April 2026):
    - Renamed REFORM_DIRECTION → FAVORABLE_DIRECTION (domain-agnostic)
    - Added base_ideology per entry (replaces hardcoded domain check in BH scoring)
    - REFORM_DIRECTION kept as backward-compatible alias

Author: Actionable Intel / Preston Robinson
Date: April 7, 2026
"""

import re
import math

# ══════════════════════════════════════════════════════════════════════════════
# FAVORABLE_DIRECTION — Single source of truth for scoring each QID
# ══════════════════════════════════════════════════════════════════════════════
#
# type: "likert" | "binary" | "multi_favorable"
# favorable_side: for likert — "agree", "oppose", or "support"
# favorable_contains: for binary — substring; for multi_favorable — list of substrings
# base_ideology: "liberal" | "conservative" — which side is the natural base for BH scoring
#                CJ/HI default to "liberal", CCS/Energy to "conservative"
# exclude_surveys: optional list of survey_ids to skip

FAVORABLE_DIRECTION = {

    # ── APPROACH TO CRIME ─────────────────────────────────────────────────
    "CJ-APPROACH1":  {"type": "binary", "favorable_contains": "do not increase"},

    # ── BAIL ──────────────────────────────────────────────────────────────
    "CJ-BAIL1":  {"type": "binary", "favorable_contains": "jailed simply because"},
    "CJ-BAIL2":  {"type": "binary", "favorable_contains": "primarily for people who pose"},
    "CJ-BAIL3":  {"type": "binary", "favorable_contains": "discretion to consider individual"},
    "CJ-BAIL4":  {"type": "binary", "favorable_contains": "reason to limit pretrial"},

    # ── CANDIDATE PREFERENCE (ballot test — reform vs. tough-on-crime) ────
    "CJ-CAND1":    {"type": "binary", "favorable_contains": "improve the system"},
    "CJ-Q54":      {"type": "binary", "favorable_contains": "improve the system"},
    "CJ-CAND-OMN1": {"type": "binary", "favorable_contains": "Candidate A"},  # reform-oriented candidate = Ax1 system-faith proxy
    "CJ-CAND-OMN1-B": {"type": "multi_favorable", "favorable_contains": ["Candidate A", "first candidate"]},  # same ballot test, alt response labels

    # ── ISSUE SALIENCE (single-issue "would you support a candidate who...") ─
    # No counter-case presented; measures issue appeal, not electoral viability
    "CJ-CAND2":    {"type": "likert", "favorable_side": "support"},    # more likely = reform (LWOP replacement)
    "CJ-CAND3":    {"type": "likert", "favorable_side": "support"},    # more likely = reform (sentence review)
    "CJ-Q106":     {"type": "likert", "favorable_side": "support"},    # more likely = reform (DV/trafficking consideration)

    # ── CLEMENCY ──────────────────────────────────────────────────────────
    "CJ-CLEMENCY1": {"type": "binary", "favorable_contains": "important tool"},

    # ── COMPASSION / ELDERLY RELEASE ──────────────────────────────────────
    "CJ-COMPASSION1": {"type": "likert", "favorable_side": "support"},
    "CJ-COMPASSION2": {"type": "likert", "favorable_side": "agree"},
    "CJ-COMPASSION3": {"type": "binary", "favorable_contains": "Releasing elderly"},
    "CJ-COMPASSION4": {"type": "binary", "favorable_contains": "compassionate release is a responsible"},
    "CJ-ELDERLY1":    {"type": "binary", "favorable_contains": "Releasing elderly"},
    "CJ-ELDERLY-COST1": {"type": "binary", "favorable_contains": "compassionate release is a responsible"},
    "CJ-Q85":    {"type": "likert", "favorable_side": "support"},    # same as COMPASSION1
    "CJ-Q86":    {"type": "likert", "favorable_side": "agree"},      # same as COMPASSION2
    "CJ-Q87":    {"type": "binary", "favorable_contains": "Releasing elderly"},
    "CJ-Q88":    {"type": "binary", "favorable_contains": "compassionate release is a responsible"},
    "CJ-VICTIM-COMPASSION1": {"type": "likert", "favorable_side": "agree"},

    # ── CONDITIONS ────────────────────────────────────────────────────────
    "CJ-CONDITIONS1": {"type": "binary", "favorable_contains": "safe and humane"},

    # ── COURT REVIEW / SENTENCE REVIEW ────────────────────────────────────
    "CJ-COURTREVIEW1": {"type": "binary", "favorable_contains": "regular process to review"},
    "CJ-Q89":      {"type": "binary", "favorable_contains": "regular process to review"},
    "CJ-SENTREVIEW1": {"type": "binary", "favorable_contains": "regular process to review"},
    "CJ-REVIEW1":  {"type": "binary", "favorable_contains": "opportunity for review"},
    "CJ-RETRO1":   {"type": "binary", "favorable_contains": "opportunity for review"},

    # ── CRIME PERCEPTION ──────────────────────────────────────────────────
    # CJ-CRIME1 STRUCK Apr 12 2026 (Preston): r=−0.19 with CRIME2/3.
    # "Crime going back down from Covid spike" correlates POSITIVELY with REDEMPTION/MENTAL_ADDICTION
    # but NEGATIVELY with the crime-attribution items. Genuine content split — not a direction error.
    # CRIME1 measures crime-trend perception; CRIME2/3 measure crime-attribution. Don't average.
    # "CJ-CRIME1":   {"type": "likert", "favorable_side": "agree"},
    "CJ-CRIME2":   {"type": "likert", "favorable_side": "oppose"},   # DISAGREE = reform (rejects police-work-alone attribution)
    "CJ-CRIME3":   {"type": "likert", "favorable_side": "oppose"},   # DISAGREE = reform (rejects reform-caused-crime)

    # ── DATA / TRANSPARENCY ───────────────────────────────────────────────
    "CJ-DATA1":    {"type": "likert", "favorable_side": "agree"},    # police report crime stats

    # ── DEATH PENALTY ─────────────────────────────────────────────────────
    "CJ-DP1":      {"type": "binary", "favorable_contains": "Oppose"},
    "CJ-DP2":      {"type": "multi_favorable", "favorable_contains": ["Certain beyond any doubt", "oppose the death penalty"]},
    "CJ-DP3":      {"type": "multi_favorable", "favorable_contains": ["A great deal", "oppose the death penalty"]},
    "CJ-DP4":      {"type": "multi_favorable", "favorable_contains": ["irreversible", "oppose the death penalty"]},
    "CJ-DP5":      {"type": "binary", "favorable_contains": "Life in prison"},
    "CJ-DP6":      {"type": "binary", "favorable_contains": "Support pausing"},
    # CJ-DP-OMN1 moved to SKIPPED_QIDS — message-testing format (picks among reform frames), not reform orientation
    "CJ-DP-OMN2":  {"type": "likert", "favorable_side": "support"},  # moratorium on executions
    "CJ-PROS2":    {"type": "binary", "favorable_contains": "irreversible"},  # reclassified → DP (death penalty evidence certainty, not prosecutor-related)
    # NC-DP-CERTAINTY1 excluded — verbatim dup of NC-DP4 (see _COMPOUND_CONSTRUCT comment)
    "NC-DP4":      {"type": "binary", "favorable_contains": "irreversible"},

    # ── DETERRENCE ────────────────────────────────────────────────────────
    "CJ-DETER1":       {"type": "binary", "favorable_contains": "do not make us safer"},
    "CJ-DETER2":       {"type": "binary", "favorable_contains": "little deterrent"},
    "CJ-DETER-OMN1":   {"type": "multi_favorable", "favorable_contains": ["do not make us safer", "long prison sentences do not"]},
    "CJ-DETER-OMN1-B": {"type": "binary", "favorable_contains": "do not make us safer"},

    # ── DISCRETION ────────────────────────────────────────────────────────
    "CJ-DISCRET1": {"type": "likert", "favorable_side": "agree"},    # judges should have more discretion

    # ── DOMESTIC VIOLENCE ─────────────────────────────────────────────────
    "CJ-DV1":      {"type": "binary", "favorable_contains": "Consider abuse"},
    "CJ-DV2":      {"type": "likert", "favorable_side": "support"},
    "CJ-DV3":      {"type": "likert", "favorable_side": "support"},
    "CJ-DV4":      {"type": "binary", "favorable_contains": "should be considered because"},
    "CJ-DV5":      {"type": "likert", "favorable_side": "support"},
    "CJ-DV6":      {"type": "binary", "favorable_contains": "opportunity for sentence review"},
    "CJ-DV7":      {"type": "binary", "favorable_contains": "continuing to punish"},  # reclassified → SENTREVIEW (sentencing risk tradeoff, not DV-specific)
    "CJ-DV-OMN1a": {"type": "binary", "favorable_contains": "history of abuse should be considered"},
    "CJ-DV-OMN1b": {"type": "likert", "favorable_side": "support"},  # more likely = reform
    "CJ-DV-OMN2":  {"type": "binary", "favorable_contains": "Appeal for resentencing"},  # reclassified → REVIEW (retroactive resentencing, not DV-specific)
    "CJ-Q26":      {"type": "binary", "favorable_contains": "consider evidence"},

    # ── DRUG POSSESSION ───────────────────────────────────────────────────
    "CJ-DRUG1":     {"type": "binary", "favorable_contains": "misdemeanor"},
    "CJ-DRUGPOSS1": {"type": "binary", "favorable_contains": "misdemeanor"},

    # ── EARLY RELEASE ─────────────────────────────────────────────────────
    "CJ-EARLYRELEASE1": {"type": "binary", "favorable_contains": "early release"},
    "CJ-Q84":       {"type": "binary", "favorable_contains": "early release"},

    # ── EQUITY ────────────────────────────────────────────────────────────
    # CJ-EQUITY1 is multi-option (5 choices), not binary — skip
    # CJ-RACIAL1, CJ-Q91, CJ-Q115: concerned about disparities
    "CJ-RACIAL1":  {"type": "likert", "favorable_side": "support"},  # concerned = reform
    "CJ-Q91":      {"type": "likert", "favorable_side": "support"},
    "CJ-Q115":     {"type": "likert", "favorable_side": "support"},

    # ── EXPUNGEMENT / RECORD ──────────────────────────────────────────────
    "CJ-EXPUNGE-OMN1": {"type": "likert", "favorable_side": "agree"},
    "CJ-Q97":      {"type": "likert", "favorable_side": "support"},
    "CJ-Q118":     {"type": "likert", "favorable_side": "support"},
    "CJ-RECORD1":  {"type": "binary", "favorable_contains": "clearing or sealing"},
    "NC-EXPUNGE1":     {"type": "likert", "favorable_side": "support"},
    "NC-RECORD-CLEAR1": {"type": "likert", "favorable_side": "support"},

    # ── FAMILY ────────────────────────────────────────────────────────────
    "CJ-FAMILY1":  {"type": "binary", "favorable_contains": "limit harm to children"},

    # ── FELONY CLASSIFICATION ─────────────────────────────────────────────
    "CJ-CLASS1":   {"type": "likert", "favorable_side": "support"},
    "CJ-Q142":     {"type": "likert", "favorable_side": "support"},

    # ── FINES & FEES ──────────────────────────────────────────────────────
    "CJ-FINES1":   {"type": "binary", "favorable_contains": "ability to pay"},
    "CJ-FINES2":   {"type": "binary", "favorable_contains": "should not face additional"},
    "CJ-FINES3":   {"type": "likert", "favorable_side": "agree"},
    "CJ-FINES4":   {"type": "binary", "favorable_contains": "alternatives"},

    # ── FISCAL ────────────────────────────────────────────────────────────
    "CJ-FISCAL1":  {"type": "binary", "favorable_contains": "better spent"},
    "CJ-SPENDING1": {"type": "binary", "favorable_contains": "focus resources"},
    "NC-FISCAL1":  {"type": "binary", "favorable_contains": "focus resources"},
    "VA-FISCAL1":  {"type": "binary", "favorable_contains": "focus resources"},
    "CJ-Q116":     {"type": "binary", "favorable_contains": "rehabilitation"},

    # ── INNOCENCE ─────────────────────────────────────────────────────────
    "CJ-INNOCENCE1": {"type": "multi_favorable", "favorable_contains": ["support this program"]},

    # ── INVESTMENT IN COMMUNITIES ─────────────────────────────────────────
    "CJ-INVEST-OMN1": {"type": "likert", "favorable_side": "agree"},
    "CJ-INVEST1":  {"type": "likert", "favorable_side": "agree"},
    "CJ-Q124":     {"type": "likert", "favorable_side": "agree"},

    # ── JUVENILE JUSTICE ──────────────────────────────────────────────────
    "CJ-JUV1":     {"type": "binary", "favorable_contains": "different consideration"},
    # CJ-JUV-OMN1, OMN2, OMN3 moved to SKIPPED — 2024 message-testing pair, not standalone
    # reform-direction items. Analytical value is in cross-tab (who agrees with BOTH
    # contradictory framings), not individual favorable rate.
    # CJ-Q119 also moved — identical question text to JUV-OMN2, same issue.

    # ── LITERACY / EDUCATION ──────────────────────────────────────────────
    "CJ-LIT1":     {"type": "binary", "favorable_contains": "required when needed"},
    "CJ-LIT-OMN1a": {"type": "binary", "favorable_contains": "support"},
    "CJ-LIT-OMN1-B": {"type": "likert", "favorable_side": "support"},
    "CJ-LIT-OMN2": {"type": "likert", "favorable_side": "support"},  # more likely = reform
    "CJ-LIT-OMN3": {"type": "likert", "favorable_side": "support"},
    "CJ-LIT-OMN4": {"type": "likert", "favorable_side": "support"},

    # ── LWOP (Life Without Parole) ────────────────────────────────────────
    "CJ-LWOP1":    {"type": "binary", "favorable_contains": "review"},

    # ── MANDATORY MINIMUMS ────────────────────────────────────────────────
    "CJ-MAND1":    {"type": "binary", "favorable_contains": "discretion"},
    "CJ-MAND2":    {"type": "binary", "favorable_contains": "depart"},
    # CJ-MAND-OMN1/OMN2 moved to SKIPPED_RETAIN — message-testing pair (2024):
    # OMN1 = pro-reform framing ("judges shouldn't be constrained by legislature")
    # OMN2 = anti-reform framing ("judges are too soft on crime" — racially coded in southern context)
    "CJ-Q110":     {"type": "binary", "favorable_contains": "individual role"},
    "NC-MAND-DEPART1": {"type": "binary", "favorable_contains": "depart"},
    "NC-MAND2":    {"type": "binary", "favorable_contains": "depart"},

    # ── MENTAL HEALTH & ADDICTION (merged construct) ────────────────────────
    "CJ-MENTAL1":  {"type": "likert", "favorable_side": "agree"},   # mentally ill → treatment facility
    "CJ-MENTAL2":  {"type": "likert", "favorable_side": "agree"},   # mentally ill → treatment facility
    "CJ-MENTAL3":  {"type": "likert", "favorable_side": "agree"},   # mentally ill → outpatient treatment
    "CJ-ADDICT1":  {"type": "likert", "favorable_side": "agree"},   # addiction → treatment facility
    "CJ-ADDICT2":  {"type": "likert", "favorable_side": "agree"},   # addiction → treatment facility
    "CJ-ADDICT3":  {"type": "likert", "favorable_side": "agree"},   # addiction → outpatient treatment
    "CJ-APPROACH2":  {"type": "binary", "favorable_contains": "Mental health"},  # MH services vs prison deterrent
    "CJ-CRIMEAPPROACH1": {"type": "binary", "favorable_contains": "Mental health"},  # MH services vs prison deterrent
    "CJ-Q107":     {"type": "binary", "favorable_contains": "mental health"},
    "CJ-Q117":     {"type": "binary", "favorable_contains": "mental health"},
    "CJ-Q189":     {"type": "likert", "favorable_side": "agree"},
    "CJ-Q190":     {"type": "likert", "favorable_side": "agree"},   # addiction → treatment facility (was in ADDICT)
    "CJ-Q193":     {"type": "likert", "favorable_side": "agree"},
    "CJ-Q194":     {"type": "likert", "favorable_side": "agree"},   # addiction → treatment facility (was in ADDICT)
    "CJ-Q201":     {"type": "likert", "favorable_side": "agree"},
    "CJ-Q202":     {"type": "likert", "favorable_side": "agree"},   # addiction → outpatient treatment (was in ADDICT)

    # ── PAROLE / GOOD TIME ────────────────────────────────────────────────
    "CJ-PAROLE1":  {"type": "binary", "favorable_contains": "Earn time"},
    "CJ-Q197":     {"type": "likert", "favorable_side": "agree"},    # sentence reductions for good behavior
    "CJ-REVIEW-OMN4": {"type": "likert", "favorable_side": "agree"},  # good-time credit (reclassified from REVIEW)

    # ── PLEA BARGAINING ───────────────────────────────────────────────────
    "CJ-PLEA1":    {"type": "binary", "favorable_contains": "pressured"},

    # ── PROMISE / EQUAL JUSTICE ───────────────────────────────────────────
    "CJ-PROMISE1": {"type": "likert", "favorable_side": "oppose"},   # "Falls short" = reform

    # ── PROPORTIONALITY ───────────────────────────────────────────────────
    "CJ-PROP1":    {"type": "binary", "favorable_contains": "individual actions"},
    # CJ-PROP-OMN1 moved to SKIPPED_RETAIN — message-testing with ambiguous accomplice scenario (2024)
    "CJ-Q92":      {"type": "binary", "favorable_contains": "individual actions"},
    "CJ-Q111":     {"type": "likert", "favorable_side": "support"},  # separate accomplice crime
    "CJ-Q114":     {"type": "binary", "favorable_contains": "judge and jury"},

    # ── PROSECUTORS ───────────────────────────────────────────────────────
    "CJ-PROS1":    {"type": "multi_favorable", "favorable_contains": ["pressure to secure convictions", "under pressure"]},
    "CJ-PROS-OMN1": {"type": "multi_favorable", "favorable_contains": ["I do not trust", "Trust but verify", "more oversight"]},

    # ── PUBLIC DEFENDERS ──────────────────────────────────────────────────
    "CJ-PD1":      {"type": "binary", "favorable_contains": "afford private attorneys"},
    "CJ-PD2":      {"type": "likert", "favorable_side": "agree"},
    "CJ-PD2-B":    {"type": "likert", "favorable_side": "agree"},
    "CJ-Q33":      {"type": "likert", "favorable_side": "agree"},

    # ── REENTRY ───────────────────────────────────────────────────────────
    "CJ-REENTRY1":     {"type": "binary", "favorable_contains": "help provide basic literacy"},
    "CJ-REENTRY-OMN1": {"type": "likert", "favorable_side": "agree"},
    "CJ-REENTRY-OMN2": {"type": "likert", "favorable_side": "agree"},
    "CJ-Q204":     {"type": "likert", "favorable_side": "agree"},    # job placement > prison
    "CJ-REHAB1":   {"type": "likert", "favorable_side": "agree"},    # rehabilitative programming

    # ── REVIEW / SECOND LOOK ──────────────────────────────────────────────
    "CJ-REVIEW2":      {"type": "likert", "favorable_side": "agree"},
    "CJ-REVIEW-OMN1":  {"type": "likert", "favorable_side": "agree"},
    "CJ-REVIEW-OMN1-B": {"type": "likert", "favorable_side": "agree"},
    # CJ-REVIEW-OMN2 moved to SKIPPED_RETAIN — violent+10yr framing test (trailed violent+20yr in same survey)
    # CJ-REVIEW-OMN4 reclassified → GOODTIME (good-time credit, not sentence review)
    # CJ-REVIEW3 moved to SKIPPED_RETAIN — kitchen-sink multi-option, artificially high (85.6%)

    # ── TOUGH ON CRIME ────────────────────────────────────────────────────
    "CJ-TOUGHCRIME1": {"type": "likert", "favorable_side": "oppose"},  # DISAGREE = reform
    "CJ-LAW85-1":    {"type": "likert", "favorable_side": "oppose"},   # DISAGREE = reform (85% serve rule)

    # ── TRAFFICKING ───────────────────────────────────────────────────────
    "CJ-TRAFFICK1": {"type": "likert", "favorable_side": "agree"},
    "CJ-TRAFFICK2": {"type": "likert", "favorable_side": "agree"},

    # ── TREATMENT / DRUG COURTS ───────────────────────────────────────────
    "CJ-Q130":          {"type": "likert", "favorable_side": "agree"},
    "CJ-TREATMENT-OMN1": {"type": "likert", "favorable_side": "agree"},

    # ── SYSTEM IMPACT PERCEPTION (system trust proxy) ────────────────────────
    # Belief that tough-on-crime didn't deliver = doesn't trust the system's promises
    "CJ-IMPACT1":  {"type": "multi_favorable", "favorable_contains": ["less safe", "about the same"]},  # laws didn't improve safety = reform-favorable

    # ── TRUST ─────────────────────────────────────────────────────────────
    # CRITICAL: Low trust = reform-favorable (old method had this BACKWARDS)
    "CJ-TRUST1":   {"type": "likert", "favorable_side": "oppose"},   # low trust = reform

    # ── VIRGINIA ITEMS ────────────────────────────────────────────────────
    "VA-COUNSEL2":     {"type": "binary", "favorable_contains": "Yes"},
    "VA-FIRSTAPPEAR1": {"type": "binary", "favorable_contains": "Yes"},

    # ── LOUISIANA STATE ITEMS ─────────────────────────────────────────────
    "LA-AGING1":    {"type": "binary", "favorable_contains": "Age, health, and rehabilitation"},
    "LA-COURT1":    {"type": "binary", "favorable_contains": "carefully review"},
    "LA-EXPUNGE1":  {"type": "binary", "favorable_contains": "more affordable"},
    "LA-GOODTIME1": {"type": "binary", "favorable_contains": "greater opportunity"},
    # LA-JUDICIAL1 and LA-JUDICIAL2 removed — judicial election items, not CJ reform attitudes; moved to SKIPPED_RETAIN
    "LA-JURY1":     {"type": "binary", "favorable_contains": "opportunity for review"},
    "LA-REVISIT1":  {"type": "binary", "favorable_contains": "willing to revisit"},

    # ── OKLAHOMA STATE ITEMS ─────────────────────────────────────────────
    # OK-CJ-2024-001 influence-scale battery: "How much does X influence case outcomes?"
    # Favorable = acknowledges ANY influence (major OR minor) — reform position is that these factors DO affect outcomes.
    # Unfavorable = denies influence ("Not enough to change an outcome" / "No influence at all") — status quo denial.
    # Using both tiers because "A minor influence" is the modal response on gender (33%) — scoring it unfavorable
    # would misread the plurality position. The fault line is acknowledgment vs. denial, not magnitude.
    "CJ-OK-EQUITY-LAWYER": {"type": "multi_favorable", "favorable_contains": ["major influence", "minor influence"]},  # wealth/lawyer access
    "CJ-Q178":             {"type": "multi_favorable", "favorable_contains": ["major influence", "minor influence"]},  # defendant's race
    "CJ-Q180":             {"type": "multi_favorable", "favorable_contains": ["major influence", "minor influence"]},  # defendant's gender
    "CJ-Q181":             {"type": "multi_favorable", "favorable_contains": ["major influence", "minor influence"]},  # public defender workload
    "CJ-Q182":             {"type": "multi_favorable", "favorable_contains": ["major influence", "minor influence"]},  # prosecutor's political interests
    "CJ-Q184":             {"type": "multi_favorable", "favorable_contains": ["major influence", "minor influence"]},  # judge's temperament
    "CJ-Q185":             {"type": "multi_favorable", "favorable_contains": ["major influence", "minor influence"]},  # media coverage
    "CJ-OK-APPROACH-LEADERS": {"type": "binary", "favorable_contains": "Smart on crime"},
    "CJ-OK-COVID-CRIME":     {"type": "likert", "favorable_side": "agree"},   # crime up from Covid, falling back
    "CJ-OK-DETER-2024":      {"type": "binary", "favorable_contains": "do not make us safer"},
    "CJ-OK-DP-EXONERATION":  {"type": "multi_favorable", "favorable_contains": ["DNA evidence should be required", "risk of executing an innocent", "oppose the death penalty"]},
    "CJ-OK-DV-ABUSE-MITIGATION": {"type": "binary", "favorable_contains": "history of abuse should be considered"},
    "CJ-OK-DV-TRAFFICKING":  {"type": "likert", "favorable_side": "agree"},   # trafficking victims deserve consideration
    "CJ-OK-DV-TREATMENT":    {"type": "likert", "favorable_side": "agree"},   # treatment facility instead of prison
    "CJ-OK-JUV-LWOP":        {"type": "binary", "favorable_contains": "possibility of being rehabilitated"},
    "CJ-OK-LIT-GED":         {"type": "likert", "favorable_side": "support"},
    "CJ-OK-PAROLE-GOODTIME": {"type": "likert", "favorable_side": "agree"},
    # CJ-OK-PROP-ACCOMPLICE moved to SKIPPED_RETAIN — message-testing with ambiguous accomplice scenario (2024)
    "CJ-OK-PROS-TRUST":      {"type": "multi_favorable", "favorable_contains": ["I do not trust", "Trust but verify", "more oversight"]},
    "CJ-OK-PROS2-FLEXIBILITY": {"type": "binary", "favorable_contains": "flexibility to account for individual"},
    "CJ-OK-RECORD-JUV":      {"type": "likert", "favorable_side": "agree"},   # records should be confidential
    "CJ-JUV-OMN3":           {"type": "likert", "favorable_side": "agree"},   # same question, reclassified from JUV SKIPPED → RECORD
    "CJ-OK-REENTRY-LITERACY": {"type": "likert", "favorable_side": "support"},
    "CJ-OK-REFORM-BLAME":    {"type": "likert", "favorable_side": "oppose"},  # DISAGREE = reform (rejects reform-caused-crime)
    "CJ-OK-REVIEW-LIMITED":  {"type": "binary", "favorable_contains": "allow limited sentence review"},
    "CJ-OK-REVIEW-SECONDLOOK": {"type": "likert", "favorable_side": "agree"},

    # ── NEW JERSEY STATE ITEMS ───────────────────────────────────────────
    "CJ-NJ-JUV-ACCOUNTABILITY": {"type": "binary", "favorable_contains": "prioritize rehabilitation"},
    "CJ-NJ-JUV-CANDIDATE":  {"type": "likert", "favorable_side": "support"},  # more likely = reform
    "CJ-NJ-JUV-DECISION":   {"type": "binary", "favorable_contains": "judge should make that decision"},
    "CJ-NJ-JUV-JUDGE":      {"type": "likert", "favorable_side": "support"},
    "CJ-NJ-JUV-WAIVER":     {"type": "binary", "favorable_contains": "remain in the juvenile justice system"},

    # ── NORTH CAROLINA STATE ITEMS ───────────────────────────────────────
    "NC-CAND-DV1":       {"type": "likert", "favorable_side": "support"},  # more likely = reform
    "NC-CAND1":          {"type": "likert", "favorable_side": "support"},  # reclassified → ISSUE_SALIENCE (no counter-case)
    "NC-DISPARITIES1":   {"type": "likert", "favorable_side": "support"},  # concerned = reform

    # ── VIRGINIA STATE ITEMS (additions) ─────────────────────────────────
    "VA-ALPR1":          {"type": "binary", "favorable_contains": "Oppose"},  # oppose surveillance
    "VA-COUNSEL1":       {"type": "binary", "favorable_contains": "Support"},  # support right to counsel
    "VA-DISPARITIES1":   {"type": "likert", "favorable_side": "support"},  # concerned = reform
    "VA-REFORM1":        {"type": "multi_favorable", "favorable_contains": ["more safe"]},  # "No change in safety" = neutral, not favorable
    "VA-REFORMS1":       {"type": "multi_favorable", "favorable_contains": ["more safe"]},  # "No change in safety" = neutral, not favorable

    # ── ADDITIONAL CJ ITEMS ──────────────────────────────────────────────
    "LA-JURY1-B":        {"type": "multi_favorable", "favorable_contains": ["eligible for resentencing", "receive new trials"]},

    # ── HEALTH INSURANCE (policy-relevant additions) ─────────────────────
    "HI-REGULATION1":    {"type": "binary", "favorable_contains": "government should regulate"},
    "HI-FREEMARKET1":    {"type": "binary", "favorable_contains": "needs more state government oversight"},

    # ── CCS / ENERGY DOMAIN ───────────────────────────────────────────────
    "CCS-COMPETE1":   {"type": "likert", "favorable_side": "agree"},
    "CCS-COMPETE1-B": {"type": "likert", "favorable_side": "agree"},
    "CCS-EMINENT1":   {"type": "likert", "favorable_side": "agree"},
    "CCS-ENV1":       {"type": "likert", "favorable_side": "agree"},
    "CCS-GND1":       {"type": "likert", "favorable_side": "agree"},
    # NOTE: CCS-JOBS1, JOBS1-B, LOCAL1, PIPE1, SAFETY1, SAFETY1-B, STORAGE1/1-B/2/2-B,
    # TAX1, WASTE1, WELLS1 removed — not present in DB (phantom entries from old config)

    "CCS-INCENTIVE1":     {"type": "binary", "favorable_contains": "support incentives"},
    "CCS-OPINION1":       {"type": "multi_favorable", "favorable_contains": ["protects and creates jobs", "reduces pollution"]},
    "CCS-RISK1":          {"type": "likert", "favorable_side": "oppose"},   # DISAGREE = reform (CCS is NOT too risky)
    "CCS-SAFE1":          {"type": "likert", "favorable_side": "agree"},    # agree CCS is proven safe
    "CCS-SCAM1":          {"type": "likert", "favorable_side": "oppose"},   # DISAGREE = reform (CCS is NOT a scam)
    "CCS-SCAM1-B":        {"type": "likert", "favorable_side": "oppose"},   # DISAGREE = reform (CCS is NOT a waste)

    # ── HEALTH INSURANCE (policy-relevant only) ───────────────────────────
    "HI-REGULATION2": {"type": "binary", "favorable_contains": "additional regulation"},
}

# Backward-compatible alias
REFORM_DIRECTION = FAVORABLE_DIRECTION


# ══════════════════════════════════════════════════════════════════════════════
# DEFAULT BASE IDEOLOGY BY DOMAIN PREFIX
# ══════════════════════════════════════════════════════════════════════════════
#
# Used by VIP scoring when an entry doesn't specify its own base_ideology.
# The BH "ideological core" calculation uses this to decide whether the
# natural base is liberal or conservative.

DOMAIN_BASE_IDEOLOGY = {
    "CJ": "liberal",      # CJ reform base is liberal
    "NC": "liberal",      # NC CJ items
    "VA": "liberal",      # VA CJ items
    "LA": "liberal",      # LA CJ items
    "NJ": "liberal",      # NJ juvenile justice
    "HI": "liberal",      # Health insurance regulation
    "CCS": "conservative", # Carbon capture / energy — industry-friendly base
    "POL": "liberal",      # Default for political items
    "EBR": "liberal",      # Default for EBR items
}


def get_base_ideology(qid):
    """
    Return the base ideology for BH scoring.
    Checks the entry's own base_ideology first, then falls back to domain default.
    """
    config = FAVORABLE_DIRECTION.get(qid, {})
    if "base_ideology" in config:
        return config["base_ideology"]
    # Fall back to domain prefix
    prefix = qid.split("-")[0] if qid else ""
    return DOMAIN_BASE_IDEOLOGY.get(prefix, "liberal")


# ══════════════════════════════════════════════════════════════════════════════
# SKIPPED_DEMOGRAPHIC — Already captured in L1; EXCLUDE from L2 at LOAD time
# ══════════════════════════════════════════════════════════════════════════════
#
# These QIDs duplicate L1 fields (party, age, gender, race, education) or are
# pure screeners (voter reg, likely voter) with no analytical value in L2.
# The LOAD stage filters these out before upsert to reduce L2 row count.

SKIPPED_DEMOGRAPHIC = {
    # Age / gender / race (already in L1 demographic columns)
    "CJ-Q35", "CJ-Q67", "CJ-Q67-B", "CJ-Q90",  # CJ-Q67-B is NJ voter-reg screener (same as CJ-Q67)
    # Voter registration screeners
    "CJ-VOTEREG1", "CJ-OK-VOTEREG-2025", "NC-VOTEREG1", "VA-VOTEREG1", "POL-VOTEREG1",
    # Likely voter / vote certainty
    "CJ-VOTE1", "CJ-VOTE1-B", "CJ-OK-VOTE-CERTAIN2024",
    # Region / geography
    "CJ-OK-REGION", "CJ-METRO1",
    # Housing / income
    "CJ-OK-HOUSING", "CJ-OK-INCOME", "EBR-HOUSING",
    # Party ID (already in L1 party_id)
    "CCS-PARTY1",
}


# ══════════════════════════════════════════════════════════════════════════════
# SKIPPED_RETAIN — Not VIP-scoreable, but KEEP in L2 for downstream analysis
# ══════════════════════════════════════════════════════════════════════════════
#
# These QIDs are not scoreable for reform direction (no favorable/unfavorable),
# but they stay in L2 because they serve the broader polling infrastructure:
#   - Media consumption & religion → BF (Belief Filter) battery for archetypes
#   - CJ system perception & factor attribution → future BF constructs
#   - Horse-race, favorability, candidate matchups → SLA & client deliverables
#   - Non-CJ policy (education, infrastructure, energy) → omnibus polling value
#   - HI/CCS brand research → client deliverables
#
# The LOAD stage keeps these. The SCORE stage ignores them (not in REFORM_DIRECTION).

SKIPPED_RETAIN = {
    # ── BF CORE: Media consumption (behavioral past-action) ─────────────
    "EBR-CHURCH", "EBR-CNN", "EBR-FOX-NEWS", "EBR-LOCAL-NEWSPAPERS",
    "EBR-LOCAL-TV-MORNING-SHOWS", "EBR-LOCAL-TV-NEWS", "EBR-SOCIAL-MEDIA",
    "EBR-STREAMING-TV", "EBR-TALK-RADIO", "EBR-FAMILY-AND-FRIENDS",
    "POL-CHURCH", "POL-CNN", "POL-FOX-NEWS", "POL-LOCAL-NEWSPAPERS",
    "POL-LOCAL-TV-MORNING-SHOWS", "POL-LOCAL-TV-NEWS", "POL-SOCIAL-MEDIA",
    "POL-STREAMING-TV", "POL-TALK-RADIO", "POL-FAMILY-AND-FRIENDS",
    # ── BF CORE: Religion (behavioral) ──────────────────────────────────
    "CJ-CHURCH1", "NC-CHURCH1", "NC-CHURCHFREQ1",
    # ── BF: CJ system involvement (experiential) ───────────────────────
    "CJ-Q108", "NC-CJINVOLVE1", "NC-PERSONAL-CJ1",
    # ── BF: Factor attribution / system perception ──────────────────────
    "CJ-FACTOR-GENDER", "CJ-FACTOR-JUDGE", "CJ-FACTOR-LAWYER",
    "CJ-FACTOR-MEDIA", "CJ-FACTOR-PD", "CJ-FACTOR-PROS", "CJ-FACTOR-RACE",
    "CJ-Q178", "CJ-Q180", "CJ-Q181", "CJ-Q182", "CJ-Q184", "CJ-Q185",
    "CJ-OK-EQUITY-LAWYER",
    # ── BF: Safety perception, crime attribution, equity, fiscal ────────
    "CJ-SAFETY1", "CJ-CRIME2", "CJ-EQUITY1", "CJ-FISCAL2",
    # CJ-IMPACT1 moved to REFORM_DIRECTION — system-trust proxy
    # ── BF: Purpose of prison / review rankings (JSON) ──────────────────
    "CJ-EQUITY1-RANK", "CJ-PURPOSE1", "CJ-PURPOSE1-C", "CJ-PURPOSE1b",
    "CJ-REVIEW-OMN3",
    # CJ-CAND-OMN1-B moved to FAVORABLE_DIRECTION (same ballot test as CAND-OMN1, alt response labels)
    # ── Death penalty message-testing (picks among reform frames, not orientation)
    "CJ-DP-OMN1",
    # ── Juvenile records message-testing pair (2024) — designed to find people
    # who agree with BOTH contradictory framings; not standalone reform items.
    # CJ-Q119 is identical question text to JUV-OMN2 (different survey wave).
    "CJ-JUV-OMN1", "CJ-JUV-OMN2", "CJ-Q119",
    # NOTE: CJ-JUV-OMN3 removed from SKIPPED — same question as CJ-OK-RECORD-JUV,
    # reclassified to RECORD construct. Scored as likert agree.
    # ── Proportionality accomplice message-testing (2024) — ambiguous scenario
    # lets respondent imagine anything from getaway driver to active participant;
    # replaced by contextual versions (CJ-Q92, CJ-Q114) that got real opinions.
    "CJ-PROP-OMN1", "CJ-OK-PROP-ACCOMPLICE",
    # ── Apr 10 2026: TRAFFICK construct retired (Preston) ────────────────
    # Human trafficking sentencing items — not on the reform-attitude spectrum
    "CJ-TRAFFICK1", "CJ-TRAFFICK2",
    # ── Apr 10 2026: non-CJ items surfaced by audit_construct_coverage ──
    # These ride on CJ-prefixed surveys (LA/VA omnibus) but measure doctor,
    # insurance, metro, prison-conditions, duplicate voter-reg, etc — not
    # reform-attitude items. Added so the coverage audit runs clean.
    "CJ-CONDITIONS1",        # prison conditions ceiling-effect item (retired 2026)
    "CJ-LA-DOCTOR", "CJ-LA-INSURANCE", "CJ-LA-INSURANCE-2",
    "CJ-LA-INSURANCE-COST", "CJ-LA-TRIAL-COST",
    "CJ-VA-METRO-CLOSEST",
    "CJ-VOTE1-B-B",          # double-B suffix voter-registration screener
    # CCS domain items not already covered upstream
    "CCS-COMPETE1", "CCS-COMPETE1-B",
    "CCS-EMINENT1", "CCS-EMINENT1-B",
    "CCS-ENV1", "CCS-GND1", "CCS-INCENTIVE1", "CCS-OPINION1",
    "CCS-PRI-HOMEINS-B",
    "CCS-RISK1", "CCS-SAFE1",
    "CCS-SCAM1", "CCS-SCAM1-B",
    "CCS-TRUMP1-B",
    # ENERGY domain (LA energy/election omnibus — not CJ)
    "ENERGY-LA-CARBON-2", "ENERGY-LA-CARBON-3",
    "ENERGY-LA-ELECTION-SENATE", "ENERGY-LA-ELECTION-SENATE-2",
    "ENERGY-LA-INFORMATION-TRUST", "ENERGY-LA-PARISH-RESIDE",
    # ── Sentence review framing tests + kitchen sink ─────────────────────
    # OMN2 = violent+10yr (trailed violent+20yr in same survey; isolates timeframe effect)
    # REVIEW3 = multi-option "which factor matters most" — kitchen sink, artificially high
    "CJ-REVIEW-OMN2", "CJ-REVIEW3",
    # ── Mandatory minimums message-testing pair (2024) ───────────────────
    # OMN1 = "judges shouldn't be constrained"; OMN2 = "judges too soft on crime"
    "CJ-MAND-OMN1", "CJ-MAND-OMN2",
    # ── CJ favorability ratings (SLA deliverables) ──────────────────────
    "CJ-Q94", "CJ-Q96", "CJ-Q160", "CJ-Q168", "CJ-Q169", "CJ-TRUMP1",
    "CJ-OK-PRES2024", "CJ-OK-TRUMP-FAV",
    # ── Horse-race / political preference (SLA + omnibus deliverables) ──
    "POL-GOV2027-BALLOT", "POL-LANDRY-VS-LUNDY", "POL-LANDRY-VS-WILSON",
    "POL-LA-DIRECTION", "POL-WAGUESPACK", "POL-AUDITING1", "POL-VOTESYS1",
    "POL-VOTE1-PRES24", "POL-VOTE1-SEN26",
    "POL-CRIMINAL-JUSTICE-VOTE", "POL-EDUCATION-STATEMENT",
    "POL-CANDDIATE-SUPPORT-RESTORATION",
    # ── EBR candidate matchups (SLA deliverables) ───────────────────────
    "EBR-BROOME-VS-EDWARDS", "EBR-BROOME-VS-GUIDRY", "EBR-BROOME-VS-JAMES",
    "EBR-BROOME-VS-WHITE", "EBR-CONSIDER-REPUBLICAN", "EBR-CRIMINAL-JUSTICE-VOTE",
    "EBR-EDUCATION-STATEMENT", "EBR-GAUTREAUX-VS-GUIDRY", "EBR-JAMES-VS-WILSON",
    "EBR-REPUBLICAN-2024", "EBR-YOUR-SUPPORT",
    # ── HI brand/preference (client deliverables) ───────────────────────
    "HI-BCBS-CONNECT", "HI-BCBS-HISTORY1", "HI-BCBS-NAME", "HI-PET1",
    "HI-PETINS1", "HI-REBRAND1", "HI-LOCALCHOICE1", "HI-MERGERS1",
    "HI-COSTVALUE1a", "HI-COSTVALUE1b", "HI-NONPROFIT-VS-FP",
    # ── CCS non-policy (client deliverables) ────────────────────────────
    "CCS-LANDRY-CCS1", "CCS-LANDRY-CCS1-B", "CCS-LANDRY-CCS2a", "CCS-LANDRY-CCS2b",
    "CCS-TRUMP1", "CCS-SAFESCALE1",
    # ── CCS priority ranking items ──────────────────────────────────────
    "CCS-PRI-AUTOINS-2025", "CCS-PRI-AUTOINS-2026", "CCS-PRI-CCS",
    "CCS-PRI-CRIME-2025", "CCS-PRI-CRIME-2026", "CCS-PRI-EMINENT",
    "CCS-PRI-HEALTH-2025", "CCS-PRI-HEALTH-2026", "CCS-PRI-HOMEINS",
    "CCS-PRI-INFLATION", "CCS-PRI-SCHOOL-2025", "CCS-PRI-SCHOOL-2026",
    "CCS-PRI-TARIFF", "CCS-PRI-TAX-2025", "CCS-PRI-TAXREDUCE-2026",
    # ── LA non-directional ──────────────────────────────────────────────
    "LA-JUDICIAL1",  # judicial election priority — not CJ reform attitude
    "LA-JUDICIAL2",  # judicial independence — not CJ reform attitude
    # ── EBR domain (political / local issues — SLA deliverables) ────────
    "EBR-2020-PRESIDENT", "EBR-2024-PRESIDENT", "EBR-ADMINISTRATOR",
    "EBR-BLIGHT", "EBR-CAUCUS-CHAIR", "EBR-COACH",
    "EBR-CONSIDER-MOVING", "EBR-CONSOLIDATING", "EBR-CYBER-BULLYING",
    "EBR-DAILY-ROUTINE", "EBR-DEFENDED-CRIMINALS", "EBR-EAST-POLICE-DOING-GOOD",
    "EBR-ENDORSED", "EBR-FEEL-LESS-SAFE",
    "EBR-FUNDING", "EBR-GOVERNOR-VOTE-COMBINED",
    "EBR-GOVERNOR-VOTE-NO-ROTATE", "EBR-GOVERNOR-VOTE-ROTATED",
    "EBR-HURT-KILLED-BY-FETANYL", "EBR-LAW-ENFORCEMENT-TAX",
    "EBR-LAWSUIT", "EBR-LIED-TO-COUNCIL",
    "EBR-MAYOR-PRESIDENT-SECOND-CHOICE", "EBR-MAYOR-PRESIDENT-VOTE",
    "EBR-MOVING", "EBR-MURDERS", "EBR-NEW-PRISON", "EBR-NOT-VOTED",
    "EBR-OPINION-OF-BROOME", "EBR-OPINION-OF-CLARK", "EBR-OPINION-OF-EDWARDS",
    "EBR-OPINION-OF-GAUTREAUX", "EBR-OPINION-OF-GUIDRY", "EBR-OPINION-OF-HARRIS",
    "EBR-OPINION-OF-JAMES", "EBR-OPINION-OF-LANDRY", "EBR-OPINION-OF-MOORE",
    "EBR-OPINION-OF-MYERS", "EBR-OPINION-OF-TRUMP", "EBR-OPINION-OF-WELBORN",
    "EBR-OPINION-OF-WHITE", "EBR-OPINION-OF-WILSON",
    "EBR-OPPOSED-ST-GEORGE", "EBR-OWES-IRS", "EBR-PATROLLING",
    "EBR-POLICE-DOING-GOOD", "EBR-POTUS", "EBR-QUALITY-OF-LIFE",
    "EBR-RAIL-LINE", "EBR-RE-ELECT-BROOM", "EBR-RE-ELECT-BROOME",
    "EBR-RE-ELECT-CLARK", "EBR-RE-ELECT-GAUTREAUX", "EBR-RE-ELECT-MOORE",
    "EBR-RE-ELECT-WELBORN", "EBR-RE-ELECT-WILSON",
    "EBR-RECEIVED-SUPPORT", "EBR-SECOND-CHOICE", "EBR-SECOND-CHOICE-COMBINED",
    "EBR-SECOND-CHOICE-NO-ROTATE", "EBR-SECOND-CHOICE-ROTATED",
    "EBR-SERVED-2-TERMS", "EBR-ST-GEORGE",
    "EBR-ST-GEORGE-2023",
    "EBR-TRAFFIC-SITUATION", "EBR-UNSPENT-FUNDS", "EBR-VICTIMS-OF-SCAMS",
    "EBR-VOTE-KNOWING-INFO", "EBR-VS-PREVIOUS-ELECTIONS",
    # ── POL domain (LA political / policy — omnibus value) ──────────────
    "POL-ABORTION", "POL-ACCESS-TO-PROGRAMS", "POL-ADDITIONAL-TRANSPORTATION",
    "POL-APPROACH", "POL-BALLOT1", "POL-BALLOTCLARITY1", "POL-BCBS-SALE1",
    "POL-BEHAVIORAL-PROBLEMS", "POL-BETTER-PAY", "POL-BLIGHT",
    "POL-BLIGHTED-PROPERTY", "POL-CANDDIATE-SUPPORT-ROADS",
    "POL-CHILD-SUPPORT", "POL-CLEAR-PATH",
    "POL-COMPUTER-AIDED-EDUCATION", "POL-CONSTITUTIONAL-AMENDMENT",
    "POL-CONSTRUCTION-TRADES", "POL-CONTAMINATION", "POL-DRINKING-WATER",
    "POL-EARLY-CHILDHOOD-EDUCATION", "POL-ECONOMY-OUTSIDE-METRO",
    "POL-EDUCATION-FOR-PRISONERS", "POL-ELECTION1", "POL-ELECTION1-B",
    "POL-ELECTIONDATES1", "POL-ELECTRIC-HYBRID-CARS", "POL-ENTERGY-INSURANCE",
    "POL-FARM-FRESH-FOODS",
    "POL-FAV-BIDEN", "POL-FAV-CASSIDY", "POL-FAV-EDWARDS", "POL-FAV-FIELDS",
    "POL-FAV-FLEMING", "POL-FAV-GRAVES", "POL-FAV-HARRIS", "POL-FAV-HIGGINS",
    "POL-FAV-KENNEDY", "POL-FAV-LANDRY", "POL-FAV-LETLOW", "POL-FAV-NUNGESSER",
    "POL-FAV-SKRMETTA", "POL-FAV-TEMPLE", "POL-FAV-TRUMP-FMR", "POL-FAV-TRUMP-PRES",
    "POL-GED-PROGRAMS", "POL-GOV2027-REELECT",
    "POL-GOVERNOR-2ND-CHOICE", "POL-GOVERNOR-VOTE",
    "POL-GUNFREE1", "POL-GUNS1", "POL-HE-APPLIANCES", "POL-INCOME-TAX",
    "POL-INCREASE-AUTISM-FUNDING", "POL-INCREASE-EDUCATION-FUNDING",
    "POL-INCREASE-GAS-TAX", "POL-INCREASE-IN-SALES-TAX",
    "POL-INVEST-IN-PORTS", "POL-JOB-GROWTH-IN-BIOFUELS",
    "POL-JOB-GROWTH-IN-SOLAR-INDUSTRY", "POL-JOB-GROWTH-IN-WIND",
    "POL-JOB-GROWTH-NATURAL-GAS", "POL-KIDS-NEED-PE", "POL-LOBBYISTS",
    "POL-LONG-PRISON-SENTENCES", "POL-LOW-INCOME-HOUSING",
    "POL-MAILVOTE1", "POL-MAINTENANCE-BACKLOG", "POL-MENTAL-HEALTH-SERVICES",
    "POL-MORE-ARMED-OFFICERS",
    "POL-OPINION-OF-HEWITT", "POL-OPINION-OF-LANDRY", "POL-OPINION-OF-LUNDY",
    "POL-OPINION-OF-SCHRODER", "POL-OPINION-OF-WAGUESPACK", "POL-OPINION-OF-WILSON",
    "POL-ORGANIC-GROCERIES", "POL-PAPER1", "POL-PASSENGER-RAIL",
    "POL-PERMANENT-RAISES", "POL-PHOTOID1", "POL-POOR-DIETS",
    "POL-PRES2024", "POL-PRES2024-HARRIS", "POL-PRIMARY1",
    "POL-PROGRAM-TO-COMPLETE", "POL-PROPERTY-INSURANCE",
    "POL-PROSECUTING-REPEAT-OFFENDERS", "POL-QRCODE1",
    "POL-RAISE-TEACHER-PAY", "POL-REDUCE-RE-OFFENDING",
    "POL-REGISTRATION-FEES", "POL-REGULATE-MARIJUANA",
    "POL-RELOCATING-STUDENTS", "POL-RETURN-AUTHORITY",
    "POL-SALESTAX1", "POL-SCHOOL-LUNCHES", "POL-SECOND-PROGRAM",
    "POL-SENATE1", "POL-SENATE2026", "POL-SENATEGENERAL1",
    "POL-SENATEPRI1", "POL-SENATEPRI1b",
    "POL-SENTENCES-EFFECTIVE", "POL-SENTENCES-INCREASED",
    "POL-STUDENT-LOAN-PAYMENTS", "POL-SUPPLEMENTAL-PAY",
    "POL-SUPPORT-OFFSHORE-INDUSTRY", "POL-SUPPORT-ROOF-TOP-INDUSTRY",
    "POL-SUPPORT-SOLAR-FARM-INDUSTRY",
    "POL-TAX-FREE-SAVINGS-ACCOUNTS", "POL-TAXLOCAL1",
    "POL-TOLLS", "POL-TOPS", "POL-TOUCHSCREEN1", "POL-TOUCHSCREEN1-B",
    "POL-TRADE-EDUCATION", "POL-TRAINED-DOGS",
    "POL-TREATMENT-PROGRAMS-BETTER", "POL-VOTE-KNOWING-INFO",
    "POL-VOTESYS1-2025", "POL-VOTESYS1-B",
    "POL-WEED-KILLERS-PESTICIDES", "POL-YEAR-ROUND-SCHOOL",
    # ── HI domain (brand research / non-policy — client deliverables) ──
    "HI-AFFORD1", "HI-BCBS-1.9M", "HI-BCBS-90YR", "HI-BCBS-FACTS1",
    "HI-BCBS-LEGISCRIT", "HI-BCBS-MERGER", "HI-BCBS-MERGERRATE",
    "HI-BCBS-MILITARY", "HI-BCBS-NONPROFIT", "HI-BCBS-POLITE",
    "HI-BCBS-VOLUNTEER", "HI-BCBS-WORK",
    "HI-CARE-DOC1", "HI-CARE-GOV1", "HI-CARE-INS1", "HI-CARE-PHARM1", "HI-CARE-PHARMA1",
    "HI-CASHBACK1", "HI-COMMUNITY1", "HI-COVERAGE1",
    "HI-FACTORS1", "HI-FACTORS1-B", "HI-FACTORS2",
    "HI-FAV-BCBS", "HI-FAV-CANES", "HI-FAV-ENTERGY", "HI-FAV-LEGIS",
    "HI-FAV-LSU", "HI-FAV-OCHSNER", "HI-FAV-RFK", "HI-FAV-ROUSES",
    "HI-FAV2-AETNA", "HI-FAV2-AMBETTER", "HI-FAV2-BCBS", "HI-FAV2-CENTENE",
    "HI-FAV2-CIGNA", "HI-FAV2-HUMANA", "HI-FAV2-UHC",
    "HI-FAV3-AETNA", "HI-FAV3-AMBETTER", "HI-FAV3-CENTENE",
    "HI-FAV3-CIGNA", "HI-FAV3-HUMANA", "HI-FAV3-LABL", "HI-FAV3-UHC",
    "HI-FORPROFIT1", "HI-GENERIC1", "HI-GENERIC2", "HI-HSA1",
    "HI-INVOLVE-BCBS", "HI-INVOLVE-CANES", "HI-INVOLVE-ENTERGY",
    "HI-INVOLVE-OCHSNER", "HI-INVOLVE-ROUSES",
    "HI-MEDLOSS1", "HI-NONPROFIT1", "HI-OPINION-TREND",
    "HI-PETCOST1", "HI-PETFAMILY1", "HI-PETINS2", "HI-PETVET1",
    "HI-PREMIUMS1", "HI-STEPTHERAPY1", "HI-TRUST-RANK1", "HI-TRUST1",
    "HI-VACCINE1",
}

# Backward-compatible alias — union of both sets (used by scoring to skip)
SKIPPED_QIDS = SKIPPED_DEMOGRAPHIC | SKIPPED_RETAIN


# ══════════════════════════════════════════════════════════════════════════════
# CONSTRUCT GROUPINGS — Internal code grouping sets (implementation only).
# These variable names are legacy scaffolding. The organizing framework is
# the persuasion tier architecture (Entry → Bridge → Downstream), not axes.
# ══════════════════════════════════════════════════════════════════════════════

AXIS_1_CONSTRUCTS = {
    "BAIL", "TRUST", "PLEA", "PROS", "ALPR", "FINES",
    "PROMISE", "INNOCENCE", "CAND", "IMPACT", "ISSUE_SALIENCE",
    # ── Apr 12 2026 (Preston): DV moved here ─────────────────────────────
    # All 5 DV items ask about circumstances causing crime (DV/trafficking
    # victimization as mitigating factor) — Bridge tier.
    "DV",
    # ── Apr 10 2026 restructure (Preston) ─────────────────────────────────
    "RACIAL_DISPARITIES",  # split from DISPARITIES: racial-framing items only
    "ECON_DISPARITIES",    # split from DISPARITIES: socioeconomic-factor items
    "MENTAL_ADDICTION",    # rename of MENTAL-PREV, absorbs MENTAL + ADDICT + TREATMENT (all prevention framing)
    # ── Apr 10 2026 dead-construct prune ──────────────────────────────────
    # Removed: EQUITY, PD, RACIAL, DISPARITIES, RECORD-CLEAR, FIRSTAPPEAR,
    # COUNSEL, MENTAL-PREV. All folded into RACIAL_DISPARITIES /
    # ECON_DISPARITIES / MENTAL_ADDICTION / REPRESENTATION (see AXIS_3 below).
}

AXIS_2_CONSTRUCTS = {
    "REENTRY",
    "SENTREVIEW", "RECORD", "EXPUNGE", "JUV", "FAMILY",
    "CJINVOLVE", "ELDERLY",
    "JURY", "COURT", "CAND-DV",
    "COURTREVIEW", "ELDERLY-COST",
    # ── Apr 10 2026 restructure (Preston) ─────────────────────────────────
    "REDEMPTION",  # rename of COMPASSION, absorbs REHAB — "can people change" compassionate-release cluster
    # ── Apr 10 2026 dead-construct prune ──────────────────────────────────
    # Removed: COMPASSION, REHAB, TRAFFICK. Folded into REDEMPTION or
    # parked in SKIPPED_RETAIN.
    # NOTE: "VICTIM-COMPASSION" was already removed — duplicate QID alias.
    # ── Apr 11 2026 Phase 1.5 dead-construct prune ───────────────────────
    # Removed (empty declared buckets, verified Apr 10):
    #   RETRO → SENTREVIEW, REVIEW → SENTREVIEW, CLEMENCY → SENTREVIEW,
    #   PAROLE → REDEMPTION, EARLYRELEASE → SENTREVIEW/ELDERLY,
    #   GOODTIME → REDEMPTION, REVISIT → SENTREVIEW, AGING → ELDERLY
}

AXIS_3_CONSTRUCTS = {
    "DETER", "MAND", "LWOP", "DRUGPOSS", "PROP",
    "FISCAL", "APPROACH", "LIT", "REFORM_LEGITIMACY", "JUDICIAL",
    "SPENDING", "TOUGHCRIME", "DRUG", "LAW85",
    "INVEST", "DATA",
    "DISCRET", "MAND-DEPART",
    # ── Apr 10 2026 (Preston, post-cluster verification) ──────────────────
    # DP cluster verification revealed two conceptually distinct facets
    # jammed into one construct (median r = 0.088; CJ-DP1 ↔ NC-DP4 at
    # r = −0.146). Split approved by Preston:
    #   DP_ABOLITION   — support-vs-oppose-the-institution framing
    #   DP_RELIABILITY — evidence-certainty framing (within-support caution)
    # CJ-DP-OMN1 stays in SKIPPED_QIDS as a mixed-frame LA omnibus item.
    # Old "DP" and "DP-CERTAINTY" constructs retired in favor of the split.
    "DP_ABOLITION",
    "DP_RELIABILITY",
    # ── Apr 10 2026 (Preston, post-cluster verification) ──────────────────
    # REPRESENTATION was split based on the cluster-verification pass.
    # PD-funding items and COUNSEL items correlate r ≈ 0.01–0.05 — they are
    # not one construct. VA-COUNSEL1 ↔ VA-COUNSEL2 correlate r = 0.22 —
    # weak but kept together per Preston's call.
    "PD_FUNDING",      # CJ-PD1, CJ-PD2, CJ-PD2-B (and CJ-Q33, which is a
                       # verbatim duplicate of CJ-PD2-B — canonical merge queued)
    "COUNSEL_ACCESS",  # VA-COUNSEL1 (constitutional right) + VA-COUNSEL2
                       # (counsel at first appearance). Plus VA-FIRSTAPPEAR1
                       # if/when it returns from phantom.
    # ── Apr 10 2026 dead-construct prune ──────────────────────────────────
    # Removed: CLASS, MENTAL, ADDICT, TREATMENT. Folded into PROP (CLASS) or
    # MENTAL_ADDICTION.
    # REMOVED: CONDITIONS (ceiling effect — poorly worded, near-universal agreement)
    # REMOVED: CRIME (CJ-OK-COVID-CRIME is a partisan snapshot from 2024, not a reform attitude)
    # RENAMED (Apr 10 2026): REFORM → REFORM_LEGITIMACY. The three items (CJ-OK-REFORM-BLAME,
    #   VA-REFORM1, VA-REFORMS1) measure belief that past reforms succeeded / rejection of the
    #   "reforms caused crime" narrative — these are system-trust proxies, not reform-support
    #   items. Produced a −11.8 trust-permeability gap in the Apr 10 run (trusters scored higher
    #   than distrusters) because the items invert the trust-as-filter direction by construction.
    # CONSOLIDATED: REFORMS was a duplicate of REFORM caused by VA-REFORMS1 stripping to REFORMS
    #   while VA-REFORM1 stripped to REFORM — same question text, split across two constructs.
    #   Both now route to REFORM_LEGITIMACY via _COMPOUND_CONSTRUCT.
}

AXIS_ASSIGNMENTS = {}
for c in AXIS_1_CONSTRUCTS:
    AXIS_ASSIGNMENTS[c] = 1
for c in AXIS_2_CONSTRUCTS:
    AXIS_ASSIGNMENTS[c] = 2
for c in AXIS_3_CONSTRUCTS:
    AXIS_ASSIGNMENTS[c] = 3


# ══════════════════════════════════════════════════════════════════════════════
# HELPER: Extract construct from QID
# ══════════════════════════════════════════════════════════════════════════════

def get_construct(qid):
    """
    Extract construct name from QID.
    CJ-BAIL1 → BAIL, CJ-DV-OMN1a → DV, NC-DP4 → DP, CJ-Q107 → None (Q-series)
    """
    if not qid:
        return None

    # Check explicit overrides first (reclassifications + compound QIDs)
    if qid in _Q_SERIES_CONSTRUCT:
        return _Q_SERIES_CONSTRUCT[qid]
    if qid in _COMPOUND_CONSTRUCT:
        return _COMPOUND_CONSTRUCT[qid]

    # Strip domain prefix (CJ-, NC-, VA-, LA-, CCS-, HI-, POL-, EBR-)
    parts = qid.split("-")
    if len(parts) < 2:
        return None

    prefix = parts[0]
    if prefix in ("CJ", "NC", "VA", "LA", "CCS", "HI", "POL", "EBR"):
        rest = "-".join(parts[1:])
        # Handle two-level state prefix: CJ-OK-*, CJ-NJ-* → strip state code too
        if prefix == "CJ" and len(parts) >= 3 and parts[1] in ("OK", "NJ", "MA", "LA", "VA", "NC"):
            rest = "-".join(parts[2:])
    else:
        rest = qid

    # Q-series (CJ-Q107, CJ-Q33) — map to construct via REFORM_DIRECTION
    # Includes -B suffix fallback: CJ-Q115-B inherits CJ-Q115's construct
    # so that cross-state copies of the same Q-item route automatically.
    if rest.startswith("Q") and len(rest) > 1 and rest[1:].split("-")[0].isdigit():
        hit = _Q_SERIES_CONSTRUCT.get(qid)
        if hit is not None:
            return hit
        # Try stripping a trailing -B / -C / -D suffix (cross-state copies)
        if qid.endswith(("-B", "-C", "-D")):
            return _Q_SERIES_CONSTRUCT.get(qid[:-2])
        return None

    # Strip trailing numbers and OMN/B suffixes
    # BAIL1 → BAIL, DV-OMN1a → DV, REVIEW-OMN1-B → REVIEW
    # Fix Apr 12 2026: [A-Z]? was stripping trailing word letters (DOCTOR→DOCTO).
    # Now requires a dash before single capitals so only -B/-C/-D suffixes match.
    construct = re.sub(r"(?:[-]OMN\d*[a-z]?|[-]?[0-9]+[a-z]?|[-][A-Z])$", "", rest)
    construct = re.sub(r"(?:[-]OMN\d*[a-z]?|[-]?[0-9]+[a-z]?)$", "", construct)
    construct = construct.rstrip("-")

    if not construct:
        return None
    return construct.upper()


# Manual mapping for compound QIDs that don't parse cleanly
# (state-specific items with descriptive suffixes)
_COMPOUND_CONSTRUCT = {
    # CJ-OK items
    "CJ-OK-APPROACH-LEADERS": "APPROACH",
    "CJ-OK-COVID-CRIME": "CRIME",
    "CJ-OK-DETER-2024": "DETER",
    "CJ-OK-DP-EXONERATION": "DP_ABOLITION",  # Apr 10: DP split. Mixed-frame omnibus — two of three favorable options are abolition positions ("oppose DP", "risk of executing innocent"); third is a reliability position ("DNA required"). Routed to DP_ABOLITION by majority; flag for review.
    "CJ-OK-DV-ABUSE-MITIGATION": "DV",
    "CJ-OK-DV-TRAFFICKING": "DV",
    "CJ-OK-DV-TREATMENT": "DV",
    "CJ-OK-JUV-LWOP": "JUV",
    "CJ-OK-LIT-GED": "LIT",
    "CJ-OK-PAROLE-GOODTIME": "REDEMPTION",  # Apr 12: was PAROLE (dead) → REDEMPTION (v7 canonical)
    # CJ-OK-PROP-ACCOMPLICE moved to SKIPPED_RETAIN (message-testing)
    "CJ-OK-PROS-TRUST": "PROS",
    "CJ-OK-PROS2-FLEXIBILITY": "PROS",
    "CJ-OK-RECORD-JUV": "RECORD",
    "CJ-JUV-OMN3": "RECORD",  # reclassified from JUV SKIPPED — juvenile records should be confidential
    "CJ-OK-REENTRY-LITERACY": "REENTRY",
    "CJ-OK-REFORM-BLAME": "REFORM_LEGITIMACY",  # trust proxy — see AXIS_3 comment
    "VA-REFORM1": "REFORM_LEGITIMACY",           # trust proxy + consolidates the REFORM/REFORMS duplicate
    "VA-REFORMS1": "REFORM_LEGITIMACY",          # same question text as VA-REFORM1
    "CJ-OK-REVIEW-LIMITED": "SENTREVIEW",   # Apr 12: was REVIEW (dead) → SENTREVIEW (v7 canonical)
    "CJ-OK-REVIEW-SECONDLOOK": "SENTREVIEW",  # Apr 12: was REVIEW (dead) → SENTREVIEW (v7 canonical)
    # CJ-NJ items
    "CJ-NJ-JUV-ACCOUNTABILITY": "JUV",
    "CJ-NJ-JUV-CANDIDATE": "ISSUE_SALIENCE",  # reclassified from JUV — candidate support framing, not direct juvenile attitude
    "CJ-NJ-JUV-DECISION": "JUDICIAL",  # reclassified from JUV — judge vs prosecutor discretion, juvenile context is incidental
    "CJ-NJ-JUV-JUDGE": "JUDICIAL",  # reclassified from JUV — support/oppose legislation on judge vs prosecutor decision
    "CJ-NJ-JUV-WAIVER": "JUV",
    # Edge cases where regex misparses
    "CJ-LAW85-1": "LAW85",
    # CJ-VICTIM-COMPASSION1 is the same question as CJ-COMPASSION2 / CJ-Q86
    # ("The victim's opinion supporting or opposing compassionate release…")
    # It was given a separate QID in NC/VA surveys — now routes to REDEMPTION.
    "CJ-VICTIM-COMPASSION1": "REDEMPTION",

    # ══════════════════════════════════════════════════════════════════════
    # Apr 10 2026 restructure (Preston) — explicit QID overrides
    # ══════════════════════════════════════════════════════════════════════
    # ── Apr 10 2026 (Preston, post-cluster verification) ──────────────────
    # REPRESENTATION split into PD_FUNDING + COUNSEL_ACCESS.
    # Empirical basis: cross-facet correlations between PD-funding items and
    # COUNSEL items are r ≈ 0.01–0.05 (essentially zero). VA-COUNSEL1 and
    # VA-COUNSEL2 correlate r = 0.22 — weak but non-zero, kept together by
    # Preston's call. See REPRESENTATION_cluster_Apr10_2026/findings memo.
    "CJ-PD1":          "PD_FUNDING",
    "CJ-PD2":          "PD_FUNDING",
    "CJ-PD2-B":        "PD_FUNDING",

    # ── Apr 10 2026 (Preston, DP split from cluster verification) ─────────
    # DP was split into DP_ABOLITION (institution support/oppose) and
    # DP_RELIABILITY (evidence-certainty within support). Root cause:
    # CJ-DP1 ↔ NC-DP4 correlated at r = −0.146 because NC-DP4 is a
    # within-support cautiousness item, not an abolition item.
    "CJ-DP1":             "DP_ABOLITION",     # "Support / Oppose the death penalty"
    "CJ-DP5":             "DP_ABOLITION",     # forced choice DP vs. life in prison
    "CJ-DP6":             "DP_ABOLITION",     # "Support pausing" executions — moratorium
    "CJ-DP-OMN2":         "DP_ABOLITION",     # moratorium-on-executions likert
    "CJ-DP2":             "DP_RELIABILITY",   # how certain must guilt be
    "CJ-DP3":             "DP_RELIABILITY",   # DNA evidence confidence
    "CJ-DP4":             "DP_RELIABILITY",   # "irreversible" reliability frame
    # NC-DP-CERTAINTY1 EXCLUDED Apr 12 2026 (Preston): verbatim duplicate of NC-DP4
    # (r=1.000, n=954, both NC-CJ-2026-001). Same Alchemer question, two pipeline QIDs.
    # Canonical registry merged them (CQ_DP_RELIABILITY_UNLABELED_2); scoring layer
    # still carried both because it operates on pipeline QIDs, not canonical IDs.
    # Keep NC-DP4 as the surviving pipeline QID.
    # "NC-DP-CERTAINTY1":   "DP_RELIABILITY",
    "NC-DP4":             "DP_RELIABILITY",   # "irreversible" reliability frame — surviving QID after NC-DP-CERTAINTY1 merge

    # ── Apr 10 2026 (Preston, BAIL cluster verification) ──────────────────
    # BAIL median r = 0.155. Preston's call: CJ-BAIL3 is a judicial-
    # discretion question, not a bail question. "Fixed bail schedules vs.
    # judicial discretion" cuts both reform directions. Move to JUDICIAL;
    # keep the favorable marker but flag for scoring-direction review under
    # JUDICIAL construct semantics.
    "CJ-BAIL3":           "JUDICIAL",
    "VA-COUNSEL1":     "COUNSEL_ACCESS",
    "VA-COUNSEL2":     "COUNSEL_ACCESS",
    "VA-FIRSTAPPEAR1": "COUNSEL_ACCESS",  # phantom in registry; scheduled for cleanup DELETE

    # REDEMPTION: rename of COMPASSION, absorbs REHAB
    # ("can people change" — compassionate release + rehabilitation)
    "CJ-COMPASSION1": "REDEMPTION",
    "CJ-COMPASSION2": "REDEMPTION",
    "CJ-COMPASSION3": "REDEMPTION",
    "CJ-COMPASSION4": "REDEMPTION",
    "CJ-REHAB1":      "REDEMPTION",

    # RACIAL_DISPARITIES: split from DISPARITIES, merged RACIAL in
    "NC-DISPARITIES1": "RACIAL_DISPARITIES",
    "VA-DISPARITIES1": "RACIAL_DISPARITIES",
    "CJ-RACIAL1":      "RACIAL_DISPARITIES",

    # MENTAL_ADDICTION: rename of MENTAL-PREV, absorbs MENTAL + ADDICT + TREATMENT
    "CJ-MENTAL1":         "MENTAL_ADDICTION",
    "CJ-MENTAL2":         "MENTAL_ADDICTION",
    "CJ-MENTAL3":         "MENTAL_ADDICTION",
    "CJ-TREATMENT-OMN1":  "MENTAL_ADDICTION",
    "CJ-APPROACH2-B":     "MENTAL_ADDICTION",  # cross-state copy of CJ-APPROACH2

    # PROP: absorbs felony-classification items (CLASS bucket retired —
    # Q142/CLASS1 are about felony severity tiers, not socioeconomic class)
    "CJ-CLASS1": "PROP",
}

# Manual mapping for Q-series items to constructs
_Q_SERIES_CONSTRUCT = {
    "CJ-Q26":  "DV",
    "CJ-Q33":  "PD_FUNDING",  # Apr 10: was PD; verbatim duplicate of CJ-PD2-B (canonical merge queued)
    "CJ-Q54":  "CAND",  # ballot test — same question as CJ-CAND1/CJ-CAND-OMN1 (was APPROACH, reclassified)
    "CJ-Q84":  "SENTREVIEW",  # Apr 12: was EARLYRELEASE (dead) → SENTREVIEW (v7 canonical)
    "CJ-Q85":  "REDEMPTION",  # Apr 10: renamed from COMPASSION
    "CJ-Q86":  "REDEMPTION",  # Apr 10: renamed from COMPASSION
    "CJ-Q87":  "ELDERLY",
    "CJ-Q88":  "ELDERLY",
    "CJ-Q89":  "SENTREVIEW",
    "CJ-Q91":  "RACIAL_DISPARITIES",  # Apr 10: merged RACIAL into RACIAL_DISPARITIES
    "CJ-Q92":  "PROP",
    "CJ-Q97":  "EXPUNGE",
    # CJ-Q106 reclassified → ISSUE_SALIENCE (see override below)
    "CJ-Q107": "MENTAL_ADDICTION",  # Apr 10: MENTAL-PREV renamed → MENTAL_ADDICTION (absorbs MENTAL/ADDICT/TREATMENT)
    "CJ-Q110": "MAND",
    "CJ-Q111": "PROP",
    "CJ-Q114": "PROP",
    "CJ-Q115": "ECON_DISPARITIES",  # Apr 10: socioeconomic-factor item, split from DISPARITIES
    "CJ-Q116": "FISCAL",
    "CJ-Q117": "MENTAL_ADDICTION",  # Apr 10: renamed from MENTAL-PREV
    "CJ-Q118": "EXPUNGE",
    "CJ-Q119": "JUV",
    "CJ-Q124": "INVEST",
    "CJ-Q130": "MENTAL_ADDICTION",  # Apr 10: was TREATMENT — absorbed into MENTAL_ADDICTION
    "CJ-Q142": "PROP",  # Apr 10: was CLASS — felony-classification severity tiers; PROP construct
    "CJ-Q189": "MENTAL_ADDICTION",  # Apr 10: absorbed
    "CJ-Q190": "MENTAL_ADDICTION",  # Apr 10: absorbed
    "CJ-Q193": "MENTAL_ADDICTION",  # Apr 10: absorbed
    "CJ-Q194": "MENTAL_ADDICTION",  # Apr 10: absorbed
    "CJ-Q197": "REDEMPTION",  # Apr 12: was PAROLE (dead) → REDEMPTION (v7 canonical)
    "CJ-PROS2": "DP_RELIABILITY",  # Apr 10: was DP; post-split, "irreversible → only when certain" is a reliability item. Verbatim duplicate of NC-DP4 (canonical merge Group 3).
    "CJ-REVIEW-OMN4": "REDEMPTION",  # Apr 12: was GOODTIME (dead) → REDEMPTION (v7 canonical, good-time credit)
    "CJ-DV-OMN2": "SENTREVIEW",  # Apr 12: was REVIEW (dead) → SENTREVIEW (v7 canonical, retroactive resentencing)
    "CJ-DV7": "DV",  # Apr 12: returned to DV (Preston). Item text is "risk of continuing to punish people for crimes shaped by abuse" — that's abuse-context sentencing, not general sentence review. Was briefly SENTREVIEW but α diagnostic showed it doesn't cohere with review items.
    "CJ-CAND2": "ISSUE_SALIENCE",  # reclassified from CAND — single-issue salience, no counter-case
    "CJ-CAND3": "ISSUE_SALIENCE",  # reclassified from CAND — single-issue salience, no counter-case
    "CJ-Q106": "ISSUE_SALIENCE",   # reclassified from CAND — single-issue salience, no counter-case
    "NC-CAND1": "ISSUE_SALIENCE",  # reclassified from CAND — single-issue salience, no counter-case
    "CJ-Q201": "MENTAL_ADDICTION",  # Apr 10: absorbed
    "CJ-Q202": "MENTAL_ADDICTION",  # Apr 10: absorbed
    "CJ-ADDICT1": "MENTAL_ADDICTION",  # Apr 10: absorbed
    "CJ-ADDICT2": "MENTAL_ADDICTION",  # Apr 10: absorbed
    "CJ-ADDICT3": "MENTAL_ADDICTION",  # Apr 10: absorbed
    "CJ-APPROACH2": "MENTAL_ADDICTION",  # Apr 10: renamed from MENTAL-PREV
    "CJ-CRIMEAPPROACH1": "MENTAL_ADDICTION",  # Apr 10: renamed from MENTAL-PREV
    "CJ-Q204": "REENTRY",
}


def get_axis(qid):
    """Return construct grouping number (1, 2, or 3) for a QID, or None.

    Internal code grouping only — not a conceptual framework. Only CJ-domain
    QIDs get assignments. Non-CJ prefixes (CCS-, HI-, POL-, EBR-) are excluded
    even when their construct name happens to match an AXIS_*_CONSTRUCTS entry
    (e.g. HI-TRUST1 → "TRUST" is a health-insurance item, not a CJ item).
    """
    if not qid:
        return None

    # Only CJ-domain QIDs (CJ-* or state-prefixed CJ items) get axis numbers.
    # Accepted prefixes: CJ-, and state codes (NC-, VA-, LA-, OK-, MA-, NJ-)
    # that are used for state-specific CJ questions.
    prefix = qid.split("-")[0] if qid else ""
    _CJ_PREFIXES = {"CJ", "NC", "VA", "LA", "OK", "MA", "NJ"}
    if prefix not in _CJ_PREFIXES:
        return None

    construct = get_construct(qid)
    if construct is None:
        return None
    return AXIS_ASSIGNMENTS.get(construct)


# ══════════════════════════════════════════════════════════════════════════════
# CLASSIFY RESPONSE v2 — Likert scale classification with bug fixes
# ══════════════════════════════════════════════════════════════════════════════

def classify_response_v2(response_text):
    """
    Classify a Likert-scale response into direction and intensity.

    Returns: (direction, intensity)
        direction: "favorable" | "unfavorable" | "neutral"
        intensity: 1.0 (strong) | 0.5 (moderate/bare) | 0.0 (neutral)

    v2 fixes:
        - Bare "Support"/"Agree" → ("favorable", 0.5), not "neutral"
        - Bare "Oppose"/"Disagree" → ("unfavorable", 0.5), not "neutral"
    """
    if not response_text:
        return ("neutral", 0.0)

    text = str(response_text).strip().rstrip(".")

    # Strong favorable
    if re.match(r"(?i)^strongly\s+(support|agree|approve|favor)", text):
        return ("favorable", 1.0)
    # Moderate favorable (Somewhat)
    if re.match(r"(?i)^somewhat\s+(support|agree|approve|favorable)", text):
        return ("favorable", 0.5)
    # Strong unfavorable
    if re.match(r"(?i)^strongly\s+(oppose|disagree|disapprove|unfavorable)", text):
        return ("unfavorable", 1.0)
    # Moderate unfavorable (Somewhat)
    if re.match(r"(?i)^somewhat\s+(oppose|disagree|disapprove|unfavorable)", text):
        return ("unfavorable", 0.5)

    # ── v2 FIX: Bare Support/Agree/Oppose/Disagree ──
    if re.match(r"(?i)^support$", text):
        return ("favorable", 0.5)
    if re.match(r"(?i)^agree$", text):
        return ("favorable", 0.5)
    if re.match(r"(?i)^oppose$", text):
        return ("unfavorable", 0.5)
    if re.match(r"(?i)^disagree$", text):
        return ("unfavorable", 0.5)

    # Very favorable/unfavorable (favorability scale)
    if re.match(r"(?i)^very\s+favorable", text):
        return ("favorable", 1.0)
    if re.match(r"(?i)^somewhat\s+favorable", text):
        return ("favorable", 0.5)
    if re.match(r"(?i)^very\s+unfavorable", text):
        return ("unfavorable", 1.0)
    if re.match(r"(?i)^somewhat\s+unfavorable", text):
        return ("unfavorable", 0.5)

    # Likely/unlikely scales
    if re.match(r"(?i)^much\s+more\s+likely", text):
        return ("favorable", 1.0)
    if re.match(r"(?i)^(more likely|somewhat more likely)", text):
        return ("favorable", 0.5)
    if re.match(r"(?i)^much\s+less\s+likely", text):
        return ("unfavorable", 1.0)
    if re.match(r"(?i)^(less likely|somewhat less likely)", text):
        return ("unfavorable", 0.5)

    # Concerned scales
    if re.match(r"(?i)^very\s+concerned", text):
        return ("favorable", 1.0)
    if re.match(r"(?i)^somewhat\s+concerned", text):
        return ("favorable", 0.5)
    if re.match(r"(?i)^(not at all concerned|only a little concerned|not very concerned)", text):
        return ("unfavorable", 0.5)

    # Trust scales — note: high trust labels map to "favorable" here,
    # but TRUST1 has favorable_side="oppose" which flips the interpretation
    if re.match(r"(?i)^(a lot of trust|a great deal)", text):
        return ("favorable", 1.0)
    if re.match(r"(?i)^(some trust|a fair amount)", text):
        return ("favorable", 0.5)
    if re.match(r"(?i)^(not much trust|not at all|no trust)", text):
        return ("unfavorable", 0.5)

    # Promise/lives-up scales
    if re.match(r"(?i)^largely lives up", text):
        return ("favorable", 1.0)
    if re.match(r"(?i)^falls short", text):
        return ("unfavorable", 0.5)
    if re.match(r"(?i)^falls far short", text):
        return ("unfavorable", 1.0)

    # Neutral / Not sure
    if re.match(r"(?i)^(not sure|no opinion|undecided|neither|no answer|don.t know|no preference|no difference)", text):
        return ("neutral", 0.0)

    # Strong disagree (bare "Strongly Disagree" without oppose/agree prefix)
    if re.match(r"(?i)^strongly\s+disagree", text):
        return ("unfavorable", 1.0)

    # Unrecognized — neutral
    return ("neutral", 0.0)


# ══════════════════════════════════════════════════════════════════════════════
# SCORE_CONTENT — Main scoring function
# ══════════════════════════════════════════════════════════════════════════════

def score_content(qid, response, survey_id=None):
    """
    Score a single response using content-based favorable direction.

    Domain-agnostic: works for any policy domain (CJ, energy, HI, education,
    candidates) as long as the QID has an entry in FAVORABLE_DIRECTION.

    Args:
        qid: Question ID (e.g., "CJ-BAIL1", "CCS-RISK1", "EDU-VOUCHER1")
        response: Response text (e.g., "Cash bail often results...")
        survey_id: Optional survey ID for exclude_surveys check

    Returns:
        (favorable, intensity, has_intensity)
        favorable: 1 (favorable), 0 (unfavorable), None (unscorable)
        intensity: float (0.5 or 1.0) or float('nan') for binary/multi
        has_intensity: True if intensity is meaningful (Likert), False otherwise
    """
    if not qid or not response:
        return (None, None, False)

    config = FAVORABLE_DIRECTION.get(qid)
    # Apr 10 2026: -B/-C/-D suffix fallback. Cross-state copies like
    # CJ-Q91-B, CJ-Q115-B, CJ-APPROACH2-B inherit their parent's scoring
    # config, mirroring the get_construct() fallback added earlier.
    # Without this, raw rows exist but scored=0 and the cluster analyzer
    # reports SINGLE_ITEM / UNVERIFIABLE for valid constructs.
    if config is None and len(qid) >= 2 and qid[-2] == "-" and qid[-1] in "BCD":
        config = FAVORABLE_DIRECTION.get(qid[:-2])
    if config is None:
        return (None, None, False)

    # Check survey exclusion
    if survey_id and survey_id in config.get("exclude_surveys", []):
        return (None, None, False)

    response_text = str(response).strip()
    scoring_type = config["type"]

    # ── LIKERT scoring ──
    if scoring_type == "likert":
        direction, intensity = classify_response_v2(response_text)

        if direction == "neutral":
            # Count neutrals in denominator (not favorable) so "not sure" responses
            # don't inflate support rates. Returns (0, 0.0, False) — counted but not favorable.
            return (0, 0.0, False)

        fav_side = config["favorable_side"]

        # Map classifier direction to favorable based on configured side
        if fav_side in ("agree", "support"):
            favorable = 1 if direction == "favorable" else 0
        elif fav_side == "oppose":
            # Reversed: classifier "unfavorable" = our favorable
            favorable = 1 if direction == "unfavorable" else 0
        else:
            return (None, None, False)

        return (favorable, intensity, True)

    # ── BINARY scoring ──
    elif scoring_type == "binary":
        fav_substring = config["favorable_contains"]
        if fav_substring.lower() in response_text.lower():
            return (1, float('nan'), False)
        else:
            neutral_terms = {"not sure", "no opinion", "undecided", "don't know",
                           "no preference", "not sure / no opinion"}
            if response_text.lower().strip().rstrip(".") in neutral_terms:
                return (None, None, False)
            return (0, float('nan'), False)

    # ── MULTI_FAVORABLE scoring ──
    elif scoring_type == "multi_favorable":
        fav_substrings = config["favorable_contains"]
        response_lower = response_text.lower()

        for substring in fav_substrings:
            if substring.lower() in response_lower:
                return (1, float('nan'), False)

        neutral_terms = {"not sure", "no opinion", "undecided", "don't know",
                       "no preference", "not sure / no opinion", "i am not sure"}
        if response_text.lower().strip().rstrip(".") in neutral_terms:
            return (None, None, False)

        return (0, float('nan'), False)

    return (None, None, False)


# ══════════════════════════════════════════════════════════════════════════════
# CONVENIENCE: Score a full DataFrame
# ══════════════════════════════════════════════════════════════════════════════

def score_dataframe(df, qid_col="question_id", response_col="response",
                    survey_col="survey_id"):
    """
    Score an entire DataFrame of L2 responses.

    Adds columns: favorable (0/1/NaN), intensity (float/NaN), has_intensity (bool)
    Returns the DataFrame with new columns.
    """
    import pandas as pd

    results = []
    for _, row in df.iterrows():
        fav, intensity, has_int = score_content(
            row[qid_col], row[response_col],
            row.get(survey_col)
        )
        results.append({"favorable": fav, "intensity": intensity, "has_intensity": has_int})

    result_df = pd.DataFrame(results)
    return pd.concat([df.reset_index(drop=True), result_df], axis=1)


# ══════════════════════════════════════════════════════════════════════════════
# CONSTRUCT-LEVEL SCORING — Reach + Conviction (two-dimensional)
# ══════════════════════════════════════════════════════════════════════════════
#
# Reach:      What % of scoreable respondents are favorable? (binary 0/1)
# Conviction: Among favorable respondents, how locked in are they? (0.0–1.0)
#
# For likert items, conviction = real intensity (0.5 bare, 1.0 strong).
# For binary items, conviction is imputed from the mean likert intensity
# in the same construct. If no likert siblings exist, default = 0.75.
#
# Usage:
#     from content_scoring import score_construct
#     result = score_construct(scored_responses)
#     # result = {"reach": 67.3, "conviction": 0.72, "n": 5297, ...}

def score_construct(scored_items):
    """
    Compute reach and conviction for a set of scored responses within one construct.

    Args:
        scored_items: list of dicts, each with:
            - favorable: 0 or 1
            - intensity: float or NaN
            - has_intensity: bool (True for likert, False for binary/multi)

    Returns:
        dict with:
            - reach: float (0–100), % of scoreable responses that are favorable
            - conviction: float (0.0–1.0), mean intensity among favorable respondents
              (likert = real, binary = imputed from likert siblings)
            - conviction_source: str ("likert" if imputed from real data, "default" if 0.75 fallback)
            - likert_mean_intensity: float, the average intensity of likert-favorable responses
            - n_scoreable: int, total scoreable responses
            - n_favorable: int, count of favorable responses
            - n_likert: int, count of likert-type responses
            - n_binary: int, count of binary/multi responses
    """
    import math

    if not scored_items:
        return {
            "reach": 0.0, "conviction": 0.0, "conviction_source": "none",
            "likert_mean_intensity": 0.0,
            "n_scoreable": 0, "n_favorable": 0, "n_likert": 0, "n_binary": 0,
        }

    n_scoreable = len(scored_items)
    n_favorable = sum(1 for i in scored_items if i["favorable"] == 1)
    n_likert = sum(1 for i in scored_items if i.get("has_intensity", False))
    n_binary = n_scoreable - n_likert

    # Reach: simple favorable rate
    reach = n_favorable / n_scoreable * 100 if n_scoreable > 0 else 0.0

    # Conviction: intensity among favorable respondents
    # Step 1: compute mean intensity from likert-favorable responses
    likert_fav_intensities = [
        i["intensity"] for i in scored_items
        if i["favorable"] == 1
        and i.get("has_intensity", False)
        and i.get("intensity") is not None
        and not math.isnan(i["intensity"])
    ]

    if likert_fav_intensities:
        likert_mean = sum(likert_fav_intensities) / len(likert_fav_intensities)
        conviction_source = "likert"
    else:
        likert_mean = 0.75  # no likert items in construct → midpoint default
        conviction_source = "default"

    # Step 2: compute conviction across all favorable respondents
    conviction_values = []
    for i in scored_items:
        if i["favorable"] != 1:
            continue
        if i.get("has_intensity", False) and i.get("intensity") is not None and not math.isnan(i["intensity"]):
            conviction_values.append(i["intensity"])
        else:
            # Binary/multi: impute from likert siblings
            conviction_values.append(likert_mean)

    conviction = sum(conviction_values) / len(conviction_values) if conviction_values else 0.0

    return {
        "reach": round(reach, 1),
        "conviction": round(conviction, 3),
        "conviction_source": conviction_source,
        "likert_mean_intensity": round(likert_mean, 3),
        "n_scoreable": n_scoreable,
        "n_favorable": n_favorable,
        "n_likert": n_likert,
        "n_binary": n_binary,
    }


# ══════════════════════════════════════════════════════════════════════════════
# SELF-TEST
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("content_scoring.py — self-test")
    print(f"  REFORM_DIRECTION: {len(REFORM_DIRECTION)} QIDs")
    print(f"  SKIPPED_QIDS: {len(SKIPPED_QIDS)} QIDs")
    print(f"  AXIS_ASSIGNMENTS: {len(AXIS_ASSIGNMENTS)} constructs")
    print()

    # Test classify_response_v2
    tests = [
        ("Strongly support", ("favorable", 1.0)),
        ("Somewhat support", ("favorable", 0.5)),
        ("Support", ("favorable", 0.5)),          # v2 fix
        ("Agree", ("favorable", 0.5)),             # v2 fix
        ("Strongly oppose", ("unfavorable", 1.0)),
        ("Oppose", ("unfavorable", 0.5)),          # v2 fix
        ("Disagree", ("unfavorable", 0.5)),        # v2 fix
        ("Not sure", ("neutral", 0.0)),
        ("Strongly agree", ("favorable", 1.0)),
        ("Strongly Disagree", ("unfavorable", 1.0)),
    ]
    passed = 0
    for text, expected in tests:
        result = classify_response_v2(text)
        status = "✓" if result == expected else "✗"
        if result != expected:
            print(f"  {status} classify_response_v2('{text}') = {result}, expected {expected}")
        passed += (result == expected)
    print(f"  classify_response_v2: {passed}/{len(tests)} passed")

    # Test score_content
    score_tests = [
        ("CJ-BAIL1", "Cash bail often results in people being jailed simply because they cannot afford to pay.", None,
         (1, float('nan'), False)),
        ("CJ-BAIL1", "Cash bail is a fair and effective way to ensure people return to court.", None,
         (0, float('nan'), False)),
        ("CJ-PD2", "Strongly agree.", None,
         (1, 1.0, True)),
        ("CJ-PD2", "Disagree", None,
         (0, 0.5, True)),
        ("CJ-TRUST1", "No trust at all.", None,
         (1, 0.5, True)),  # Low trust = reform-favorable (reversed)
        ("CJ-TRUST1", "A lot of trust.", None,
         (0, 1.0, True)),  # High trust = reform-unfavorable
        ("UNKNOWN-QID", "anything", None,
         (None, None, False)),
    ]
    passed = 0
    for qid, resp, sid, expected in score_tests:
        result = score_content(qid, resp, sid)
        # NaN comparison
        match = True
        for r, e in zip(result, expected):
            if r is None and e is None:
                continue
            elif isinstance(r, float) and isinstance(e, float) and math.isnan(r) and math.isnan(e):
                continue
            elif r != e:
                match = False
                break
        status = "✓" if match else "✗"
        if not match:
            print(f"  {status} score_content('{qid}', '{resp[:40]}...') = {result}, expected {expected}")
        passed += match
    print(f"  score_content: {passed}/{len(score_tests)} passed")

    # Test get_construct / get_axis
    construct_tests = [
        ("CJ-BAIL1", "BAIL", 1),
        ("CJ-DV-OMN1a", "DV", 2),
        ("CJ-DP5", "DP_ABOLITION", 3),    # Apr 10 DP split
        ("CJ-Q107", "MENTAL_ADDICTION", 1),  # Apr 10 rename from MENTAL-PREV
        ("NC-DP4", "DP_RELIABILITY", 3),  # Apr 10 DP split
        ("CJ-BAIL3", "JUDICIAL", 3),      # Apr 10 reclass — judicial discretion, not bail
    ]
    passed = 0
    for qid, exp_construct, exp_axis in construct_tests:
        c = get_construct(qid)
        a = get_axis(qid)
        match = (c == exp_construct) and (a == exp_axis)
        if not match:
            print(f"  ✗ get_construct('{qid}') = {c} (expected {exp_construct}), get_axis = {a} (expected {exp_axis})")
        passed += match
    print(f"  get_construct/get_axis: {passed}/{len(construct_tests)} passed")
    print()
    print("Done.")
