"""
script_generator.py — Inline script generation for MediaMaker.

Builds the generation prompt from the creative system context (register,
Rule 1 variant, structural moves, production doctrine, data anchor, audience)
and calls the Anthropic API to produce a ready-to-use script in the correct
format for the selected medium.

Preston's voice markers that the prompt enforces:
  - Concession-First (Rule 1) — always open on the opponent's strongest point
  - Data as drama — the statistic stands alone, stated plainly before pivoting
  - Silence as editorial power — punctuation, line breaks, and pauses ARE the persuasion
  - Villain implied, never named on screen
  - Rule 6 Bookend — the close echoes the open but the meaning has deepened
  - Underwriting — space after every key moment; crowded script = crowded screen
  - Silent Track — for TV/Digital, text cards carry the complete argument without audio
"""

from __future__ import annotations
from typing import Optional

# ── Format word count limits ──────────────────────────────────────
FORMAT_WORD_COUNTS = {
    "TV :30":      75,
    "TV :60":      150,
    "Radio :30":   90,
    "Radio :60":   180,
    "Digital :30": 60,
    "Corporate":   250,   # flexible — this is a target, not a hard cap
}

# ── Format types that require video/silent track sections ─────────
VIDEO_FORMATS = {"TV :30", "TV :60", "Digital :30"}
RADIO_FORMATS = {"Radio :30", "Radio :60"}


def _moves_block(req_moves: list[str], structural_moves: dict) -> str:
    """Format required structural moves for the prompt."""
    lines = []
    for move in req_moves:
        m = structural_moves.get(move, {})
        desc = m.get("description", "")
        lines.append(f"  • {move}")
        if desc:
            lines.append(f"    {desc}")
    return "\n".join(lines) if lines else "  (none specified)"


