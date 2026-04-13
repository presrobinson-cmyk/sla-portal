"""
creative_system.py — Preston Robinson Creative Production System
Extracted from 5 session carry PDFs covering 53 analyzed pieces.
Registers R1–R36 + Radio Issue Contrast, 6 Signature Rules,
19 Rule 1 Variants, 3 Foundational Principles, 7 Production Doctrine
rules, 50+ Structural Moves.

Version: 1.0 (Apr 13 2026)
Source: session carry media session1-5.pdf + CreativeStyleProfile v1.3/v1.4
"""

# ══════════════════════════════════════════════════════════════════
# FORMAT CODES
# ══════════════════════════════════════════════════════════════════

FORMAT_TV_30 = "TV :30"
FORMAT_TV_60 = "TV :60"
FORMAT_RADIO_30 = "Radio :30"
FORMAT_RADIO_60 = "Radio :60"
FORMAT_DIGITAL_30 = "Digital :30/:15"
FORMAT_CORPORATE = "Corporate Suite"

ALL_FORMATS = [
    FORMAT_TV_30, FORMAT_TV_60,
    FORMAT_RADIO_30, FORMAT_RADIO_60,
    FORMAT_DIGITAL_30, FORMAT_CORPORATE,
]


# ══════════════════════════════════════════════════════════════════
# REGISTERS — R1–R36 + Radio Issue Contrast
# ══════════════════════════════════════════════════════════════════
# Each register: code, name, description, formats, defining_characteristics,
# required_moves, optional_moves, rule1_hint, example_piece, notes

REGISTERS = {

    "R8": {
        "code": "R8",
        "name": "Aspirational Bio",
        "description": "Opens with personal origin, pivots to policy through character. The foundational candidate bio register.",
        "formats": [FORMAT_TV_30, FORMAT_TV_60, FORMAT_DIGITAL_30],
        "defining_characteristics": [
            "Personal origin story that doubles as inoculation",
            "Character arc: humble roots → earned accomplishment → policy consequence",
            "Soft contrast close (implicit, not explicit — Rule 5)",
            "Bookend: same word/image opens and closes with deepened meaning",
        ],
        "required_moves": ["Origin Story as Inoculation", "Soft Contrast Close"],
        "optional_moves": ["Faith Integration", "Electability Close", "Personal Pledge Close"],
        "rule1_hint": "Community Label Open or Heritage Duration Open — concede the opponent's turf first",
        "example_piece": "Hunter Lundy TV Bio (:30)",
        "notes": "TV vs. Radio Bio Pattern: TV leads with image, Radio leads with voice. Lundy :30 TV won Telly + Reed Awards.",
    },

    "R8_RADIO": {
        "code": "R8_RADIO",
        "name": "Aspirational Bio (Radio)",
        "description": "Radio variant of R8. Voice carries the origin story. Expands where TV compresses.",
        "formats": [FORMAT_RADIO_60, FORMAT_RADIO_30],
        "defining_characteristics": [
            "Voice IS the evidence — no visuals to anchor credibility",
            "Setup expands in :60 (more origin depth), close locks same as TV",
            "Deliberate pause after key phrase replaces TV text card (Rule 4 radio equivalent)",
            "Longer emotional dwell time than TV version",
        ],
        "required_moves": ["Origin Story as Inoculation", "Three-Beat Candidate Introduction"],
        "optional_moves": ["Faith Integration", "Electability Close", "Personal Pledge Close"],
        "rule1_hint": "Rhetorical Question Concession works well in radio — audience has time to answer it mentally",
        "example_piece": "Hunter Lundy Radio :60",
        "notes": "Cross-Medium Adaptation: TV :30 leads (establishes the image), Radio :60 expands the story depth.",
    },

    "R9": {
        "code": "R9",
        "name": "Institutional Warning PSA",
        "description": "Candidate as institutional defender. Frames the election as a choice about protecting a valued institution.",
        "formats": [FORMAT_TV_30, FORMAT_TV_60, FORMAT_DIGITAL_30],
        "defining_characteristics": [
            "Institution (court, school, hospital) is the protagonist",
            "Threat to institution = implicit opponent (Rule 5 — villain never named)",
            "Candidate positioned as protector, not attacker",
            "Behavioral Directive Close — tells audience exactly what to do",
        ],
        "required_moves": ["Behavioral Directive Close"],
        "optional_moves": ["Policy Sprint", "Intent Escalation"],
        "rule1_hint": "Preemptive Concession — acknowledge the institution has problems before declaring it worth saving",
        "example_piece": None,
        "notes": "Implied villain (Rule 5) is architecturally required here — naming the opponent would undermine the protective frame.",
    },

    "R10": {
        "code": "R10",
        "name": "Opponent-Pivot Contrast Bio",
        "description": "Leads with the opponent's own words, then pivots to the candidate's record. The contrast comes from the opponent's mouth.",
        "formats": [FORMAT_TV_30, FORMAT_TV_60, FORMAT_DIGITAL_30],
        "defining_characteristics": [
            "Opponent's direct quote appears on screen — EXCEPTION to Rule 5 (opponent named/quoted by design)",
            "Pivot is the structural engine: 'They said X. Here's what we did instead.'",
            "Candidate's record is the resolution, not the attack",
            "Electability Close often works well here",
        ],
        "required_moves": ["Electability Close"],
        "optional_moves": ["Credential-to-Consequence Architecture", "Soft Contrast Close"],
        "rule1_hint": "Opponent Concession as Opening — use the opponent's own strongest argument against them",
        "example_piece": "Hunter Lundy TV Contrast",
        "notes": "Rule 5 exception: the opponent's words appear because they ARE the concession. The pivot is the inoculation.",
    },

    "R11a": {
        "code": "R11a",
        "name": "Legislative Advocacy PSA — Statistical/Authority",
        "description": "Issue advocacy (not candidate) led by data and institutional authority. Evidence-first argument structure.",
        "formats": [FORMAT_TV_30, FORMAT_TV_60, FORMAT_DIGITAL_30],
        "defining_characteristics": [
            "Statistics as the credibility anchor (not a spokesperson)",
            "Institutional voice or narrator carries the argument",
            "Policy Sprint is the structural core — multiple stats in rapid sequence",
            "Behavioral Directive Close: specific legislative action requested",
        ],
        "required_moves": ["Policy Sprint", "Behavioral Directive Close"],
        "optional_moves": ["Audience-Calibrated Stat Deployment", "Plain-Language Translation"],
        "rule1_hint": "Stat-as-Concession Open — lead with a statistic that seems to support the opposition, then reframe",
        "example_piece": None,
        "notes": "Distinguish from R11b by source of authority: R11a = data/institution, R11b = personal witness.",
    },

    "R11b": {
        "code": "R11b",
        "name": "Legislative Advocacy PSA — Personal Witness",
        "description": "Issue advocacy led by a real person's experience. The witness IS the evidence.",
        "formats": [FORMAT_TV_30, FORMAT_TV_60, FORMAT_DIGITAL_30],
        "defining_characteristics": [
            "First-person testimony anchors credibility",
            "Witness's story = the statistical argument made human",
            "Avoid summarizing the story in VO — let the witness speak",
            "Behavioral Directive Close",
        ],
        "required_moves": ["Behavioral Directive Close", "Credential-to-Consequence Architecture"],
        "optional_moves": ["Origin Story as Inoculation", "Universalizing Inoculation"],
        "rule1_hint": "Emotional Self-Disclosure — open with the witness acknowledging the emotional weight before making the argument",
        "example_piece": None,
        "notes": "The witness's specificity is the inoculation. Vague witnesses lose credibility.",
    },

    "R12": {
        "code": "R12",
        "name": "Corporate Change Advocacy",
        "description": "Full corporate change advocacy suite. The organization is the protagonist committing to transformation. Rule 5 architecturally absent — no external villain by design.",
        "formats": [FORMAT_TV_30, FORMAT_TV_60, FORMAT_DIGITAL_30, FORMAT_CORPORATE],
        "defining_characteristics": [
            "Organization makes a public commitment (not a claim — a promise)",
            "Locked phrase carries the suite ('promise' for BCBSLA)",
            "Rule 5 structurally absent: no implied villain — the frame is solidarity, not contrast",
            "Silent Track applies for digital: text cards must carry complete argument without audio",
            "Dual-Version Production: :30 TV + :60 Radio serve different audience dwell times",
        ],
        "required_moves": ["Locked Phrases", "Dual-Version Production"],
        "optional_moves": ["Portable Identity Module", "Complexity Embodiment Split"],
        "rule1_hint": "Industry Concession — the organization concedes the industry has not always served people well before committing to change",
        "example_piece": "BCBSLA 'Change' :30 TV / 'Promise' :60 TV / 'Better Blue' :30 TV / 'Trust' :60 Radio / 'Trust' :30 Digital",
        "notes": "BCBSLA suite: 'promise' is the suite master word. 5-piece suite: Change/:30, Promise/:60, Better Blue/:30, Trust/:60R, Trust/:30D. 'Trust' :30 TV = Telly Award.",
    },

    "R13": {
        "code": "R13",
        "name": "Proxy Attack",
        "description": "Attack delivered through a third-party voice — not the candidate or narrator. The proxy absorbs the attack.",
        "formats": [FORMAT_TV_30, FORMAT_TV_60, FORMAT_DIGITAL_30],
        "defining_characteristics": [
            "Third party (voter, expert, opponent's own constituent) delivers the contrast",
            "Candidate or sponsor stays above the fray",
            "Proxy's credibility is the inoculation",
        ],
        "required_moves": ["Credential-to-Consequence Architecture"],
        "optional_moves": ["Universalizing Inoculation"],
        "rule1_hint": "Voter Loyalty Concession — proxy concedes their prior loyalty before explaining why they're switching",
        "example_piece": None,
        "notes": None,
    },

    "R14": {
        "code": "R14",
        "name": "Direct Contrast Bio",
        "description": "Head-to-head contrast between candidate and opponent. More direct than R10 — both records on screen simultaneously.",
        "formats": [FORMAT_TV_30, FORMAT_TV_60, FORMAT_DIGITAL_30],
        "defining_characteristics": [
            "Split-frame or alternating evidence: candidate record vs. opponent record",
            "Intent Escalation: contrast deepens across the spot",
            "Text cards anchor both sides of the contrast",
            "Behavioral Directive Close",
        ],
        "required_moves": ["Intent Escalation", "Behavioral Directive Close"],
        "optional_moves": ["Policy Sprint", "Electability Close"],
        "rule1_hint": "Thesis Concession — concede that both candidates have records, then let the records speak",
        "example_piece": None,
        "notes": None,
    },

    "R15": {
        "code": "R15",
        "name": "Geographically Targeted Constituency Bio",
        "description": "Bio tailored to a specific geographic community or region. Local specificity IS the inoculation.",
        "formats": [FORMAT_TV_30, FORMAT_TV_60, FORMAT_RADIO_60],
        "defining_characteristics": [
            "Geographic anchoring — specific place names, local landmarks",
            "Potholes as Specificity Anchor: hyper-local detail = trustworthiness signal",
            "Three-Beat Candidate Introduction",
            "Community Liberation Close or Electability Close",
        ],
        "required_moves": ["Three-Beat Candidate Introduction", "Potholes as Specificity Anchor"],
        "optional_moves": ["Origin Story as Inoculation", "Faith Integration"],
        "rule1_hint": "Community Label Open — concede the community's identity and concerns before claiming to represent them",
        "example_piece": None,
        "notes": None,
    },

    "R16": {
        "code": "R16",
        "name": "Single-Issue Endorsement Ad",
        "description": "An endorser speaks on a single issue only. Credibility is narrow and deep, not broad.",
        "formats": [FORMAT_TV_30, FORMAT_TV_60, FORMAT_DIGITAL_30],
        "defining_characteristics": [
            "Endorser's credential on THIS issue only (not a general endorsement)",
            "Single issue = depth of credibility",
            "Endorser speaks directly to camera",
        ],
        "required_moves": ["Credential-to-Consequence Architecture"],
        "optional_moves": ["Name Recognition Inoculation"],
        "rule1_hint": "Insider Concession — endorser concedes they don't agree on everything before making the narrow endorsement",
        "example_piece": None,
        "notes": None,
    },

    "R17": {
        "code": "R17",
        "name": "Base Defense / Inoculation Ad",
        "description": "Candidate defends their base record against an expected attack. Pre-empts the attack by making it first.",
        "formats": [FORMAT_TV_30, FORMAT_TV_60, FORMAT_RADIO_60],
        "defining_characteristics": [
            "Opens with the attack — Preemptive Concession IS the structure",
            "Faith Integration common (base protection often invokes shared values)",
            "Resolution is the candidate's record, not a counter-attack",
        ],
        "required_moves": ["Universalizing Inoculation"],
        "optional_moves": ["Faith Integration", "Origin Story as Inoculation"],
        "rule1_hint": "Preemptive Concession — address the attack before the opponent makes it",
        "example_piece": None,
        "notes": None,
    },

    "R18": {
        "code": "R18",
        "name": "Bio Truth-Teller Contrast",
        "description": "Candidate as the one who will tell uncomfortable truths. Contrast is built on honesty, not record.",
        "formats": [FORMAT_TV_30, FORMAT_TV_60, FORMAT_RADIO_60],
        "defining_characteristics": [
            "Truth-telling IS the credential",
            "Three-Beat Candidate Introduction anchors the honesty claim",
            "Opponent's dishonesty is implied, not named (Rule 5 typically)",
        ],
        "required_moves": ["Three-Beat Candidate Introduction", "Origin Story as Inoculation"],
        "optional_moves": ["Soft Contrast Close", "Personal Pledge Close"],
        "rule1_hint": "Rumor Absorption — absorb the rumor about the candidate before using truth-telling to dissolve it",
        "example_piece": None,
        "notes": None,
    },

    "R19": {
        "code": "R19",
        "name": "Policy Thesis Radio",
        "description": "Radio-native policy argument. Audio carries the complete argument — no visual support.",
        "formats": [FORMAT_RADIO_60, FORMAT_RADIO_30],
        "defining_characteristics": [
            "Thesis stated early and clearly — audio can't rely on visual reinforcement",
            "Policy Sprint structure: rapid evidence build",
            "Deliberate pause replaces text card (Rule 4 radio equivalent)",
            "CTA is the resolution",
        ],
        "required_moves": ["Policy Sprint"],
        "optional_moves": ["Plain-Language Translation", "Audience-Calibrated Stat Deployment"],
        "rule1_hint": "Complexity Concession — concede the issue is genuinely complicated before presenting the clear solution",
        "example_piece": None,
        "notes": "Radio :60 is almost always better than :30 for policy argument. The extra 30 seconds allows evidence to breathe.",
    },

    "R20": {
        "code": "R20",
        "name": "Electoral Issue Brief",
        "description": "Tight issue brief connecting a problem directly to electoral choice. Issue is the protagonist.",
        "formats": [FORMAT_TV_30, FORMAT_TV_60, FORMAT_RADIO_60],
        "defining_characteristics": [
            "Issue framed as a choice, not a problem",
            "Data anchor early",
            "Behavioral Directive Close links issue to vote",
        ],
        "required_moves": ["Behavioral Directive Close"],
        "optional_moves": ["Audience-Calibrated Stat Deployment", "Policy Sprint"],
        "rule1_hint": "Stat-as-Concession Open — lead with the number that seems to favor the other side",
        "example_piece": None,
        "notes": None,
    },

    "R21": {
        "code": "R21",
        "name": "Community Economic Pride Advocacy",
        "description": "Radio advocacy built on community economic pride. No external villain — the frame is solidarity and investment.",
        "formats": [FORMAT_RADIO_60],
        "defining_characteristics": [
            "Community is the protagonist and the beneficiary",
            "Rule 5 variant: no villain — solidarity frame precludes contrast",
            "Faith Integration common in this register",
            "Economic specificity as credibility anchor",
        ],
        "required_moves": ["Faith Integration"],
        "optional_moves": ["Potholes as Specificity Anchor", "Community Liberation Close"],
        "rule1_hint": "Heritage Duration Open — concede how long the community has struggled before announcing the investment",
        "example_piece": None,
        "notes": "Radio-only register. The community economic pride frame collapses in visual media — the intimacy of audio is load-bearing.",
    },

    "R22": {
        "code": "R22",
        "name": "CJ Reform TV Brief",
        "description": "Data-driven criminal justice reform argument. Heavy text cards, evidence-first structure, reform as common sense.",
        "formats": [FORMAT_TV_30, FORMAT_TV_60, FORMAT_DIGITAL_30],
        "defining_characteristics": [
            "Data anchor carries the reform argument — person not required",
            "Heavy text card usage (Rule 3: seven-word limit per card)",
            "Silent Track ready: text card sequence carries full argument without audio",
            "Implied villain is 'the old system' — not a specific person (Rule 5)",
        ],
        "required_moves": ["Policy Sprint"],
        "optional_moves": ["Plain-Language Translation", "Behavioral Directive Close"],
        "rule1_hint": "Contractual Concession — concede what the current system was designed to do before showing it failed",
        "example_piece": None,
        "notes": "SLA Portal context: use live MrP numbers as the Data Anchor. The data IS the message.",
    },

    "R24": {
        "code": "R24",
        "name": "Environmental Issue Position TV",
        "description": "Issue advocacy where the industry/corporation is the addressee, not the villain. Frame Reclamation is the structural move.",
        "formats": [FORMAT_TV_30, FORMAT_TV_60, FORMAT_DIGITAL_30],
        "defining_characteristics": [
            "Industry is addressed directly — not demonized",
            "Frame Reclamation: take back language the opposition owns",
            "Rule 5 variant: industry is the addressee, not the contrast (4th absence context)",
            "Visual embodies the problem; audio resolves it (Complexity Embodiment Split applies)",
        ],
        "required_moves": ["Frame Reclamation", "Complexity Embodiment Split"],
        "optional_moves": ["Intent Escalation"],
        "rule1_hint": "Industry Concession — concede the industry's contribution before reframing accountability as shared interest",
        "example_piece": None,
        "notes": None,
    },

    "R25": {
        "code": "R25",
        "name": "Incumbent Warmth Re-election Bio",
        "description": "Re-election bio built on warmth and community connection. Strength through relationship, not accomplishment.",
        "formats": [FORMAT_TV_30, FORMAT_TV_60, FORMAT_DIGITAL_30],
        "defining_characteristics": [
            "Warmth IS the argument — community relationship precedes policy record",
            "Rule 5 variant: incumbent expansion frame precludes comparison (4th absence context)",
            "Soft Contrast Close — contrast is implicit, not explicit",
            "Bookend on a relational word (home, heart, community)",
        ],
        "required_moves": ["Soft Contrast Close"],
        "optional_moves": ["Faith Integration", "Potholes as Specificity Anchor"],
        "rule1_hint": "Voter Loyalty Concession — concede that re-election is earned, not assumed",
        "example_piece": "Gautreaux 'Heart'",
        "notes": "Session 4: Gautreaux 'Heart' is the corpus exemplar for R25.",
    },

    "R26": {
        "code": "R26",
        "name": "Ballot Proposition Advocacy Ad",
        "description": "Civic issue advocacy for a ballot measure. Text cards carry the complete argument for muted viewers.",
        "formats": [FORMAT_TV_30, FORMAT_TV_60, FORMAT_DIGITAL_30],
        "defining_characteristics": [
            "Proposition language appears on screen (text card rule applies)",
            "Silent Track: best Silent Track test in corpus — text cards carry complete civic argument",
            "Frame Reclamation common: reclaim 'safety' or 'community' language",
            "Implied villain is abstract ('the system', 'politicians') — Rule 5 intact",
        ],
        "required_moves": ["Frame Reclamation"],
        "optional_moves": ["Policy Sprint", "Behavioral Directive Close"],
        "rule1_hint": "Definitional Concession — concede the opponent's definition of the issue, then expand it",
        "example_piece": "EBRSO 'Ballot'",
        "notes": "EBRSO 'Ballot' = best civic advocacy Silent Track in corpus (Session 4 analysis).",
    },

    "R27": {
        "code": "R27",
        "name": "Performance Indictment Attack",
        "description": "Attack ad built on the incumbent's performance record. The record is the indictment — no personal attack needed.",
        "formats": [FORMAT_TV_30, FORMAT_TV_60, FORMAT_DIGITAL_30],
        "defining_characteristics": [
            "Incumbent's own record is the evidence — their words or their numbers",
            "Veiled Disqualification: record implies incompetence without making the character claim",
            "Text cards anchor each indictment point",
            "Question or interrogative close: asks 'Can we afford another four years?'",
        ],
        "required_moves": ["Intent Escalation"],
        "optional_moves": ["Policy Sprint", "Behavioral Directive Close"],
        "rule1_hint": "Contractual Concession — concede what the incumbent promised, then show what they delivered",
        "example_piece": "KCP 'Hardly Working'",
        "notes": "Session 4 CRITICAL: target is Karen Carter Peterson (KCP). Register renamed from Performance Attack → Performance Indictment Attack (Session 5).",
    },

    "R28": {
        "code": "R28",
        "name": "Voter Agency Empowerment",
        "description": "Empowers the voter as the protagonist. The candidate or issue is secondary — voter's power is the message.",
        "formats": [FORMAT_TV_30, FORMAT_TV_60, FORMAT_DIGITAL_30],
        "defining_characteristics": [
            "Voter addressed directly ('You have the power')",
            "Community Liberation Close — the vote is the liberation act",
            "Interrogative/Fatalism Challenge: challenges voter fatalism or cynicism",
            "Two-Second Rule: digital hook must grab in 2 seconds or viewers skip",
        ],
        "required_moves": ["Community Liberation Close"],
        "optional_moves": ["Interrogative/Fatalism Challenge", "Universalizing Inoculation"],
        "rule1_hint": "Voter Loyalty Concession — concede the voter's right to be skeptical before making the empowerment argument",
        "example_piece": "'Trust Yourself'",
        "notes": "Session 5: 'Trust Yourself' is the corpus exemplar. One of the 5 strongest pieces in the corpus.",
    },

    "R29": {
        "code": "R29",
        "name": "Single-Issue Economic Pledge Brief",
        "description": "Candidate makes a narrow, specific economic pledge. The specificity is the credibility.",
        "formats": [FORMAT_TV_30, FORMAT_TV_60, FORMAT_DIGITAL_30],
        "defining_characteristics": [
            "One issue, one pledge, one concrete number or outcome",
            "Candidate directly to camera for the pledge",
            "Potholes as Specificity Anchor: hyper-specific detail signals authenticity",
            "Personal Pledge Close",
        ],
        "required_moves": ["Personal Pledge Close", "Potholes as Specificity Anchor"],
        "optional_moves": ["Credential-to-Consequence Architecture"],
        "rule1_hint": "Complexity Concession — concede that economic issues are complicated, then strip it to one clear pledge",
        "example_piece": "'Insurance'",
        "notes": "Session 5 corpus. The specificity of the pledge IS the inoculation against 'just promises' attacks.",
    },

    "R30": {
        "code": "R30",
        "name": "Multi-Issue Incumbent Intro Brief",
        "description": "Short incumbent introduction covering multiple issues. Breadth signals experience.",
        "formats": [FORMAT_TV_30, FORMAT_DIGITAL_30],
        "defining_characteristics": [
            "Multiple issues in tight sequence — Policy Sprint is required",
            "Incumbent's record as the evidence base",
            "Momentum Close: 'The work continues'",
            "Two-Second Rule: must establish who this is immediately",
        ],
        "required_moves": ["Policy Sprint", "Momentum Close"],
        "optional_moves": ["Behavioral Directive Close"],
        "rule1_hint": "Thesis Concession — concede that incumbency requires accountability before presenting the record",
        "example_piece": "'Ready' (Adams)",
        "notes": "Session 5. Distinguish from R25 (warmth-led) — R30 is record-led, breadth-signaling.",
    },

    "R31": {
        "code": "R31",
        "name": "Cronyism Network Attack",
        "description": "Attack exposing a network of self-dealing relationships. The network is the villain — no single person is isolated.",
        "formats": [FORMAT_TV_30, FORMAT_TV_60, FORMAT_DIGITAL_30],
        "defining_characteristics": [
            "Network mapping visible on screen (connecting lines, names)",
            "Each node in the network is introduced with a specific allegation",
            "Veiled Disqualification: the network implies corruption without making the word 'corrupt' necessary",
            "Interrogative close: 'Who does he really work for?'",
        ],
        "required_moves": ["Intent Escalation"],
        "optional_moves": ["Policy Sprint"],
        "rule1_hint": "Contractual Concession — concede the official's stated role before showing who they actually serve",
        "example_piece": "'Safari'",
        "notes": "Session 5: 'Safari' is one of the 5 strongest pieces in the corpus. Network frame is load-bearing.",
    },

    "R32": {
        "code": "R32",
        "name": "Extended Metaphor Corruption Bio",
        "description": "A single extended metaphor carries the entire corruption argument. The most sophisticated attack register.",
        "formats": [FORMAT_TV_30, FORMAT_TV_60, FORMAT_DIGITAL_30],
        "defining_characteristics": [
            "One metaphor, extended through the entire spot",
            "Metaphor is introduced in the opening concession",
            "Each piece of evidence maps onto the metaphor",
            "Bookend on the metaphor's key word — meaning escalates",
        ],
        "required_moves": ["Bookend (Meaning Escalation Variant)"],
        "optional_moves": ["Intent Escalation", "Veiled Disqualification"],
        "rule1_hint": "Definitional Concession — concede the 'innocent' definition of the metaphor before revealing the corrupt one",
        "example_piece": "'Fortune'",
        "notes": "Session 5: 'Fortune' is the #1 rated piece in the corpus. The metaphor makes the argument self-evident.",
    },

    "R33": {
        "code": "R33",
        "name": "PAC Positive Advocacy Brief",
        "description": "PAC-funded positive advocacy for a candidate. Third-party credibility separates this from candidate-funded R8.",
        "formats": [FORMAT_TV_30, FORMAT_TV_60, FORMAT_DIGITAL_30],
        "defining_characteristics": [
            "Sponsor disclosure is structural (required by law) — integrate it, don't just tag it",
            "Portable Identity Module: the candidate's identity must be established without the candidate's voice",
            "Credential-to-Consequence Architecture",
            "Narrator carries credibility (PAC, not candidate)",
        ],
        "required_moves": ["Portable Identity Module", "Credential-to-Consequence Architecture"],
        "optional_moves": ["Soft Contrast Close"],
        "rule1_hint": "Insider Concession — the PAC concedes it has an interest before explaining why the candidate earns support despite that",
        "example_piece": "'Ready' (Pearson)",
        "notes": "Session 5. Kevin Pearson race was corrected (Session 5 critical correction).",
    },

    "R34": {
        "code": "R34",
        "name": "Narrator-Led Credential Bio",
        "description": "Narrator (not candidate) builds the credential case. Candidate speaks only for the pledge.",
        "formats": [FORMAT_TV_30, FORMAT_TV_60, FORMAT_DIGITAL_30],
        "defining_characteristics": [
            "Narrator owns the evidence; candidate owns the promise",
            "Credential-to-Consequence Architecture is the spine",
            "Candidate's direct-to-camera moment is the bookend close",
            "Personal Pledge Close",
        ],
        "required_moves": ["Credential-to-Consequence Architecture", "Personal Pledge Close"],
        "optional_moves": ["Name Recognition Inoculation"],
        "rule1_hint": "Thesis Concession — narrator concedes the credentials alone aren't enough before making the character claim",
        "example_piece": "'Home'",
        "notes": "Session 5. The separation of narrator (evidence) and candidate (promise) is the structural load-bearer.",
    },

    "R35": {
        "code": "R35",
        "name": "Judicial Vacancy Bio",
        "description": "Judicial candidate bio. The vacancy itself is the opening — the seat matters before the candidate does.",
        "formats": [FORMAT_TV_30, FORMAT_TV_60, FORMAT_DIGITAL_30],
        "defining_characteristics": [
            "The vacant seat / judicial role is introduced first",
            "Candidate's legal credentials are the inoculation",
            "Non-partisan framing is structurally required",
            "Behavioral Directive Close: 'Vote for [Name] for [Court]'",
        ],
        "required_moves": ["Credential-to-Consequence Architecture", "Behavioral Directive Close"],
        "optional_moves": ["Name Recognition Inoculation"],
        "rule1_hint": "Definitional Concession — concede what a judge is supposed to do before showing this candidate embodies it",
        "example_piece": "'Five Judges' / 'Promise' (Myers)",
        "notes": "Session 5. The vacancy frame sets up why the credential matters — don't lead with the credential first.",
    },

    "R36": {
        "code": "R36",
        "name": "Constituent Betrayal Attack",
        "description": "Attack from the perspective of betrayed constituents. The victims are the attackers, not the campaign.",
        "formats": [FORMAT_TV_30, FORMAT_TV_60, FORMAT_DIGITAL_30],
        "defining_characteristics": [
            "Constituent voices carry the indictment (R36 is a proxy attack variant)",
            "Betrayal is the emotional engine — specific promises shown alongside specific failures",
            "Veiled Disqualification: 'He forgot about us' rather than 'He's corrupt'",
            "Interrogative/Fatalism Challenge close: 'How many times will you trust him?'",
        ],
        "required_moves": ["Credential-to-Consequence Architecture"],
        "optional_moves": ["Voter Loyalty Concession", "Intent Escalation"],
        "rule1_hint": "Voter Loyalty Concession — open with the constituent's loyalty before the betrayal revelation",
        "example_piece": "'Storm'",
        "notes": "Session 5. The constituent-as-victim frame is what separates R36 from standard attacks.",
    },

    "RADIO_ISSUE_CONTRAST": {
        "code": "RADIO_ISSUE_CONTRAST",
        "name": "Radio Issue Contrast",
        "description": "Radio-native contrast between two policy positions. Audio carries complete argument without visual support.",
        "formats": [FORMAT_RADIO_30, FORMAT_RADIO_60],
        "defining_characteristics": [
            "Two positions stated clearly in audio — no visual split frame possible",
            "Deliberate pause separates the contrast (Rule 4 radio equivalent)",
            "Policy Sprint structure for the contrast evidence",
            "Behavioral Directive Close",
        ],
        "required_moves": ["Policy Sprint", "Behavioral Directive Close"],
        "optional_moves": ["Plain-Language Translation"],
        "rule1_hint": "Opponent Claim Inversion — use the opponent's stated position as the concession, then show the consequences",
        "example_piece": "Hunter Lundy Radio Issue Contrast",
        "notes": "Foundational radio register. The silence between the two positions IS the persuasion move.",
    },
}