def build_prompt(
    *,
    topic_label: str,
    construct: str,
    tier: str,
    tier_role: str,
    selected_format: str,
    reg_name: str,
    reg_description: str,
    reg_characteristics: list[str],
    req_moves: list[str],
    opt_moves: list[str],
    r1_name: str,
    r1_desc: str,
    anchor_text: str,
    audience: str,
    audience_rationale: str,
    live_pct: Optional[float],
    r_pct: Optional[float],
    d_pct: Optional[float],
    words_work: list[str],
    words_avoid: list[str],
    frame: str,
    inoculation: str,
    cta: str,
    state_data: dict,                 # {state_abbr: pct}
    bill_text: str,
    assets_text: str,
    additional_notes: str,
    structural_moves: dict,           # full STRUCTURAL_MOVES dict
    rules: dict,                      # full RULES dict
    principles: dict,                 # full PRINCIPLES dict
    production_doctrine: dict,        # full PRODUCTION_DOCTRINE dict
) -> str:
    """Build the full generation prompt from all creative system components."""

    word_limit = FORMAT_WORD_COUNTS.get(selected_format, 150)
    is_video = selected_format in VIDEO_FORMATS
    is_radio = selected_format in RADIO_FORMATS

    # ── Partisan gap interpretation ───────────────────────────────
    partisan_note = ""
    if r_pct is not None and d_pct is not None:
        gap = d_pct - r_pct
        if abs(gap) <= 8:
            partisan_note = (
                f"Bipartisan support confirmed (D-R gap = {gap:+.1f}pts). "
                "Do NOT frame this as a left-leaning message. "
                "The audience is voters of all parties — this is common-ground territory."
            )
        elif gap > 15:
            partisan_note = (
                f"This construct has a partisan gap of {gap:+.1f}pts (D-R). "
                "Republican identity resistance is real. "
                "Open with something a conservative voter could say. "
                "Avoid language that reads as progressive — frame on values, not ideology."
            )
        elif gap < -10:
            partisan_note = (
                f"Republicans actually lean MORE favorable here ({gap:+.1f}pts R-D). "
                "Lean into that. The conservative audience is an asset, not a liability."
            )
        else:
            partisan_note = f"Moderate partisan gap ({gap:+.1f}pts D-R). Neutral framing preferred."

    # ── State variation context ────────────────────────────────────
    state_context = ""
    if state_data:
        sorted_s = sorted(state_data.items(), key=lambda x: x[1], reverse=True)
        state_context = "State support (strongest first): " + ", ".join(
            f"{s} {round(p)}%" for s, p in sorted_s
        )
        spread = max(v for _, v in sorted_s) - min(v for _, v in sorted_s)
        if spread <= 8:
            state_context += f"\nSpread = {spread:.0f}pts — message transfers nationally. Don't over-localize."
        else:
            state_context += f"\nSpread = {spread:.0f}pts — state-specific adaptation likely needed."

    # ── Production doctrine (condensed) ───────────────────────────
    doctrine_lines = [
        "Follow these production principles without exception:",
        "• Authenticity over polish: real imperfection beats slick performance. "
        "If it sounds like a political ad, rewrite it.",
        "• Data as drama: the statistic is the most dramatic thing in the script. "
        "State it. Pause. Let it land. Do not embed it in a sentence.",
        "• Silence as editorial power: pauses ARE the persuasion. "
        "A script that fills every second is a script that persuades no one.",
        "• Underwriting: after every key text card or statement, leave space. "
        "If the script reads full on paper, it will play crowded.",
        "• No false resolution: end in irresolution that requires action, "
        "not comfortable closure. The audience should feel the unfinished work.",
    ]
    if is_video:
        doctrine_lines.append(
            "• Silent Track: text cards must carry the COMPLETE argument for viewers "
            "watching without audio. Design the text card sequence first."
        )
    if is_radio:
        doctrine_lines.append(
            "• Radio: every claim must stand on audio alone. No visual crutch. "
            "Concrete images in words. The listener's imagination is your production budget."
        )
    doctrine_block = "\n".join(doctrine_lines)

    # ── Format output spec ─────────────────────────────────────────
    if is_video:
        output_spec = f"""Write the script in this exact format:

AUDIO: [Spoken words only. {word_limit} words MAXIMUM — count strictly.]
VIDEO: [Shot-by-shot visual description. One line per shot. Real, shootable images only.]
TEXT CARDS: [On-screen text. One card per line. EVERY card ≤ 7 words. No exceptions.]
SILENT TRACK: [1-2 sentences: music tone, tempo, sound design. Specific enough to brief a composer.]

Then write:
RULE CHECK:
• Rule 1 (Concession-First): [quote the opening line — does it concede the opponent's strongest point?]
• Rule 3 (7-word cards): [list any cards over limit, or confirm all pass]
• Rule 5 (Villain): [confirm opponent is implied but not named]
• Rule 6 (Bookend): [what is the bookend word, open meaning → close meaning]
• Silent Track: [can the text card sequence alone carry the argument? yes/no]
• Word count: [exact count of AUDIO words]"""

    elif is_radio:
        output_spec = f"""Write the script in this exact format:

AUDIO: [All spoken words. {word_limit} words MAXIMUM — count strictly. Every word earns its place.]
PRODUCTION NOTE: [1-2 sentences: casting direction, music/SFX, pacing note. What does the booth need to know?]

Then write:
RULE CHECK:
• Rule 1 (Concession-First): [quote the opening line]
• Rule 6 (Bookend): [bookend word, open meaning → close meaning]
• Word count: [exact count of AUDIO words]"""

    else:  # Corporate
        output_spec = f"""Write the script in this exact format:

AUDIO: [Spoken words. Target {word_limit} words.]
FORMAT NOTES: [Any production guidance for this format.]

RULE CHECK:
• Rule 1 (Concession-First): [quote the opening line]
• Rule 6 (Bookend): [bookend word, open meaning → close meaning]"""

    # ── Assemble full prompt ───────────────────────────────────────
    prompt_parts = [
        "You are writing a political advertising script. "
        "This is professional campaign media — not content marketing, not a public affairs memo. "
        "Follow every constraint below exactly. No decoration. No hedging.",
        "",
        "=" * 60,
        f"FORMAT: {selected_format}",
        f"AUDIO WORD LIMIT: {word_limit} words (strict — TV and radio run to the clock)",
        "",
        f"REGISTER: {reg_name}",
        reg_description,
        "",
    ]

    if reg_characteristics:
        prompt_parts += [
            "Register characteristics (this piece must exhibit these):",
            *[f"  • {c}" for c in reg_characteristics],
            "",
        ]

    prompt_parts += [
        "=" * 60,
        doctrine_block,
        "",
        "=" * 60,
        "SIGNATURE RULES — all must be followed:",
        "",
        "RULE 1 — CONCESSION-FIRST:",
        "Never open on your own side. The first words acknowledge the strongest thing the other side would say.",
        f"Rule 1 variant for this register: {r1_name}",
        f"  {r1_desc}",
        "  If the opening line would ONLY resonate with supporters, Rule 1 is not active. Rewrite.",
        "",
        "RULE 2 — B-ROLL AS EVIDENCE:",
        "Every visual claim requires a real, shootable image. No stock clichés. No vague 'community' footage.",
        "",
        "RULE 3 — 7-WORD TEXT CARD LIMIT:",
        "Every on-screen text card is 7 words or fewer. No exceptions. Count every word.",
        "",
        "RULE 4 — TEXT CARD + PAUSE = THE MOVE:",
        "A text card is not a headline. It appears, holds, and disappears. The hold IS the persuasion. "
        "Do not stack cards. Do not rush them.",
        "",
        "RULE 5 — VILLAIN IMPLIED, NEVER NAMED:",
        "The opposition, the system, the bad actor — referenced through context and implication only. "
        "Naming creates sympathy and shifts attention. The listener already knows who you mean.",
        "",
        "RULE 6 — BOOKEND:",
        "The piece ends on the same word it opened with, but the meaning has deepened through the argument. "
        "OPEN MEANING → argument built → CLOSE MEANING (transformed). "
        "This is not wordplay. This is structural logic.",
        "",
        "=" * 60,
        "DATA ANCHOR (state this verbatim somewhere in the first third):",
        f'  "{anchor_text}"',
        "",
        "USAGE: The number stands alone. State it plainly. Silence. Then pivot.",
        "Do NOT embed it in a longer sentence. Do NOT soften it with qualifiers.",
        "The data IS the drama.",
        "",
        "=" * 60,
        f"TOPIC: {topic_label}",
        f"PERSUASION TIER: {tier}",
        f"TIER STRATEGY: {tier_role}",
        "",
        f"AUDIENCE: {audience}",
    ]

    if audience_rationale:
        prompt_parts.append(f"  {audience_rationale}")

    prompt_parts += [""]

    if r_pct is not None and d_pct is not None:
        prompt_parts += [
            "PARTY SPLITS:",
            f"  Republican support: {round(r_pct)}%   Democrat support: {round(d_pct)}%   Overall: {round(live_pct) if live_pct else '—'}%",
            f"  {partisan_note}",
            "",
        ]

    if state_context:
        prompt_parts += [state_context, ""]

    if words_work:
        prompt_parts += [
            "LANGUAGE THAT WORKS (use these exact phrases or close synonyms):",
            *[f"  • {w}" for w in words_work],
            "",
        ]

    if words_avoid:
        prompt_parts += [
            "LANGUAGE TO AVOID (these trigger resistance and close minds):",
            *[f"  • {w}" for w in words_avoid],
            "",
        ]

    if frame or inoculation or cta:
        prompt_parts.append("STRATEGIC GUIDANCE:")
        if frame:
            prompt_parts.append(f"  Frame: {frame}")
        if inoculation:
            prompt_parts.append(f"  Inoculation: {inoculation}")
        if cta:
            prompt_parts.append(f"  Call to action: {cta}")
        prompt_parts.append("")

    prompt_parts += [
        "=" * 60,
        "REQUIRED STRUCTURAL MOVES (must be present, in this order):",
        _moves_block(req_moves, structural_moves),
    ]

    if opt_moves:
        prompt_parts += [
            "",
            "OPTIONAL MOVES (consider if they serve the register):",
            *[f"  ○ {m}" for m in opt_moves],
        ]

    prompt_parts.append("")

    # Source materials
    has_sources = any([bill_text.strip(), assets_text.strip(), additional_notes.strip()])
    if has_sources:
        prompt_parts.append("=" * 60)
        prompt_parts.append("SOURCE MATERIALS (incorporate if relevant):")
        if bill_text.strip():
            prompt_parts += ["", f"POLICY/BILL CONTEXT:\n{bill_text.strip()[:1200]}"]
        if assets_text.strip():
            prompt_parts += ["", f"AVAILABLE SPOKESPEOPLE/VOICES:\n{assets_text.strip()[:600]}"]
        if additional_notes.strip():
            prompt_parts += ["", f"ADDITIONAL NOTES:\n{additional_notes.strip()[:400]}"]
        prompt_parts.append("")

    prompt_parts += [
        "=" * 60,
        output_spec,
        "",
        "Write nothing outside the specified format above.",
        "Do not add preamble, explanation, or caveats. Start directly with AUDIO:",
    ]

    return "\n".join(prompt_parts)