# ══════════════════════════════════════════════════════════════════
# FORMAT → REGISTER MAPPING
# ══════════════════════════════════════════════════════════════════

FORMAT_REGISTERS = {
    FORMAT_TV_30: [
        "R8", "R9", "R10", "R11a", "R11b", "R12", "R13", "R14",
        "R15", "R16", "R17", "R18", "R20", "R22", "R24", "R25",
        "R26", "R27", "R28", "R29", "R30", "R31", "R32", "R33",
        "R34", "R35", "R36",
    ],
    FORMAT_TV_60: [
        "R8", "R9", "R10", "R11a", "R11b", "R12", "R13", "R14",
        "R15", "R16", "R17", "R18", "R20", "R22", "R24", "R25",
        "R26", "R27", "R28", "R31", "R32", "R33", "R34", "R35", "R36",
    ],
    FORMAT_RADIO_30: ["R8_RADIO", "RADIO_ISSUE_CONTRAST"],
    FORMAT_RADIO_60: [
        "R8_RADIO", "R15", "R17", "R18", "R19", "R20", "R21", "RADIO_ISSUE_CONTRAST",
    ],
    FORMAT_DIGITAL_30: [
        "R8", "R9", "R10", "R11a", "R11b", "R12", "R14",
        "R22", "R24", "R25", "R26", "R27", "R28", "R29",
        "R30", "R31", "R32", "R33", "R34", "R35", "R36",
    ],
    FORMAT_CORPORATE: ["R12"],
}


# ══════════════════════════════════════════════════════════════════
# SIGNATURE RULES — 6 core rules applied to all scripts
# ══════════════════════════════════════════════════════════════════

RULES = {
    1: {
        "name": "Concession-First",
        "description": (
            "Every script opens by conceding the opponent's strongest point. "
            "The concession is not weakness — it is the move that earns the audience's trust "
            "before the argument begins. Pick the variant that fits the register and audience."
        ),
        "validation_check": (
            "Does the script open with something the opponent or skeptic would agree with? "
            "If the opening line would only resonate with supporters, Rule 1 is not active."
        ),
        "has_variants": True,
    },
    2: {
        "name": "Visual Grammar",
        "description": (
            "B-roll is evidence, not decoration. Every visual must prove something. "
            "If a shot could be removed without losing an argument, it must be replaced. "
            "Ask of each shot: what does this prove?"
        ),
        "validation_check": (
            "List the argument each piece of b-roll makes. If any shot has no argument, "
            "replace it."
        ),
        "has_variants": False,
    },
    3: {
        "name": "Compressed Language",
        "description": (
            "Maximum meaning per word. Seven-word limit for text cards. No filler. "
            "If a word doesn't earn its place, cut it. "
            "Radio equivalent: no filler phrases ('uh', 'you know', 'and so')."
        ),
        "validation_check": (
            "Read every text card. More than 7 words? Rewrite. "
            "In VO: can any sentence be cut by 30% without losing meaning?"
        ),
        "has_variants": False,
    },
    4: {
        "name": "Text as Punctuation",
        "description": (
            "Text card + pause = the move. The text card lands the argument; "
            "the pause lets it sink. Don't rush from card to VO. "
            "Radio equivalent: deliberate pause after a key phrase. "
            "The pause is not dead air — it is the argument landing."
        ),
        "validation_check": (
            "Does each text card have a beat of silence after it? "
            "Is the VO attempting to explain what the text card already said? (Remove the VO.)"
        ),
        "has_variants": True,
        "variants": {
            "Standard": "Text card + pause. The default application.",
            "Underwriting Addendum": "When the script reads full on paper, it WILL perform crowded on screen. Leave room for the beat.",
            "Relational Card Variant": "A text card that names a relationship ('Father. Husband. Sheriff.') followed by a visual that embodies it.",
        },
    },
    5: {
        "name": "Implied Villain",
        "description": (
            "The villain is never named on screen unless the register specifically requires it. "
            "The audience fills in the blank — which is more powerful than being told. "
            "Four documented absence contexts where Rule 5 is architecturally absent."
        ),
        "validation_check": (
            "Is the opponent named on screen in a way that is NOT required by the register? "
            "If yes, remove the name and let the audience complete the thought."
        ),
        "has_variants": True,
        "absence_contexts": {
            "R10 Exception": "Opponent's own words appear because they ARE the concession.",
            "R12 Corporate": "No external villain — solidarity frame precludes contrast.",
            "R21 Community": "Community solidarity frame — naming a villain breaks the solidarity.",
            "R24 Environmental": "Industry is the addressee, not the villain.",
            "R25 Incumbent Expansion": "Re-election frame precludes comparison — expansion, not contrast.",
        },
    },
    6: {
        "name": "Bookend",
        "description": (
            "The same word appears at the open and close of the script, "
            "but its meaning deepens through the argument. "
            "The audience hears 'promise' at the start as a simple word; "
            "they hear it at the close as a covenant."
        ),
        "validation_check": (
            "Identify the bookend word. Does the argument between open and close "
            "earn the deeper meaning the close requires? "
            "If the bookend word means the same thing at open and close, the Rule 6 move hasn't landed."
        ),
        "has_variants": True,
        "variants": {
            "Standard": "Same word, deepened meaning through argument.",
            "Meaning Escalation": "The bookend word escalates in emotional weight — not just deepened but transformed.",
            "EBRSO Door Bookend": "The strongest bookend in corpus — 'door' means exclusion at open, opportunity at close.",
        },
    },
}