def generate_script(
    prompt: str,
    api_key: str,
    model: str = "claude-opus-4-6",
) -> tuple[str, Optional[str]]:
    """
    Call the Anthropic API and return (script_text, error_message).

    Returns (result, None) on success, ("", error_str) on failure.
    Uses claude-opus-4-6 for best voice fidelity.
    """
    try:
        import anthropic as _anthropic
        client = _anthropic.Anthropic(api_key=api_key)
        message = client.messages.create(
            model=model,
            max_tokens=1200,
            messages=[{"role": "user", "content": prompt}],
            temperature=1.0,   # full creativity — this is art direction, not extraction
        )
        result = message.content[0].text.strip()
        return result, None
    except Exception as e:
        return "", str(e)


def parse_audio_word_count(script_text: str) -> Optional[int]:
    """Extract word count from the AUDIO: section of a generated script."""
    import re
    m = re.search(r"AUDIO:\s*(.+?)(?=\nVIDEO:|\nPRODUCTION NOTE:|\nFORMAT NOTE:|\nRULE CHECK:|$)",
                  script_text, re.DOTALL | re.IGNORECASE)
    if m:
        audio_text = m.group(1).strip()
        words = len(audio_text.split())
        return words
    return None


def flag_rule_violations(script_text: str, word_limit: int, selected_format: str) -> list[str]:
    """
    Quick heuristic check for common rule violations.
    Returns list of warning strings (empty list = no obvious issues).
    """
    import re
    warnings = []

    # Word count check
    wc = parse_audio_word_count(script_text)
    if wc and wc > word_limit + 5:  # 5-word buffer for formatting
        warnings.append(f"⚠️ AUDIO word count appears high ({wc} words vs {word_limit} limit). "
                        "Trim before production.")

    # Text card length check — find TEXT CARDS section
    tc_match = re.search(r"TEXT CARDS:\s*(.+?)(?=\nSILENT|\nRULE CHECK:|$)",
                         script_text, re.DOTALL | re.IGNORECASE)
    if tc_match:
        cards = [line.strip().strip('"').strip('"') for line in tc_match.group(1).strip().split("\n")
                 if line.strip() and not line.strip().startswith("#")]
        over_limit = [c for c in cards if c and len(c.split()) > 7]
        if over_limit:
            warnings.append(f"⚠️ Text card(s) exceed 7-word Rule 3 limit: {'; '.join(over_limit)}")

    # Rule 1 heuristic — if AUDIO doesn't open with question, but, though, even, while, etc.
    audio_match = re.search(r"AUDIO:\s*(.{0,60})", script_text, re.IGNORECASE)
    if audio_match:
        first_words = audio_match.group(1).strip().lower()
        concession_triggers = ["but ", "though", "even if", "yes, ", "some say", "critics", "many say",
                               "it's true", "fair enough", "you might", "what if", "while "]
        if not any(t in first_words for t in concession_triggers):
            warnings.append(
                "ℹ️ Opening line may not be a Rule 1 concession — check that it acknowledges the opponent's position."
            )

    return warnings