# ══════════════════════════════════════════════════════════════════
# RULE 1 VARIANTS — 19 documented concession opens
# ══════════════════════════════════════════════════════════════════

RULE1_VARIANTS = {
    "Rhetorical Question Concession": {
        "description": "Opens with a question the audience already answers one way. The concession is built into the question.",
        "example": "'Do you believe everyone deserves a fair shot?' — audience says yes before you make the argument.",
        "best_for": ["R8", "R8_RADIO", "R19", "RADIO_ISSUE_CONTRAST"],
    },
    "Opponent Concession as Opening": {
        "description": "Uses the opponent's own words or strongest argument as the opening. The opponent makes your concession for you.",
        "example": "[Opponent's quote on screen] 'He said it himself...'",
        "best_for": ["R10", "R27", "R36"],
    },
    "Rumor Absorption": {
        "description": "Names the rumor or attack before the opponent can deploy it, then dissolves it.",
        "example": "'You've heard the attack. Here's the truth.'",
        "best_for": ["R17", "R18"],
    },
    "Insider Concession": {
        "description": "Concedes from a position of insider knowledge — acknowledges the industry or institution's own failures.",
        "example": "From a doctor: 'I know how our system failed. That's why I'm here.'",
        "best_for": ["R16", "R33", "R11b"],
    },
    "Voter Loyalty Concession": {
        "description": "Concedes respect for the voter's current allegiance before asking for a change.",
        "example": "'You've supported [opponent] for years. Your loyalty is real. But look at what we got.'",
        "best_for": ["R13", "R36", "R28"],
    },
    "Preemptive Concession": {
        "description": "Addresses the attack before it comes. Takes the punch before it's thrown.",
        "example": "'They're going to say I raised your taxes. Here's what they won't tell you.'",
        "best_for": ["R17", "R9"],
    },
    "Opponent Claim Inversion": {
        "description": "Concedes the opponent's claim, then shows it means the opposite of what they intended.",
        "example": "'She says she's tough on crime. Let's look at what that actually produced.'",
        "best_for": ["R27", "RADIO_ISSUE_CONTRAST"],
    },
    "Thesis Concession": {
        "description": "Concedes the general principle the opponent is arguing for, then shows this candidate embodies it better.",
        "example": "'We all agree government should be accountable. Here's what accountability actually looks like.'",
        "best_for": ["R14", "R30", "R34"],
    },
    "Emotional Self-Disclosure": {
        "description": "Opens with the speaker acknowledging their own emotional stake — vulnerability as disarming move.",
        "example": "'I won't pretend this was easy. My family went through this too.'",
        "best_for": ["R11b", "R8", "R35"],
    },
    "Community Label Open": {
        "description": "Concedes the community's identity and its tensions before claiming to represent it.",
        "example": "'We are a law-and-order state. We always have been. And that's exactly why this law must change.'",
        "best_for": ["R8", "R15", "R21"],
    },
    "Industry Concession": {
        "description": "Concedes industry terminology and values before redirecting them.",
        "example": "'Insurance is about security. We believe that too. Here's what security actually requires.'",
        "best_for": ["R12", "R24", "R29"],
    },
    "Stat-as-Concession Open": {
        "description": "Leads with a statistic that seems to support the opposition, then reframes it.",
        "example": "'Louisiana is one of the toughest-on-crime states in America. And we have one of the highest recidivism rates.'",
        "best_for": ["R11a", "R20", "R22"],
    },
    "Heritage Duration Open": {
        "description": "Concedes the historical depth of the opposing tradition before showing why it has run its course.",
        "example": "'For 40 years, this has been the law. For 40 years, it hasn't worked.'",
        "best_for": ["R21", "R22", "R8_RADIO"],
    },
    "Inverted Concession Pivot": {
        "description": "Concedes the opponent's frame entirely, then shows it leads to the opposite conclusion.",
        "example": "'If you believe in personal responsibility — and I know you do — then you believe people can change.'",
        "best_for": ["R8", "R19"],
    },
    "Definitional Concession": {
        "description": "Concedes the opponent's definition of a term, then expands it to include what they excluded.",
        "example": "'They define safety as more prisons. We define safety as fewer victims.'",
        "best_for": ["R26", "R32", "R35"],
    },
    "Complexity Concession": {
        "description": "Concedes the issue is genuinely complex before presenting the clear solution.",
        "example": "'Criminal justice is complicated. The research is complicated. But the human cost is simple.'",
        "best_for": ["R19", "R22", "R29"],
    },
    "Contractual Concession": {
        "description": "Concedes a prior commitment, contract, or promise before showing it was broken.",
        "example": "'We trusted you with this office. You made a promise. Let's look at the promise.'",
        "best_for": ["R27", "R31", "R36"],
    },
    "Declarative Pause": {
        "description": "A single declarative statement — often 'It's true' or similar — that absorbs the opposition's main claim before pivoting.",
        "example": "'It's true. Taxes went up. Here's what they built.'",
        "best_for": ["R27", "R30"],
        "notes": "Session 5 correction: originally called 'It's True' variant — renamed to Declarative Pause for generalizability.",
    },
    "Veiled Disqualification": {
        "description": "Concedes the opponent's formal qualifications before revealing the disqualifying behavior.",
        "example": "'He's been in office 12 years. By any measure, he's experienced. Experienced at what?'",
        "best_for": ["R27", "R31", "R36"],
        "notes": "Session 5 correction: this was previously unnamed. Now formalized as a Rule 1 variant.",
    },
}


# ══════════════════════════════════════════════════════════════════
# FOUNDATIONAL PRINCIPLES — 3 principles applied as quality checks
# ══════════════════════════════════════════════════════════════════

PRINCIPLES = {
    "Underwriting": {
        "name": "Underwriting",
        "description": (
            "The silence is half the move. If the script reads full on paper, "
            "it WILL perform crowded on screen. "
            "Always leave room for the beat to sink in. "
            "What you don't say creates the space for what you do say to land."
        ),
        "test": (
            "Read the script aloud at broadcast pace. "
            "If every second is filled with audio, the Underwriting principle is violated. "
            "Identify 2-3 beats where silence should replace audio."
        ),
        "applies_to": ["all formats"],
    },
    "Silent Track": {
        "name": "Silent Track",
        "description": (
            "Cover the audio. Read only the text cards in order. "
            "Does the text-card sequence carry the complete argument "
            "for a viewer who never hears the audio? "
            "If not, the script fails muted viewers — who are the majority in digital."
        ),
        "test": (
            "Print the text cards only. "
            "Number them. "
            "Can you reconstruct the full argument from the cards alone? "
            "If any card is blank in isolation, it needs to be a complete thought."
        ),
        "applies_to": [FORMAT_TV_30, FORMAT_TV_60, FORMAT_DIGITAL_30],
    },
    "Complexity Embodiment Split": {
        "name": "Complexity Embodiment Split",
        "description": (
            "When applicable: the visual channel embodies the problem; "
            "the audio channel resolves it. "
            "They work opposite poles simultaneously. "
            "The viewer sees the complexity while hearing the resolution."
        ),
        "test": (
            "Cover the audio: does the visual tell a story of a problem? "
            "Cover the video: does the audio tell a story of resolution? "
            "If both channels tell the same story, the split is not active."
        ),
        "applies_to": [FORMAT_TV_30, FORMAT_TV_60, FORMAT_DIGITAL_30],
        "canonical_example": "R24 Environmental, R12 BCBSLA Corporate",
    },
}


# ══════════════════════════════════════════════════════════════════
# PRODUCTION DOCTRINE — 7 rules from Session 5
# ══════════════════════════════════════════════════════════════════

PRODUCTION_DOCTRINE = {
    "A": {
        "name": "Bio = Less Visual Clutter",
        "rule": "Bio spots perform better with fewer visual elements. Space is credibility.",
    },
    "B": {
        "name": "Digital = Audio-Off First",
        "rule": (
            "Design every digital spot to work without audio. "
            "Audio-off is the default state for most digital viewers. "
            "If the spot requires audio to make sense, redesign."
        ),
    },
    "C": {
        "name": "TV = Usually :30",
        "rule": "TV spots should default to :30 unless the register specifically requires :60 depth.",
    },
    "D": {
        "name": "Digital Pricing",
        "rule": "Digital :15 and :30 have different CPM and completion-rate profiles. Match length to goal.",
    },
    "E": {
        "name": "Radio :60 Almost Always Better",
        "rule": (
            "Radio :60 is almost always the better investment. "
            "The extra 30 seconds allows the argument to breathe. "
            ":30 radio is for jingle/ID work, not argument work."
        ),
    },
    "F": {
        "name": "Digital Requires Fast Hook — Two-Second Rule",
        "rule": (
            "Digital video must establish the core message within 2 seconds "
            "or viewers will skip. "
            "The Two-Second Rule: if the hook isn't present in the first 2 seconds, "
            "the spot is already losing."
        ),
    },
    "G": {
        "name": "OTT/Set-Top Exception",
        "rule": (
            "OTT and set-top box delivery behaves more like broadcast TV — "
            "viewers are in lean-back mode, not thumb-scroll mode. "
            "The Two-Second Rule is relaxed; Underwriting applies fully."
        ),
    },
}


# ══════════════════════════════════════════════════════════════════
# STRUCTURAL MOVES — 50+ documented moves across all sessions
# ══════════════════════════════════════════════════════════════════

STRUCTURAL_MOVES = {
    # ── OPENING MOVES ──
    "Origin Story as Inoculation": {
        "description": "The candidate's personal history pre-empts the character attack. Story IS the inoculation.",
        "applicable_registers": ["R8", "R8_RADIO", "R15", "R17", "R18"],
    },
    "Three-Beat Candidate Introduction": {
        "description": "Three rapid credential beats — Name. Role. Why it matters. Sets up everything that follows.",
        "applicable_registers": ["R15", "R18", "R8_RADIO"],
    },
    "Potholes as Specificity Anchor": {
        "description": "Hyper-local, specific detail (literally: knows the potholes) signals trustworthiness.",
        "applicable_registers": ["R15", "R25", "R29"],
    },
    "Name Recognition Inoculation": {
        "description": "Acknowledges low name recognition as a feature, not a bug. 'You don't know me yet. Here's why that's about to change.'",
        "applicable_registers": ["R34", "R35", "R16"],
    },
    "Credential-to-Consequence Architecture": {
        "description": "Credential is stated, then immediately linked to a consequence for the voter. 'She's a doctor — that's why she knows what this cost you.'",
        "applicable_registers": ["R10", "R11b", "R13", "R16", "R33", "R34", "R35", "R36"],
    },
    "Universalizing Inoculation": {
        "description": "Expands the in-group to include the skeptic. 'Even people who disagree with me on other things...'",
        "applicable_registers": ["R11b", "R17"],
    },

    # ── ARGUMENT STRUCTURE ──
    "Policy Sprint": {
        "description": "Rapid-fire evidence sequence — multiple stats or facts in tight succession. The accumulation IS the argument.",
        "applicable_registers": ["R11a", "R14", "R19", "R20", "R22", "R30"],
    },
    "Intent Escalation": {
        "description": "The contrast deepens across the spot. Each beat reveals more intent. The close is the most damning.",
        "applicable_registers": ["R14", "R27", "R31", "R36"],
    },
    "Sprint-to-Depth": {
        "description": "Policy Sprint followed by single deep-dive moment. Fast evidence build, then one beat held longer.",
        "applicable_registers": ["R11a", "R22"],
        "canonical_example": "Lundy Sprint-to-Depth fully mapped in Session 3.",
    },
    "Audience-Calibrated Stat Deployment": {
        "description": "The statistic is chosen and framed to match the specific audience's known beliefs. R support for a bipartisan stat to a Republican audience.",
        "applicable_registers": ["R11a", "R20", "R22"],
    },
    "Plain-Language Translation": {
        "description": "A complex policy term is immediately followed by its plain-language equivalent.",
        "applicable_registers": ["R11a", "R11b", "R19"],
    },
    "Complexity Embodiment Split": {
        "description": "Visual embodies the problem; audio resolves it. Both channels work simultaneously in opposite directions.",
        "applicable_registers": ["R12", "R24"],
    },
    "Frame Reclamation": {
        "description": "Reclaim a term the opposition has owned ('safety', 'freedom', 'accountability') and redefine it.",
        "applicable_registers": ["R24", "R26"],
    },

    # ── CONTRAST MOVES ──
    "Soft Contrast Close": {
        "description": "Implicit contrast at the close — the opponent is implied, never named. 'Some people made promises. He kept them.'",
        "applicable_registers": ["R8", "R25", "R18"],
    },
    "Dual-Register Ask": {
        "description": "Two different audiences addressed in the same spot with different asks.",
        "applicable_registers": ["R26", "R22"],
    },

    # ── PRODUCTION MOVES ──
    "Locked Phrases": {
        "description": "Specific phrases that travel unchanged across media — suite-level consistency. 'I won't let you down.'",
        "applicable_registers": ["R12", "R8"],
        "canonical_examples": [
            "BCBSLA: 'promise' as suite master word",
            "Lundy: 'I've always been on the side of David, not Goliath'",
            "Lundy: 'I won't let you down'",
            "Lundy: 'These politicians aren't doing what works, but I will'",
        ],
    },
    "Portable Identity Module": {
        "description": "A tight, transferable package of candidate identity that works in any spot without the candidate present.",
        "applicable_registers": ["R33", "R34"],
    },
    "Dual-Version Production": {
        "description": "Same core argument produced in two formats — TV :30 leads, Radio :60 expands. The close locks in both.",
        "applicable_registers": ["R12", "R8", "R8_RADIO"],
    },
    "Disclaimer Displacement": {
        "description": "The legal disclaimer is moved from dead space at the end to a position that serves the argument.",
        "applicable_registers": ["R12", "R33"],
    },
    "Cross-Medium Adaptation Pattern": {
        "description": "TV :30 establishes the image; Radio :60 expands the story. Setup expands in radio, close locks same as TV.",
        "applicable_registers": ["R8", "R8_RADIO", "R12"],
    },

    # ── CLOSE TYPES ──
    "Personal Pledge Close": {
        "description": "Candidate directly to camera: 'I promise.' The most personal close — earned only by the bio register.",
        "applicable_registers": ["R8", "R29", "R34"],
    },
    "Behavioral Directive Close": {
        "description": "Tells the viewer exactly what to do. 'Call your legislator.' 'Vote on [date].' 'Sign the petition.'",
        "applicable_registers": ["R9", "R11a", "R11b", "R14", "R19", "R20"],
    },
    "Electability Close": {
        "description": "Ends on electability argument — why this candidate can win, not just why they're right.",
        "applicable_registers": ["R8", "R8_RADIO", "R10"],
    },
    "Community Liberation Close": {
        "description": "The vote is framed as a liberation act for the community. 'This November, [Community] takes its future back.'",
        "applicable_registers": ["R21", "R28"],
    },
    "Interrogative/Fatalism Challenge": {
        "description": "Challenges voter cynicism or fatalism directly. 'How many times will you wait for change that never comes?'",
        "applicable_registers": ["R28", "R31", "R36"],
    },
    "Momentum Close": {
        "description": "Frames the candidate or issue as momentum in motion. 'The work continues. Join us.'",
        "applicable_registers": ["R30", "R33"],
    },
    "Bookend (Meaning Escalation Variant)": {
        "description": "The bookend word at close carries transformed meaning — not just deepened but fundamentally changed by the argument.",
        "applicable_registers": ["R32"],
        "canonical_example": "'Fortune' — the word means luck at open, corruption at close.",
    },

    # ── FAITH AND COMMUNITY MOVES ──
    "Faith Integration": {
        "description": "Faith language or imagery integrated structurally — not tacked on, but load-bearing.",
        "applicable_registers": ["R8", "R15", "R17", "R21"],
    },
    "'Us vs. Bullies' Community Frame": {
        "description": "Reframes the conflict as a community standing up to powerful bullies. Activates solidarity.",
        "applicable_registers": ["R9", "R21"],
    },
}


# ══════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ══════════════════════════════════════════════════════════════════

def get_registers_for_format(format_type):
    """
    Return list of register dicts applicable to the given format.
    format_type: one of the FORMAT_* constants.
    """
    codes = FORMAT_REGISTERS.get(format_type, [])
    return [REGISTERS[c] for c in codes if c in REGISTERS]


def get_rule1_variant(register_code, context=None):
    """
    Suggest the most natural Rule 1 variant for a given register.
    Returns the variant name and description.
    context: optional dict with topic/construct info for additional guidance.
    """
    reg = REGISTERS.get(register_code)
    if not reg:
        return None
    hint = reg.get("rule1_hint", "")
    # Find matching variant by hint keyword
    for variant_name, variant_data in RULE1_VARIANTS.items():
        if variant_name.lower() in hint.lower():
            return {"name": variant_name, **variant_data}
    # Return hint text even if no exact match
    return {"name": "Suggested approach", "description": hint}


def validate_script(script_text, format_type, register_code):
    """
    Run script text against signature rules and foundational principles.
    Returns list of {rule, check, status, note} dicts.
    format_type: one of the FORMAT_* constants.
    register_code: e.g. "R8", "R22", etc.
    """
    results = []
    reg = REGISTERS.get(register_code, {})

    # Rule 1: Concession-First
    rule1_check = RULES[1]["validation_check"]
    results.append({
        "rule": "Rule 1 — Concession-First",
        "check": rule1_check,
        "guidance": f"Suggested variant: {reg.get('rule1_hint', 'See RULE1_VARIANTS dict')}",
    })

    # Rule 3: Compressed Language
    results.append({
        "rule": "Rule 3 — Compressed Language (7-word text card limit)",
        "check": RULES[3]["validation_check"],
        "guidance": "Count words in each text card. Flag any over 7 words.",
    })

    # Rule 5: Implied Villain
    rule5_note = ""
    absence = RULES[5]["absence_contexts"]
    for ctx_name, ctx_desc in absence.items():
        if register_code in ctx_name or register_code in ctx_desc:
            rule5_note = f"Note: Rule 5 is architecturally absent for {register_code} — {ctx_desc}"
            break
    results.append({
        "rule": "Rule 5 — Implied Villain",
        "check": RULES[5]["validation_check"],
        "guidance": rule5_note or "Check: is the villain named? If so, is the register an exception?",
    })

    # Rule 6: Bookend
    results.append({
        "rule": "Rule 6 — Bookend",
        "check": RULES[6]["validation_check"],
        "guidance": "Identify the bookend word. Does it deepen in meaning from open to close?",
    })

    # Principles
    is_tv_digital = format_type in [FORMAT_TV_30, FORMAT_TV_60, FORMAT_DIGITAL_30]

    results.append({
        "rule": "Principle — Underwriting",
        "check": PRINCIPLES["Underwriting"]["test"],
        "guidance": "If every second of audio is filled, the Underwriting principle is violated.",
    })

    if is_tv_digital:
        results.append({
            "rule": "Principle — Silent Track",
            "check": PRINCIPLES["Silent Track"]["test"],
            "guidance": "Print text cards only. Can you reconstruct the argument from cards alone?",
        })

    if format_type == FORMAT_DIGITAL_30:
        results.append({
            "rule": "Production Doctrine F — Two-Second Rule",
            "check": PRODUCTION_DOCTRINE["F"]["rule"],
            "guidance": "Does the first 2 seconds of the spot establish the core message?",
        })

    return results


def get_register_display_list(format_type):
    """
    Return list of (code, name, description) tuples for UI display.
    Sorted alphabetically by name.
    """
    regs = get_registers_for_format(format_type)
    return sorted(
        [(r["code"], r["name"], r["description"]) for r in regs],
        key=lambda x: x[1],
    )


def get_required_moves_for_register(register_code):
    """Return list of required structural move names for a register."""
    reg = REGISTERS.get(register_code, {})
    return reg.get("required_moves", [])


def get_structural_move(move_name):
    """Return structural move dict by name."""
    return STRUCTURAL_MOVES.get(move_name, {})
